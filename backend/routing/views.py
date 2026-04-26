from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Hospital, RouteAuditLog
from .serializers import HospitalSerializer, RouteAuditLogSerializer
from .services.hospital_selector import HospitalSelector
from .services.routing_engine import RoutingEngine
from .services.traffic_cache import TrafficCache

class HospitalListUpdateView(generics.ListAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer

class HospitalDetailUpdateView(generics.UpdateAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    http_method_names = ['patch']

class RouteCalculationView(APIView):
    def post(self, request):
        lat = float(request.data.get('lat'))
        lng = float(request.data.get('lng'))
        urgence_type = request.data.get('type_urgence', 'general')
        
        # Twist 02: Support for exact start time
        now = timezone.now()
        hour = int(request.data.get('hour') or request.data.get('heure') or now.hour)
        minute = int(request.data.get('minute', now.minute))
        
        engine = RoutingEngine()
        cache = TrafficCache.get_instance()
        
        # Filter hospitals by specialty (Twist 01 logic)
        eligible = Hospital.objects.filter(urgences_disponibles=True)
        if urgence_type == 'trauma':
            eligible = eligible.filter(specialites__contains='trauma')
        
        # Twist 02: TD-Algorithm
        path, hospital_id, total_cost, nodes_explored, duration_ms, location_name = engine.find_route(lat, lng, eligible, hour, minute)
        
        if not path:
            return Response({"error": "Impossible de trouver un chemin"}, status=404)
        
        # Decision metadata
        hopital = Hospital.objects.get(id=hospital_id)
        hospital_data = [{
            "id": h.id, 
            "name": h.name, 
            "wait": h.temps_attente_min,
            "status_age_sec": (now - h.last_status_update).total_seconds()
        } for h in eligible]
        
        # Twist 02: Freshness stats
        traffic_stats = cache.get_stats()
        
        # Audit Log (Twist 01 + 02)
        audit = RouteAuditLog.objects.create(
            depart_lat=lat,
            depart_lng=lng,
            depart_nom=location_name,
            hopital_choisi=hopital,
            hopitaux_consideres=hospital_data,
            raison_choix=f"Optimisation temps total ({total_cost:.1f}min) incluant attente ({hopital.temps_attente_min}min)",
            eta_minutes=total_cost,
            nb_noeuds_explores=nodes_explored,
            temps_calcul_ms=duration_ms,
            path_geojson={"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[c[1], c[0]] for c in path]}},
            fraicheur_donnees=traffic_stats
        )
        
        # Return full audit for UI (Hackathon speed)
        audit_data = RouteAuditLogSerializer(audit).data
        
        return Response({
            "path": path,
            "hospital": {
                "id": hopital.id,
                "name": hopital.name,
                "lat": hopital.lat,
                "lng": hopital.lng,
                "wait": hopital.temps_attente_min
            },
            "eta": round(total_cost, 1),
            "audit": audit_data,
            "location_name": location_name,
            "traffic_stats": traffic_stats
        })


class AuditLogListView(generics.ListAPIView):
    queryset = RouteAuditLog.objects.all().order_by('-timestamp')
    serializer_class = RouteAuditLogSerializer

class InjectBlockageView(APIView):
    def post(self, request):
        import random
        from .services.graph_builder import GraphBuilder
        cache = TrafficCache.get_instance()
        builder = GraphBuilder.get_instance()
        G = builder.get_graph()
        
        # Twist 02 Demo: Block near the departure if provided
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        target_ids = []
        if lat and lng:
            # Block nodes/edges within roughly 500m
            # Very simple bounding box filter for speed
            for u, v, data in G.edges(data=True):
                node_data = G.nodes[u]
                if 'lat' in node_data:
                    dist = builder.haversine(float(lat), float(lng), node_data['lat'], node_data['lng'])
                    if dist < 2000: # 2 Kilometers radius
                        target_ids.append(data.get('segment_id'))

        
        # Fallback to random if no lat/lng or no segments found
        if not target_ids:
            edges = list(G.edges(data=True))
            selected = random.sample(edges, min(20, len(edges)))
            target_ids = [d.get('segment_id') for u, v, d in selected]
            
        now = timezone.now()
        
        blocked_count = 0
        for sid in target_ids:
            if sid:
                # Twist 02: Block for ALL slots of the day to be sure
                for s in range(288):
                    cache.update_segment(sid, s, 999.0)
                blocked_count += 1
        
        cache.smooth_fifo()
        
        return Response({
            "message": f"DÉMO: {blocked_count} segments murés pour 24h",
            "blocked_count": blocked_count
        })





