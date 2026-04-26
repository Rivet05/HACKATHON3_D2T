import time
import random
import threading
from django.core.management.base import BaseCommand
from routing.services.traffic_cache import TrafficCache
from routing.services.graph_builder import GraphBuilder

class Command(BaseCommand):
    help = 'Simule le flux de trafic dynamique toutes les 5 minutes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Démarrage du simulateur de trafic dynamique (Twist 02)..."))
        self.cache = TrafficCache.get_instance()
        self.graph = GraphBuilder.get_instance().get_graph()
        self.road_ids = list(self.cache._slots.keys())
        
        if not self.road_ids:
            self.stdout.write(self.style.ERROR("Erreur: Cache trafic vide. Importez les données d'abord."))
            return

        self.run_cycle()

    def run_cycle(self):
        # Calcul du slot actuel (0-287)
        now = time.localtime()
        current_slot = (now.tm_hour * 12) + (now.tm_min // 5)
        
        # 1. Mise à jour de 20% des segments au hasard
        target_count = int(len(self.road_ids) * 0.20)
        to_update = random.sample(self.road_ids, target_count)
        
        for rid in to_update:
            # Fluctuation de +/- 15% par rapport à la valeur nominale
            current_val = self.cache.get_multiplier(rid, current_slot * 5)
            new_val = max(1.0, current_val * random.uniform(0.85, 1.15))
            self.cache.update_segment(rid, current_slot, new_val)

        # 2. Injection sporadique d'un blocage total (Ambulance Recalcul Test)
        if random.random() < 0.3: # 30% de chance d'un incident majeur par cycle
            block_id = random.choice(self.road_ids)
            self.cache.update_segment(block_id, current_slot, 999.0)
            self.stdout.write(self.style.WARNING(f"INCIDENT: Blocage total injecté sur le segment {block_id}"))

        # 3. Lissage FIFO global
        self.cache.smooth_fifo()
        
        self.stdout.write(f"[{time.strftime('%H:%M:%S')}] Cycle de simulation OK (Slot {current_slot})")
        
        # Relance dans 5 minutes (300 secondes)
        # Pour le hackathon, on peut accélérer la démo avec un délai plus court si nécessaire
        threading.Timer(300, self.run_cycle).start()
