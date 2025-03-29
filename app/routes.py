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