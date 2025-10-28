from flask import Flask, render_template, jsonify, request, session
from flask_session import Session
from database import get_db_connection, test_connection
import os

app = Flask(__name__)

# Configuración
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
Session(app)

# Importar módulos
from modules.prospectos import prospectos_bp
from modules.prospectos_activos import prospectos_activos_bp

# Registrar blueprints
app.register_blueprint(prospectos_bp, url_prefix='/prospectos')
app.register_blueprint(prospectos_activos_bp, url_prefix='/prospectos_activos')

@app.route('/')
def index():
    """Página principal del dashboard - redirige a prospectos raw"""
    return render_template('base.html', current_module='prospectos')

@app.route('/configuraciones')
def configuraciones():
    """Página de configuraciones"""
    return render_template('base.html', current_module='configuraciones')

@app.route('/api/theme', methods=['GET', 'POST'])
def theme():
    """API para gestionar el tema del usuario"""
    if request.method == 'POST':
        data = request.get_json()
        theme_color = data.get('theme', '#25D366')
        session['theme_color'] = theme_color
        return jsonify({'success': True, 'theme': theme_color})
    else:
        theme_color = session.get('theme_color', '#25D366')
        return jsonify({'theme': theme_color})

@app.route('/health')
def health():
    """Endpoint para verificar el estado de la aplicación"""
    return jsonify({
        'status': 'ok',
        'message': 'WhatsApp Dashboard is running'
    })

@app.route('/db-test')
def db_test():
    """Endpoint para probar la conexión a la base de datos"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            cursor.close()
            conn.close()
            return jsonify({
                'status': 'success',
                'message': 'Database connection successful',
                'version': db_version
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'Could not connect to database'
        }), 500

if __name__ == '__main__':
    print("Iniciando WhatsApp Dashboard...")
    print("Probando conexión a la base de datos...")
    test_connection()
    app.run(host='0.0.0.0', port=5000, debug=True)
