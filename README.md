# TWIST 01 — Destination Dynamique Multi-Hôpitaux & Moteur Résilient

## Hypothèse brisée
L'hypothèse que "la destination est un hôpital fixe et disponible" est fausse. Dans une urgence réelle, l'état du patient, la saturation des services et la qualité imprévisible des routes exigent un calcul de coût global (Chemin + Hôpital).

## Ce qui a été implémenté (Socle Technique)

### 1. Algorithme A* Multi-destination (Super-Nœud)
L'algorithme ne cherche pas un chemin vers *un* hôpital, mais vers le meilleur hôpital éligible.
- **Innovation** : Utilisation d'un nœud virtuel `HOPITAL_DEST` connecté dynamiquement à tous les hôpitaux via des arêtes virtuelles (poids = temps d'attente à l'hôpital). 
- **Résultat** : Optimisation globale en une seule passe A*.

### 2. Réalité de Terrain & Spécificités Africaines
- **Dégradation Dynamique** : Les vitesses de base (OSM) sont radicalement pénalisées selon le revêtement (`surface=unpaved` ou `dirt` plafonnés à 20km/h).
- **Bypass d'Urgence** : Le moteur autorise les ambulances à braver les sens uniques en cas d'isolement complet, en appliquant une pénalité de coût massive (x20) pour forcer la préférence au sens légal.
- **Connectivité Résiliente** : Indexation spatiale arrondissant les coordonnées à 7 décimales pour "recoller" les segments de route OpenStreetMap défectueux.

### 3. Performance & Indexation Spatiale
- **Indexation Vectorisée (Numpy)** : Recherche du nœud le plus proche en $O(log N)$ via des opérations matricielles. Capable de gérer le graphe de Yaoundé (> 1M de segments) sans latence au clic.
- **Stratégie Multi-Point** : Si le point de clic est une impasse isolée, le système tente automatiquement les 5 nœuds adjacents les plus proches pour garantir un routage vers le réseau principal.

### 4. État Défendable (Audit Log)
Chaque calcul produit un "État Défendable" en base de données :
- **Traçabilité** : Stockage du contexte complet (Heure, Trafic, Hôpitaux considérés).
- **Causalité** : Explication textuelle de la décision (ex: "Hôpital B rejeté à cause d'une saturation trauma de +15min").

## Architecture
```text
[ React Frontend ] <----(GeoJSON/JSON)---- [ Django REST API ]
       |                                         |
       |--- Click Map (Start)                    |--- Routing Engine (A* Optimized)
       |--- Filter (Type Urgence)                |--- Spatial Index (Numpy)
       |--- Visualisation Temps Réel             |--- Graph (1M nodes - OSM export.geojson)
                                                 |--- Audit Logger (PostGre/SQLite)
```

## Lancer le projet

### Backend
```bash
cd backend
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py load_seed_data  # Importation haute précision
python3 manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Accéder à : http://localhost:5173