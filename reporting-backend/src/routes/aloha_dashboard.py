"""
Aloha Holdings Executive Dashboard API
Consolidated view across all 8 subsidiary companies (5 SAP + 3 NetSuite)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Organization
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

aloha_dashboard_bp = Blueprint('aloha_dashboard', __name__)

# All subsidiaries with their ERP type
ALL_SUBSIDIARIES = {
    'sap_sandia': {'name': 'Sandia', 'erp': 'SAP'},
    'sap_mercury': {'name': 'Mercury', 'erp': 'SAP'},
    'sap_ultimate_solutions': {'name': 'Ultimate Solutions', 'erp': 'SAP'},
    'sap_avalon': {'name': 'Avalon', 'erp': 'SAP'},
    'sap_orbot': {'name': 'Orbot', 'erp': 'SAP'},
    'ns_hawaii_care': {'name': 'Hawaii Care and Cleaning', 'erp': 'NetSuite'},
    'ns_kauai_exclusive': {'name': 'Kauai Exclusive', 'erp': 'NetSuite'},
    'ns_heavenly_vacations': {'name': 'Heavenly Vacations', 'erp': 'NetSuite'},
}


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
    Get consolidated executive summary across all 8 subsidiaries.
    Returns placeholder data until ERP connections are configured.
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
        for source_id, info in ALL_SUBSIDIARIES.items():
            config = data_sources.get(source_id, {})
            is_connected = config.get('connected', False)
            if is_connected:
                connected_count += 1
            subsidiaries.append({
                'id': source_id,
                'name': info['name'],
                'erp_type': info['erp'],
                'connected': is_connected,
                'system_type': config.get('system_type', config.get('erp_type', 'Not configured')),
            })
        
        # If no connections configured, return setup guidance
        if connected_count == 0:
            return jsonify({
                'status': 'setup_required',
                'message': 'No ERP connections configured yet. Please configure data sources first.',
                'subsidiaries': subsidiaries,
                'sap_count': 5,
                'netsuite_count': 3,
                'setup_steps': [
                    'Go to Data Sources page',
                    'Configure SAP connections for Sandia, Mercury, Ultimate Solutions, Avalon, Orbot',
                    'Configure NetSuite connections for Hawaii Care and Cleaning, Kauai Exclusive, Heavenly Vacations',
                    'Test each connection',
                    'Run initial data sync'
                ]
            }), 200
        
        # Placeholder consolidated metrics (will be populated by ETL)
        return jsonify({
            'status': 'active',
            'last_sync': None,
            'subsidiaries': subsidiaries,
            'connected_subsidiaries': connected_count,
            'total_subsidiaries': 8,
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
                    'erp_type': sub['erp_type'],
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
        
        return jsonify({
            'year': year,
            'status': 'awaiting_erp_connection',
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
            'status': 'awaiting_erp_connection',
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
            'status': 'awaiting_erp_connection',
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
