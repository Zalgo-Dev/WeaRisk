import requests
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from ratelimit import limits, sleep_and_retry

MAX_CALLS_PER_MINUTE = 30
MAX_CALLS_PER_HOUR = 1000
ONE_MINUTE = 60
ONE_HOUR = 3600

with open('utils/departements.json', encoding='utf-8') as f:
    DEPARTMENTS = json.load(f)

WEATHER_PARAMS = {
    "hourly": ["temperature_2m", "precipitation", "wind_gusts_10m", "relative_humidity_2m"],
    "daily": ["temperature_2m_max", "precipitation_sum"],
    "timezone": "Europe/Paris",
    "forecast_days": 1
}

class WeatherCollector:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.request_count = 0
        self.start_time = time.time()

    @sleep_and_retry
    @limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
    @limits(calls=MAX_CALLS_PER_HOUR, period=ONE_HOUR)
    def make_api_call(self, params):
        """Gère automatiquement les limites de taux"""
        self.request_count += 1
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API: {str(e)}")
            return None

    def process_department(self, department):
        """Traite un seul département"""
        params = {
            "latitude": department["latitude"],
            "longitude": department["longitude"],
            **WEATHER_PARAMS
        }
        
        data = self.make_api_call(params)
        if not data:
            return None

        return self.calculate_risks(data, department)

    def calculate_risks(self, data, department):
        """Calcule les risques avec gestion des valeurs manquantes"""
        try:
            hourly = data.get("hourly", {})
            daily = data.get("daily", {})
            
            risks = []
            for i in range(len(hourly.get("time", []))):
                temp = hourly.get("temperature_2m", [None])[i] or 0
                precip = hourly.get("precipitation", [None])[i] or 0
                wind = hourly.get("wind_gusts_10m", [None])[i] or 0
                humidity = hourly.get("relative_humidity_2m", [None])[i] or 0
                
                risk = {
                    "electrical": min((wind * 0.2) + (max(humidity - 80, 0) * 0.1), 100),
                    "flood": min(precip * 2, 100),
                    "heat": min(max(temp - 30, 0) * 2, 100),
                    "wind": min(wind * 0.3, 100),
                    "timestamp": hourly["time"][i]
                }
                
                risk["overall"] = round(
                    risk["electrical"] * 0.2 +
                    risk["flood"] * 0.3 +
                    risk["heat"] * 0.2 +
                    risk["wind"] * 0.3, 2
                )
                
                risks.append({
                    "department_code": department["code"],
                    "department_name": department["name"],
                    **risk
                })
            
            return risks
        except Exception as e:
            print(f"Erreur calcul risques {department['name']}: {str(e)}")
            return None

def save_to_db(data):
    """Sauvegarde optimisée avec transaction unique"""
    conn = sqlite3.connect('utils/weather_risks.db')
    try:
        conn.executemany("""
        INSERT INTO risks (department_code, department_name, timestamp,
                          electrical_risk, flood_risk, heat_risk, wind_risk, overall_risk)
        VALUES (:department_code, :department_name, :timestamp,
                :electrical, :flood, :heat, :wind, :overall)
        """, data)
        conn.commit()
    finally:
        conn.close()

def initialize_db():
    """Crée la table si elle n'existe pas"""
    conn = sqlite3.connect('utils/weather_risks.db')
    conn.execute("""
    CREATE TABLE IF NOT EXISTS risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_code TEXT,
        department_name TEXT,
        timestamp TEXT,
        electrical_risk REAL,
        flood_risk REAL,
        heat_risk REAL,
        wind_risk REAL,
        overall_risk REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.close()

def batch_collect():
    """Collecte par lots avec gestion des limites"""
    collector = WeatherCollector()
    initialize_db()
    
    batch_size = 20
    for i in range(0, len(DEPARTMENTS), batch_size):
        batch = DEPARTMENTS[i:i + batch_size]
        all_risks = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(collector.process_department, dept) for dept in batch]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    all_risks.extend(result)
        
        if all_risks:
            save_to_db(all_risks)
            print(f"Lot {i//batch_size + 1} sauvegardé - {len(all_risks)} enregistrements")
        
        if (i + batch_size) < len(DEPARTMENTS):
            time.sleep(10)

if __name__ == "__main__":
    print("Début de la collecte...")
    start = time.time()
    batch_collect()
    print(f"Collecte terminée en {time.time() - start:.2f} secondes")