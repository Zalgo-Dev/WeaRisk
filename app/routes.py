from flask import Blueprint, render_template

main_routes = Blueprint('main', __name__, static_folder="static", template_folder="templates")

@main_routes.route('/')
def index():
    return render_template('index.html')

@main_routes.route('/risques')
def risques():
    return render_template('risques.html')