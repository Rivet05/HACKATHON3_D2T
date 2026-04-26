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

    def get_edge_cost(self, u, v, data, now_mins, vehicle_type='ambulance', is_counter_flow=False):
        dist_m = data.get('distance_m', 1000)
        road_type = data.get('road_type', 'residential')
        seg_id = data.get('segment_id')
        
        if not self.traffic_cache.is_passable(seg_id, now_mins, vehicle_type):
            return 1000000.0
            
        # Twist 04 & 05 Survival: Never return infinity for blockages, just very high cost
        traffic_mult = self.traffic_cache.get_multiplier(seg_id, now_mins)
        if traffic_mult >= 99.0:
            traffic_mult = 500.0 # High cost but not infinite
            
        penalite_type = self.PENALITE_TYPE.get(road_type, 1.2)
        
        # Twist 05 Simulation: Sens interdit autorisé avec pénalité massive (x50) pour survie
        wrong_way_mult = 50.0 if is_counter_flow else (20.0 if data.get('is_wrong_way') else 1.0)
        
        weather_mult = 1.0
        if self.traffic_cache.is_raining(seg_id, now_mins):
            weather_mult = 1.5 if vehicle_type == 'fire' else 1.2

        base_speed = 50 / 3.6
        if road_type in ['trunk', 'primary']: base_speed = 70 / 3.6
        
        real_speed = base_speed / (traffic_mult * penalite_type * wrong_way_mult * weather_mult)
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

        queue = [(0, 0, 0, start_node, None, [])] # priority, current_cost, current_var, node, prev_node, path
        visited = {} # (node, prev_node) -> (cost, variance)
        found_path = None
        final_cost = 0
        final_variance = 0
        nodes_explored = 0

        while queue:
            priority, current_cost, current_var, current_node, prev_node, path = heapq.heappop(queue)
            nodes_explored += 1
            
            if current_node == target_node:
                found_path = path + [current_node]
                final_cost = current_cost
                final_variance = current_var
                break
                
            state = (current_node, prev_node)
            if state in visited and visited[state][0] <= current_cost:
                continue
            visited[state] = (current_cost, current_var)
            
            if current_node in G:
                for neighbor, edge_data in G[current_node].items():
                    arrival_time_mins = base_time_mins + (current_cost / 60.0)
                    
                    # Twist 07: TURN COSTS
                    turn_penalty = 0
                    if prev_node and prev_node in G and neighbor in G:
                        # Simple Angle Calculation
                        p = G.nodes[prev_node]
                        c = G.nodes[current_node]
                        n = G.nodes[neighbor]
                        if all(k in p and k in c and k in n for k in ['lat', 'lng']):
                            # Vectors
                            v1 = (c['lat'] - p['lat'], c['lng'] - p['lng'])
                            v2 = (n['lat'] - c['lat'], n['lng'] - c['lng'])
                            # Dot product for cosine
                            dot = v1[0]*v2[0] + v1[1]*v2[1]
                            mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
                            mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
                            if mag1 > 0 and mag2 > 0:
                                cos_theta = max(-1, min(1, dot / (mag1 * mag2)))
                                angle = math.degrees(math.acos(cos_theta))
                                if angle > 45: # Significant turn
                                    turn_penalty = 15.0 # 15s penalty
                                if angle > 90: # Sharp turn / U-turn
                                    turn_penalty = 45.0 # 45s penalty
                    
                    if edge_data.get('is_virtual'):
                        edge_cost = edge_data.get('weight', 0)
                        edge_var = 0
                    else:
                        edge_cost = self.get_edge_cost(current_node, neighbor, edge_data, arrival_time_mins, vehicle_type) + turn_penalty
                        # Twist 06/07: Uncertainty increases with complexity of maneuver
                        traffic_mult = edge_data.get('traffic_multiplier', 1.0)
                        edge_var = (edge_cost * 0.1) * traffic_mult * (2.0 if turn_penalty > 0 else 1.0)
                    
                    if edge_cost < 1000000.0:
                        new_cost = current_cost + edge_cost
                        new_var = current_var + (edge_var ** 2)
                        h_val = self.haversine(G.nodes[neighbor].get('lat', lat), G.nodes[neighbor].get('lng', lng), 3.84, 11.5) / (70/3.6)
                        heapq.heappush(queue, (new_cost + h_val, new_cost, new_var, neighbor, current_node, path + [current_node]))

                # 2. Bypass d'urgence (Predecessors = Counter-flow)
                for neighbor in G.predecessors(current_node):
                    if neighbor in G[current_node]: continue
                    edge_data = G.get_edge_data(neighbor, current_node)
                    arrival_time_mins = base_time_mins + (current_cost / 60.0)
                    edge_cost = self.get_edge_cost(neighbor, current_node, edge_data, arrival_time_mins, vehicle_type, is_counter_flow=True)
                    
                    if edge_cost < 1000000.0:
                        new_cost = current_cost + edge_cost
                        new_var = current_var + (edge_cost * 0.2) ** 2 # Higher uncertainty in counter-flow
                        h_val = self.haversine(G.nodes[neighbor].get('lat', lat), G.nodes[neighbor].get('lng', lng), 3.84, 11.5) / (70/3.6)
                        heapq.heappush(queue, (new_cost + h_val, new_cost, new_var, neighbor, current_node, path + [current_node]))

        duration_ms = int((time.time() - start_calc_time) * 1000)
        
        if found_path:
            coords_path = []
            segment_ids = []
            for node_id in found_path:
                if node_id in G and 'lat' in G.nodes[node_id]:
                    coords_path.append([G.nodes[node_id]['lat'], G.nodes[node_id]['lng']])
            
            # Extract segment IDs
            for i in range(len(found_path)-1):
                u, v = found_path[i], found_path[i+1]
                edge_data = G.get_edge_data(u, v) or G.get_edge_data(v, u) # Fallback for counter-flow
                if edge_data and 'segment_id' in edge_data:
                    segment_ids.append(edge_data['segment_id'])
            
            # Find chosen hospital
            h_node = found_path[-2]
            edge_to_target = G.get_edge_data(h_node, target_node)
            hospital_id = edge_to_target.get('hospital_id') if edge_to_target else None

            total_sd = math.sqrt(final_variance)
            return coords_path, hospital_id, final_cost / 60.0, nodes_explored, duration_ms, location_name, segment_ids, total_sd / 60.0
            
        return None, None, 0, 0, 0, location_name, [], 0
