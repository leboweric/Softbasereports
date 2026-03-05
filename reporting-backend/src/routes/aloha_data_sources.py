"""
Aloha Holdings Data Sources API
Manages connections to 3 SAP ERP systems (one per subsidiary company)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Organization
import json
import os
import logging

logger = logging.getLogger(__name__)

aloha_data_sources_bp = Blueprint('aloha_data_sources', __name__)

# Valid SAP source IDs (one per subsidiary company)
VALID_SAP_SOURCES = ['sap_sandia_plastics', 'sap_kauai_exclusive', 'sap_hawaii_care']

# Human-readable names
SUBSIDIARY_NAMES = {
    'sap_sandia_plastics': 'Sandia Plastics',
    'sap_kauai_exclusive': 'Kauai Exclusive',
    'sap_hawaii_care': 'Hawaii Care & Cleaning',
}

# Valid SAP system types
VALID_SAP_TYPES = ['s4hana', 'business_one', 'ecc', 'bydesign', 'business_bydesign']

# Valid connection methods
VALID_CONNECTION_METHODS = ['odata', 'service_layer', 'rfc', 'db_direct', 'api']


def _get_org_settings(org):
    """Parse organization settings JSON"""
    if hasattr(org, 'settings') and org.settings:
        try:
            return json.loads(org.settings) if isinstance(org.settings, str) else org.settings
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


def _mask_credentials(source_config):
    """Mask sensitive fields in data source config for API responses"""
    masked = dict(source_config)
    sensitive_fields = ['password', 'api_key', 'secret', 'token']
    for field in sensitive_fields:
        if field in masked and masked[field]:
            masked[field] = '***'
    return masked


@aloha_data_sources_bp.route('/api/aloha/data-sources', methods=['GET'])
@jwt_required()
def get_data_sources():
    """Get all configured SAP data sources for Aloha Holdings"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return jsonify({'error': 'User not found or no organization'}), 404
        
        org = Organization.query.get(user.organization_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Verify this is an Aloha user
        if org.name != 'Aloha Holdings':
            return jsonify({'error': 'This endpoint is only available for Aloha Holdings'}), 403
        
        settings = _get_org_settings(org)
        data_sources = settings.get('data_sources', {})
        
        # Mask sensitive fields
        masked_sources = {}
        for source_id, config in data_sources.items():
            if source_id in VALID_SAP_SOURCES:
                masked_sources[source_id] = _mask_credentials(config)
        
        return jsonify({
            'sources': masked_sources,
            'valid_system_types': VALID_SAP_TYPES,
            'valid_connection_methods': VALID_CONNECTION_METHODS
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Aloha data sources: {e}")
        return jsonify({'error': str(e)}), 500


@aloha_data_sources_bp.route('/api/aloha/data-sources/<source_id>', methods=['PUT'])
@jwt_required()
def update_data_source(source_id):
    """Update a specific SAP data source configuration"""
    try:
        if source_id not in VALID_SAP_SOURCES:
            return jsonify({'error': f'Invalid source ID. Must be one of: {VALID_SAP_SOURCES}'}), 400
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return jsonify({'error': 'User not found or no organization'}), 404
        
        org = Organization.query.get(user.organization_id)
        if not org or org.name != 'Aloha Holdings':
            return jsonify({'error': 'This endpoint is only available for Aloha Holdings'}), 403
        
        settings = _get_org_settings(org)
        if 'data_sources' not in settings:
            settings['data_sources'] = {}
        
        data = request.get_json()
        
        # Validate system_type if provided
        if 'system_type' in data and data['system_type'] and data['system_type'] not in VALID_SAP_TYPES:
            return jsonify({'error': f'Invalid system_type. Must be one of: {VALID_SAP_TYPES}'}), 400
        
        # Validate connection_method if provided
        if 'connection_method' in data and data['connection_method'] and data['connection_method'] not in VALID_CONNECTION_METHODS:
            return jsonify({'error': f'Invalid connection_method. Must be one of: {VALID_CONNECTION_METHODS}'}), 400
        
        # Merge with existing config (don't overwrite password with '***')
        existing = settings['data_sources'].get(source_id, {})
        for key, value in data.items():
            if key in ['password', 'api_key', 'secret', 'token'] and value == '***':
                continue  # Don't overwrite with masked value
            existing[key] = value
        
        settings['data_sources'][source_id] = existing
        org.settings = json.dumps(settings)
        db.session.commit()
        
        logger.info(f"Updated Aloha data source {source_id}: {data.get('name', 'unnamed')}")
        
        return jsonify({
            'message': f'{source_id} configuration saved',
            'source': _mask_credentials(existing)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating Aloha data source {source_id}: {e}")
        return jsonify({'error': str(e)}), 500


@aloha_data_sources_bp.route('/api/aloha/data-sources/<source_id>/test', methods=['POST'])
@jwt_required()
def test_data_source(source_id):
    """Test connection to a specific SAP data source"""
    try:
        if source_id not in VALID_SAP_SOURCES:
            return jsonify({'error': f'Invalid source ID'}), 400
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return jsonify({'error': 'User not found'}), 404
        
        org = Organization.query.get(user.organization_id)
        if not org or org.name != 'Aloha Holdings':
            return jsonify({'error': 'Access denied'}), 403
        
        settings = _get_org_settings(org)
        source_config = settings.get('data_sources', {}).get(source_id, {})
        
        if not source_config:
            return jsonify({'success': False, 'message': 'Data source not configured'}), 400
        
        system_type = source_config.get('system_type', '')
        connection_method = source_config.get('connection_method', '')
        host = source_config.get('host', '')
        
        if not system_type:
            return jsonify({
                'success': False,
                'message': 'SAP system type not configured. Please select S/4HANA, Business One, ECC, or ByDesign.'
            }), 400
        
        if not host:
            return jsonify({
                'success': False,
                'message': 'Host/server address not configured.'
            }), 400
        
        # Test based on connection method
        if connection_method == 'odata':
            return _test_odata_connection(source_config)
        elif connection_method == 'service_layer':
            return _test_service_layer_connection(source_config)
        elif connection_method == 'db_direct':
            return _test_db_connection(source_config)
        elif connection_method == 'api':
            return _test_api_connection(source_config)
        else:
            return jsonify({
                'success': False,
                'message': f'Connection method "{connection_method}" not yet implemented. Supported: odata, service_layer, db_direct, api'
            }), 400
        
    except Exception as e:
        logger.error(f"Error testing Aloha data source {source_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def _test_odata_connection(config):
    """Test SAP OData API connection (S/4HANA, ECC)"""
    try:
        import requests as req
        
        host = config.get('host', '')
        port = config.get('port', '443')
        username = config.get('username', '')
        password = config.get('password', '')
        client = config.get('client', '')
        
        # Build OData service URL
        base_url = f"https://{host}:{port}/sap/opu/odata/sap/"
        
        # Try to reach the OData metadata endpoint
        params = {}
        if client:
            params['sap-client'] = client
        
        response = req.get(
            f"{base_url}API_BUSINESS_PARTNER/$metadata",
            auth=(username, password) if username else None,
            params=params,
            timeout=15,
            verify=True
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'Successfully connected to SAP OData at {host}. Metadata retrieved.'
            }), 200
        elif response.status_code == 401:
            return jsonify({
                'success': False,
                'message': 'Authentication failed. Check username and password.'
            }), 400
        elif response.status_code == 403:
            return jsonify({
                'success': False,
                'message': 'Access denied. The user may not have OData service authorization.'
            }), 400
        else:
            return jsonify({
                'success': False,
                'message': f'Connection returned status {response.status_code}: {response.text[:200]}'
            }), 400
            
    except req.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'message': f'Cannot reach {config.get("host")}. Check hostname and network/firewall settings.'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'OData test failed: {str(e)}'}), 500


def _test_service_layer_connection(config):
    """Test SAP Business One Service Layer connection"""
    try:
        import requests as req
        
        host = config.get('host', '')
        port = config.get('port', '50000')
        company_db = config.get('company_db', '')
        username = config.get('username', '')
        password = config.get('password', '')
        
        # Service Layer login endpoint
        login_url = f"https://{host}:{port}/b1s/v1/Login"
        
        payload = {
            'CompanyDB': company_db,
            'UserName': username,
            'Password': password
        }
        
        response = req.post(
            login_url,
            json=payload,
            timeout=15,
            verify=False  # B1 Service Layer often uses self-signed certs
        )
        
        if response.status_code == 200:
            session_id = response.json().get('SessionId', '')
            # Logout
            try:
                req.post(
                    f"https://{host}:{port}/b1s/v1/Logout",
                    cookies={'B1SESSION': session_id},
                    timeout=5,
                    verify=False
                )
            except:
                pass
            
            return jsonify({
                'success': True,
                'message': f'Successfully connected to SAP Business One Service Layer at {host}. Company DB: {company_db}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Login failed ({response.status_code}): {response.text[:200]}'
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Service Layer test failed: {str(e)}'}), 500


def _test_db_connection(config):
    """Test direct database connection to SAP HANA or SQL Server"""
    try:
        host = config.get('host', '')
        port = config.get('port', '')
        username = config.get('username', '')
        password = config.get('password', '')
        company_db = config.get('company_db', '')
        system_type = config.get('system_type', '')
        
        if system_type in ['s4hana', 'ecc']:
            # SAP HANA connection
            try:
                from hdbcli import dbapi
                conn = dbapi.connect(
                    address=host,
                    port=int(port) if port else 30015,
                    user=username,
                    password=password,
                    databaseName=company_db
                )
                cursor = conn.cursor()
                cursor.execute("SELECT CURRENT_TIMESTAMP FROM DUMMY")
                result = cursor.fetchone()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully connected to SAP HANA at {host}. Server time: {result[0]}'
                }), 200
            except ImportError:
                return jsonify({
                    'success': False,
                    'message': 'HANA database driver (hdbcli) not installed. Install with: pip install hdbcli'
                }), 500
                
        elif system_type == 'business_one':
            # SAP B1 uses SQL Server or HANA
            try:
                import pyodbc
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port or '1433'};DATABASE={company_db};UID={username};PWD={password}"
                conn = pyodbc.connect(conn_str, timeout=15)
                cursor = conn.cursor()
                cursor.execute("SELECT GETDATE()")
                result = cursor.fetchone()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully connected to SAP B1 database at {host}. Server time: {result[0]}'
                }), 200
            except ImportError:
                return jsonify({
                    'success': False,
                    'message': 'SQL Server driver (pyodbc) not installed.'
                }), 500
        else:
            return jsonify({
                'success': False,
                'message': f'Direct DB connection not supported for system type: {system_type}'
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database connection test failed: {str(e)}'}), 500


def _test_api_connection(config):
    """Test generic API connection"""
    try:
        import requests as req
        
        host = config.get('host', '')
        api_key = config.get('api_key', '')
        
        if not host.startswith('http'):
            host = f'https://{host}'
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        response = req.get(host, headers=headers, timeout=15)
        
        return jsonify({
            'success': response.status_code < 400,
            'message': f'API responded with status {response.status_code}' + 
                       (f': {response.text[:200]}' if response.status_code >= 400 else '')
        }), 200 if response.status_code < 400 else 400
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'API test failed: {str(e)}'}), 500


@aloha_data_sources_bp.route('/api/aloha/subsidiaries', methods=['GET'])
@jwt_required()
def get_subsidiaries():
    """Get summary of all subsidiary companies and their connection status"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return jsonify({'error': 'User not found'}), 404
        
        org = Organization.query.get(user.organization_id)
        if not org or org.name != 'Aloha Holdings':
            return jsonify({'error': 'Access denied'}), 403
        
        settings = _get_org_settings(org)
        data_sources = settings.get('data_sources', {})
        
        subsidiaries = []
        for source_id in VALID_SAP_SOURCES:
            config = data_sources.get(source_id, {})
            subsidiaries.append({
                'id': source_id,
                'name': config.get('name', source_id.replace('sap_subsidiary_', 'Subsidiary ')),
                'system_type': config.get('system_type', 'Not configured'),
                'connected': config.get('connected', False),
                'host': config.get('host', ''),
                'connection_method': config.get('connection_method', ''),
            })
        
        return jsonify({'subsidiaries': subsidiaries}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
