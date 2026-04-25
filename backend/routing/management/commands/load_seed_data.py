import json
import os
from django.core.management.base import BaseCommand
from routing.models import Hospital
from django.conf import settings

class Command(BaseCommand):
    help = 'Load seed data for hospitals'

    def handle(self, *args, **options):
        data_path = os.path.join(settings.BASE_DIR, 'data/sample_hospitals.json')
        
        with open(data_path, 'r') as f:
            hospitals = json.load(f)
            
        for h_data in hospitals:
            Hospital.objects.update_or_create(
                name=h_data['name'],
                defaults={
                    'lat': h_data['lat'],
                    'lng': h_data['lng'],
                    'urgences_disponibles': h_data['urgences_disponibles'],
                    'specialites': h_data['specialites'],
                    'temps_attente_min': h_data['temps_attente_min'],
                    'node_id': h_data['node_id']
                }
            )
            
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(hospitals)} hospitals'))
