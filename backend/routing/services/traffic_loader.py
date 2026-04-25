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
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                seg_id = row['segment_id']
                traffic[seg_id] = {int(k.split('_')[1]): float(v) for k, v in row.items() if k.startswith('hour_')}
        self._traffic_data = traffic
        return traffic

    def get_multiplier(self, segment_id, hour):
        if not self._traffic_data:
            self.get_all_traffic()
        return self._traffic_data.get(segment_id, {}).get(hour, 1.0)

    def get_all_traffic(self):
        if not self._traffic_data:
            data_path = os.path.join(os.path.dirname(__file__), '../../data/sample_traffic.csv')
            self.load_traffic(data_path)
        return self._traffic_data
