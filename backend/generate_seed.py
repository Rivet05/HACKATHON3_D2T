import json
import random
import csv

def generate_data():
    nodes = []
    edges = []
    
    # Base coordinates for Yaounde
    base_lat, base_lng = 3.848, 11.502
    
    # Create nodes in a grid
    cols, rows = 7, 8  # ~56 nodes
    for i in range(rows):
        for j in range(cols):
            node_id = f"node_{i*cols + j}"
            lat = base_lat + (i * 0.01)
            lng = base_lng + (j * 0.01)
            nodes.append({
                "type": "Feature",
                "id": node_id,
                "geometry": { "type": "Point", "coordinates": [lng, lat] },
                "properties": { "id": node_id }
            })

    # Create edges
    segment_id_counter = 1
    road_types = ["primary", "secondary", "residential", "track"]
    
    for i in range(rows):
        for j in range(cols):
            u_id = f"node_{i*cols + j}"
            
            # Connect to right
            if j < cols - 1:
                v_id = f"node_{i*cols + j + 1}"
                seg_id = f"seg_{segment_id_counter}"
                rt = random.choice(road_types)
                edges.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            nodes[i*cols + j]["geometry"]["coordinates"],
                            nodes[i*cols + j + 1]["geometry"]["coordinates"]
                        ]
                    },
                    "properties": {
                        "segment_id": seg_id,
                        "u": u_id,
                        "v": v_id,
                        "distance_m": random.randint(800, 1500),
                        "road_type": rt
                    }
                })
                segment_id_counter += 1
            
            # Connect to down
            if i < rows - 1:
                v_id = f"node_{(i+1)*cols + j}"
                seg_id = f"seg_{segment_id_counter}"
                rt = random.choice(road_types)
                edges.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            nodes[i*cols + j]["geometry"]["coordinates"],
                            nodes[(i+1)*cols + j]["geometry"]["coordinates"]
                        ]
                    },
                    "properties": {
                        "segment_id": seg_id,
                        "u": u_id,
                        "v": v_id,
                        "distance_m": random.randint(800, 1500),
                        "road_type": rt
                    }
                })
                segment_id_counter += 1

    geojson = {
        "type": "FeatureCollection",
        "features": nodes + edges
    }
    
    with open('data/sample_network.geojson', 'w') as f:
        json.dump(geojson, f, indent=2)

    # Traffic CSV
    with open('data/sample_traffic.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        header = ["segment_id"] + [f"hour_{i}" for i in range(24)]
        writer.writerow(header)
        
        for edge in edges:
            seg_id = edge["properties"]["segment_id"]
            row = [seg_id]
            for h in range(24):
                # Peak hours: 7-9 and 17-19
                if (7 <= h <= 9) or (17 <= h <= 19):
                    multiplier = round(random.uniform(1.8, 2.8), 2)
                else:
                    multiplier = round(random.uniform(1.0, 1.3), 2)
                row.append(multiplier)
            writer.writerow(row)

if __name__ == "__main__":
    generate_data()
