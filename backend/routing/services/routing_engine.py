import heapq
import math
import time
import os
from .graph_builder import GraphBuilder
from .traffic_cache import TrafficCache
from ..models import Hospital

class RoutingEngine:
    VITESSE_BASE = {
        "primary": 60,
        "secondary": 45,
        "residential": 30,
        "track": 15,
        "path": 8
    }
    PENALITE_TYPE = {
        "primary": 1.0,
        "secondary": 1.1,
        "residential": 1.2,
        "track": 1.8,
        "path": 2.5
    }

    def __init__(self):
        self.graph_builder = GraphBuilder.get_instance()
        self.traffic_cache = TrafficCache.get_instance()

    def get_location_name(self, lat, lng):
        if lat > 3.90: return "Messassi / Olembé"
        if lat > 3.88:
            if lng > 11.52: return "Bastos"
            return "Etoudi"
        if lat > 3.86:
            if lng > 11.53: return "Nlongkak"
            if lng > 11.51: return "Centre-Ville"
            return "Mokolo"
        if lat > 3.84:
            if lng > 11.52: return "Mimboman / Kondengui"
            if lng > 11.50: return "Biyem-Assi"
            return "Mendong"
        return "Mvan / Ahala"

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def get_edge_cost(self, u, v, data, now_mins, vehicle_type='ambulance'):
        dist_m = data.get('distance_m', 1000)
        road_type = data.get('road_type', 'residential')
        seg_id = data.get('segment_id')
        
        # Twist 03: Profile-based passability
        # Check explicit ID match first
        if not self.traffic_cache.is_passable(seg_id, now_mins, vehicle_type):
            return 1000000.0
            
        # BRIDGE ID GAP: If no explicit ID match, use road_type heuristics
        profile_mult = 1.0
        if vehicle_type == 'fire':
            if road_type in ['residential', 'living_street', 'service']:
                profile_mult = 5.0 # Narrow street penalty for big trucks
            elif road_type in ['primary', 'trunk']:
                profile_mult = 0.8 # Trucks are faster/prefer main roads

        traffic_mult = self.traffic_cache.get_multiplier(seg_id, now_mins)
        if traffic_mult >= 99.0:
            return 1000000.0
            
        penalite_type = self.PENALITE_TYPE.get(road_type, 1.2)
        wrong_way_mult = 20.0 if data.get('is_wrong_way') else 1.0
        
        # Weather impact
        weather_mult = 1.0
        if self.traffic_cache.is_raining(seg_id, now_mins):
            weather_mult = 1.5 if vehicle_type == 'fire' else 1.2

        base_speed = 50 / 3.6
        if road_type in ['trunk', 'primary']: base_speed = 70 / 3.6
        if road_type == 'residential': base_speed = 30 / 3.6
        
        real_speed = base_speed / (traffic_mult * penalite_type * wrong_way_mult * weather_mult * profile_mult)
        return dist_m / max(real_speed, 1.0)

    def find_route(self, lat, lng, eligible_hospitals, hour, minute, vehicle_type='ambulance'):
        start_calc_time = time.time()
        G = self.graph_builder.get_graph()
        base_time_mins = hour * 60 + minute
        location_name = self.get_location_name(lat, lng)

        start_node = "START_VIRTUAL"
        target_node = "HOSPITAL_VIRTUAL"
        
        if start_node in G: G.remove_node(start_node)
        if target_node in G: G.remove_node(target_node)

        # Connect Start
        nearest_starts = self.graph_builder.find_nearest_nodes(lat, lng, k=5)
        G.add_node(start_node, lat=lat, lng=lng, is_virtual=True)
        for n in nearest_starts:
            d = self.haversine(lat, lng, G.nodes[n]['lat'], G.nodes[n]['lng'])
            G.add_edge(start_node, n, weight=d/(30/3.6), distance_m=d, is_virtual=True)

        # Connect Hospitals
        G.add_node(target_node, is_virtual=True)
        for h in eligible_hospitals:
            h_node = self.graph_builder.find_nearest_node(h.lat, h.lng)
            G.add_edge(h_node, target_node, weight=h.temps_attente_min * 60, is_virtual=True, hospital_id=h.id)

        # A* Search
        queue = [(0, 0, start_node, [])]
        visited = {}
        found_path = None
        final_cost = 0
        nodes_explored = 0

        while queue:
            priority, current_cost, current_node, path = heapq.heappop(queue)
            nodes_explored += 1
            if current_node == target_node:
                found_path = path + [current_node]
                final_cost = current_cost
                break
            if current_node in visited and visited[current_node] <= current_cost:
                continue
            visited[current_node] = current_cost
            
            if current_node in G:
                for neighbor, edge_data in G[current_node].items():
                    arrival_time_mins = base_time_mins + (current_cost / 60.0)
                    if edge_data.get('is_virtual'):
                        edge_cost = edge_data.get('weight', 0)
                    else:
                        edge_cost = self.get_edge_cost(current_node, neighbor, edge_data, arrival_time_mins, vehicle_type)
                    
                    if edge_cost >= 1000000.0: continue
                    
                    new_cost = current_cost + edge_cost
                    # Heuristic: approx distance to center (fixed point for hackathon simplicity)
                    h_val = self.haversine(G.nodes[neighbor].get('lat', lat), G.nodes[neighbor].get('lng', lng), 3.84, 11.50) / (70/3.6)
                    heapq.heappush(queue, (new_cost + h_val, new_cost, neighbor, path + [current_node]))

        duration_ms = int((time.time() - start_calc_time) * 1000)
        
        if found_path:
            h_node = found_path[-2]
            edge_data = G.get_edge_data(h_node, target_node)
            chosen_hospital_id = edge_data.get('hospital_id')
            
            coords_path = []
            for node_id in found_path:
                if node_id in G and 'lat' in G.nodes[node_id]:
                    coords_path.append([G.nodes[node_id]['lat'], G.nodes[node_id]['lng']])
            
            return coords_path, chosen_hospital_id, final_cost / 60.0, nodes_explored, duration_ms, location_name
            
        return None, 0, 0, 0, 0, location_name
