"""
Aloha Holdings Executive Dashboard API
Consolidated view across subsidiary companies, filtered by user's subsidiary access.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Organization
from src.routes.aloha_subsidiary_access import get_user_allowed_subsidiaries, ALL_SUBSIDIARIES
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
    Get consolidated executive summary across subsidiaries the user has access to.
    Returns placeholder data until ERP connections are configured.
    """
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_user(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]

        # Get user's allowed subsidiaries
        allowed_subs = get_user_allowed_subsidiaries(user_id)

        if not allowed_subs:
            return jsonify({
                'status': 'no_access',
                'message': 'You do not have access to any subsidiaries. Contact your administrator.',
                'subsidiaries': [],
                'sap_count': 0,
                'netsuite_count': 0,
            }), 200

        settings = _get_org_settings(org)
        data_sources = settings.get('data_sources', {})

        # Build subsidiary status — only for allowed subsidiaries
        subsidiaries = []
        connected_count = 0
        sap_count = 0
        netsuite_count = 0
        for source_id in allowed_subs:
            info = ALL_SUBSIDIARIES.get(source_id)
            if not info:
                continue
            config = data_sources.get(source_id, {})
            is_connected = config.get('connected', False)
            if is_connected:
                connected_count += 1
            if info['erp_type'] == 'SAP':
                sap_count += 1
            else:
                netsuite_count += 1
            subsidiaries.append({
                'id': source_id,
                'name': info['name'],
                'erp_type': info['erp_type'],
                'connected': is_connected,
                'system_type': config.get('system_type', config.get('erp_type', 'Not configured')),
            })

        # If no connections configured, return setup guidance
        if connected_count == 0:
            sap_names = [s['name'] for s in subsidiaries if s['erp_type'] == 'SAP']
            ns_names = [s['name'] for s in subsidiaries if s['erp_type'] == 'NetSuite']
            steps = ['Go to Data Sources page']
            if sap_names:
                steps.append(f"Configure SAP connections for {', '.join(sap_names)}")
            if ns_names:
                steps.append(f"Configure NetSuite connections for {', '.join(ns_names)}")
            steps.extend(['Test each connection', 'Run initial data sync'])

            return jsonify({
                'status': 'setup_required',
                'message': 'No ERP connections configured yet. Please configure data sources first.',
                'subsidiaries': subsidiaries,
                'sap_count': sap_count,
                'netsuite_count': netsuite_count,
                'setup_steps': steps
            }), 200

        # Placeholder consolidated metrics (will be populated by ETL)
        return jsonify({
            'status': 'active',
            'last_sync': None,
            'subsidiaries': subsidiaries,
            'connected_subsidiaries': connected_count,
            'total_subsidiaries': len(subsidiaries),
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
    """Get consolidated financial data across user's allowed subsidiaries"""
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_user(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]

        allowed_subs = get_user_allowed_subsidiaries(user_id)
        if not allowed_subs:
            return jsonify({'status': 'no_access', 'message': 'No subsidiary access assigned.'}), 200

        year = request.args.get('year', datetime.now().year, type=int)

        return jsonify({
            'year': year,
            'status': 'awaiting_erp_connection',
            'allowed_subsidiaries': allowed_subs,
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
    """Get consolidated inventory data across user's allowed subsidiaries"""
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_user(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]

        allowed_subs = get_user_allowed_subsidiaries(user_id)
        if not allowed_subs:
            return jsonify({'status': 'no_access', 'message': 'No subsidiary access assigned.'}), 200

        subsidiary = request.args.get('subsidiary', 'all')

        # Validate subsidiary filter against user's access
        if subsidiary != 'all' and subsidiary not in allowed_subs:
            return jsonify({'error': 'Access denied to this subsidiary'}), 403

        return jsonify({
            'status': 'awaiting_erp_connection',
            'subsidiary_filter': subsidiary,
            'allowed_subsidiaries': allowed_subs,
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
    """Get consolidated order data across user's allowed subsidiaries"""
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_user(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]

        allowed_subs = get_user_allowed_subsidiaries(user_id)
        if not allowed_subs:
            return jsonify({'status': 'no_access', 'message': 'No subsidiary access assigned.'}), 200

        subsidiary = request.args.get('subsidiary', 'all')
        days = request.args.get('days', 30, type=int)

        # Validate subsidiary filter against user's access
        if subsidiary != 'all' and subsidiary not in allowed_subs:
            return jsonify({'error': 'Access denied to this subsidiary'}), 403

        return jsonify({
            'status': 'awaiting_erp_connection',
            'subsidiary_filter': subsidiary,
            'allowed_subsidiaries': allowed_subs,
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
