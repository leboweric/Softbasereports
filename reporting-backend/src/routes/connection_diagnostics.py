from flask import Blueprint, jsonify, make_response
from flask_jwt_extended import jwt_required
import os
import logging
from datetime import datetime
import traceback
import json

from flask_jwt_extended import get_jwt_identity
from src.models.user import User
from src.utils.tenant_utils import get_tenant_schema

logger = logging.getLogger(__name__)

diagnostics_bp = Blueprint('diagnostics', __name__)

@diagnostics_bp.route('/api/diagnostics/azure-sql-test', methods=['GET'])
@jwt_required()
def test_azure_sql_connection():
    """Comprehensive Azure SQL connection test with detailed error logging"""
    
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'credentials_provided': {
            'server': 'evo1-sql-replica.database.windows.net',
            'database': 'evo',
            'username': 'ben002user',
            'password': '***PROVIDED***'
        },
        'tests': []
    }
    
    # Test 1: Basic pymssql connection
    test_basic = {
        'test_name': 'Basic Connection Test',
        'description': 'Standard connection using provided credentials',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        import pymssql
        test_basic['pymssql_version'] = getattr(pymssql, '__version__', 'unknown')
        
        conn = pymssql.connect(
            server='evo1-sql-replica.database.windows.net',
            user='ben002user',
            password='g6O8CE5mT83mDYOW',
            database='evo',
            timeout=30,
            login_timeout=30
        )
        conn.close()
        test_basic['result'] = 'SUCCESS'
        test_basic['message'] = 'Connection successful'
    except Exception as e:
        test_basic['result'] = 'FAILED'
        test_basic['error_type'] = type(e).__name__
        test_basic['error_code'] = getattr(e, 'args', [None])[0] if hasattr(e, 'args') else None
        test_basic['error_message'] = str(e)
        test_basic['full_traceback'] = traceback.format_exc()
        
        # Extract key error details
        error_str = str(e)
        if "Client with IP address" in error_str:
            import re
            ip_match = re.search(r"Client with IP address '(\d+\.\d+\.\d+\.\d+)'", error_str)
            if ip_match:
                test_basic['blocked_ip_address'] = ip_match.group(1)
                test_basic['firewall_detected'] = True
    
    results['tests'].append(test_basic)
    
    # Test 2: Connection with port
    test_port = {
        'test_name': 'Connection with Explicit Port',
        'description': 'Connection with port 1433 explicitly specified',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        import pymssql
        conn = pymssql.connect(
            server='evo1-sql-replica.database.windows.net,1433',
            user='ben002user',
            password='g6O8CE5mT83mDYOW',
            database='evo'
        )
        conn.close()
        test_port['result'] = 'SUCCESS'
    except Exception as e:
        test_port['result'] = 'FAILED'
        test_port['error_type'] = type(e).__name__
        test_port['error_message'] = str(e)[:500]  # Truncate for readability
    
    results['tests'].append(test_port)
    
    # Test 3: Azure format username
    test_azure_format = {
        'test_name': 'Azure Username Format',
        'description': 'Using username@server format',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        import pymssql
        conn = pymssql.connect(
            server='evo1-sql-replica.database.windows.net',
            user='ben002user@evo1-sql-replica',
            password='g6O8CE5mT83mDYOW',
            database='evo'
        )
        conn.close()
        test_azure_format['result'] = 'SUCCESS'
    except Exception as e:
        test_azure_format['result'] = 'FAILED'
        test_azure_format['error_type'] = type(e).__name__
        test_azure_format['error_message'] = str(e)[:500]
    
    results['tests'].append(test_azure_format)
    
    # Test 4: Network connectivity
    test_network = {
        'test_name': 'Network Connectivity Test',
        'description': 'Test if we can reach the server',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        import socket
        # Try to resolve the hostname
        ip = socket.gethostbyname('evo1-sql-replica.database.windows.net')
        test_network['server_ip'] = ip
        
        # Try to connect to port 1433
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, 1433))
        sock.close()
        
        if result == 0:
            test_network['port_1433_reachable'] = True
            test_network['result'] = 'REACHABLE'
        else:
            test_network['port_1433_reachable'] = False
            test_network['result'] = 'PORT_BLOCKED'
    except Exception as e:
        test_network['result'] = 'FAILED'
        test_network['error'] = str(e)
    
    results['tests'].append(test_network)
    
    # Summary
    all_failed = all(test.get('result') == 'FAILED' for test in results['tests'][:3])
    firewall_detected = any(test.get('firewall_detected', False) for test in results['tests'])
    
    results['summary'] = {
        'all_connection_attempts_failed': all_failed,
        'firewall_detected': firewall_detected,
        'blocked_ip': next((test.get('blocked_ip_address') for test in results['tests'] if test.get('blocked_ip_address')), None),
        'error_code_40615_present': any('40615' in str(test.get('error_code', '')) for test in results['tests']),
        'conclusion': 'Azure SQL firewall is blocking connections from Railway servers' if firewall_detected else 'Connection failed for unknown reasons'
    }
    
    # Format as text report for easy sharing
    report_lines = [
        "AZURE SQL CONNECTION DIAGNOSTIC REPORT",
        "=" * 50,
        f"Generated: {results['timestamp']}",
        f"Server: {results['credentials_provided']['server']}",
        f"Database: {results['credentials_provided']['database']}",
        f"Username: {results['credentials_provided']['username']}",
        "",
        "TEST RESULTS:",
        "-" * 50
    ]
    
    for test in results['tests']:
        report_lines.extend([
            f"\n{test['test_name']}:",
            f"  Description: {test['description']}",
            f"  Result: {test['result']}"
        ])
        
        if test.get('error_message'):
            report_lines.append(f"  Error: {test['error_message']}")
        
        if test.get('blocked_ip_address'):
            report_lines.append(f"  BLOCKED IP ADDRESS: {test['blocked_ip_address']}")
            report_lines.append(f"  FIREWALL DETECTED: YES")
    
    report_lines.extend([
        "",
        "SUMMARY:",
        "-" * 50,
        f"All connection attempts failed: {results['summary']['all_connection_attempts_failed']}",
        f"Firewall detected: {results['summary']['firewall_detected']}",
        f"Azure SQL Error 40615 present: {results['summary']['error_code_40615_present']}"
    ])
    
    if results['summary']['blocked_ip']:
        report_lines.extend([
            f"Railway Server IP being blocked: {results['summary']['blocked_ip']}",
            "",
            "ACTION REQUIRED:",
            f"Please add IP address {results['summary']['blocked_ip']} to the Azure SQL firewall rules,",
            "or enable 'Allow Azure services and resources to access this server'",
            "in the Azure Portal under SQL Server -> Networking settings."
        ])
    
    results['text_report'] = "\n".join(report_lines)
    
    return jsonify(results), 200

@diagnostics_bp.route('/api/diagnostics/azure-sql-report', methods=['GET'])
@jwt_required()
def get_azure_sql_report():
    """Get a downloadable text report of the connection issues"""
    
    # Run the diagnostic test
    import json
    test_result = test_azure_sql_connection()
    data = json.loads(test_result[0].data)
    
    # Create response with text report
    response = make_response(data['text_report'])
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = f'attachment; filename=azure_sql_diagnostic_report_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.txt'
    
    return response