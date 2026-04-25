from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Hospital, RouteAuditLog
from .serializers import HospitalSerializer, RouteAuditLogSerializer
from .services.hospital_selector import HospitalSelector
from .services.routing_engine import RoutingEngine

class HospitalListUpdateView(generics.ListAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer

class HospitalDetailUpdateView(generics.UpdateAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    http_method_names = ['patch']

class RouteCalculationView(APIView):
    def post(self, request):
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        hour = int(request.data.get('heure', 12))
        type_urgence = request.data.get('type_urgence', 'general')
        
        if lat is None or lng is None:
            return Response({"error": "Missing coordinates"}, status=status.HTTP_400_BAD_REQUEST)
            
        # 1. Filter hospitals
        eligible, consideres = HospitalSelector.get_eligible_hospitals(type_urgence)
        
        if not eligible:
            return Response({"error": "Aucun hôpital disponible pour cette urgence"}, status=status.HTTP_404_NOT_FOUND)
            
        # 2. Run ROI
        engine = RoutingEngine()
        path, hospital_id, total_cost, nodes_explored, duration_ms, location_name = engine.find_route(lat, lng, eligible, hour)
        
        if not path:
            return Response({"error": "Impossible de trouver un chemin"}, status=status.HTTP_404_NOT_FOUND)
            
        chosen_hospital = Hospital.objects.get(id=hospital_id)
        
        # 3. Create Audit Log
        # Reason for choice: Compare with other hospitals if possible or just state ETA
        # For simplicity, we just calculate the difference or state it's the best
        raison = f"ETA {total_cost:.1f} min (incl. {chosen_hospital.temps_attente_min} min attente). Meilleure option identifiée."
        
        audit = RouteAuditLog.objects.create(
            depart_lat=lat,
            depart_lng=lng,
            depart_nom=location_name,
            hopital_choisi=chosen_hospital,
            hopitaux_consideres=consideres,
            raison_choix=raison,
            eta_minutes=total_cost,
            nb_noeuds_explores=nodes_explored,
            temps_calcul_ms=duration_ms,
            path_geojson={"type": "LineString", "coordinates": [[c[1], c[0]] for c in path]}
        )
        
        return Response({
            "path": path,
            "hopital": HospitalSerializer(chosen_hospital).data,
            "eta_minutes": total_cost,
            "total_cost": total_cost,
            "audit": RouteAuditLogSerializer(audit).data
        })

class AuditLogListView(generics.ListAPIView):
    queryset = RouteAuditLog.objects.all().order_by('-timestamp')
    serializer_class = RouteAuditLogSerializer
