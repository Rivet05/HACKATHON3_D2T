# 🚑 Emergency Path - Smart African City Routing (Yaoundé)

Système de routage d'urgence hautement résilient conçu pour le Hackathon Hackverse 3. Ce projet démontre une architecture capable de gérer des environnements urbains complexes, imprévisibles et changeants en temps réel.

## 🌟 Twists Réalisés

### 🧠 Twist 01 & 02 : Audit & Réalité Urbaine
- **Audit Log Complet** : Traçabilité totale des décisions (pourquoi cet hôpital ? impact du trafic ?).
- **Données Réelles** : Réseau routier de Yaoundé (GeoJSON) et flux de trafic historiques (CSV).
- **Super-Node A*** : Algorithme temporel (TD-A*) optimisé pour l'Afrique.

### 🚒 Twist 03 : Profils de Véhicules & Météo
- **Profils Métiers** : Paramétrage dynamique pour Ambulances, Pompiers (gabarit) et Police.
- **Météo Dynamique** : Coefficient de friction et de visibilité impactant le temps de trajet en temps réel.

### 🚀 Twist 04 : Résilience d'Urgence (Active Monitoring)
- **Pulse 3s** : Surveillance active de l'intégrité de la mission par polling asynchrone.
- **Contamination Detection** : Identification des "zones mortes" routières apparaissant mid-trajet.
- **Auto-correction** : Recalcul instantané et transparent pour l'opérateur.

### 💉 Twist 05 : Contamination par Dépendances
- **Surveillance de Statut** : L'itinéraire est dynamiquement invalidé si l'Hôpital cible change de capacité (ex: saturation trauma).
- **Mode Survie (Urgence Absolue)** : Algorithme de secours autorisant le contre-sens et le passage forcé si aucune autre issue n'existe.

## 🛠️ Guide de Démonstration (Le "Wow" Final)

1. **Calcul** : Sélectionnez un point de départ et le type **TRAUMA**.
2. **Sabotage Route** : Cliquez sur "SABOTEUR ROUTE". L'alerte clignote en rouge et l'IA contourne le blocage.
3. **Sabotage Hôpital** : Cliquez sur "SABOTEUR HÔPITAL". L'alerte passe en orange (**Saturation Trauma**) et l'ambulance change de destination vers le prochain hôpital trauma disponible.
4. **Zéro Échec** : Même enfermé dans une impasse sabotée, le système active le **Mode Survie** pour trouver une issue héroïque.

## ⚙️ Installation Rapide

### Backend (Django)
```bash
cd backend
pip install -r requirements.txt
python manage.py load_seed_data  # Importe Yaoundé et les Hôpitaux
python manage.py runserver
```

### Frontend (React/Vite)
```bash
cd frontend
npm install
npm run dev
```

---
*Réalisé avec Passion par l'équipe D2T - Hackverse 3 (Avril 2026)*
*Techno : Django REST, React, Leaflet, NetworkX, NumPy.*