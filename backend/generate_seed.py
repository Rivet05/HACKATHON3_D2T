import json
import random
import csv

def get_curved_coords(c1, c2):
    """Add a random intermediate point to create a curve."""
    lng1, lat1 = c1
    lng2, lat2 = c2
    
    # Midpoint
    mid_lng = (lng1 + lng2) / 2
    mid_lat = (lat1 + lat2) / 2
    
    # Add random offset (approx 50-100m)
    offset_lng = random.uniform(-0.001, 0.001)
    offset_lat = random.uniform(-0.001, 0.001)
    
    return [c1, [mid_lng + offset_lng, mid_lat + offset_lat], c2]

def generate_data():
    nodes = []
    edges = []
    
    # Base coordinates for Yaounde
    base_lat, base_lng = 3.848, 11.502
    
    # Create nodes with some jitter (so it's not a perfect grid)
    cols, rows = 7, 8
    for i in range(rows):
        for j in range(cols):
            node_id = f"node_{i*cols + j}"
            lat = base_lat + (i * 0.01) + random.uniform(-0.002, 0.002)
            lng = base_lng + (j * 0.01) + random.uniform(-0.002, 0.002)
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
            u_idx = i*cols + j
            u_id = f"node_{u_idx}"
            
            # Connect to right
            if j < cols - 1:
                v_idx = i*cols + (j + 1)
                v_id = f"node_{v_idx}"
                seg_id = f"seg_{segment_id_counter}"
                rt = random.choice(road_types)
                
                coords = get_curved_coords(nodes[u_idx]["geometry"]["coordinates"], nodes[v_idx]["geometry"]["coordinates"])
                
                edges.append({
                    "type": "Feature",
                    "geometry": { "type": "LineString", "coordinates": coords },
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
                v_idx = (i+1)*cols + j
                v_id = f"node_{v_idx}"
                seg_id = f"seg_{segment_id_counter}"
                rt = random.choice(road_types)
                
                coords = get_curved_coords(nodes[u_idx]["geometry"]["coordinates"], nodes[v_idx]["geometry"]["coordinates"])
                
                edges.append({
                    "type": "Feature",
                    "geometry": { "type": "LineString", "coordinates": coords },
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
                if (7 <= h <= 9) or (17 <= h <= 19):
                    multiplier = round(random.uniform(1.8, 2.8), 2)
                else:
                    multiplier = round(random.uniform(1.0, 1.3), 2)
                row.append(multiplier)
            writer.writerow(row)

if __name__ == "__main__":
    generate_data()
