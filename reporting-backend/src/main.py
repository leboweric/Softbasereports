"""
Softbase Reports Backend API
Version: 1.0.3 - URGENT: Fix login navigation data
"""
import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# Force redeploy - navigation cleanup for Database Explorer and AI Query removal
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp
from src.routes.reports import reports_bp
from src.routes.ai_query import ai_query_bp
from src.routes.custom_reports import custom_reports_bp
from src.routes.organization import organization_bp
from src.routes.database import database_bp
from src.routes.database_explorer import explorer_bp
from src.routes.debug import debug_bp
from src.routes.test_connections import test_bp
from src.routes.softbase_data import softbase_bp
from src.routes.connection_diagnostics import diagnostics_bp
from src.routes.simple_test import simple_test_bp
from src.routes.softbase_reports import softbase_reports_bp
from src.routes.dashboard_optimized import dashboard_optimized_bp
from src.routes.accounting_diagnostics import accounting_diagnostics_bp
from src.routes.diagnostics.expense_search_diagnostic import expense_search_diagnostic_bp
from src.routes.diagnostics.invoice_columns_diagnostic import invoice_columns_diagnostic_bp
from src.routes.diagnostics.find_expense_accounts import find_expense_accounts_bp
from src.routes.diagnostics.gl_table_structure import gl_table_structure_bp
from src.routes.diagnostics.analyze_gl_accounts import analyze_gl_accounts_bp
from src.routes.diagnostics.monthly_expense_debug import monthly_expense_debug_bp
from src.routes.dashboard_pace import dashboard_pace_bp
from src.routes.diagnostics.sales_pace_debug import sales_pace_debug_bp
from src.routes.sales_forecast import sales_forecast_bp
from src.routes.ai_predictions import ai_predictions_bp
from src.routes.ai_query_test import ai_query_test_bp
from src.routes.equipment_diagnostic import equipment_diagnostic_bp
from src.routes.full_schema_export import full_schema_export_bp
from src.routes.simple_schema_export import simple_schema_export_bp
from src.routes.table_discovery import table_discovery_bp
from src.routes.employee_lookup import employee_bp
from src.routes.employee_diagnostic import employee_diagnostic_bp
from src.routes.invoice_field_diagnostic import invoice_field_diagnostic_bp
from src.routes.work_order_notes import notes_bp
from src.routes.postgres_diagnostic import postgres_diagnostic_bp
from src.routes.minitrac import minitrac_bp
from src.routes.user_management import user_management_bp
from src.routes.password_fix import password_fix_bp
from src.routes.password_fix_new import password_fix_bp as password_fix_new_bp
from src.routes.temp_login import temp_login_bp
from src.routes.user_diagnostic import user_diagnostic_bp
from src.routes.commission_settings import commission_settings_bp
from src.routes.rental_availability_diagnostic import rental_diag_bp
from src.routes.rental_exclusion_analysis import rental_exclusion_analysis_bp
from src.routes.rental_dept_diagnostic import rental_dept_diagnostic_bp
from src.routes.rental_status_discovery import rental_status_discovery_bp
from src.routes.rental_availability_test import rental_test_bp
from src.routes.rental_unit_investigation import rental_investigation_bp
from src.routes.check_rental_fleet import check_rental_fleet_bp
from src.routes.quote_diagnostic import quote_diagnostic_bp
from src.routes.check_hold_status import check_hold_bp
from src.services.postgres_service import get_postgres_db
from src.init_rbac import initialize_all_rbac

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
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(ai_query_bp, url_prefix='/api/ai')
app.register_blueprint(custom_reports_bp, url_prefix='/api/custom-reports')
app.register_blueprint(organization_bp, url_prefix='/api/organization')
app.register_blueprint(database_bp)
app.register_blueprint(explorer_bp)
app.register_blueprint(debug_bp)
app.register_blueprint(test_bp)
app.register_blueprint(softbase_bp)
app.register_blueprint(diagnostics_bp)
app.register_blueprint(simple_test_bp)
app.register_blueprint(softbase_reports_bp)
app.register_blueprint(dashboard_optimized_bp)
app.register_blueprint(accounting_diagnostics_bp)
app.register_blueprint(expense_search_diagnostic_bp)
app.register_blueprint(invoice_columns_diagnostic_bp)
app.register_blueprint(find_expense_accounts_bp)
app.register_blueprint(gl_table_structure_bp)
app.register_blueprint(analyze_gl_accounts_bp)
app.register_blueprint(monthly_expense_debug_bp)
app.register_blueprint(dashboard_pace_bp)
app.register_blueprint(sales_pace_debug_bp)
app.register_blueprint(sales_forecast_bp)
app.register_blueprint(ai_predictions_bp)
app.register_blueprint(ai_query_test_bp, url_prefix='/api/ai-test')
app.register_blueprint(equipment_diagnostic_bp)
app.register_blueprint(full_schema_export_bp)
app.register_blueprint(simple_schema_export_bp)
app.register_blueprint(table_discovery_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(employee_diagnostic_bp)
app.register_blueprint(invoice_field_diagnostic_bp)
app.register_blueprint(notes_bp, url_prefix='/api/work-orders')
app.register_blueprint(postgres_diagnostic_bp)
app.register_blueprint(minitrac_bp)
app.register_blueprint(user_management_bp, url_prefix='/api')
app.register_blueprint(password_fix_bp)
app.register_blueprint(password_fix_new_bp)
app.register_blueprint(temp_login_bp)
app.register_blueprint(user_diagnostic_bp)
app.register_blueprint(commission_settings_bp)
app.register_blueprint(rental_diag_bp)
app.register_blueprint(rental_exclusion_analysis_bp)
app.register_blueprint(rental_dept_diagnostic_bp)
app.register_blueprint(rental_status_discovery_bp)
app.register_blueprint(rental_test_bp)
app.register_blueprint(rental_investigation_bp)
app.register_blueprint(check_rental_fleet_bp)
app.register_blueprint(quote_diagnostic_bp)
app.register_blueprint(check_hold_bp)

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
    
    # Initialize RBAC roles and permissions
    try:
        initialize_all_rbac()
    except Exception as e:
        print(f"⚠️  RBAC initialization failed: {e}")
        # Don't crash the app if RBAC init fails
        pass

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
    # Initialize PostgreSQL tables on startup
    try:
        postgres_db = get_postgres_db()
        if postgres_db:
            postgres_db.create_tables()
            print("✅ PostgreSQL tables initialized")
    except Exception as e:
        print(f"⚠️ Could not initialize PostgreSQL tables: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

