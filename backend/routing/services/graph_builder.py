import json
import networkx as nx
import os

class GraphBuilder:
    _instance = None
    _graph = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_graph(self, geojson_path):
        G = nx.DiGraph()
        
        with open(geojson_path, 'r') as f:
            data = json.load(f)
            
        for feature in data['features']:
            geom = feature['geometry']
            props = feature['properties']
            
            if geom['type'] == 'Point':
                node_id = props['id']
                lng, lat = geom['coordinates']
                G.add_node(node_id, lat=lat, lng=lng)
                
            elif geom['type'] == 'LineString':
                u = props['u']
                v = props['v']
                G.add_edge(u, v, **props)
                # Bi-directional for simplicity in this MVP
                G.add_edge(v, u, **props)
                
        self._graph = G
        return G

    def get_graph(self):
        if self._graph is None:
            # Default path for convenience
            data_path = os.path.join(os.path.dirname(__file__), '../../data/sample_network.geojson')
            self.load_graph(data_path)
        return self._graph
