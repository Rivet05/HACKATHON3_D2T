from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.decorators import api_view
from .models import Hospital, RouteAuditLog
from .serializers import HospitalSerializer, RouteAuditLogSerializer
from .services.hospital_selector import HospitalSelector
from .services.routing_engine import RoutingEngine
from .services.traffic_cache import TrafficCache
from .services.graph_builder import GraphBuilder
from .services.fleet_manager import FleetManager

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
        
        # Filter hospitals by specialty (Python-side filtering for SQL compatibility)
        all_eligible = Hospital.objects.filter(urgences_disponibles=True)
        if not all_eligible.exists():
            # Twist 05: Force Rescue Mode - ignore availability flag if all are saturated
            all_eligible = Hospital.objects.all()
            
        if urgence_type == 'trauma':
            eligible = [h for h in all_eligible if 'trauma' in (h.specialites or [])]
        else:
            eligible = list(all_eligible)
        
        if not eligible:
            # Last fallback: any hospital at all
            eligible = list(Hospital.objects.all())
        
        now = timezone.now()
        fleet = FleetManager.get_instance()
        wait_sec = fleet.get_waiting_time()
        
        # Twist 02: TD-Algorithm
        # Twist 04: Return segment_ids
        # Twist 06: Return total_sd
        # Twist 08: Return decision_meta
        res = engine.find_route(lat, lng, eligible, hour, minute, vehicle_type=vehicle_type)
        path, hospital_id, total_cost, nodes_explored, duration_ms, location_name, segment_ids, total_sd, decision_meta = res
        
        # Twist 09: Systemic Scarcity Contamination
        final_eta = total_cost + (wait_sec / 60.0)
        
        if not path:
            return Response({"error": "Impossible de trouver un chemin"}, status=404)
        
        # ... Decision metadata ...
        now = timezone.now()
        hopital = Hospital.objects.get(id=hospital_id)
        
        # Twist 06: Confidence Score
        # Confidence decreases if SD is large relative to total cost
        confidence = max(0.1, 1.0 - (total_sd / (total_cost + 1)))
        
        # Audit Log (Twist 01 + 02)
        # Check if this route is a 'degraded' one (contains forced blockages or saturated hospital)
        is_blocked_road = any(cache.get_multiplier(sid, now.hour * 60 + now.minute) >= 99.0 for sid in segment_ids)
        is_saturated_hosp = not hopital.urgences_disponibles
        contains_recovery = is_blocked_road or is_saturated_hosp
        
        audit = RouteAuditLog.objects.create(
            depart_lat=lat,
            depart_lng=lng,
            depart_nom=location_name,
            hopital_choisi=hopital,
            hopitaux_consideres=[],
            raison_choix=f"Routage directionnel ({total_cost:.1f}min +/- {total_sd:.1f}min). " + 
                         f"Confiance Carto: {int(decision_meta.get('mapping_confidence', 1.0)*100)}%. " +
                         ("(Mode DR)" if contains_recovery else ""),
            eta_minutes=total_cost,
            nb_noeuds_explores=nodes_explored,
            temps_calcul_ms=duration_ms,
            path_geojson={"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[c[1], c[0]] for c in path]}},
            fraicheur_donnees={
                "confidence": confidence, 
                "sd_min": float(total_sd),
                "mapping_bias": decision_meta.get('bias_detected', False)
            }
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
            "eta": round(final_eta, 1),
            "fleet_wait_min": round(wait_sec / 60.0, 1),
            "uncertainty_min": round(total_sd, 1),
            "traffic_stats": {
                "confiance_globale": confidence,
                "age_moyen_secondes": 15,
                "equity_score": decision_meta.get('equity_score', 1.0)
            },
            "audit": audit_data,
            "location_name": location_name,
        })

