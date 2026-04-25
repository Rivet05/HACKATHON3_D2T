import heapq
import math
import time
import networkx as nx
from .graph_builder import GraphBuilder
from .traffic_loader import TrafficLoader

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
        self.traffic_loader = TrafficLoader.get_instance()

    def get_location_name(self, lat, lng):
        if lat > 3.87:
            return "Etoudi / Bastos" if lng > 11.51 else "Bastos / Golf"
        elif lat > 3.84:
            return "Centre-Ville / Messa" if lng > 11.51 else "Mokolo / Madagascar"
        else:
            return "Mvan / Ekounou" if lng > 11.51 else "Biyem-Assi / Mendong"

    def get_edge_cost(self, u, v, data, hour):
        dist_m = data.get('distance_m', 1000)
        road_type = data.get('road_type', 'residential')
        seg_id = data.get('segment_id')
        
        vitesse_kmh = self.VITESSE_BASE.get(road_type, 30)
        vitesse_ms = vitesse_kmh / 3.6
        
        temps_pur_s = dist_m / vitesse_ms
        temps_pur_min = temps_pur_s / 60
        
        traffic_mult = self.traffic_loader.get_multiplier(seg_id, hour)
        penalite = self.PENALITE_TYPE.get(road_type, 1.2)
        
        return temps_pur_min * traffic_mult * penalite

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000  # radius of Earth in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def find_route(self, start_lat, start_lng, eligible_hospitals, hour):
        G = self.graph_builder.get_graph()
        
        # 1. Find nearest node to start
        start_node = None
        min_dist = float('inf')
        for node, data in G.nodes(data=True):
            d = self.haversine(start_lat, start_lng, data['lat'], data['lng'])
            if d < min_dist:
                min_dist = d
                start_node = node
        
        if not start_node:
            return None, 0, 0, 0, 0, "Lieu inconnu"
            
        location_name = self.get_location_name(start_lat, start_lng)
            
        # 2. Add virtual super-node "HOPITAL_DEST"
        dest_node = "HOPITAL_DEST"
        v_edges = []
        for h in eligible_hospitals:
            # Join hospital node to super-node with weight = waiting time
            # Note: G is a DiGraph, so we add edge FROM hospital TO super-node or vice versa?
            # We want to go FROM start TO super-node. 
            # So start -> ... -> hospital -> super-node.
            G.add_edge(h.node_id, dest_node, weight=h.temps_attente_min, is_virtual=True)
            v_edges.append((h.node_id, dest_node))

        # 3. Custom A* implementation
        # Heuristic: min haversine dist to any eligible hospital / (max speed / 60)
        max_speed_mpm = (60 / 3.6) * 60 # primary speed in meters per minute
        
        def heuristic(n):
            if n == dest_node: return 0
            node_data = G.nodes[n]
            min_h_dist = float('inf')
            for h in eligible_hospitals:
                d = self.haversine(node_data['lat'], node_data['lng'], h.lat, h.lng)
                if d < min_h_dist:
                    min_h_dist = d
            return (min_h_dist / max_speed_mpm)

        start_time = time.time()
        
        queue = [(0, start_node, 0, [])]
        visited = {}
        nodes_explored = 0
        
        found_path = None
        final_cost = 0
        
        while queue:
            (priority, current_node, current_cost, path) = heapq.heappop(queue)
            nodes_explored += 1
            
            if current_node in visited and visited[current_node] <= current_cost:
                continue
                
            visited[current_node] = current_cost
            new_path = path + [current_node]
            
            if current_node == dest_node:
                found_path = new_path
                final_cost = current_cost
                break
                
            for neighbor, edge_data in G[current_node].items():
                if edge_data.get('is_virtual'):
                    edge_cost = edge_data['weight']
                else:
                    edge_cost = self.get_edge_cost(current_node, neighbor, edge_data, hour)
                
                total_cost = current_cost + edge_cost
                if neighbor not in visited or visited[neighbor] > total_cost:
                    h_val = heuristic(neighbor)
                    heapq.heappush(queue, (total_cost + h_val, neighbor, total_cost, new_path))

        # 4. Cleanup virtual node
        for u, v in v_edges:
            G.remove_edge(u, v)
        G.remove_node(dest_node)
        
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        
        # Convert path to GeoJSON/Coords
        coords_path = []
        chosen_hospital_id = None
        
        if found_path:
            # The second to last node is the hospital node_id
            hospital_node_id = found_path[-2]
            for h in eligible_hospitals:
                if h.node_id == hospital_node_id:
                    chosen_hospital_id = h.id
                    break
            
            for node_id in found_path[:-1]: # exclude virtual node
                node_data = G.nodes[node_id]
                coords_path.append([node_data['lat'], node_data['lng']])
                
        return coords_path, chosen_hospital_id, final_cost, nodes_explored, duration_ms, location_name
