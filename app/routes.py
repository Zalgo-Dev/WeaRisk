from flask import Blueprint, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime, timedelta

main_routes = Blueprint('main', __name__, static_folder="static", template_folder="templates")

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'utils', 'weather_risks.db')

def get_risks_data(department=None, limit=100):
    """Récupère les données de risques depuis la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT department_name, timestamp, 
               electrical_risk, flood_risk, 
               heat_risk, wind_risk, overall_risk
        FROM risks
        WHERE timestamp >= datetime('now', '-1 day')
    """
    params = []
    
    if department:
        query += " AND department_name LIKE ?"
        params.append(f"%{department}%")
    
    query += " ORDER BY timestamp DESC, overall_risk DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]

def get_all_departments():
    """Récupère la liste des départements disponibles"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT department_name FROM risks ORDER BY department_name")
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

@main_routes.route('/')
def index():
    return render_template('index.html')

@main_routes.route('/risks')
def risks():
    department = request.args.get('department', '').strip()
    risks_data = get_risks_data(department if department else None)
    departments = get_all_departments()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'html': render_template('risk_partial.html', risques=risks_data),
            'count': len(risks_data)
        })
    
    return render_template('risks.html', 
                         risques=risks_data,
                         departments=departments,
                         selected_department=department)

@main_routes.route('/api/risks')
def api_risks():
    department = request.args.get('department', '').strip()
    limit = request.args.get('limit', 100, type=int)
    risks_data = get_risks_data(department if department else None, limit)
    return jsonify(risks_data)

# Nouvelles routes pour la carte
@main_routes.route('/map')
def map_view():
    """Affiche la page de carte interactive des risques climatiques"""
    return render_template('map.html')

@main_routes.route('/api/map-data')
def map_data():
    """API endpoint pour fournir les données de risque pour la carte"""
    risk_type = request.args.get('risk_type', 'overall_risk')
    timestamp = request.args.get('timestamp')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Vérifier si la base existe et contient des données
        try:
            cursor.execute("SELECT COUNT(*) FROM risks")
            count = cursor.fetchone()[0]
            if count == 0:
                return jsonify({
                    'error': 'La base de données ne contient aucune donnée'
                }), 404
        except sqlite3.OperationalError:
            return jsonify({
                'error': 'La table des risques n\'existe pas dans la base de données'
            }), 404
        
        # Récupérer d'abord tous les timestamps disponibles (pour le menu déroulant)
        cursor.execute("SELECT DISTINCT timestamp FROM risks ORDER BY timestamp DESC")
        timestamps = [row[0] for row in cursor.fetchall()]
        
        # Si aucun timestamp n'est spécifié, utiliser le plus récent
        if not timestamp and timestamps:
            timestamp = timestamps[0]
        
        # Vérifier les colonnes disponibles
        cursor.execute("PRAGMA table_info(risks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Construire la requête en fonction des colonnes disponibles
        if 'department_code' in columns and 'department_name' in columns:
            select_columns = ['department_code', 'department_name']
        elif 'department_code' in columns:
            select_columns = ['department_code', 'department_code AS department_name']
        elif 'department_name' in columns:
            select_columns = ['department_name', 'department_name AS department_code']
        else:
            return jsonify({
                'error': 'La structure de la base de données ne contient pas les colonnes nécessaires'
            }), 500
        
        # Ajouter les colonnes de risque si elles existent
        risk_columns = ['electrical_risk', 'flood_risk', 'heat_risk', 'wind_risk', 'overall_risk']
        for col in risk_columns:
            if col in columns:
                select_columns.append(col)
            else:
                select_columns.append('0 AS ' + col)
        
        # Construire la requête SQL
        query = "SELECT " + ", ".join(select_columns) + " FROM risks"
        
        # Ajouter la condition de timestamp si nécessaire
        if timestamp:
            query += " WHERE timestamp = ?"
            cursor.execute(query, (timestamp,))
        else:
            # Si pas de timestamp, prendre les données les plus récentes
            query += " ORDER BY timestamp DESC LIMIT 100"
            cursor.execute(query)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not results:
            return jsonify({
                'timestamps': timestamps,
                'current_timestamp': timestamp,
                'data': []
            })
        
        return jsonify({
            'timestamps': timestamps,
            'current_timestamp': timestamp,
            'data': results
        })
        
    except Exception as e:
        print(f"Erreur API map-data: {str(e)}")
        return jsonify({
            'error': f"Une erreur s'est produite: {str(e)}"
        }), 500