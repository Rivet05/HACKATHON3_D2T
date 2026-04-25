import json
import networkx as nx
import os
import math

class GraphBuilder:
    _instance = None
    _graph = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_graph(self, file_path):
        G = nx.DiGraph()
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        elements = data.get('elements', [])
        nodes_map = {}
        
        # 1. Parse Nodes
        for el in elements:
            if el['type'] == 'node':
                nodes_map[el['id']] = {
                    'lat': el['lat'],
                    'lng': el.get('lon') or el.get('lng')
                }
                G.add_node(el['id'], **nodes_map[el['id']])

        # 2. Parse Ways
        for el in elements:
            if el['type'] == 'way':
                way_id = el['id']
                node_ids = el['nodes']
                tags = el.get('tags', {})
                
                # Calculate distance and add edges between consecutive nodes
                for i in range(len(node_ids) - 1):
                    u, v = node_ids[i], node_ids[i+1]
                    if u in nodes_map and v in nodes_map:
                        dist = self.haversine(
                            nodes_map[u]['lat'], nodes_map[u]['lng'],
                            nodes_map[v]['lat'], nodes_map[v]['lng']
                        )
                        
                        # Store geometry as a simple list of 2 points for now 
                        # (since way segments are atomic in this model)
                        geometry = [
                            [nodes_map[u]['lng'], nodes_map[u]['lat']],
                            [nodes_map[v]['lng'], nodes_map[v]['lat']]
                        ]
                        
                        edge_props = {
                            'segment_id': str(way_id), # road_id in traffic csv
                            'distance_m': dist,
                            'road_type': tags.get('highway', 'residential'),
                            'surface': tags.get('surface', 'asphalt'),
                            'oneway': tags.get('oneway', 'no')
                        }
                        
                        G.add_edge(u, v, geometry=geometry, **edge_props)
                        
                        if edge_props['oneway'] != 'yes':
                            G.add_edge(v, u, geometry=geometry[::-1], **edge_props)
                
        self._graph = G
        return G

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000 
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def get_graph(self):
        if self._graph is None:
            # Switch to official synthetic roads file
            data_path = os.path.join(os.path.dirname(__file__), '../../data/yaounde_roads_synthetic.geojson')
            # Fallback if file doesn't exist (safety)
            if not os.path.exists(data_path):
                 data_path = os.path.join(os.path.dirname(__file__), '../../data/sample_network.geojson')
            
            self.load_graph(data_path)
        return self._graph
