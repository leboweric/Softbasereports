from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import re
from datetime import datetime

simple_test_bp = Blueprint('simple_test', __name__)

@simple_test_bp.route('/api/simple-test/azure-sql', methods=['GET'])
@jwt_required()
def simple_azure_test():
    """Simple test to demonstrate Azure SQL firewall error"""
    
    result = {
        'test': 'Azure SQL Connection',
        'credentials': {
            'server': 'evo1-sql-replica.database.windows.net',
            'database': 'evo',
            'username': 'ben002user',
            'status': 'Using provided credentials'
        }
    }
    
    try:
        import pymssql
        
        # Attempt connection
        conn = pymssql.connect(
            server='evo1-sql-replica.database.windows.net',
            user='ben002user',
            password='g6O8CE5mT83mDYOW',
            database='evo',
            timeout=30
        )
        conn.close()
        
        result['status'] = 'SUCCESS'
        result['message'] = 'Connected successfully!'
        
    except Exception as e:
        result['status'] = 'FAILED'
        result['error'] = {
            'type': type(e).__name__,
            'message': str(e),
            'error_code': getattr(e, 'args', [None])[0] if hasattr(e, 'args') else None
        }
        
        # Extract IP if present
        error_str = str(e)
        if "Client with IP address" in error_str:
            import re
            ip_match = re.search(r"Client with IP address '(\d+\.\d+\.\d+\.\d+)'", error_str)
            if ip_match:
                result['blocked_ip'] = ip_match.group(1)
                result['firewall_issue'] = True
                result['solution'] = "Please add this IP to Azure SQL firewall or enable 'Allow Azure services'"
    
    return jsonify(result), 200

@simple_test_bp.route('/api/test/azure-connection', methods=['GET'])
def public_azure_test():
    """Public endpoint to test Azure SQL connection - no auth required"""
    
    result = {
        'test': 'Azure SQL Connection Check',
        'timestamp': datetime.now().isoformat(),
        'server': 'evo1-sql-replica.database.windows.net'
    }
    
    try:
        import pymssql
        
        # Attempt connection
        conn = pymssql.connect(
            server='evo1-sql-replica.database.windows.net',
            user='ben002user',
            password='g6O8CE5mT83mDYOW',
            database='evo',
            timeout=10
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        result['status'] = 'SUCCESS'
        result['message'] = 'Connected successfully to Azure SQL!'
        result['sql_version'] = version[:50] + '...' if len(version) > 50 else version
        
    except Exception as e:
        result['status'] = 'FAILED'
        result['error'] = str(e)
        
        # Extract IP if firewall error
        error_str = str(e)
        if "Client with IP address" in error_str:
            import re
            ip_match = re.search(r"Client with IP address '(\d+\.\d+\.\d+\.\d+)'", error_str)
            if ip_match:
                blocked_ip = ip_match.group(1)
                result['blocked_ip'] = blocked_ip
                result['is_railway_ip'] = blocked_ip.startswith('162.220.234.')
                result['message'] = f"Firewall blocking IP: {blocked_ip}"
    
    return jsonify(result), 200