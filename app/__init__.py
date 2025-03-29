from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    from .routes import main_routes
    app.register_blueprint(main_routes)
    
    return app