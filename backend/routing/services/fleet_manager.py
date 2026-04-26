import time

class FleetManager:
    _instance = None
    _active_missions = [] # List of (expiration_time)
    _max_vehicles = 2

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def launch_mission(self, duration_mins=10):
        """Consume a vehicle for X minutes"""
        expiration = time.time() + (duration_mins * 60)
        self._active_missions.append(expiration)
        return True

    def get_available_count(self):
        # Clean up finished missions
        now = time.time()
        self._active_missions = [m for m in self._active_missions if m > now]
        return max(0, self._max_vehicles - len(self._active_missions))

    def reset(self):
        self._active_missions = []

    def get_waiting_time(self):
        """Return waiting time in seconds if fleet is saturated"""
        if self.get_available_count() > 0:
            return 0
        
        # If saturated, wait for the first vehicle to return
        now = time.time()
        if not self._active_missions:
            return 0
        
        return max(0, min(self._active_missions) - now)
