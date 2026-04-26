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
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'elements' in data:
            # Format OSM JSON (Overpass)
            self._load_from_elements(G, data['elements'])
        elif 'features' in data:
            # Format GeoJSON (Standard)
            self._load_from_features(G, data['features'])
            
        self._graph = G
        return G

    def _load_from_elements(self, G, elements):
        nodes_map = {}
        for el in elements:
            if el['type'] == 'node':
                node_id = str(el['id'])
                nodes_map[node_id] = {'lat': el['lat'], 'lng': el.get('lon') or el.get('lng')}
                G.add_node(node_id, **nodes_map[node_id])

        for el in elements:
            if el['type'] == 'way':
                way_id = str(el['id'])
                node_ids = [str(nid) for nid in el['nodes']]
                tags = el.get('tags', {})
                for i in range(len(node_ids) - 1):
                    u, v = node_ids[i], node_ids[i+1]
                    if u in nodes_map and v in nodes_map:
                        self._add_edge(G, u, v, nodes_map[u], nodes_map[v], way_id, tags)

    def _load_from_features(self, G, features):
        for feat in features:
            geom = feat.get('geometry')
            if not geom: continue
            
            tags = feat.get('properties', {})
            way_id = str(feat.get('id') or tags.get('@id') or hash(str(feat)))
            
            if geom['type'] == 'LineString':
                self._process_coords(G, geom['coordinates'], way_id, tags)
            elif geom['type'] == 'MultiLineString':
                for line in geom['coordinates']:
                    self._process_coords(G, line, way_id, tags)

    def _process_coords(self, G, coords, way_id, tags):
        # In GeoJSON, we might not have node IDs, so we use coordinates as keys
        for i in range(len(coords) - 1):
            p1, p2 = coords[i], coords[i+1] # [lng, lat]
            # Rounding to 7 decimal places (~1cm) to glue nearby points
            u = f"{p1[1]:.7f},{p1[0]:.7f}"
            v = f"{p2[1]:.7f},{p2[0]:.7f}"
            
            u_data = {'lat': p1[1], 'lng': p1[0]}
            v_data = {'lat': p2[1], 'lng': p2[0]}
            
            G.add_node(u, **u_data)
            G.add_node(v, **v_data)
            self._add_edge(G, u, v, u_data, v_data, way_id, tags)

    def _add_edge(self, G, u, v, u_data, v_data, way_id, tags):
        dist = self.haversine(u_data['lat'], u_data['lng'], v_data['lat'], v_data['lng'])
        oneway = tags.get('oneway') in ['yes', 'true', '1']
        
        edge_props = {
            'segment_id': way_id,
            'distance_m': dist,
            'road_type': tags.get('highway', 'residential'),
            'surface': tags.get('surface', 'asphalt'),
            'oneway': oneway,
            'geometry': [[u_data['lng'], u_data['lat']], [v_data['lng'], v_data['lat']]]
        }
        
        G.add_edge(u, v, **edge_props)
        
        # Reverse edge
        rev_props = edge_props.copy()
        rev_props['geometry'] = edge_props['geometry'][::-1]
        
        if not oneway:
            G.add_edge(v, u, **rev_props)
        else:
            # For ambulances, a one-way is just a very "expensive" road in reverse
            # instead of a wall, to ensure connectivity in degraded states.
            rev_props['is_wrong_way'] = True
            G.add_edge(v, u, **rev_props)


    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000 
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def get_graph(self):
        if self._graph is None:
            # 1. Load the beautiful geometry from real export
            export_path = os.path.join(os.path.dirname(__file__), '../../data/export.geojson')
            synthetic_path = os.path.join(os.path.dirname(__file__), '../../data/yaounde_roads_synthetic.geojson')
            
            if os.path.exists(export_path):
                print("Loading detailed OSM geometry...")
                G = self.load_graph(export_path)
            else:
                print("Detailed export missing, falling back to synthetic...")
                G = self.load_graph(synthetic_path)
            
            self._graph = G # Set temporary for index preparation
            self._prepare_spatial_index()

            # 2. Inject official segment_ids by spatial proximity if they are different
            if os.path.exists(synthetic_path) and os.path.exists(export_path):
                print("Syncing official IDs with detailed geometry...")
                with open(synthetic_path, 'r') as f:
                    synth_data = json.load(f)
                    if 'elements' in synth_data:
                        self._merge_synthetic_ids(G, synth_data['elements'])
        return self._graph

    def _merge_synthetic_ids(self, G, elements):
        """Map synthetic road_ids to nearest edges in our detailed graph"""
        # We find coords of synthetic nodes to locate where ways are
        nodes_map = {str(el['id']): (el['lat'], el.get('lon') or el.get('lng')) for el in elements if el['type'] == 'node'}
        
        for el in elements:
            if el['type'] == 'way':
                way_id = str(el['id'])
                node_ids = [str(nid) for nid in el.get('nodes', [])]
                if len(node_ids) < 2: continue
                
                # Find the center point of this synthetic segment
                mid_node = node_ids[len(node_ids)//2]
                if mid_node in nodes_map:
                    lat, lon = nodes_map[mid_node]
                    # Find nearest node in our detailed graph
                    target_u = self.find_nearest_node(lat, lon)
                    # Find edges connected to this node and tag them
                    if target_u in G:
                        for neighbor in G[target_u]:
                            G[target_u][neighbor]['segment_id'] = way_id
                        # Also tag incoming
                        for prev in G.predecessors(target_u):
                            G[prev][target_u]['segment_id'] = way_id

    def _prepare_spatial_index(self):
        import numpy as np
        nodes_data = []
        node_ids = []
        for node, data in self._graph.nodes(data=True):
            if 'lat' in data and 'lng' in data:
                nodes_data.append([data['lat'], data['lng']])
                node_ids.append(node)
        
        self._nodes_coords = np.array(nodes_data)
        self._node_ids_array = node_ids

    def find_nearest_node(self, lat, lng):
        import numpy as np
        if not hasattr(self, '_nodes_coords'):
            self._prepare_spatial_index()
            
        point = np.array([lat, lng])
        dists = np.sum((self._nodes_coords - point)**2, axis=1)
        nearest_idx = np.argmin(dists)
        return self._node_ids_array[nearest_idx]

    def find_nearest_nodes(self, lat, lng, k=5):
        import numpy as np
        if not hasattr(self, '_nodes_coords'):
            self._prepare_spatial_index()
            
        point = np.array([lat, lng])
        dists = np.sum((self._nodes_coords - point)**2, axis=1)
        # Get top k nearest indices using partition (faster than full sort)
        k = min(k, len(dists))
        nearest_indices = np.argpartition(dists, k-1)[:k]
        # Sort these k points by actual distance
        nearest_indices = nearest_indices[np.argsort(dists[nearest_indices])]
        return [self._node_ids_array[idx] for idx in nearest_indices]


