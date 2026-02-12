from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import os
import logging

from flask_jwt_extended import get_jwt_identity
from src.models.user import User
from src.utils.tenant_utils import get_tenant_schema

test_bp = Blueprint('test_connections', __name__)
logger = logging.getLogger(__name__)

@test_bp.route('/api/test/connection-methods', methods=['GET'])
@jwt_required()
def test_connection_methods():
    """Try different connection methods to Azure SQL"""
    results = []
    
    server = os.environ.get('AZURE_SQL_SERVER', 'evo1-sql-replica.database.windows.net')
    database = os.environ.get('AZURE_SQL_DATABASE', 'evo')
    username = os.environ.get('AZURE_SQL_USERNAME', 'ben002user')
    password = os.environ.get('AZURE_SQL_PASSWORD', 'g6O8CE5mT83mDYOW')
    
    # Test 1: Standard connection
    try:
        import pymssql
        conn = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database
        )
        conn.close()
        results.append({'method': 'Standard', 'status': 'success'})
    except Exception as e:
        results.append({'method': 'Standard', 'status': 'failed', 'error': str(e)[:200]})
    
    # Test 2: With port
    try:
        import pymssql
        conn = pymssql.connect(
            server=f"{server},1433",
            user=username,
            password=password,
            database=database
        )
        conn.close()
        results.append({'method': 'With port 1433', 'status': 'success'})
    except Exception as e:
        results.append({'method': 'With port 1433', 'status': 'failed', 'error': str(e)[:200]})
    
    # Test 3: With username@server format
    try:
        import pymssql
        server_name = server.split('.')[0]
        azure_username = f"{username}@{server_name}"
        conn = pymssql.connect(
            server=server,
            user=azure_username,
            password=password,
            database=database
        )
        conn.close()
        results.append({'method': f'Username format: {azure_username}', 'status': 'success'})
    except Exception as e:
        results.append({'method': f'Username format: {azure_username}', 'status': 'failed', 'error': str(e)[:200]})
    
    # Test 4: Try different TDS versions
    for tds_version in ['7.0', '7.1', '7.2', '7.3', '7.4', '8.0']:
        try:
            import pymssql
            conn = pymssql.connect(
                server=server,
                user=username,
                password=password,
                database=database,
                tds_version=tds_version
            )
            conn.close()
            results.append({'method': f'TDS version {tds_version}', 'status': 'success'})
        except Exception as e:
            results.append({'method': f'TDS version {tds_version}', 'status': 'failed', 'error': str(e)[:200]})
    
    # Test 5: Without encryption
    try:
        import pymssql
        conn = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            encrypt=False
        )
        conn.close()
        results.append({'method': 'Without encryption', 'status': 'success'})
    except Exception as e:
        results.append({'method': 'Without encryption', 'status': 'failed', 'error': str(e)[:200]})
    
    return jsonify({
        'server': server,
        'database': database,
        'username': username,
        'results': results
    }), 200