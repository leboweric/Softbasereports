"""
VITAL Zoom Integration Routes
Provides API endpoints for Zoom Phone call center data and meeting analytics
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

vital_zoom_bp = Blueprint('vital_zoom', __name__)


def get_zoom_service():
    """Get VITAL Zoom service instance"""
    from src.services.vital_zoom_service import VitalZoomService
    return VitalZoomService()


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

@vital_zoom_bp.route('/api/vital/zoom/health', methods=['GET'])
def zoom_health_check():
    """Check Zoom API connectivity (no auth required for health check)"""
    try:
        service = get_zoom_service()
        result = service.test_connection()
        
        if result['status'] == 'connected':
            return jsonify({
                "status": "healthy",
                "message": "Zoom API connection successful"
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


# ==================== DASHBOARD ENDPOINTS ====================

@vital_zoom_bp.route('/api/vital/zoom/dashboard', methods=['GET'])
@jwt_required()
def get_zoom_dashboard():
    """Get comprehensive call center dashboard data"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_zoom_service()
        dashboard_data = service.get_call_center_dashboard()
        
        return jsonify({
            "success": True,
            "data": dashboard_data
        })
    except Exception as e:
        logger.error(f"Zoom dashboard error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== CALL VOLUME TREND ====================

@vital_zoom_bp.route('/api/vital/zoom/call-volume-trend', methods=['GET'])
@jwt_required()
def get_call_volume_trend():
    """Get daily call volume trend with spike detection"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 30, type=int)
        service = get_zoom_service()
        
        # Get call logs
        call_logs = service.get_call_logs(days=days, page_size=300)
        calls = call_logs.get('call_logs', [])
        
        # Aggregate by date
        from collections import defaultdict
        from datetime import datetime
        
        daily_counts = defaultdict(lambda: {'total': 0, 'inbound': 0, 'outbound': 0})
        
        for call in calls:
            date_str = call.get('date_time', '')[:10]  # Extract YYYY-MM-DD
            if date_str:
                daily_counts[date_str]['total'] += 1
                direction = call.get('direction', '')
                if direction == 'inbound':
                    daily_counts[date_str]['inbound'] += 1
                elif direction == 'outbound':
                    daily_counts[date_str]['outbound'] += 1
        
        # Convert to sorted list
        trend_data = []
        for date, counts in sorted(daily_counts.items()):
            trend_data.append({
                'date': date,
                'total': counts['total'],
                'inbound': counts['inbound'],
                'outbound': counts['outbound']
            })
        
        # Calculate average and detect spikes (> 1.5x average)
        if trend_data:
            avg_calls = sum(d['total'] for d in trend_data) / len(trend_data)
            spike_threshold = avg_calls * 1.5
            
            for day in trend_data:
                day['is_spike'] = day['total'] > spike_threshold
                day['avg'] = round(avg_calls, 1)
        
        return jsonify({
            "success": True,
            "data": {
                "trend": trend_data,
                "period": f"{call_logs.get('from_date')} to {call_logs.get('to_date')}",
                "total_calls": call_logs.get('total', 0)
            }
        })
    except Exception as e:
        logger.error(f"Call volume trend error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== USER ENDPOINTS ====================

@vital_zoom_bp.route('/api/vital/zoom/users', methods=['GET'])
@jwt_required()
def get_zoom_users():
    """Get list of Zoom users"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_zoom_service()
        users = service.get_users()
        
        return jsonify({
            "success": True,
            "data": users
        })
    except Exception as e:
        logger.error(f"Zoom users error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_zoom_bp.route('/api/vital/zoom/phone-users', methods=['GET'])
@jwt_required()
def get_phone_users():
    """Get list of Zoom Phone users"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_zoom_service()
        users = service.get_phone_users()
        
        return jsonify({
            "success": True,
            "data": users
        })
    except Exception as e:
        logger.error(f"Phone users error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== CALL CENTER ENDPOINTS ====================

@vital_zoom_bp.route('/api/vital/zoom/call-logs', methods=['GET'])
@jwt_required()
def get_call_logs():
    """Get call history/logs"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 30, type=int)
        days = min(days, 90)  # Limit to 90 days
        
        service = get_zoom_service()
        call_logs = service.get_call_logs(days=days)
        
        return jsonify({
            "success": True,
            "data": call_logs
        })
    except Exception as e:
        logger.error(f"Call logs error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_zoom_bp.route('/api/vital/zoom/call-queues', methods=['GET'])
@jwt_required()
def get_call_queues():
    """Get call queues"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_zoom_service()
        queues = service.get_call_queues()
        
        return jsonify({
            "success": True,
            "data": queues
        })
    except Exception as e:
        logger.error(f"Call queues error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== MEETING ENDPOINTS ====================

@vital_zoom_bp.route('/api/vital/zoom/meetings', methods=['GET'])
@jwt_required()
def get_meetings():
    """Get meetings dashboard data"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 30, type=int)
        days = min(days, 90)  # Limit to 90 days
        
        service = get_zoom_service()
        meetings = service.get_meetings_dashboard(days=days)
        
        return jsonify({
            "success": True,
            "data": meetings
        })
    except Exception as e:
        logger.error(f"Meetings error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_zoom_bp.route('/api/vital/zoom/daily-report', methods=['GET'])
@jwt_required()
def get_daily_report():
    """Get daily usage report"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        service = get_zoom_service()
        report = service.get_daily_report(year=year, month=month)
        
        return jsonify({
            "success": True,
            "data": report
        })
    except Exception as e:
        logger.error(f"Daily report error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== RECORDINGS/TRANSCRIPTS ====================

@vital_zoom_bp.route('/api/vital/zoom/recordings', methods=['GET'])
@jwt_required()
def get_recordings():
    """Get recordings with transcripts"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 30, type=int)
        days = min(days, 90)  # Limit to 90 days
        
        service = get_zoom_service()
        recordings = service.get_recordings(days=days)
        
        return jsonify({
            "success": True,
            "data": recordings
        })
    except Exception as e:
        logger.error(f"Recordings error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
