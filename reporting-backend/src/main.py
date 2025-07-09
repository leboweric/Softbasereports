import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.reports import reports_bp
from src.routes.ai_query import ai_query_bp
from src.routes.custom_reports import custom_reports_bp
from src.routes.organization import organization_bp
from src.routes.database import database_bp
from src.routes.database_explorer import explorer_bp
from src.routes.debug import debug_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', os.environ.get('SECRET_KEY', 'dev-jwt-key-change-in-production'))
app.config['JWT_TOKEN_LOCATION'] = ['headers']

# Enable CORS for all routes
CORS(app, 
    origins="*",  # Allow all origins temporarily for debugging
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    supports_credentials=True,
    expose_headers=["Content-Type", "Authorization"]
)

# Initialize JWT
jwt = JWTManager(app)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(ai_query_bp, url_prefix='/api/ai')
app.register_blueprint(custom_reports_bp, url_prefix='/api/custom-reports')
app.register_blueprint(organization_bp, url_prefix='/api/organization')
app.register_blueprint(database_bp)
app.register_blueprint(explorer_bp)
app.register_blueprint(debug_bp)

# Database configuration
# Use PostgreSQL if DATABASE_URL is set, otherwise fall back to SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Railway PostgreSQL URL (postgres:// -> postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fall back to SQLite for local development
    database_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(database_dir, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(database_dir, 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Softbase Reports API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

