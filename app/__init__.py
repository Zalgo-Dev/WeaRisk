from datetime import datetime
import json
from flask import Flask
from pathlib import Path

MONTHS_FR = {
    "January": "janvier",
    "February": "février",
    "March": "mars",
    "April": "avril",
    "May": "mai",
    "June": "juin",
    "July": "juillet",
    "August": "août",
    "September": "septembre",
    "October": "octobre",
    "November": "novembre",
    "December": "décembre"
}

def risk_color(value):
    """Retourne une couleur RGB en dégradé linéaire entre vert pastel (0%) et rouge pastel (100%)."""
    try:
        t = float(value) / 100.0
    except Exception:
        t = 0
    # Couleurs de référence
    green = (202, 255, 191)  # Vert pastel pour risque min (0%)
    red = (255, 173, 173)    # Rouge pastel pour risque max (100%)
    
    r = int(green[0] * (1 - t) + red[0] * t)
    g = int(green[1] * (1 - t) + red[1] * t)
    b = int(green[2] * (1 - t) + red[2] * t)
    return f"rgb({r}, {g}, {b})"

def format_datetime(value):
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M")
    month_en = dt.strftime("%B")
    month_fr = MONTHS_FR.get(month_en, month_en)
    day = dt.day
    return f"{day} {month_fr} {dt.year} à {dt.strftime('%Hh%M')}"

def create_app():
    app = Flask(__name__)

    # Chargement de la configuration
    config_path = Path(__file__).parent.parent / "utils" / "config.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
            for section in config:
                for key, value in config[section].items():
                    app.config[f"{section.upper()}_{key.upper()}"] = value
    except Exception as e:
        print(f"Erreur de chargement de la configuration: {str(e)}")
        # Valeurs par défaut
        app.config.update({
            "WEATHER_REALTIME": True,
            "SERVER_PORT": 8080,
            "SERVER_DEBUG": False
        })

    # Enregistrement du blueprint
    try:
        from app.routes import main_routes
        app.register_blueprint(main_routes)
        print("Blueprint 'main_routes' enregistré avec succès")
        print(f"Routes disponibles: {[str(rule) for rule in app.url_map.iter_rules()]}")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du blueprint: {str(e)}")
        raise  # On propage l'erreur car c'est critique

    # Enregistrement des filtres Jinja
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['risk_color'] = risk_color
    
    return app