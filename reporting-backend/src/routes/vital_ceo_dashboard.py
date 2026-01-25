"""
VITAL CEO Dashboard Optimized API
Reads from pre-aggregated mart tables for fast loading
Falls back to live APIs when mart data is stale
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from src.services.postgres_service import PostgreSQLService
from src.services.cache_service import cache_service

logger = logging.getLogger(__name__)

vital_ceo_bp = Blueprint('vital_ceo', __name__)

# VITAL org_id
VITAL_ORG_ID = 6

# Cache TTLs
CACHE_TTL_SHORT = 60       # 1 minute
CACHE_TTL_MEDIUM = 300     # 5 minutes
CACHE_TTL_LONG = 900       # 15 minutes


def get_db():
    """Get PostgreSQL database connection"""
    return PostgreSQLService()


@vital_ceo_bp.route('/api/vital/ceo/dashboard', methods=['GET'])
@jwt_required()
def get_ceo_dashboard():
    """
    Get all CEO Dashboard data in a single optimized call
    Reads from mart tables for fast performance
    """
    try:
        days = request.args.get('days', 30, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = f"vital_ceo_dashboard:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                cached['from_cache'] = True
                return jsonify(cached)
        
        db = get_db()
        
        # Get all data from mart tables
        result = {
            'success': True,
            'from_cache': False,
            'data_freshness': {},
            'mobile_app': get_mobile_app_data(db, days),
            'call_center': get_call_center_data(db, days),
            'cms': get_cms_data(db, days),
            'hubspot': get_hubspot_data(db),
            'finance': get_finance_summary(db)
        }
        
        # Cache the result
        cache_service.set(cache_key, result, CACHE_TTL_MEDIUM)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"CEO Dashboard error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@vital_ceo_bp.route('/api/vital/ceo/mobile-app', methods=['GET'])
@jwt_required()
def get_mobile_app_optimized():
    """Get mobile app data from mart tables"""
    try:
        days = request.args.get('days', 30, type=int)
        cache_key = f"vital_ceo_mobile:{days}"
        
        cached = cache_service.get(cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'from_cache': True})
        
        db = get_db()
        data = get_mobile_app_data(db, days)
        
        cache_service.set(cache_key, data, CACHE_TTL_MEDIUM)
        return jsonify({'success': True, 'data': data, 'from_cache': False})
        
    except Exception as e:
        logger.error(f"Mobile app data error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@vital_ceo_bp.route('/api/vital/ceo/call-center', methods=['GET'])
@jwt_required()
def get_call_center_optimized():
    """Get call center data from mart tables"""
    try:
        days = request.args.get('days', 30, type=int)
        cache_key = f"vital_ceo_calls:{days}"
        
        cached = cache_service.get(cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'from_cache': True})
        
        db = get_db()
        data = get_call_center_data(db, days)
        
        cache_service.set(cache_key, data, CACHE_TTL_MEDIUM)
        return jsonify({'success': True, 'data': data, 'from_cache': False})
        
    except Exception as e:
        logger.error(f"Call center data error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@vital_ceo_bp.route('/api/vital/ceo/cms', methods=['GET'])
@jwt_required()
def get_cms_optimized():
    """Get CMS case data from mart tables"""
    try:
        days = request.args.get('days', 30, type=int)
        cache_key = f"vital_ceo_cms:{days}"
        
        cached = cache_service.get(cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'from_cache': True})
        
        db = get_db()
        data = get_cms_data(db, days)
        
        cache_service.set(cache_key, data, CACHE_TTL_MEDIUM)
        return jsonify({'success': True, 'data': data, 'from_cache': False})
        
    except Exception as e:
        logger.error(f"CMS data error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@vital_ceo_bp.route('/api/vital/ceo/refresh', methods=['POST'])
@jwt_required()
def refresh_ceo_dashboard():
    """Force refresh all CEO Dashboard data by clearing cache"""
    try:
        # Clear all CEO dashboard cache entries
        cache_service.delete("vital_ceo_")
        
        return jsonify({
            'success': True,
            'message': 'Dashboard cache cleared. Next request will fetch fresh data.'
        })
        
    except Exception as e:
        logger.error(f"Cache refresh error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# Data Fetching Functions (from mart tables)
# ============================================================

def get_mobile_app_data(db, days: int) -> dict:
    """Get mobile app analytics from mart_app_analytics"""
    try:
        # Get latest data and trend
        query = """
            SELECT 
                metric_date,
                daily_active_users,
                weekly_active_users,
                monthly_active_users,
                new_users,
                returning_users,
                total_sessions,
                avg_session_duration_secs,
                screens_per_session,
                top_screens
            FROM mart_app_analytics
            WHERE org_id = %s
            AND metric_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY metric_date DESC
        """
        rows = db.execute_query(query, (VITAL_ORG_ID, days))
        
        if not rows:
            return {
                'connected': False,
                'message': 'No mobile app data available'
            }
        
        latest = rows[0]
        
        # Calculate totals for the period
        total_dau = sum(r['daily_active_users'] or 0 for r in rows)
        total_sessions = sum(r['total_sessions'] or 0 for r in rows)
        total_new_users = sum(r['new_users'] or 0 for r in rows)
        
        # Build daily trend
        daily_trend = []
        for row in reversed(rows):
            daily_trend.append({
                'date': row['metric_date'].strftime('%Y-%m-%d') if row['metric_date'] else None,
                'dau': row['daily_active_users'] or 0,
                'sessions': row['total_sessions'] or 0,
                'new_users': row['new_users'] or 0
            })
        
        return {
            'connected': True,
            'last_updated': latest['metric_date'].isoformat() if latest['metric_date'] else None,
            'summary': {
                'daily_active_users': latest['daily_active_users'] or 0,
                'weekly_active_users': latest['weekly_active_users'] or 0,
                'monthly_active_users': latest['monthly_active_users'] or 0,
                'total_sessions_period': total_sessions,
                'new_users_period': total_new_users,
                'avg_session_duration': latest['avg_session_duration_secs'] or 0,
                'screens_per_session': float(latest['screens_per_session'] or 0)
            },
            'daily_trend': daily_trend
        }
        
    except Exception as e:
        logger.error(f"Error fetching mobile app data: {str(e)}")
        return {'connected': False, 'error': str(e)}


def get_call_center_data(db, days: int) -> dict:
    """Get call center metrics from mart_zoom_metrics"""
    try:
        query = """
            SELECT 
                metric_date,
                total_users,
                phone_users,
                total_calls,
                inbound_calls,
                outbound_calls,
                missed_calls,
                total_call_minutes,
                avg_call_duration_mins,
                queue_count
            FROM mart_zoom_metrics
            WHERE org_id = %s
            AND metric_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY metric_date DESC
        """
        rows = db.execute_query(query, (VITAL_ORG_ID, days))
        
        if not rows:
            return {
                'connected': False,
                'message': 'No call center data available'
            }
        
        latest = rows[0]
        
        # Calculate totals for the period
        total_calls = sum(r['total_calls'] or 0 for r in rows)
        total_inbound = sum(r['inbound_calls'] or 0 for r in rows)
        total_outbound = sum(r['outbound_calls'] or 0 for r in rows)
        total_missed = sum(r['missed_calls'] or 0 for r in rows)
        total_minutes = sum(r['total_call_minutes'] or 0 for r in rows)
        
        # Build daily trend
        daily_trend = []
        for row in reversed(rows):
            daily_trend.append({
                'date': row['metric_date'].strftime('%Y-%m-%d') if row['metric_date'] else None,
                'total': row['total_calls'] or 0,
                'inbound': row['inbound_calls'] or 0,
                'outbound': row['outbound_calls'] or 0,
                'missed': row['missed_calls'] or 0
            })
        
        return {
            'connected': True,
            'last_updated': latest['metric_date'].isoformat() if latest['metric_date'] else None,
            'summary': {
                'total_calls': total_calls,
                'inbound_calls': total_inbound,
                'outbound_calls': total_outbound,
                'missed_calls': total_missed,
                'total_minutes': total_minutes,
                'avg_call_duration': float(latest['avg_call_duration_mins'] or 0),
                'phone_users': latest['phone_users'] or 0,
                'queue_count': latest['queue_count'] or 0
            },
            'daily_trend': daily_trend
        }
        
    except Exception as e:
        logger.error(f"Error fetching call center data: {str(e)}")
        return {'connected': False, 'error': str(e)}


def get_cms_data(db, days: int) -> dict:
    """Get CMS case metrics from mart_case_metrics"""
    try:
        query = """
            SELECT 
                snapshot_date,
                total_cases,
                new_cases_30d,
                closed_cases_30d,
                cases_by_type,
                cases_by_status
            FROM mart_case_metrics
            WHERE org_id = %s
            ORDER BY snapshot_date DESC
            LIMIT 1
        """
        rows = db.execute_query(query, (VITAL_ORG_ID,))
        
        if not rows:
            return {
                'connected': False,
                'message': 'No CMS data available'
            }
        
        latest = rows[0]
        
        return {
            'connected': True,
            'last_updated': latest['snapshot_date'].isoformat() if latest['snapshot_date'] else None,
            'summary': {
                'total_cases': latest['total_cases'] or 0,
                'new_cases': latest['new_cases_30d'] or 0,
                'closed_cases': latest['closed_cases_30d'] or 0,
                'open_cases': (latest['total_cases'] or 0) - (latest['closed_cases_30d'] or 0)
            },
            'cases_by_type': latest['cases_by_type'] or {},
            'cases_by_status': latest['cases_by_status'] or {}
        }
        
    except Exception as e:
        logger.error(f"Error fetching CMS data: {str(e)}")
        return {'connected': False, 'error': str(e)}


def get_hubspot_data(db) -> dict:
    """Get HubSpot CRM data from mart_crm_deals"""
    try:
        query = """
            SELECT 
                snapshot_date,
                total_deals,
                open_deals,
                won_deals,
                lost_deals,
                total_pipeline_value,
                won_value,
                lost_value,
                average_deal_size,
                deals_by_stage
            FROM mart_crm_deals
            WHERE org_id = %s
            ORDER BY snapshot_date DESC
            LIMIT 1
        """
        rows = db.execute_query(query, (VITAL_ORG_ID,))
        
        if not rows:
            return {
                'connected': False,
                'message': 'No HubSpot data available'
            }
        
        latest = rows[0]
        
        # Calculate win rate
        won = latest['won_deals'] or 0
        lost = latest['lost_deals'] or 0
        win_rate = (won / (won + lost) * 100) if (won + lost) > 0 else 0
        
        return {
            'connected': True,
            'last_updated': latest['snapshot_date'].isoformat() if latest['snapshot_date'] else None,
            'summary': {
                'total_deals': latest['total_deals'] or 0,
                'open_deals': latest['open_deals'] or 0,
                'won_deals': won,
                'lost_deals': lost,
                'pipeline_value': float(latest['total_pipeline_value'] or 0),
                'won_value': float(latest['won_value'] or 0),
                'average_deal_size': float(latest['average_deal_size'] or 0),
                'win_rate': round(win_rate, 1)
            },
            'deals_by_stage': latest['deals_by_stage'] or {}
        }
        
    except Exception as e:
        logger.error(f"Error fetching HubSpot data: {str(e)}")
        return {'connected': False, 'error': str(e)}


def get_finance_summary(db) -> dict:
    """Get finance summary from existing finance tables"""
    try:
        # Get current year
        current_year = datetime.now().year
        
        # Get billing summary
        query = """
            SELECT 
                COUNT(*) as total_clients,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_clients,
                SUM(annual_value) as total_annual_value
            FROM finance_clients
            WHERE org_id = %s
        """
        rows = db.execute_query(query, (VITAL_ORG_ID,))
        
        if not rows or not rows[0]:
            return {'connected': False}
        
        summary = rows[0]
        
        # Get upcoming renewals count
        renewals_query = """
            SELECT COUNT(*) as count, SUM(annual_value) as value
            FROM finance_clients
            WHERE org_id = %s
            AND renewal_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '6 months'
        """
        renewals = db.execute_query(renewals_query, (VITAL_ORG_ID,))
        
        return {
            'connected': True,
            'summary': {
                'total_clients': summary['total_clients'] or 0,
                'active_clients': summary['active_clients'] or 0,
                'total_annual_value': float(summary['total_annual_value'] or 0),
                'upcoming_renewals_count': renewals[0]['count'] if renewals else 0,
                'upcoming_renewals_value': float(renewals[0]['value'] or 0) if renewals else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching finance data: {str(e)}")
        return {'connected': False, 'error': str(e)}
