"""
Softbase Reports Backend API
Version: 1.0.4 - Fixed User Management roles loading error
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
# from src.routes.diagnostics.expense_search_diagnostic import expense_search_diagnostic_bp
# from src.routes.diagnostics.invoice_columns_diagnostic import invoice_columns_diagnostic_bp
# from src.routes.diagnostics.find_expense_accounts import find_expense_accounts_bp
# from src.routes.diagnostics.gl_table_structure import gl_table_structure_bp
# from src.routes.diagnostics.analyze_gl_accounts import analyze_gl_accounts_bp
# from src.routes.diagnostics.monthly_expense_debug import monthly_expense_debug_bp
from src.routes.dashboard_pace import dashboard_pace_bp
# from src.routes.diagnostics.sales_pace_debug import sales_pace_debug_bp
from src.routes.sales_forecast import sales_forecast_bp
from src.routes.ai_predictions import ai_predictions_bp
from src.routes.ai_query_test import ai_query_test_bp
from src.routes.equipment_diagnostic import equipment_diagnostic_bp
from src.routes.equipment_pm_diagnostic import equipment_pm_diagnostic_bp
from src.routes.pm_table_diagnostic import pm_table_diagnostic_bp
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
# from src.routes.password_fix_new import password_fix_bp as password_fix_new_bp  # Temporarily disabled - duplicate name
from src.routes.temp_login import temp_login_bp
from src.routes.user_diagnostic import user_diagnostic_bp
from src.routes.commission_settings import commission_settings_bp
from src.routes.manual_commissions import manual_commissions_bp
from src.routes.rental_availability_diagnostic import rental_diag_bp
from src.routes.rental_exclusion_analysis import rental_exclusion_analysis_bp
from src.routes.rental_dept_diagnostic import rental_dept_diagnostic_bp
from src.routes.rental_status_discovery import rental_status_discovery_bp
from src.routes.rental_availability_test import rental_test_bp
from src.routes.rental_unit_investigation import rental_investigation_bp
from src.routes.check_rental_fleet import check_rental_fleet_bp
from src.routes.quote_diagnostic import quote_diagnostic_bp
from src.routes.check_hold_status import check_hold_bp
from src.routes.inventory_diagnostic import inventory_diagnostic_bp
from src.routes.accounting_inventory import accounting_inventory_bp
from src.routes.depreciation_explorer import depreciation_explorer_bp
from src.routes.diagnostics import diagnostics_bp
from src.routes.gl_inventory_diagnostic import gl_inventory_diagnostic_bp
from src.routes.gl_inventory_report import gl_inventory_report_bp
from src.routes.equipment_gl_linker import equipment_gl_linker_bp
from src.routes.final_gl_inventory_report import final_gl_inventory_report_bp
from src.routes.parts_inventory import parts_inventory_bp
from src.routes.service_shop_work_orders import service_shop_bp
from src.routes.pm_report import pm_report_bp
from src.routes.database_query import database_query_bp
from src.routes.tenant_admin import tenant_admin_bp
from src.routes.scheduled_tasks import scheduled_tasks_bp
from src.routes.customer_details import customer_details_bp
from src.routes.pm_technician_performance import pm_technician_performance_bp
from src.routes.knowledge_base import knowledge_base_bp
from src.routes.service_assistant import service_assistant_bp
from src.routes.service_assistant_analytics import analytics_bp
from src.routes.currie_report import currie_bp
from src.routes.pl_report import pl_report_bp
from src.routes.diagnostic_602600 import diagnostic_bp
from src.routes.cashflow_widget import cashflow_widget_bp
from src.routes.pl_widget import pl_widget_bp
from src.routes.january_investigation import january_investigation_bp
from src.routes.migration_investigation import migration_investigation_bp
from src.routes.softbase_months_investigation import softbase_months_bp
from src.routes.october_investigation import october_investigation_bp
from src.routes.january_expense_investigation import january_expense_bp
from src.routes.qbr import qbr_bp
from src.routes.billing import billing_bp
from src.routes.sales_rep_comp import sales_rep_comp_bp
from src.routes.schema_explorer import schema_explorer_bp
from src.routes.invoice_investigator import invoice_investigator_bp
from src.routes.vital_setup import vital_setup_bp
from src.routes.vital_data_sources import vital_data_sources_bp
from src.routes.vital_hubspot import vital_hubspot_bp
from src.routes.vital_quickbooks import vital_quickbooks_bp
from src.routes.vital_azure_sql import vital_azure_sql_bp
from src.routes.vital_zoom import vital_zoom_bp
from src.routes.vital_finance import vital_finance_bp
from src.routes.vital_mobile_app import vital_mobile_app_bp
from src.etl.scheduler import register_etl_routes, init_etl_scheduler
from src.services.postgres_service import get_postgres_db
from src.services.forecast_scheduler import init_forecast_scheduler
from src.services.cache_warmer import init_cache_warmer
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
# app.register_blueprint(expense_search_diagnostic_bp)
# app.register_blueprint(invoice_columns_diagnostic_bp)
# app.register_blueprint(find_expense_accounts_bp)
# app.register_blueprint(gl_table_structure_bp)
# app.register_blueprint(analyze_gl_accounts_bp)
# app.register_blueprint(monthly_expense_debug_bp)
app.register_blueprint(dashboard_pace_bp)
# app.register_blueprint(sales_pace_debug_bp)
app.register_blueprint(sales_forecast_bp)
app.register_blueprint(ai_predictions_bp)
app.register_blueprint(ai_query_test_bp, url_prefix='/api/ai-test')
app.register_blueprint(equipment_diagnostic_bp)
app.register_blueprint(equipment_pm_diagnostic_bp)
app.register_blueprint(pm_table_diagnostic_bp)
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
# app.register_blueprint(password_fix_new_bp)  # Temporarily disabled - duplicate blueprint name
app.register_blueprint(temp_login_bp)
app.register_blueprint(user_diagnostic_bp)
app.register_blueprint(commission_settings_bp)
app.register_blueprint(manual_commissions_bp)
app.register_blueprint(rental_diag_bp)
app.register_blueprint(rental_exclusion_analysis_bp)
app.register_blueprint(rental_dept_diagnostic_bp)
app.register_blueprint(rental_status_discovery_bp)
app.register_blueprint(rental_test_bp)
app.register_blueprint(rental_investigation_bp)
app.register_blueprint(check_rental_fleet_bp)
app.register_blueprint(quote_diagnostic_bp)
app.register_blueprint(check_hold_bp)
app.register_blueprint(inventory_diagnostic_bp)
app.register_blueprint(accounting_inventory_bp)
app.register_blueprint(depreciation_explorer_bp)
app.register_blueprint(gl_inventory_diagnostic_bp)
app.register_blueprint(gl_inventory_report_bp)
app.register_blueprint(equipment_gl_linker_bp)
app.register_blueprint(final_gl_inventory_report_bp)
app.register_blueprint(parts_inventory_bp)
app.register_blueprint(service_shop_bp)
app.register_blueprint(pm_report_bp)
app.register_blueprint(database_query_bp)
app.register_blueprint(tenant_admin_bp, url_prefix='/api/admin')
app.register_blueprint(scheduled_tasks_bp)
app.register_blueprint(customer_details_bp)
app.register_blueprint(pm_technician_performance_bp)
app.register_blueprint(knowledge_base_bp)
app.register_blueprint(service_assistant_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(currie_bp)
app.register_blueprint(pl_report_bp)
app.register_blueprint(diagnostic_bp)
app.register_blueprint(cashflow_widget_bp)
app.register_blueprint(pl_widget_bp)
app.register_blueprint(january_investigation_bp)
app.register_blueprint(migration_investigation_bp)
app.register_blueprint(softbase_months_bp)
app.register_blueprint(october_investigation_bp)
app.register_blueprint(january_expense_bp)
app.register_blueprint(qbr_bp)
app.register_blueprint(billing_bp, url_prefix='/api')
app.register_blueprint(sales_rep_comp_bp)
app.register_blueprint(schema_explorer_bp)
app.register_blueprint(invoice_investigator_bp)
app.register_blueprint(vital_setup_bp, url_prefix='/api/setup')
app.register_blueprint(vital_data_sources_bp)
app.register_blueprint(vital_hubspot_bp)
app.register_blueprint(vital_quickbooks_bp)
app.register_blueprint(vital_azure_sql_bp)
app.register_blueprint(vital_zoom_bp)
app.register_blueprint(vital_finance_bp)
app.register_blueprint(vital_mobile_app_bp)

# Register ETL management routes
register_etl_routes(app)

# app.register_blueprint(diagnostics_bp)  # Duplicate - already registered on line 119

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
    
    # Add salesman_name column if it doesn't exist (migration for existing databases)
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        if 'salesman_name' not in columns:
            print("Adding salesman_name column to user table...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN salesman_name VARCHAR(100)'))
                conn.commit()
            print("✅ salesman_name column added successfully!")
    except Exception as e:
        print(f"Note: salesman_name column migration: {e}")
    
    # Add settings column to organization table if it doesn't exist
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('organization')]
        if 'settings' not in columns:
            print("Adding settings column to organization table...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE organization ADD COLUMN settings TEXT'))
                conn.commit()
            print("✅ settings column added successfully!")
    except Exception as e:
        print(f"Note: settings column migration: {e}")

    # Add logo_url column to organization table if it doesn't exist
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('organization')]
        if 'logo_url' not in columns:
            print("Adding logo_url column to organization table...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE organization ADD COLUMN logo_url VARCHAR(255)'))
                conn.commit()
            print("✅ logo_url column added successfully!")
    except Exception as e:
        print(f"Note: logo_url column migration: {e}")
    
    # Add organization_id column to role table if it doesn't exist
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('role')]
        if 'organization_id' not in columns:
            print("Adding organization_id column to role table...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE role ADD COLUMN organization_id INTEGER REFERENCES organization(id)'))
                conn.commit()
            print("✅ organization_id column added to role table!")
    except Exception as e:
        print(f"Note: role organization_id column migration: {e}")
    
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


# Initialize PostgreSQL tables and scheduler on startup
# This runs when the app is imported by gunicorn
try:
    postgres_db = get_postgres_db()
    if postgres_db:
        postgres_db.create_tables()
        print("✅ PostgreSQL tables initialized")
except Exception as e:
    print(f"⚠️ Could not initialize PostgreSQL tables: {e}")

# Initialize the forecast scheduler (runs in background)
try:
    init_forecast_scheduler(app)
    print("✅ Forecast scheduler initialized")
except Exception as e:
    print(f"⚠️ Could not initialize forecast scheduler: {e}")

# Initialize the cache warmer (pre-warms dashboard cache on startup)
try:
    init_cache_warmer(app)
    print("✅ Cache warmer initialized")
except Exception as e:
    print(f"⚠️ Could not initialize cache warmer: {e}")

# Initialize ETL scheduler (runs daily at 2 AM if enabled)
try:
    init_etl_scheduler(app)
    print("✅ ETL scheduler initialized")
except Exception as e:
    print(f"⚠️ Could not initialize ETL scheduler: {e}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

