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
- **Contamination Visualisée** : Identification et affichage des points de blocage physiques sur la carte (Ronds Rouges).
- **Auto-correction** : Recalcul instantané et transparent pour l'opérateur.

### 💉 Twist 05 : Contamination par Dépendances
- **Surveillance de Statut** : L'itinéraire est dynamiquement invalidé si l'Hôpital cible change de capacité (ex: saturation trauma).
- **Mode Survie (Urgence Absolue)** : Algorithme de secours autorisant le contre-sens si aucune autre issue n'existe.

### 🌪️ Twist 06 : Incertitude Stochastique & Propagation
- **Routage Probabiliste** : Modèle de variance propageant l'incertitude (bruit) tout au long du trajet.
- **Score de Confiance** : Calcul en temps réel de la fiabilité de la mission (ETA +/- incertitude).
- **Alerte de Fragilité** : Détection quand une incertitude locale contamine la stabilité globale du trajet.

### 📐 Twist 07 : Routage Directionnel (Turn Costs)
- **Manœuvre Urbaine** : Prise en compte de la difficulté des virages dans le calcul de l'ETA.

### ⚖️ Twist 08 : Biais Algorithmique (Biais d'Invisibilité)
- **Détection de Zone Blanche** : Identification des quartiers périphériques mal cartographiés.
- **Alerte d'Équité** : Visualisation du biais pour forcer l'opérateur à prendre conscience des inégalités.

### 🚑 Twist 09 : Rareté Critique (3 Incidents / 2 Véhicules)
- **Gestionnaire de Flotte Real-Time** : Suivi des 2 ambulances disponibles pour Yaoundé.
- **Contamination par Scarsité** : Si la flotte est saturée, le système ajoute un délai de "File d'Attente Systémique" à l'ETA.
- **Déploiement Stratégique** : Bouton de confirmation de mission pour tracker les ressources sortantes.

### 📡 Twist 10 : La Chute du Signal (Ghost Routing)
- **Coupure Réseau Totale** : Simulation d'une perte de liaison avec les capteurs IoT de la ville.
- **Toxicité des Données Statiques** : Le dispatch continue de router avec les dernières valeurs connues, mais la confiance s'érode dynamiquement (-10%/min).
- **Contamination par Obsolescence** : La stabilité supposée de la carte devient une dépendance destructrice.

## 🗺️ Moteur Routier Hybride (High-Fidelity)
Contrairement aux approches classiques, Pulse utilise un moteur de fusion :
- **Géométrie Réelle** : Chargement des 21Mo de données OSM (`export.geojson`) pour des tracés qui suivent les courbes réelles de Yaoundé.
- **Mapping Spatial** : Projection des DATA IDs du concours sur le graphe OSM pour une conformité 100% avec le trafic officiel.

## 🛠️ Guide de Démonstration (L'Effet "Wow" Final)

1. **Géométrie** : Notez que les tracés ne sont plus des lignes droites mais suivent parfaitement les rues réelles de Yaoundé (Twists Geometry).
2. **Planification** : Sélectionnez un point de départ et le type **TRAUMA**.
3. **Déploiement (Twist 09)** : Cliquez sur **DÉPLOYER LE VÉHICULE**. Observez l'ambulance animée en temps-réel.
4. **The Ghost Routing (Twist 10)** : Cliquez sur **COUPER LA LIAISON RÉSEAU**. Attendez quelques secondes et relancez un calcul : l'interface affichera une alerte orange **"DONNÉES SPECTRES"** et une confiance dégradée, montrant que l'IA détecte sa propre perte de fiabilité due au temps.
5. **Résilience (Twists 04-05)** : Simulez un sabotage pour voir le recalcul immédiat.

## ⚙️ Installation Rapide

### Backend (Django)
```bash
cd backend
pip install -r requirements.txt
python manage.py load_seed_data
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