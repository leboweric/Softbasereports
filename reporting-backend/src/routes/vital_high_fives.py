"""
VITAL High Fives Recognition Routes
Provides API endpoints for Microsoft Teams High Fives recognition tracking and analytics
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime
from src.services.cache_service import cache_service

logger = logging.getLogger(__name__)

# Cache TTL for recognition data (10 minutes)
CACHE_TTL = 600

vital_high_fives_bp = Blueprint('vital_high_fives', __name__)


def get_teams_service():
    """Get VITAL Teams service instance"""
    from src.services.vital_teams_service import VitalTeamsService
    return VitalTeamsService()


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


# ==================== HEALTH CHECK ====================

@vital_high_fives_bp.route('/api/vital/teams/health', methods=['GET'])
def teams_health_check():
    """Check Microsoft Teams API connectivity (no auth required for health check)"""
    try:
        service = get_teams_service()
        result = service.test_connection()
        
        if result['status'] == 'connected':
            return jsonify({
                "status": "healthy",
                "message": "Microsoft Teams API connection successful"
            })
        else:
            return jsonify({
                "status": "unhealthy",
                "error": result.get('error', 'Unknown error')
            }), 500
    except ValueError as e:
        return jsonify({
            "status": "not_configured",
            "error": str(e)
        }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ==================== CHANNEL DISCOVERY ====================

@vital_high_fives_bp.route('/api/vital/teams/channels', methods=['GET'])
@jwt_required()
def get_teams_channels():
    """Get list of all teams and channels"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_teams_service()
        teams = service.get_teams()
        
        # Get channels for each team
        teams_with_channels = []
        for team in teams.get('teams', []):
            team_id = team.get('id')
            team_name = team.get('displayName')
            
            try:
                channels = service.get_team_channels(team_id)
                teams_with_channels.append({
                    "id": team_id,
                    "name": team_name,
                    "channels": channels.get('channels', [])
                })
            except Exception as e:
                logger.warning(f"Could not get channels for team {team_name}: {str(e)}")
                teams_with_channels.append({
                    "id": team_id,
                    "name": team_name,
                    "channels": [],
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "data": {
                "total_teams": len(teams_with_channels),
                "teams": teams_with_channels
            }
        })
    except Exception as e:
        logger.error(f"Teams channels error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_high_fives_bp.route('/api/vital/teams/high-fives-channel', methods=['GET'])
@jwt_required()
def find_high_fives_channel():
    """Find the High Fives channel"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_teams_service()
        result = service.find_high_fives_channel()
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Find High Fives channel error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== RECOGNITION DATA ====================

@vital_high_fives_bp.route('/api/vital/high-fives/recognitions', methods=['GET'])
@jwt_required()
def get_recognitions():
    """Get all recognition data from the High Fives channel"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 90, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = f"vital_high_fives_recognitions:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                logger.info(f"Cache HIT for High Fives recognitions (days={days})")
                return jsonify({
                    "success": True,
                    "data": cached,
                    "from_cache": True
                })
        
        logger.info(f"Cache MISS for High Fives recognitions (days={days}), fetching from Teams API")
        service = get_teams_service()
        recognitions = service.get_high_fives_recognitions(days=days)
        
        # Cache the result
        cache_service.set(cache_key, recognitions, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": recognitions,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Get recognitions error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_high_fives_bp.route('/api/vital/high-fives/summary', methods=['GET'])
@jwt_required()
def get_recognition_summary():
    """Get summary statistics for recognitions"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 30, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = f"vital_high_fives_summary:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                logger.info(f"Cache HIT for High Fives summary (days={days})")
                return jsonify({
                    "success": True,
                    "data": cached,
                    "from_cache": True
                })
        
        logger.info(f"Cache MISS for High Fives summary (days={days}), fetching from Teams API")
        service = get_teams_service()
        summary = service.get_recognition_summary(days=days)
        
        # Cache the result
        cache_service.set(cache_key, summary, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": summary,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Get recognition summary error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== MONTHLY REPORTS ====================

@vital_high_fives_bp.route('/api/vital/high-fives/monthly-report', methods=['GET'])
@jwt_required()
def get_monthly_report():
    """Get recognition report for a specific month"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = f"vital_high_fives_monthly:{year}:{month}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                logger.info(f"Cache HIT for High Fives monthly report ({year}-{month})")
                return jsonify({
                    "success": True,
                    "data": cached,
                    "from_cache": True
                })
        
        logger.info(f"Cache MISS for High Fives monthly report ({year}-{month}), fetching from Teams API")
        service = get_teams_service()
        report = service.get_monthly_recognition_report(year=year, month=month)
        
        # Cache the result
        cache_service.set(cache_key, report, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": report,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Get monthly report error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== DASHBOARD ====================

@vital_high_fives_bp.route('/api/vital/high-fives/dashboard', methods=['GET'])
@jwt_required()
def get_high_fives_dashboard():
    """Get comprehensive High Fives dashboard data"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = "vital_high_fives_dashboard"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                logger.info("Cache HIT for High Fives dashboard")
                return jsonify({
                    "success": True,
                    "data": cached,
                    "from_cache": True
                })
        
        logger.info("Cache MISS for High Fives dashboard, fetching from Teams API")
        service = get_teams_service()
        
        dashboard_data = {
            "last_updated": datetime.now().isoformat()
        }
        
        # Get channel info
        try:
            channel_info = service.find_high_fives_channel()
            dashboard_data["channel"] = channel_info
        except Exception as e:
            logger.warning(f"Could not find High Fives channel: {str(e)}")
            dashboard_data["channel"] = {"found": False, "error": str(e)}
        
        # Get current month summary
        try:
            current_month = service.get_monthly_recognition_report()
            dashboard_data["current_month"] = {
                "year": current_month.get('year'),
                "month": current_month.get('month'),
                "total_recognitions": current_month.get('total_recognitions', 0),
                "unique_givers": current_month.get('unique_givers', 0),
                "unique_receivers": current_month.get('unique_receivers', 0),
                "top_givers": current_month.get('top_givers', [])[:3],
                "top_receivers": current_month.get('top_receivers', [])[:3]
            }
        except Exception as e:
            logger.warning(f"Could not get current month data: {str(e)}")
            dashboard_data["current_month"] = {"error": str(e)}
        
        # Get previous month for comparison
        try:
            now = datetime.now()
            prev_month = now.month - 1 if now.month > 1 else 12
            prev_year = now.year if now.month > 1 else now.year - 1
            
            prev_month_data = service.get_monthly_recognition_report(year=prev_year, month=prev_month)
            dashboard_data["previous_month"] = {
                "year": prev_month_data.get('year'),
                "month": prev_month_data.get('month'),
                "total_recognitions": prev_month_data.get('total_recognitions', 0)
            }
            
            # Calculate month-over-month change
            current_total = dashboard_data.get("current_month", {}).get("total_recognitions", 0)
            prev_total = prev_month_data.get('total_recognitions', 0)
            if prev_total > 0:
                change_pct = ((current_total - prev_total) / prev_total) * 100
                dashboard_data["month_over_month_change"] = round(change_pct, 1)
            else:
                dashboard_data["month_over_month_change"] = None
        except Exception as e:
            logger.warning(f"Could not get previous month data: {str(e)}")
            dashboard_data["previous_month"] = {"error": str(e)}
        
        # Get 90-day summary
        try:
            summary_90d = service.get_recognition_summary(days=90)
            dashboard_data["summary_90_days"] = summary_90d
        except Exception as e:
            logger.warning(f"Could not get 90-day summary: {str(e)}")
            dashboard_data["summary_90_days"] = {"error": str(e)}
        
        # Get recent recognitions
        try:
            recent = service.get_high_fives_recognitions(days=7)
            dashboard_data["recent_recognitions"] = recent.get('recognitions', [])[:10]
        except Exception as e:
            logger.warning(f"Could not get recent recognitions: {str(e)}")
            dashboard_data["recent_recognitions"] = []
        
        # Cache the result
        cache_service.set(cache_key, dashboard_data, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": dashboard_data,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"High Fives dashboard error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== LEADERBOARD ====================

@vital_high_fives_bp.route('/api/vital/high-fives/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    """Get recognition leaderboard"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        service = get_teams_service()
        summary = service.get_recognition_summary(days=days)
        
        return jsonify({
            "success": True,
            "data": {
                "period_days": days,
                "top_givers": summary.get('top_givers', [])[:limit],
                "top_receivers": summary.get('top_receivers', [])[:limit],
                "total_recognitions": summary.get('total_recognitions', 0)
            }
        })
    except Exception as e:
        logger.error(f"Leaderboard error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
