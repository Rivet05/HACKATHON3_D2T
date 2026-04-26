import heapq
import math
import time
from .graph_builder import GraphBuilder
from .traffic_cache import TrafficCache

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
        if lat > 3.87:
            return "Etoudi / Bastos" if lng > 11.51 else "Bastos / Golf"
        elif lat > 3.84:
            return "Centre-Ville / Messa" if lng > 11.51 else "Mokolo / Madagascar"
        else:
            return "Mvan / Ekounou" if lng > 11.51 else "Biyem-Assi / Mendong"

    def get_edge_cost(self, u, v, data, now_mins):
        dist_m = data.get('distance_m', 1000)
        road_type = data.get('road_type', 'residential')
        seg_id = data.get('segment_id')
        
        vitesse_kmh = self.VITESSE_BASE.get(road_type, 30)
        
        # African Reality: Penalty for unpaved surfaces
        surface = data.get('surface', 'asphalt')
        if surface in ['unpaved', 'dirt', 'gravel', 'ground']:
            vitesse_kmh = min(vitesse_kmh, 20) 
            
        vitesse_ms = vitesse_kmh / 3.6
        temps_pur_min = (dist_m / vitesse_ms) / 60
        
        # Twist 02: Use TrafficCache with actual time at segment
        traffic_mult = self.traffic_cache.get_multiplier(seg_id, now_mins)
        
        # Extreme blockage injection (Twist 02)
        if traffic_mult >= 99.0:
            return 9999.0 # Effectively blocked
            
        penalite_type = self.PENALITE_TYPE.get(road_type, 1.2)
        wrong_way_mult = 20.0 if data.get('is_wrong_way') else 1.0
        
        return temps_pur_min * traffic_mult * penalite_type * wrong_way_mult

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000  # radius of Earth in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def find_route(self, start_lat, start_lng, eligible_hospitals, hour_start, min_start=0):
        G = self.graph_builder.get_graph()
        base_time_mins = hour_start * 60 + min_start
        
        # 1. Multi-retry nearest node search
        potential_starts = self.graph_builder.find_nearest_nodes(start_lat, start_lng, k=5)
        
        if not potential_starts:
            return None, 0, 0, 0, 0, "Lieu inconnu"
            
        location_name = self.get_location_name(start_lat, start_lng)
        dest_node = "HOPITAL_DEST"
        
        # 2. Add virtual super-node
        v_edges = []
        try:
            for h in eligible_hospitals:
                G.add_edge(h.node_id, dest_node, weight=h.temps_attente_min, is_virtual=True)
                v_edges.append((h.node_id, dest_node))

            # 3. Time-Dependent A* implementation
            max_speed_mpm = (60 / 3.6) * 60 
            h_coords = [(h.lat, h.lng) for h in eligible_hospitals]
            k_lat, k_lng = 111000, 111000 * 0.997
            
            def heuristic(n):
                if n == dest_node: return 0
                node_data = G.nodes[n]
                if 'lat' not in node_data: return 0 
                n_lat, n_lng = node_data['lat'], node_data['lng']
                min_m_dist = min(math.sqrt((k_lat*(n_lat-hlat))**2 + (k_lng*(n_lng-hlng))**2) for hlat, hlng in h_coords)
                return min_m_dist / max_speed_mpm

            found_path, final_cost, nodes_explored = None, 0, 0
            start_calc_time = time.time()
            
            for start_node in potential_starts:
                queue = [(0, start_node, 0, [])]
                visited = {start_node: 0}
                
                while queue:
                    if time.time() - start_calc_time > 60.0:
                        break
                         
                    (priority, current_node, current_cost, path) = heapq.heappop(queue)
                    nodes_explored += 1
                    
                    if current_node == dest_node:
                        found_path = path + [current_node]
                        final_cost = current_cost
                        break
                        
                    for neighbor, edge_data in G[current_node].items():
                        # TWIST 02: Arrival time at THIS neighbor
                        arrival_time_mins = base_time_mins + current_cost
                        
                        if edge_data.get('is_virtual'):
                            edge_cost = edge_data['weight']
                        else:
                            edge_cost = self.get_edge_cost(current_node, neighbor, edge_data, arrival_time_mins)
                            
                        total_cost = current_cost + edge_cost
                        
                        if neighbor not in visited or visited[neighbor] > total_cost:
                            visited[neighbor] = total_cost
                            h_val = heuristic(neighbor)
                            heapq.heappush(queue, (total_cost + h_val, neighbor, total_cost, path + [current_node]))
                
                if found_path: break

        finally:
            # 4. Cleanup
            for u, v in v_edges:
                if G.has_edge(u, v): G.remove_edge(u, v)
            if G.has_node(dest_node): G.remove_node(dest_node)


        
        end_time = time.time()
        duration_ms = int((end_time - start_calc_time) * 1000)
        
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
            
            for i in range(len(found_path) - 2): # exclude virtual node and its predecessor
                u, v = found_path[i], found_path[i+1]
                edge_data = G.get_edge_data(u, v)
                
                if edge_data and 'geometry' in edge_data:
                    # Collect all points except the last one to avoid duplicates with next edge
                    for lng, lat in edge_data['geometry'][:-1]:
                        coords_path.append([lat, lng])
                else:
                    # Fallback to node if no geometry
                    node_data = G.nodes[u]
                    coords_path.append([node_data['lat'], node_data['lng']])
            
            # Add the very last node (the hospital node)
            last_real_node = found_path[-2]
            node_data = G.nodes[last_real_node]
            coords_path.append([node_data['lat'], node_data['lng']])
                
        return coords_path, chosen_hospital_id, final_cost, nodes_explored, duration_ms, location_name
