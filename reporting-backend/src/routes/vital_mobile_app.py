"""
VITAL Mobile App Analytics Routes
Provides API endpoints for mobile app analytics from BigQuery GA4 data
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import os
from src.services.cache_service import cache_service

logger = logging.getLogger(__name__)

# Cache TTL for mobile app data (5 minutes)
CACHE_TTL = 300

vital_mobile_app_bp = Blueprint('vital_mobile_app', __name__)

def get_bigquery_service():
    """Get BigQuery service instance"""
    from src.services.bigquery_service import BigQueryService
    return BigQueryService()

def is_vital_user():
    """Check if current user belongs to VITAL organization"""
    try:
        from src.models.user import User, Organization
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return False
        
        org = Organization.query.get(user.organization_id)
        if org and org.name:
            return 'vital' in org.name.lower()
        return False
    except Exception as e:
        logger.error(f"Error checking VITAL user: {str(e)}")
        return False


# ==================== DASHBOARD ENDPOINTS ====================

@vital_mobile_app_bp.route('/api/vital/mobile-app/dashboard', methods=['GET'])
@jwt_required()
def get_mobile_app_dashboard():
    """Get complete mobile app analytics dashboard data (with caching)"""
    try:
        # Verify user is from VITAL organization
        if not is_vital_user():
            return jsonify({"error": "Access denied. This endpoint is only available for VITAL users."}), 403
        
        # Get days parameter (default 30)
        days = request.args.get('days', 30, type=int)
        days = min(max(days, 7), 90)  # Limit between 7 and 90 days
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Check cache first
        cache_key = f"vital_mobile_app_dashboard:{days}"
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                logger.info(f"Cache HIT for mobile app dashboard (days={days})")
                return jsonify({
                    "success": True,
                    "data": cached,
                    "from_cache": True
                })
        
        # Fetch from BigQuery
        logger.info(f"Cache MISS for mobile app dashboard (days={days}), fetching from BigQuery")
        bq = get_bigquery_service()
        dashboard_data = bq.get_dashboard_summary(days)
        
        # Cache the result
        cache_service.set(cache_key, dashboard_data, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": dashboard_data,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Mobile app dashboard error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@vital_mobile_app_bp.route('/api/vital/mobile-app/dau-mau', methods=['GET'])
@jwt_required()
def get_dau_mau():
    """Get DAU/MAU metrics"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        days = request.args.get('days', 30, type=int)
        bq = get_bigquery_service()
        data = bq.get_dau_mau_metrics(days)
        
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        logger.error(f"DAU/MAU error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_mobile_app_bp.route('/api/vital/mobile-app/daily-trend', methods=['GET'])
@jwt_required()
def get_daily_trend():
    """Get daily active users trend"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        days = request.args.get('days', 30, type=int)
        bq = get_bigquery_service()
        data = bq.get_daily_trend(days)
        
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        logger.error(f"Daily trend error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_mobile_app_bp.route('/api/vital/mobile-app/platforms', methods=['GET'])
@jwt_required()
def get_platforms():
    """Get platform breakdown"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        days = request.args.get('days', 30, type=int)
        bq = get_bigquery_service()
        data = bq.get_platform_breakdown(days)
        
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        logger.error(f"Platforms error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_mobile_app_bp.route('/api/vital/mobile-app/top-screens', methods=['GET'])
@jwt_required()
def get_top_screens():
    """Get top screens"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)
        bq = get_bigquery_service()
        data = bq.get_top_screens(days, limit)
        
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        logger.error(f"Top screens error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_mobile_app_bp.route('/api/vital/mobile-app/hourly-activity', methods=['GET'])
@jwt_required()
def get_hourly_activity():
    """Get hourly activity pattern"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        days = request.args.get('days', 30, type=int)
        bq = get_bigquery_service()
        data = bq.get_hourly_activity(days)
        
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        logger.error(f"Hourly activity error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_mobile_app_bp.route('/api/vital/mobile-app/key-actions', methods=['GET'])
@jwt_required()
def get_key_actions():
    """Get key user actions"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        days = request.args.get('days', 30, type=int)
        bq = get_bigquery_service()
        data = bq.get_key_actions(days)
        
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        logger.error(f"Key actions error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== HEALTH CHECK ====================

@vital_mobile_app_bp.route('/api/vital/mobile-app/health', methods=['GET'])
def mobile_app_health_check():
    """Check BigQuery API connectivity"""
    try:
        bq = get_bigquery_service()
        # Simple test - get DAU
        data = bq.get_dau_mau_metrics(7)
        return jsonify({
            "status": "healthy",
            "mau": data.get('mau', 0),
            "message": "BigQuery connection successful"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
