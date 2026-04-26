from .traffic_cache import TrafficCache

class RouteMonitor:
    def __init__(self):
        self.cache = TrafficCache.get_instance()

    def should_recompute(self, route_segments, start_time_mins) -> (bool, str):
        """
        Analyse la route restante et décide d'un recalcul.
        """
        if not route_segments:
            return False, ""

        # 1. Détection de blocage critique
        elapsed = 0
        for i, seg in enumerate(route_segments):
            # seg = {'id': '...', 'cost': ...}
            # On vérifie le trafic à l'heure estimée de passage
            current_slot_time = start_time_mins + elapsed
            multiplier = self.cache.get_multiplier(seg['id'], current_slot_time)
            
            if multiplier >= 99.0:
                return True, f"blocage_détecté_segment_{seg['id']}"
            
            elapsed += seg['cost']

        # 2. Analyse de la fraîcheur globale
        stats = self.cache.get_stats()
        if stats['confiance_globale'] < 0.75:
            return True, f"données_périmées_{int((1-stats['confiance_globale'])*100)}%"

        return False, "route_valide"