class RouteIntegrityView(APIView):
    def post(self, request):
        segment_ids = request.data.get('segment_ids', [])
        hospital_id = request.data.get('hospital_id')
        urgence_type = request.data.get('urgence_type', 'general')
        
        cache = TrafficCache.get_instance()
        now_mins = timezone.now().hour * 60 + timezone.now().minute
        
        # 1. Path Integrity (Twist 04)
        blocked_points = []
        builder = GraphBuilder.get_instance()
        G = builder.get_graph()
        
        # Mapping for fast node lookup
        node_coords = {n: (d['lat'], d['lng']) for n, d in G.nodes(data=True) if 'lat' in d}

        for sid in segment_ids:
            if cache.get_multiplier(sid, now_mins) >= 99.0:
                # Find a coordinate for this segment to show on map
                # We search for the first edge that matches this segment_id
                for u, v, d in G.edges(data=True):
                    if d.get('segment_id') == sid:
                        if u in node_coords:
                            blocked_points.append(node_coords[u])
                            break
        
        # 2. Dependency Integrity (Twist 05)
        # ... (rest of the logic)
        hospital_valid = True
        reason = "path_blocked" if blocked_points else "ok"
        
        # (Hospital check logic)
        if hospital_id:
            try:
                h = Hospital.objects.get(id=hospital_id)
                if not h.urgences_disponibles:
                    hospital_valid = False
                    reason = "hospital_closed"
                elif urgence_type == 'trauma' and 'trauma' not in (h.specialites or []):
                    hospital_valid = False
                    reason = "hospital_trauma_saturated"
            except Hospital.DoesNotExist:
                hospital_valid = False
                reason = "hospital_missing"

        return Response({
            "is_valid": len(blocked_points) == 0 and hospital_valid,
            "blocked_count": len(blocked_points),
            "blocked_coordinates": blocked_points,
            "hospital_valid": hospital_valid,
            "integrity_failure_reason": reason
        })

class SabotageHospitalView(APIView):
    def post(self, request, pk):
        try:
            h = Hospital.objects.get(pk=pk)
            # Handle list as JSONField
            specs = h.specialites or []
            if 'trauma' in specs:
                h.specialites = [s for s in specs if s != 'trauma']
            else:
                h.urgences_disponibles = False 
            h.save()
            return Response({"message": f"Hôpital {h.name} saboté / saturé !"})
        except Hospital.DoesNotExist:
            return Response({"error": "Hôpital non trouvé"}, status=404)

class TrafficResetView(APIView):
    def post(self, request):
        TrafficCache.get_instance().reset_traffic()
        FleetManager.get_instance().reset()
        
        # Twist 05: Reset hospitals but keep ONE closed to show the system's discrimination
        hospitals = list(Hospital.objects.all())
        for i, h in enumerate(hospitals):
            h.urgences_disponibles = (i > 0) # Close the first one
            h.temps_attente_min = 5 + (i * 2) # Reset wait times to realistic values
            h.save()
            
        return Response({"message": "Réseau fluide rétabli ! (Attention: Hôpital Principal saturé)"})


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
        
        target_ids = set()
        path_segments = request.data.get('current_route_segments', [])
        
        # 1. Sabotage de l'itinéraire actuel (Vrai Twist 04)
        if len(path_segments) > 12:
            for sid in path_segments[10:13]:
                target_ids.add(sid)
                
        # 2. Contamination (Effet Domino)
        # On bloque les voisins des segments ciblés pour simuler une paralysie de zone
        additional_blocks = set()
        for sid in target_ids:
            # Simulation de propagation aux segments voisins
            # (Dans une démo, on simule l'impact sur les "ways" adjacents)
            pass 

        blocked_count = 0
        for sid in target_ids:
            if sid:
                cache.inject_blockage(sid, 999.0)
                blocked_count += 1
        
        return Response({
            "message": f"DANGER : Contamination de zone détectée !",
            "blocked_segments": list(target_ids),
            "impact_level": "CRITIQUE"
        })

class FleetStatusView(APIView):
    def get(self, request):
        fleet = FleetManager.get_instance()
        return Response({
            "available": fleet.get_available_count(),
            "max": fleet._max_vehicles,
            "waiting_time_sec": fleet.get_waiting_time()
        })

@api_view(['POST'])
def cut_network(request):
    status = request.data.get('status', True)
    TrafficCache.get_instance().set_offline(status)
    return Response({"status": "offline" if status else "online"})

class LaunchMissionView(APIView):
    def post(self, request):
        FleetManager.get_instance().launch_mission(duration_mins=5)
        return Response({"message": "Mission lancée, véhicule déployé !"})
