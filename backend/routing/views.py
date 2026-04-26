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
        
        # Twist 03: Vehicle Type
        vehicle_type = request.data.get('vehicle_type', 'ambulance')
        
        engine = RoutingEngine()
        cache = TrafficCache.get_instance()
        
        # Filter hospitals by specialty (Twist 01 logic)
        eligible = Hospital.objects.filter(urgences_disponibles=True)
        if urgence_type == 'trauma':
            eligible = eligible.filter(specialites__contains='trauma')
        
        # Twist 02: TD-Algorithm
        # Twist 04: Return segment_ids
        path, hospital_id, total_cost, nodes_explored, duration_ms, location_name, segment_ids = engine.find_route(
            lat, lng, eligible, hour, minute, vehicle_type=vehicle_type
        )
        
        if not path:
            return Response({"error": "Impossible de trouver un chemin"}, status=404)
        
        # ... Decision metadata ...
        now = timezone.now()
        hopital = Hospital.objects.get(id=hospital_id)
        hospital_data = [{
            "id": h.id, 
            "name": h.name, 
            "wait": h.temps_attente_min,
            "status_age_sec": (now - h.last_status_update).total_seconds()
        } for h in eligible]
        
        # Audit Log (Twist 01 + 02)
        # Check if this route is a 'degraded' one (contains forced blockages)
        contains_recovery = any(cache.get_multiplier(sid, now.hour * 60 + now.minute) >= 99.0 for sid in segment_ids)
        
        audit = RouteAuditLog.objects.create(
            depart_lat=lat,
            depart_lng=lng,
            depart_nom=location_name,
            hopital_choisi=hopital,
            hopitaux_consideres=hospital_data,
            raison_choix=f"Optimisation avec survie ({total_cost:.1f}min). " + ("(MODE DÉGRADÉ)" if contains_recovery else ""),
            eta_minutes=total_cost,
            nb_noeuds_explores=nodes_explored,
            temps_calcul_ms=duration_ms,
            path_geojson={"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[c[1], c[0]] for c in path]}},
            fraicheur_donnees=cache.get_stats()
        )
        
        audit_data = RouteAuditLogSerializer(audit).data
        
        # Return result with segment_ids for Twist 04 monitoring
        return Response({
            "path": path,
            "segment_ids": segment_ids,
            "is_recovery_path": contains_recovery,
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
        })

class RouteIntegrityView(APIView):
    def post(self, request):
        segment_ids = request.data.get('segment_ids', [])
        vehicle_type = request.data.get('vehicle_type', 'ambulance')
        
        cache = TrafficCache.get_instance()
        now_mins = timezone.now().hour * 60 + timezone.now().minute
        
        blocked_segments = []
        print(f"DEBUG TWIST 04: Checking {len(segment_ids)} segments. First ones: {segment_ids[:5]}...")
        for sid in segment_ids:
            mult = cache.get_multiplier(sid, now_mins)
            if mult >= 99.0:
                print(f"!!! DETECTED BLOCKED SEGMENT: {sid} (mult={mult}) !!!")
                blocked_segments.append(sid)
        
        if not blocked_segments:
            print("DEBUG TWIST 04: All segments valid. No alert triggered.")
        
        return Response({
            "is_valid": len(blocked_segments) == 0,
            "blocked_count": len(blocked_segments),
            "blocked_segments": blocked_segments
        })

class TrafficResetView(APIView):
    def post(self, request):
        TrafficCache.get_instance().reset_traffic()
        return Response({"message": "Réseau fluide rétabli !"})


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
        
        # Twist 04: Block segments further along the path (10-15) to allow for detours
        target_ids = []
        path_segments = request.data.get('current_route_segments', [])
        if len(path_segments) > 15:
            for sid in path_segments[10:15]:
                target_ids.append(sid)
        elif path_segments:
            # Fallback if path is short
            target_ids.append(path_segments[-1])

        if lat and lng:
            for u, v, data in G.edges(data=True):
                node_data = G.nodes[u]
                if 'lat' in node_data:
                    dist = builder.haversine(float(lat), float(lng), node_data['lat'], node_data['lng'])
                    if dist < 400:
                        target_ids.append(data.get('segment_id'))
        
        # 10 segments aléatoires
        edges = list(G.edges(data=True))
        selected = random.sample(edges, min(10, len(edges)))
        target_ids.extend([d.get('segment_id') for u, v, d in selected])

        blocked_count = 0
        for sid in target_ids:
            if sid:
                now = timezone.now()
                slot = (now.hour * 12) + (now.minute // 5)
                for s in range(slot, min(288, slot + 24)):
                    cache.update_segment(sid, s, 999.0)
                blocked_count += 1
        
        return Response({"message": f"Sabotage réussi : {blocked_count} segments impactés."})





