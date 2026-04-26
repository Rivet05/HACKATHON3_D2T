import csv
import os
import time
from datetime import datetime

class TrafficCache:
    _instance = None
    _slots = {} 
    _passable_amb = {}
    _passable_fire = {}
    _rain = {}
    _last_update = {}
    _fifo_violations = 0
    _initialized = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if TrafficCache._initialized:
            return
        TrafficCache._initialized = True
        print("!!! TRAFFIC CACHE GLOBAL INITIALIZATION !!!")
        self.load_from_csv()

    @classmethod
    def load_from_csv(cls):
        data_path = os.path.join(os.path.dirname(__file__), '../../data/traffic_by_segment_hour.csv')
        if not os.path.exists(data_path): return

        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                road_id = str(row.get('road_id') or row.get('segment_id'))
                hour = int(row['hour'])
                mult = float(row.get('travel_time_multiplier', 1.0))
                is_amb = row.get('passable_ambulance', 'oui').lower() == 'oui'
                is_fire = row.get('passable_firetruck', 'oui').lower() == 'oui'
                is_rain = row.get('rain', 'non').lower() == 'oui'
                
                if road_id not in cls._slots:
                    cls._slots[road_id] = [1.0] * 288
                    cls._passable_amb[road_id] = [True] * 288
                    cls._passable_fire[road_id] = [True] * 288
                    cls._rain[road_id] = [False] * 288
                
                for m5 in range(12):
                    idx = (hour * 12) + m5
                    if idx < 288:
                        cls._slots[road_id][idx] = mult
                        cls._passable_amb[road_id][idx] = is_amb
                        cls._passable_fire[road_id][idx] = is_fire
                        cls._rain[road_id][idx] = is_rain
                cls._last_update[road_id] = time.time()
        cls.smooth_fifo()

    @classmethod
    def smooth_fifo(cls):
        cls._fifo_violations = 0
        for road_id, slots in cls._slots.items():
            for t in range(287, 0, -1):
                # Only smooth if NOT a blockage
                if slots[t-1] < 99.0 and slots[t] < 99.0:
                    if slots[t-1] > slots[t] * 1.2:
                        slots[t-1] = slots[t] * 1.1
                        cls._fifo_violations += 1

    @classmethod
    def inject_blockage(cls, road_id, multiplier=999.0):
        """Block all time slots for this segment (permanent blockage until reset)"""
        road_id = str(road_id)
        if road_id not in cls._slots:
            cls._slots[road_id] = [1.0] * 288
        cls._slots[road_id] = [multiplier] * 288
        cls._last_update[road_id] = time.time()

    @classmethod
    def update_segment(cls, road_id, slot_idx, multiplier):
        road_id = str(road_id)
        if road_id not in cls._slots:
            cls._slots[road_id] = [1.0] * 288
        cls._slots[road_id][slot_idx] = multiplier
        cls._last_update[road_id] = time.time()

    @classmethod
    def get_multiplier(cls, road_id, time_mins):
        slot_idx = int((time_mins % 1440) / 5)
        road_id = str(road_id)
        if road_id in cls._slots:
            return cls._slots[road_id][slot_idx]
        return 1.0

    @classmethod
    def is_passable(cls, road_id, time_mins, vehicle_type):
        slot_idx = int((time_mins % 1440) / 5)
        road_id = str(road_id)
        if vehicle_type == 'fire':
            if road_id in cls._passable_fire:
                return cls._passable_fire[road_id][slot_idx]
        elif vehicle_type == 'ambulance':
            if road_id in cls._passable_amb:
                return cls._passable_amb[road_id][slot_idx]
        return True

    @classmethod
    def is_raining(cls, road_id, time_mins):
        slot_idx = int((time_mins % 1440) / 5)
        road_id = str(road_id)
        return cls._rain.get(road_id, [False]*288)[slot_idx]

    @classmethod
    def reset_traffic(cls):
        cls._slots = {}
        cls._passable_amb = {}
        cls._passable_fire = {}
        cls._rain = {}
        cls._last_update = {}
        cls.load_from_csv()

    _is_offline = False
    _cut_time = None

    @classmethod
    def set_offline(cls, status=True):
        cls._is_offline = status
        cls._cut_time = time.time() if status else None

    @classmethod
    def get_stats(cls):
        now = time.time()
        ages = [now - t for t in cls._last_update.values()]
        avg_age = sum(ages) / len(ages) if ages else 0
        staleness_count = sum(1 for a in ages if a > 900)
        
        confidence = max(0, 1.0 - (staleness_count / len(cls._slots))) if cls._slots else 1.0
        
        # Twist 10: Progressive Contamination by Staleness
        if cls._is_offline and cls._cut_time:
            offline_duration_min = (now - cls._cut_time) / 60
            # Lost 10% confidence every minute of isolation
            decay = max(0, 1.0 - (offline_duration_min * 0.1))
            confidence *= decay
            
        return {
            "slots_utilises": len(cls._slots),
            "age_moyen_secondes": int(avg_age),
            "slots_perimes": staleness_count,
            "confiance_globale": confidence,
            "is_offline": cls._is_offline,
            "offline_duration_sec": int(now - cls._cut_time) if cls._cut_time else 0
        }
