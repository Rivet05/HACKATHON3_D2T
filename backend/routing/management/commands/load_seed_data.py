import json
import os
import math
from django.core.management.base import BaseCommand
from routing.models import Hospital
from django.conf import settings
from routing.services.graph_builder import GraphBuilder

class Command(BaseCommand):
    help = 'Load seed data from points_interet.json'

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000 
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def handle(self, *args, **options):
        # Clean current state for official data import
        Hospital.objects.all().delete()
        
        data_path = os.path.join(settings.BASE_DIR, 'data/points_interet.json')
        
        # We need the graph to find nearest nodes
        G = GraphBuilder.get_instance().get_graph()
        nodes = list(G.nodes(data=True))

        if not os.path.exists(data_path):
            self.stdout.write(self.style.ERROR('points_interet.json not found'))
            return

        with open(data_path, 'r') as f:
            pois = json.load(f)
            
        count = 0
        builder = GraphBuilder.get_instance()
        for poi in pois:
            if poi['type'] == 'hopital':
                lat, lon = poi['lat'], poi['lon']
                
                # Use accelerated search
                nearest_node = builder.find_nearest_node(lat, lon)
                
                # Map specific specialties based on poi data
                specialites = ["general"]
                if poi.get('capacite_trauma', 0) > 0:
                    specialites.append("trauma")
                
                Hospital.objects.update_or_create(
                    name=poi['nom'],
                    defaults={
                        'lat': lat,
                        'lng': lon,
                        'urgences_disponibles': poi.get('ouvert_24h') == 'oui',
                        'specialites': specialites,
                        'temps_attente_min': 15 if poi.get('capacite_trauma', 0) < 20 else 5, # Dynamic wait based on capacity
                        'node_id': str(nearest_node)
                    }
                )
                count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {count} hospitals from official POI file'))
