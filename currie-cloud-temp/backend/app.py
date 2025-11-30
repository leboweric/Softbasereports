"""
Currie Cloud Platform - Main Application
B2B SaaS for aggregating financial data from material handling dealerships.
"""
import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from src.config.settings import get_config
from src.models.database import db
from src.routes.auth import auth_bp
from src.routes.dealers import dealers_bp
from src.routes.reports import reports_bp
from src.routes.admin import admin_bp
from src.routes.data_sync import data_sync_bp


def create_app(config_class=None):
    """Application factory"""
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    # Configure CORS
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dealers_bp, url_prefix='/api/dealers')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(data_sync_bp, url_prefix='/api/sync')

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'currie-cloud'}

    return app


# Create app instance for Railway
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
