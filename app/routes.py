from flask import Blueprint, render_template
import json
import os

main_routes = Blueprint('main', __name__, static_folder="static", template_folder="templates")

@main_routes.route('/')
def index():
    return render_template('index.html')

@main_routes.route('/risques')
def risques():
    with open(os.path.join("data", "meteo.json"), "r", encoding="utf-8") as f:
        team_data = json.load(f)
    return render_template('risques.html')