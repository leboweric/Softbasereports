"""
Aloha Holdings Data Sources API
Manages connections to 5 SAP ERP systems and 3 NetSuite systems (8 subsidiaries total)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Organization
import json
import os
import logging

logger = logging.getLogger(__name__)

aloha_data_sources_bp = Blueprint('aloha_data_sources', __name__)

# SAP subsidiaries
SAP_SOURCES = {
    'sap_sandia': 'Sandia',
    'sap_mercury': 'Mercury',
    'sap_ultimate_solutions': 'Ultimate Solutions',
    'sap_avalon': 'Avalon',
    'sap_orbot': 'Orbot',
}

# NetSuite subsidiaries
NETSUITE_SOURCES = {
    'ns_hawaii_care': 'Hawaii Care and Cleaning',
    'ns_kauai_exclusive': 'Kauai Exclusive',
    'ns_heavenly_vacations': 'Heavenly Vacations',
}

# All valid source IDs
VALID_SOURCES = {**SAP_SOURCES, **NETSUITE_SOURCES}

# Valid SAP system types
VALID_SAP_TYPES = ['s4hana', 'business_one', 'ecc', 'bydesign', 'business_bydesign']

# Valid SAP connection methods
VALID_SAP_CONNECTION_METHODS = ['odata', 'service_layer', 'rfc', 'db_direct', 'api']

# Valid NetSuite connection methods
VALID_NS_CONNECTION_METHODS = ['token_based_auth', 'oauth2', 'suitetalk', 'restlet']


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
    sensitive_fields = ['password', 'api_key', 'secret', 'token', 'consumer_secret', 'token_secret', 'consumer_key', 'token_id']
    for field in sensitive_fields:
        if field in masked and masked[field]:
            masked[field] = '***'
    return masked


def _get_source_type(source_id):
    """Determine if a source is SAP or NetSuite"""
    if source_id.startswith('sap_'):
        return 'sap'
    elif source_id.startswith('ns_'):
        return 'netsuite'
    return None


@aloha_data_sources_bp.route('/api/aloha/data-sources', methods=['GET'])
@jwt_required()
def get_data_sources():
    """Get all configured data sources for Aloha Holdings"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return jsonify({'error': 'User not found or no organization'}), 404
        
        org = Organization.query.get(user.organization_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        if org.name != 'Aloha Holdings':
            return jsonify({'error': 'This endpoint is only available for Aloha Holdings'}), 403
        
        settings = _get_org_settings(org)
        data_sources = settings.get('data_sources', {})
        
        # Mask sensitive fields and group by type
        sap_sources = {}
        netsuite_sources = {}
        for source_id, config in data_sources.items():
            if source_id in VALID_SOURCES:
                masked = _mask_credentials(config)
                if source_id in SAP_SOURCES:
                    sap_sources[source_id] = masked
                elif source_id in NETSUITE_SOURCES:
                    netsuite_sources[source_id] = masked
        
        return jsonify({
            'sap_sources': sap_sources,
            'netsuite_sources': netsuite_sources,
            'all_sources': {**sap_sources, **netsuite_sources},
            'valid_sap_types': VALID_SAP_TYPES,
            'valid_sap_connection_methods': VALID_SAP_CONNECTION_METHODS,
            'valid_ns_connection_methods': VALID_NS_CONNECTION_METHODS,
            'subsidiary_names': VALID_SOURCES,
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Aloha data sources: {e}")
        return jsonify({'error': str(e)}), 500


@aloha_data_sources_bp.route('/api/aloha/data-sources/<source_id>', methods=['PUT'])
@jwt_required()
def update_data_source(source_id):
    """Update a specific data source configuration"""
    try:
        if source_id not in VALID_SOURCES:
            return jsonify({'error': f'Invalid source ID. Must be one of: {list(VALID_SOURCES.keys())}'}), 400
        
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
        source_type = _get_source_type(source_id)
        
        # Validate SAP-specific fields
        if source_type == 'sap':
            if 'system_type' in data and data['system_type'] and data['system_type'] not in VALID_SAP_TYPES:
                return jsonify({'error': f'Invalid system_type. Must be one of: {VALID_SAP_TYPES}'}), 400
            if 'connection_method' in data and data['connection_method'] and data['connection_method'] not in VALID_SAP_CONNECTION_METHODS:
                return jsonify({'error': f'Invalid connection_method. Must be one of: {VALID_SAP_CONNECTION_METHODS}'}), 400
        
        # Validate NetSuite-specific fields
        if source_type == 'netsuite':
            if 'connection_method' in data and data['connection_method'] and data['connection_method'] not in VALID_NS_CONNECTION_METHODS:
                return jsonify({'error': f'Invalid connection_method. Must be one of: {VALID_NS_CONNECTION_METHODS}'}), 400
        
        # Merge with existing config (don't overwrite secrets with masked values)
        existing = settings['data_sources'].get(source_id, {})
        sensitive_fields = ['password', 'api_key', 'secret', 'token', 'consumer_secret', 'token_secret', 'consumer_key', 'token_id']
        for key, value in data.items():
            if key in sensitive_fields and value == '***':
                continue
            existing[key] = value
        
        settings['data_sources'][source_id] = existing
        org.settings = json.dumps(settings)
        db.session.commit()
        
        logger.info(f"Updated Aloha data source {source_id}: {VALID_SOURCES.get(source_id, 'unknown')}")
        
        return jsonify({
            'message': f'{VALID_SOURCES.get(source_id, source_id)} configuration saved',
            'source': _mask_credentials(existing)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating Aloha data source {source_id}: {e}")
        return jsonify({'error': str(e)}), 500


@aloha_data_sources_bp.route('/api/aloha/data-sources/<source_id>/test', methods=['POST'])
@jwt_required()
def test_data_source(source_id):
    """Test connection to a specific data source"""
    try:
        if source_id not in VALID_SOURCES:
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
        
        source_type = _get_source_type(source_id)
        
        if source_type == 'sap':
            return _test_sap_connection(source_config, source_id)
        elif source_type == 'netsuite':
            return _test_netsuite_connection(source_config, source_id)
        else:
            return jsonify({'success': False, 'message': 'Unknown source type'}), 400
        
    except Exception as e:
        logger.error(f"Error testing Aloha data source {source_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def _test_sap_connection(config, source_id):
    """Test SAP connection based on connection method"""
    system_type = config.get('system_type', '')
    connection_method = config.get('connection_method', '')
    host = config.get('host', '')
    
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
    
    # Placeholder — actual SAP connection testing
    return jsonify({
        'success': False,
        'message': f'SAP {system_type} connection test for {VALID_SOURCES.get(source_id, source_id)} is pending. Connection method: {connection_method}. Awaiting credentials from IT.'
    }), 200


def _test_netsuite_connection(config, source_id):
    """Test NetSuite connection"""
    account_id = config.get('account_id', '')
    
    if not account_id:
        return jsonify({
            'success': False,
            'message': 'NetSuite Account ID not configured.'
        }), 400
    
    token_id = config.get('token_id', '')
    token_secret = config.get('token_secret', '')
    
    if not token_id or not token_secret:
        return jsonify({
            'success': False,
            'message': 'NetSuite Token-Based Authentication credentials not configured. Need Token ID and Token Secret.'
        }), 400
    
    # Placeholder — actual NetSuite connection testing
    return jsonify({
        'success': False,
        'message': f'NetSuite connection test for {VALID_SOURCES.get(source_id, source_id)} is pending. Account: {account_id}. Awaiting full credentials.'
    }), 200
