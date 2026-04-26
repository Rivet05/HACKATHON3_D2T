from rest_framework import serializers
from .models import Hospital, RouteAuditLog

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'

class RouteAuditLogSerializer(serializers.ModelSerializer):
    hopital_choisi_name = serializers.ReadOnlyField(source='hopital_choisi.name')
    
    class Meta:
        model = RouteAuditLog
        fields = ['id', 'timestamp', 'depart_lat', 'depart_lng', 'depart_nom', 'hopital_choisi', 'hopital_choisi_name', 'hopitaux_consideres', 'raison_choix', 'eta_minutes', 'nb_noeuds_explores', 'temps_calcul_ms', 'path_geojson', 'fraicheur_donnees', 'recalculs', 'destination_changee']
