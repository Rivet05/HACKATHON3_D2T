import csv
import os

class TrafficLoader:
    _instance = None
    _traffic_data = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_traffic(self, csv_path):
        traffic = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Detection du dialecte ou forcer tabulation selon ton exemple
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                road_id = row.get('road_id') or row.get('segment_id')
                if not road_id: continue
                
                hour = int(row['hour'])
                multiplier = float(row['travel_time_multiplier'])
                
                if road_id not in traffic:
                    traffic[road_id] = {}
                traffic[road_id][hour] = multiplier
                
        self._traffic_data = traffic
        return traffic

    def get_multiplier(self, segment_id, hour):
        if not self._traffic_data:
            self.get_all_traffic()
        
        # segment_id in graph is string type of road_id
        return self._traffic_data.get(str(segment_id), {}).get(hour, 1.0)

    def get_all_traffic(self):
        if not self._traffic_data:
            data_path = os.path.join(os.path.dirname(__file__), '../../data/traffic_by_segment_hour.csv')
            if not os.path.exists(data_path):
                data_path = os.path.join(os.path.dirname(__file__), '../../data/sample_traffic.csv')
            self.load_traffic(data_path)
        return self._traffic_data
