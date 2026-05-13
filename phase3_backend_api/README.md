# Phase 3 - Backend / API / synchronisation

Cette partie expose les donnees produites par la phase 2 avec FastAPI.
Elle sert de pont entre:

- la phase 2 IA / analytics
- Unity / VR
- l'interface desktop analyste

## 1. Aller Dans Le Dossier

Dans PowerShell:

```powershell
cd C:\Users\Lucky\Documents\projet_vr\phase3_backend_api
```

## 2. Installer Les Dependances

Si ce n'est pas deja fait:

```powershell
python -m pip install -r requirements.txt
```

Les dependances principales sont:

- `fastapi`
- `uvicorn`
- `python-dotenv`
- `pytest`
- `httpx`

## 3. Lancer Le Backend

Commande recommandee:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

Ensuite ouvre:

```text
http://127.0.0.1:8010/docs
```

Cette page ouvre Swagger, l'interface qui permet de tester l'API dans le
navigateur.

## 4. Si Le Port Est Bloque

Si tu vois cette erreur:

```text
ERROR: [WinError 10013] Une tentative d'acces a un socket de maniere interdite par ses autorisations d'acces a ete tentee
```

cela veut dire que Windows bloque le port ou qu'un autre service l'utilise.

Essaie un autre port:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8020 --reload
```

Puis ouvre:

```text
http://127.0.0.1:8020/docs
```

Evite `--host 0.0.0.0` sur Windows si tu n'as pas besoin d'acces depuis une
autre machine. Utilise plutot:

```powershell
--host 127.0.0.1
```

## 5. Verifier Que L'API Fonctionne

Dans le navigateur:

```text
http://127.0.0.1:8010/health
```

Tu dois recevoir une reponse du type:

```json
{
  "status": "ok",
  "environment": "development",
  "data_dir_exists": true
}
```

Tu peux aussi verifier les donnees disponibles:

```text
http://127.0.0.1:8010/api/sync/status
```

## 6. Donnees Attendues

L'API utilise ces fichiers JSON:

```text
phase3_backend_api/data/
|-- nodes_3d.json
|-- edges.json
|-- clusters.json
`-- anomalies.json
```

Si les fichiers ne sont pas dans `phase3_backend_api/data`, l'API cherche
automatiquement dans:

```text
../ph2-main/data/export
../phase2_ai_analytics/data/export
../phase1_data_engineering-main/data/export
../phase1_data_engineering/data/export
```

Dans ton projet actuel, les donnees de la phase 2 sont deja detectees:

- `nodes_3d.json`
- `clusters_summary.json`
- `anomalies.json`

Il peut manquer `edges.json`, qui doit venir de la phase 1.
Si `edges.json` n'existe pas, l'API peut maintenant lire directement
`../edges.csv` a la racine du projet.

## 7. Importer Les Exports Dans Le Backend

Pour copier les exports detectes vers `phase3_backend_api/data`, utilise dans
Swagger:

```text
POST /api/sync/from-phase2
```

Ou en PowerShell:

```powershell
curl -X POST "http://127.0.0.1:8010/api/sync/from-phase2"
```

Pour recharger le cache apres modification des JSON:

```text
POST /api/sync/reload
```

## 8. Routes Principales

```text
GET  /health
GET  /api/nodes
GET  /api/nodes/{node_id}
GET  /api/nodes/summary

GET  /api/edges
GET  /api/edges/{edge_id}

GET  /api/clusters
GET  /api/clusters/{cluster_label}
GET  /api/clusters/{cluster_label}/nodes

GET  /api/anomalies
GET  /api/anomalies/top
GET  /api/anomalies/summary
GET  /api/anomalies/{node_id}

GET  /api/sync/status
POST /api/sync/reload
POST /api/sync/import
POST /api/sync/from-phase2
POST /api/sync/events
WS   /api/sync/ws
```

## 9. Exemples A Tester

Afficher 100 noeuds:

```text
http://127.0.0.1:8010/api/nodes?limit=100
```

Afficher les noeuds critiques:

```text
http://127.0.0.1:8010/api/nodes?risk_level=critique&limit=50
```

Afficher les anomalies les plus fortes:

```text
http://127.0.0.1:8010/api/anomalies/top?limit=20
```

Afficher les clusters:

```text
http://127.0.0.1:8010/api/clusters
```

Afficher les noeuds d'un cluster:

```text
http://127.0.0.1:8010/api/clusters/4/nodes?limit=100
```

## 10. Utilisation Avec Unity

Dans Unity, l'URL de base est:

```text
http://127.0.0.1:8010
```

Endpoints utiles pour Unity:

```text
/api/nodes?limit=5000
/api/edges?limit=5000
/api/clusters
/api/anomalies/top?limit=100
/api/sync/ws
```

Unity peut recuperer les donnees avec des requetes HTTP classiques. Pour la
synchronisation en temps reel, Unity peut se connecter au WebSocket:

```text
ws://127.0.0.1:8010/api/sync/ws
```

## 11. Utilisation Avec Le Client Desktop

Le client desktop peut utiliser les memes endpoints:

```text
/api/nodes
/api/anomalies
/api/clusters
/api/sync/events
```

Exemple d'evenement envoye au backend:

```json
{
  "type": "select_node",
  "payload": {
    "node_id": "C1351320610"
  }
}
```

Route a utiliser:

```text
POST /api/sync/events
```

Le backend renvoie ensuite l'evenement aux clients connectes au WebSocket.

## 12. Lancer Les Tests

Commande recommandee sur Windows:

```powershell
python -m pytest tests -p no:cacheprovider --basetemp .pytest_tmp
```

Resultat attendu:

```text
6 passed
```

## 13. Structure

```text
phase3_backend_api/
|-- app/
|   |-- main.py
|   |-- config.py
|   |-- routes/
|   |-- services/
|   `-- models/
|-- data/
|-- tests/
|-- logs/
|-- requirements.txt
|-- .env
`-- README.md
```

## 14. Resume Rapide

```powershell
cd C:\Users\Lucky\Documents\projet_vr\phase3_backend_api
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

Puis ouvrir:

```text
http://127.0.0.1:8010/docs
```
