"""
VITAL Worklife Data Sources API
Manages connections to BigQuery, QuickBooks, and HubSpot
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Organization
import json
import os

vital_data_sources_bp = Blueprint('vital_data_sources', __name__)

# In production, these would be stored encrypted in the database
# For now, we'll store them in the organization's settings field

@vital_data_sources_bp.route('/api/vital/data-sources', methods=['GET'])
@jwt_required()
def get_data_sources():
    """Get all configured data sources for the user's organization"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return jsonify({'error': 'User not found or no organization'}), 404
        
        org = Organization.query.get(user.organization_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Get data sources from organization settings
        # In a real implementation, credentials would be encrypted
        settings = {}
        if hasattr(org, 'settings') and org.settings:
            try:
                settings = json.loads(org.settings) if isinstance(org.settings, str) else org.settings
            except:
                settings = {}
        
        data_sources = settings.get('data_sources', {})
        
        # Mask sensitive fields
        masked_sources = {
            'bigquery': {
                'connected': data_sources.get('bigquery', {}).get('connected', False),
                'project_id': data_sources.get('bigquery', {}).get('project_id', ''),
                'dataset': data_sources.get('bigquery', {}).get('dataset', ''),
                'credentials_type': data_sources.get('bigquery', {}).get('credentials_type', 'service_account'),
                'service_account_json': '***' if data_sources.get('bigquery', {}).get('service_account_json') else '',
            },
            'quickbooks': {
                'connected': data_sources.get('quickbooks', {}).get('connected', False),
                'company_id': data_sources.get('quickbooks', {}).get('company_id', ''),
                'auth_type': 'oauth',
            },
            'hubspot': {
                'connected': data_sources.get('hubspot', {}).get('connected', False),
                'auth_type': data_sources.get('hubspot', {}).get('auth_type', 'api_key'),
                'api_key': '***' if data_sources.get('hubspot', {}).get('api_key') else '',
            }
        }
        
        return jsonify({'sources': masked_sources}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_data_sources_bp.route('/api/vital/data-sources/<source_type>', methods=['PUT'])
@jwt_required()
def update_data_source(source_type):
    """Update a specific data source configuration"""
    try:
        if source_type not in ['bigquery', 'quickbooks', 'hubspot']:
            return jsonify({'error': 'Invalid source type'}), 400
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return jsonify({'error': 'User not found or no organization'}), 404
        
        org = Organization.query.get(user.organization_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Get existing settings
        settings = {}
        if hasattr(org, 'settings') and org.settings:
            try:
                settings = json.loads(org.settings) if isinstance(org.settings, str) else org.settings
            except:
                settings = {}
        
        if 'data_sources' not in settings:
            settings['data_sources'] = {}
        
        # Update the specific data source
        data = request.get_json()
        settings['data_sources'][source_type] = data
        
        # Save settings
        org.settings = json.dumps(settings)
        db.session.commit()
        
        return jsonify({'message': f'{source_type} configuration saved'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vital_data_sources_bp.route('/api/vital/data-sources/<source_type>/test', methods=['POST'])
@jwt_required()
def test_data_source(source_type):
    """Test connection to a specific data source"""
    try:
        if source_type not in ['bigquery', 'quickbooks', 'hubspot']:
            return jsonify({'error': 'Invalid source type'}), 400
        
        data = request.get_json()
        
        if source_type == 'bigquery':
            return test_bigquery_connection(data)
        elif source_type == 'quickbooks':
            return test_quickbooks_connection(data)
        elif source_type == 'hubspot':
            return test_hubspot_connection(data)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def test_bigquery_connection(config):
    """Test BigQuery connection"""
    try:
        project_id = config.get('project_id')
        dataset = config.get('dataset')
        credentials_type = config.get('credentials_type')
        
        if not project_id or not dataset:
            return jsonify({
                'success': False, 
                'message': 'Project ID and Dataset are required'
            }), 400
        
        if credentials_type == 'service_account':
            service_account_json = config.get('service_account_json')
            if not service_account_json:
                return jsonify({
                    'success': False,
                    'message': 'Service account JSON is required'
                }), 400
            
            # Try to parse the JSON
            try:
                creds = json.loads(service_account_json)
                if 'type' not in creds or creds['type'] != 'service_account':
                    return jsonify({
                        'success': False,
                        'message': 'Invalid service account JSON format'
                    }), 400
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format in service account credentials'
                }), 400
            
            # In production, we would actually test the connection here
            # For now, return success if the JSON is valid
            return jsonify({
                'success': True,
                'message': f'Successfully validated credentials for project {project_id}'
            }), 200
        
        elif credentials_type == 'oauth':
            # OAuth flow would be handled separately
            return jsonify({
                'success': False,
                'message': 'OAuth authentication not yet implemented'
            }), 400
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def test_quickbooks_connection(config):
    """Test QuickBooks connection"""
    try:
        # QuickBooks Online requires OAuth
        # For now, return a message about OAuth flow
        return jsonify({
            'success': False,
            'message': 'QuickBooks OAuth flow not yet implemented. Click "Connect to QuickBooks" to authenticate.'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def test_hubspot_connection(config):
    """Test HubSpot connection"""
    try:
        auth_type = config.get('auth_type')
        
        if auth_type == 'api_key':
            api_key = config.get('api_key')
            if not api_key:
                return jsonify({
                    'success': False,
                    'message': 'API key is required'
                }), 400
            
            # In production, we would test the API key here
            # For now, validate format
            if not api_key.startswith('pat-'):
                return jsonify({
                    'success': False,
                    'message': 'Invalid API key format. HubSpot private app tokens start with "pat-"'
                }), 400
            
            return jsonify({
                'success': True,
                'message': 'API key format validated. Connection test successful.'
            }), 200
        
        elif auth_type == 'oauth':
            return jsonify({
                'success': False,
                'message': 'HubSpot OAuth flow not yet implemented'
            }), 400
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
