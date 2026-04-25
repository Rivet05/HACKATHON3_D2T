# TWIST 01 — Destination dynamique multi-hôpitaux

## Hypothèse brisée
L'hypothèse que "la destination est un hôpital fixe et disponible" est fausse. Dans une urgence réelle (Yaoundé/Douala), certains hôpitaux sont saturés, d'autres n'ont pas la spécialité requise, et le temps d'attente sur place est aussi critique que le temps de trajet.

## Ce qui a changé
- **Multi-destination** : L'algorithme ne cherche plus un chemin vers UN hôpital, mais le meilleur couple (Hôpital, Chemin).
- **Super-nœud virtuel** : Utilisation d'un point d'arrivée fictif connecté à tous les hôpitaux éligibles pour résoudre le problème en une seule passe A*.
- **État Dynamique** : Les hôpitaux peuvent être marqués comme saturés via l'interface admin, ce qui les exclut instantanément des futurs calculs.
- **Audit Log** : Chaque calcul est audité en base avec les raisons du choix (comparaison des ETA et disponibilité).

## Architecture
```text
[ React Frontend ] <----(GeoJSON/JSON)---- [ Django REST API ]
       |                                         |
       |--- Click Map (Start)                    |--- Routing Engine (A*)
       |--- Filter (Type Urgence)                |--- Graph (OSM NetworkX)
       |--- Admin Toggle (Hospital state)        |--- Traffic (CSV Memory)
                                                 |--- Audit Logger (DB)
```

## Algorithme
L'algorithme implémenté est un **A* Multi-destination**. 
1. Un **super-nœud** "DEST" est ajouté dynamiquement au graphe.
2. Des arêtes sont créées entre chaque hôpital éligible et "DEST", avec un poids égal au `temps_attente_min`.
3. L'heuristique utilisée est la distance Haversine minimale vers n'importe quel hôpital éligible (optimiste, donc admissible).
4. La complexité est $O(E \log V)$ dans le pire cas, mais optimisée par l'heuristique spatiale.

## Limites connues (préparation TWIST 02)
- Les poids du trafic sont calculés à $T=départ$ et considérés stables pour toute la durée du trajet.
- Le moteur ne prend pas encore en compte les changements de trafic en "temps réel" pendant que l'ambulance roule.
- Le graphe est chargé intégralement en mémoire (OK pour 50-5000 nœuds, à optimiser pour 1M+).

## Lancer le projet

### Backend
```bash
cd backend
pip install -r requirements.txt
python3 manage.py makemigrations routing
python3 manage.py migrate
python3 manage.py load_seed_data
python3 manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Accéder à : http://localhost:5173