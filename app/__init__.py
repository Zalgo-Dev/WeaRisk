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

def format_datetime(value):
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M")
    month_en = dt.strftime("%B")
    month_fr = MONTHS_FR.get(month_en, month_en)
    day = dt.day
    return f"{day} {month_fr} {dt.year} à {dt.strftime('%Hh%M')}"

def create_app():
    app = Flask(__name__)

    config_path = Path(__file__).parent.parent / "utils" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    for section in config:
        for key, value in config[section].items():
            app.config[f"{section.upper()}_{key.upper()}"] = value

    from .routes import main_routes
    app.register_blueprint(main_routes)

    app.jinja_env.filters['format_datetime'] = format_datetime

    return app
