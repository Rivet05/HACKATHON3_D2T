from ..models import Hospital

class HospitalSelector:
    @staticmethod
    def get_eligible_hospitals(type_urgence=None):
        hospitals = Hospital.objects.filter(urgences_disponibles=True)
        
        eligible = []
        ineligible = []
        
        all_hospitals = Hospital.objects.all()
        for h in all_hospitals:
            reason = None
            is_eligible = True
            
            if not h.urgences_disponibles:
                is_eligible = False
                reason = "urgences_fermées"
            elif type_urgence and type_urgence not in h.specialites and "general" not in h.specialites:
                is_eligible = False
                reason = f"specialité_{type_urgence}_non_disponible"
            
            status = {
                "id": h.id,
                "name": h.name,
                "eligible": is_eligible,
                "reason": reason,
                "temps_attente": h.temps_attente_min
            }
            
            if is_eligible:
                eligible.append(h)
            
            ineligible.append(status) # "consideres" includes all
            
        return eligible, ineligible
