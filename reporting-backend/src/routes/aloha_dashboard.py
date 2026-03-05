"""
Aloha Holdings Executive Dashboard API
Consolidated view across all 3 SAP subsidiary companies
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Organization
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

aloha_dashboard_bp = Blueprint('aloha_dashboard', __name__)


def _get_org_settings(org):
    """Parse organization settings JSON"""
    if hasattr(org, 'settings') and org.settings:
        try:
            return json.loads(org.settings) if isinstance(org.settings, str) else org.settings
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


def _verify_aloha_user(user_id):
    """Verify user belongs to Aloha Holdings and return user, org"""
    user = User.query.get(user_id)
    if not user or not user.organization_id:
        return None, None, ('User not found', 404)
    
    org = Organization.query.get(user.organization_id)
    if not org or org.name != 'Aloha Holdings':
        return None, None, ('Access denied', 403)
    
    return user, org, None


@aloha_dashboard_bp.route('/api/aloha/dashboard/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """
    Get consolidated executive summary across all subsidiaries.
    Returns placeholder data until SAP connections are configured.
    """
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_user(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]
        
        settings = _get_org_settings(org)
        data_sources = settings.get('data_sources', {})
        
        # Build subsidiary status
        subsidiaries = []
        connected_count = 0
        for source_id in ['sap_sandia_plastics', 'sap_kauai_exclusive', 'sap_hawaii_care']:
            config = data_sources.get(source_id, {})
            is_connected = config.get('connected', False)
            if is_connected:
                connected_count += 1
            subsidiaries.append({
                'id': source_id,
                'name': config.get('name', source_id.replace('sap_', '').replace('_', ' ').title()),
                'connected': is_connected,
                'system_type': config.get('system_type', 'Not configured'),
            })
        
        # If no SAP connections configured, return setup guidance
        if connected_count == 0:
            return jsonify({
                'status': 'setup_required',
                'message': 'No SAP connections configured yet. Please configure data sources first.',
                'subsidiaries': subsidiaries,
                'setup_steps': [
                    'Go to Data Sources page',
                    'Configure SAP connection for each subsidiary',
                    'Test each connection',
                    'Run initial data sync'
                ]
            }), 200
        
        # Placeholder consolidated metrics (will be populated by ETL once SAP is connected)
        return jsonify({
            'status': 'active',
            'last_sync': None,  # Will be set by ETL
            'subsidiaries': subsidiaries,
            'connected_subsidiaries': connected_count,
            'total_subsidiaries': 3,
            'consolidated': {
                'total_revenue': None,
                'total_expenses': None,
                'net_income': None,
                'total_orders': None,
                'total_inventory_value': None,
                'total_ar': None,
                'total_ap': None,
            },
            'by_subsidiary': {
                sub['id']: {
                    'name': sub['name'],
                    'revenue': None,
                    'expenses': None,
                    'net_income': None,
                    'orders': None,
                } for sub in subsidiaries
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Aloha dashboard summary: {e}")
        return jsonify({'error': str(e)}), 500


@aloha_dashboard_bp.route('/api/aloha/dashboard/financials', methods=['GET'])
@jwt_required()
def get_financials():
    """Get consolidated financial data across subsidiaries"""
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_user(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]
        
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Placeholder - will be populated once SAP ETL is running
        return jsonify({
            'year': year,
            'status': 'awaiting_sap_connection',
            'monthly_data': [],
            'ytd_summary': {
                'revenue': None,
                'cogs': None,
                'gross_profit': None,
                'operating_expenses': None,
                'net_income': None,
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Aloha financials: {e}")
        return jsonify({'error': str(e)}), 500


@aloha_dashboard_bp.route('/api/aloha/dashboard/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    """Get consolidated inventory data across subsidiaries"""
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_user(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]
        
        subsidiary = request.args.get('subsidiary', 'all')
        
        return jsonify({
            'status': 'awaiting_sap_connection',
            'subsidiary_filter': subsidiary,
            'inventory': [],
            'summary': {
                'total_items': None,
                'total_value': None,
                'by_warehouse': [],
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Aloha inventory: {e}")
        return jsonify({'error': str(e)}), 500


@aloha_dashboard_bp.route('/api/aloha/dashboard/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Get consolidated order data across subsidiaries"""
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_user(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]
        
        subsidiary = request.args.get('subsidiary', 'all')
        days = request.args.get('days', 30, type=int)
        
        return jsonify({
            'status': 'awaiting_sap_connection',
            'subsidiary_filter': subsidiary,
            'days': days,
            'orders': [],
            'summary': {
                'total_orders': None,
                'total_value': None,
                'open_orders': None,
                'completed_orders': None,
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Aloha orders: {e}")
        return jsonify({'error': str(e)}), 500
