import os
import json
import threading
import time
from datetime import datetime, timedelta
from app import create_app
from utils.get_data import batch_collect

# Configuration
CONFIG_PATH = 'utils/config.json'
DB_PATH = os.path.join("utils", "weather_risks.db")

def load_config():
    """Charge la configuration depuis le fichier JSON"""
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    return {
        'realtime': config.get("weather", {}).get("realtime", False),
        'port': config.get("server", {}).get("port", 5000),
        'debug': config.get("server", {}).get("debug", False),
        'check_interval': config.get("weather", {}).get("update_check_interval", 1800)
    }

def needs_refresh():
    """Détermine si la base de données nécessite une mise à jour"""
    if not os.path.exists(DB_PATH):
        return True
    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(DB_PATH))
    return file_age > timedelta(hours=12)

def refresh_data():
    """Effectue la mise à jour des données"""
    print("Mise à jour des données en cours...")
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        batch_collect()
        print("Mise à jour terminée avec succès")
    except Exception as e:
        print(f"Échec de la mise à jour: {str(e)}")

def start_background_refresh(interval):
    """Démarre le thread de rafraîchissement périodique"""
    def refresh_loop():
        while True:
            time.sleep(interval)
            if needs_refresh():
                refresh_data()
    
    print(f"Mode temps réel activé (vérification toutes {interval//60} minutes)")
    thread = threading.Thread(target=refresh_loop, daemon=True)
    thread.start()

def main():
    config = load_config()
    app = create_app()

    # Initialisation au démarrage
    if not config['debug'] or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if needs_refresh():
            refresh_data()
        
        if config['realtime']:
            start_background_refresh(config['check_interval'])

    # Lancer le serveur
    app.run(host='0.0.0.0', port=config['port'], debug=config['debug'])

if __name__ == '__main__':
    main()