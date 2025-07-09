from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import os
import sys
import importlib.util

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/api/debug/environment', methods=['GET'])
@jwt_required()
def check_environment():
    """Debug endpoint to check environment and modules"""
    
    # Check environment variables
    env_vars = {
        'AZURE_SQL_SERVER': os.environ.get('AZURE_SQL_SERVER', 'NOT SET'),
        'AZURE_SQL_DATABASE': os.environ.get('AZURE_SQL_DATABASE', 'NOT SET'),
        'AZURE_SQL_USERNAME': os.environ.get('AZURE_SQL_USERNAME', 'NOT SET'),
        'AZURE_SQL_PASSWORD': 'SET' if os.environ.get('AZURE_SQL_PASSWORD') else 'NOT SET',
        'PORT': os.environ.get('PORT', 'NOT SET'),
        'PYTHON_VERSION': sys.version
    }
    
    # Check if SQL modules are available
    modules_status = {}
    
    # Check pyodbc (primary driver)
    try:
        import pyodbc
        modules_status['pyodbc'] = {
            'available': True,
            'version': pyodbc.version,
            'drivers': pyodbc.drivers()
        }
    except ImportError as e:
        modules_status['pyodbc'] = {
            'available': False,
            'error': str(e)
        }
    
    
    # Test actual database connection
    connection_test = {'status': 'not_tested', 'error': None}
    
    if modules_status['pyodbc']['available']:
        try:
            from ..services.azure_sql_service import AzureSQLService
            db = AzureSQLService()
            if db.test_connection():
                # Try to get version info
                version_info = db.execute_query("SELECT @@VERSION AS version")
                connection_test = {
                    'status': 'connected',
                    'sql_version': version_info[0]['version'] if version_info else 'unknown'
                }
            else:
                connection_test = {
                    'status': 'failed',
                    'error': 'Connection test failed'
                }
        except Exception as e:
            connection_test = {
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    return jsonify({
        'environment': env_vars,
        'modules': modules_status,
        'connection_test': connection_test,
        'system_info': {
            'platform': sys.platform,
            'python_path': sys.path[:5]  # First 5 paths
        }
    }), 200

@debug_bp.route('/api/debug/test-query', methods=['GET'])
@jwt_required()
def test_query():
    """Test a simple query against the database"""
    try:
        from ..services.azure_sql_service import AzureSQLService
        
        db = AzureSQLService()
        
        # Test basic connection
        if not db.test_connection():
            return jsonify({
                'success': False,
                'error': 'Connection test failed'
            }), 500
        
        # Get tables
        tables = db.get_tables()
        
        # Try a simple query
        test_results = db.execute_query("SELECT TOP 5 name FROM sys.tables")
        
        return jsonify({
            'success': True,
            'tables_count': len(tables),
            'first_5_tables': tables[:5] if tables else [],
            'sys_tables': test_results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'error_details': {
                'module': e.__module__ if hasattr(e, '__module__') else 'unknown',
                'args': str(e.args) if hasattr(e, 'args') else 'none'
            }
        }), 500

@debug_bp.route('/api/debug/jwt-test', methods=['GET'])
@jwt_required()
def test_jwt():
    """Test JWT token decoding"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        return jsonify({
            'identity': identity,
            'identity_type': type(identity).__name__,
            'claims': claims
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        }), 500