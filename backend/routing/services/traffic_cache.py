import csv
import os
import time
from datetime import datetime

class TrafficCache:
    _instance = None
    _slots = {} # { road_id: [multipliers for 288 slots] }
    _last_update = {} # { road_id: timestamp }
    _fifo_violations = 0

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.load_from_csv()

    def load_from_csv(self):
        data_path = os.path.join(os.path.dirname(__file__), '../../data/traffic_by_segment_hour.csv')
        if not os.path.exists(data_path):
            return

        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                road_id = str(row.get('road_id') or row.get('segment_id'))
                hour = int(row['hour'])
                mult = float(row['travel_time_multiplier'])
                
                if road_id not in self._slots:
                    self._slots[road_id] = [1.0] * 288
                
                # Fill the 12 slots for this hour
                for slot_offset in range(12):
                    self._slots[road_id][hour * 12 + slot_offset] = mult
                
                self._last_update[road_id] = time.time()
        
        self.smooth_fifo()

    def smooth_fifo(self):
        """
        Garantit que partir plus tard ne fait pas arriver plus tôt.
        Si slot[t] + cost[t] > slot[t+1] + cost[t+1] ... lissage.
        Pour simplifier en hackathon : slot[t] = max(slot[t], slot[t+1]*0.98) 
        (le trafic ne peut pas s'évaporer instantanément de façon non-physique)
        """
        self._fifo_violations = 0
        for road_id, slots in self._slots.items():
            for t in range(287, 0, -1):
                if slots[t-1] > slots[t] * 1.2: # Chute brutale > 20%
                    slots[t-1] = slots[t] * 1.1
                    self._fifo_violations += 1

    def update_segment(self, road_id, slot_idx, multiplier):
        road_id = str(road_id)
        if road_id not in self._slots:
            self._slots[road_id] = [1.0] * 288
            
        self._slots[road_id][slot_idx] = multiplier
        self._last_update[road_id] = time.time()


    def get_multiplier(self, road_id, time_mins):
        slot_idx = int((time_mins % 1440) / 5)
        road_id = str(road_id)
        
        if road_id not in self._slots:
            return 1.0
            
        multiplier = self._slots[road_id][slot_idx]
        if multiplier >= 99.0:
            print(f"!!! ENGINE DETECTED BLOCKAGE ON {road_id} !!!")
        return multiplier


    def get_stats(self):
        now = time.time()
        ages = [now - t for t in self._last_update.values()]
        avg_age = sum(ages) / len(ages) if ages else 0
        staleness_count = sum(1 for a in ages if a > 900) # > 15min
        
        return {
            "slots_utilises": len(self._slots),
            "age_moyen_secondes": int(avg_age),
            "slots_perimes": staleness_count,
            "confiance_globale": max(0, 1.0 - (staleness_count / len(self._slots))) if self._slots else 1.0,
            "fifo_violations_lissées": self._fifo_violations
        }
