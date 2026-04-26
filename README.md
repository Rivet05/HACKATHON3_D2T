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
- **Pénalité de Données** : L'IA "marginalise" ces zones en augmentant l'incertitude par défaut, exposant le risque d'abandon systémique.
- **Alerte d'Équité** : Visualisation du biais pour forcer l'opérateur à prendre conscience des inégalités de desserte.

## 🛠️ Guide de Démonstration (Le "Wow" Final)

1. **Calcul** : Sélectionnez un point de départ et le type **TRAUMA**.
2. **Sabotage Route** : Cliquez sur "SABOTEUR ROUTE". Des ronds rouges apparaissent sur la carte, l'alerte clignote et l'IA contourne les obstacles.
3. **Sabotage Hôpital** : Cliquez sur "SABOTEUR HÔPITAL". L'IA détecte la "Saturation Trauma" et redirige immédiatement vers un centre valide.
4. **Zéro Échec** : Même bloqué, le système active le **Mode Survie** pour trouver une issue héroïque.
5. **Incertitude** : Observez l'ETA fluctuer avec une marge d'erreur (± X min) et la barre de confiance changer de couleur selon la stabilité du parcours.

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