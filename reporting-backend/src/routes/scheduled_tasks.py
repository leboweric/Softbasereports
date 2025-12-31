"""
Scheduled Tasks Routes
Endpoints for cron jobs and scheduled operations
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import logging

from src.services.scheduled_forecast_service import ScheduledForecastService

logger = logging.getLogger(__name__)

scheduled_tasks_bp = Blueprint('scheduled_tasks', __name__)


@scheduled_tasks_bp.route('/api/cron/daily-forecast', methods=['POST'])
def daily_forecast_cron():
    """
    Daily forecast generation endpoint
    Called by Railway Cron or external scheduler at 8 AM daily
    
    No authentication required for cron jobs (use Railway's internal cron)
    For external cron, add a secret token check if needed
    """
    try:
        logger.info("Daily forecast cron job triggered")
        
        success = ScheduledForecastService.generate_daily_forecast()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Daily forecast generated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate daily forecast'
            }), 500
            
    except Exception as e:
        logger.error(f"Daily forecast cron job failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scheduled_tasks_bp.route('/api/cron/test-daily-forecast', methods=['POST'])
@jwt_required()
def test_daily_forecast():
    """
    Test endpoint for daily forecast generation
    Requires authentication - for manual testing only
    """
    try:
        logger.info("Manual test of daily forecast triggered")
        
        success = ScheduledForecastService.generate_daily_forecast()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Daily forecast test completed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Daily forecast test failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Daily forecast test failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scheduled_tasks_bp.route('/api/scheduler/status', methods=['GET'])
@jwt_required()
def get_scheduler_status():
    """
    Get the status of the background scheduler and its jobs.
    """
    try:
        from src.services.forecast_scheduler import get_scheduler_status as get_status
        
        status = get_status()
        
        return jsonify({
            'success': True,
            'scheduler': status
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scheduled_tasks_bp.route('/api/scheduler/trigger-snapshot', methods=['POST'])
@jwt_required()
def trigger_manual_snapshot():
    """
    Manually trigger a mid-month forecast snapshot.
    Useful for testing or capturing snapshots outside the scheduled time.
    """
    try:
        from src.services.forecast_scheduler import trigger_snapshot_now
        
        logger.info("Manual mid-month snapshot triggered by user")
        
        success = trigger_snapshot_now()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Mid-month snapshot captured successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to capture snapshot'
            }), 500
            
    except Exception as e:
        logger.error(f"Manual snapshot trigger failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
