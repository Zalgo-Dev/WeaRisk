
# 🌦️ WeaRisk

**WeaRisk** est une plateforme de collecte et d’analyse des risques climatiques en France, basée sur des données météorologiques en temps réel.  
Elle permet de surveiller les risques potentiels (inondations, chaleur, vent, surtensions électriques...) par département, avec stockage local en base de données et affichage via une interface web.

---

## 🚀 Fonctionnalités

- 🔄 Récupération automatique des données météo via l'API **Open-Meteo**
- ⚠️ Calcul de risques horaires par département :
  - Risque d’inondation
  - Risque de chaleur
  - Risque électrique
  - Risque de vent
- 🧠 Score global de risque par heure
- 🗺️ Couverture : tous les départements français (via `departements.json`)
- 🧩 Interface web Flask avec affichage des risques
- 💾 Stockage local en SQLite
- ⏱️ Mise à jour automatique toutes les 12h si activée

---

## 🛠️ Architecture du projet

```
WeaRisk/
│
├── run.py                  # Point d'entrée du serveur Flask
│
├── utils/                  # Outils et logique de collecte météo
│   ├── config.json         # Configuration générale (port, mode realtime)
│   ├── departements.json   # Coordonnées des départements français
│   └── get_data.py         # Script de collecte et d'analyse des données météo
│
├── app/                    # Partie principale de l'application web
│   ├── __init__.py         # Initialisation de l'app Flask + filtres Jinja
│   ├── routes.py           # Définition des routes
│
│   ├── static/             # Fichiers statiques (frontend)
│   │   ├── css/
│   │   │   └── style.css   # Styles CSS personnalisés
│   │   └── js/
│   │       └── index.js    # JS pour interactions frontend
│
│   └── templates/          # Templates HTML (Jinja2)
│       ├── index.html              # Page d’accueil
│       ├── risks.html              # Vue principale des risques climatiques
│       ├── risk_partial.html       # Partial pour rendu dynamique (AJAX, etc.)
│       └── include/                # Éléments communs HTML
│           ├── base.html           # Template de base avec blocs
│           ├── navbar.html         # Barre de navigation
│           └── footer.html         # Pied de page

```

---

## ⚙️ Installation & Lancement

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

Si tu n’as pas de `requirements.txt`, voici les dépendances de base :

```bash
pip install flask requests ratelimit
```

### 2. Lancer l’application

```bash
python run.py
```

Par défaut, le site sera lancé sur le port défini dans `utils/config.json`.

---

## ⚙️ Configuration (`utils/config.json`)

```json
{
  "weather": {
    "realtime": true
  },
  "server": {
    "port": 8080
  }
}
```

- `realtime: true` → met à jour automatiquement la base toutes les 12h
- `port` → définit le port de lancement du serveur Flask

---

## 💾 Base de données

La base `weather_risks.db` est stockée dans `utils/` et contient une table `risks` avec :

- `department_code`
- `department_name`
- `timestamp`
- `electrical_risk`
- `flood_risk`
- `heat_risk`
- `wind_risk`
- `overall_risk`

---

## 📚 À faire / Améliorations possibles

- Ajout d’une carte interactive avec Leaflet
- Filtres dynamiques par département
- Export CSV / PDF
- Interface admin
- API REST publique

---

## 🧠 Auteurs & Crédits

Projet réalisé dans le cadre d’un hackathon.  
Utilise l’API [Open-Meteo](https://open-meteo.com/).

---

## 📄 Licence

Ce projet est protégé.  
Toute reproduction, distribution, modification, ou utilisation du code en dehors du cadre de **WeaRisk** est strictement interdite sans autorisation écrite préalable.

Le code source est fourni à titre informatif uniquement.  
**Aucun droit de réutilisation ou de redistribution n'est accordé.**

