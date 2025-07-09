from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import traceback

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