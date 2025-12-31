"""
Forecast Scheduler Service
Runs background scheduled tasks within the Flask application.
Captures mid-month forecast snapshots on the 15th of each month.
"""

import logging
import atexit
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None


def capture_mid_month_snapshot():
    """
    Capture the mid-month forecast snapshot.
    Called automatically on the 15th of each month at 8:00 AM.
    """
    try:
        # Import here to avoid circular imports
        from src.routes.sales_forecast import _fetch_sales_forecast_data, save_forecast_to_history
        
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        
        logger.info(f"🎯 Capturing mid-month forecast snapshot for {current_year}-{current_month:02d}-{current_day:02d}")
        
        # Fetch the forecast data
        forecast_result = _fetch_sales_forecast_data(current_year, current_month, current_day)
        
        # Save to history with snapshot flag
        save_forecast_to_history(forecast_result, is_scheduled_snapshot=True)
        
        logger.info(f"✅ Mid-month snapshot captured successfully: ${forecast_result['forecast']['projected_total']:,.2f}")
        
    except Exception as e:
        logger.error(f"❌ Failed to capture mid-month snapshot: {str(e)}")


def init_forecast_scheduler(app):
    """
    Initialize the forecast scheduler.
    Should be called once when the Flask app starts.
    
    Args:
        app: The Flask application instance
    """
    global _scheduler
    
    # Only initialize once
    if _scheduler is not None:
        logger.info("Forecast scheduler already initialized")
        return
    
    try:
        _scheduler = BackgroundScheduler()
        
        # Schedule mid-month snapshot on the 15th at 8:00 AM
        # Cron format: minute hour day month day_of_week
        _scheduler.add_job(
            func=capture_mid_month_snapshot,
            trigger=CronTrigger(day=15, hour=8, minute=0),
            id='mid_month_forecast_snapshot',
            name='Mid-Month Forecast Snapshot (15th at 8 AM)',
            replace_existing=True
        )
        
        # Start the scheduler
        _scheduler.start()
        logger.info("✅ Forecast scheduler started - Mid-month snapshots will be captured on the 15th at 8:00 AM")
        
        # Shut down the scheduler when the app exits
        atexit.register(lambda: _scheduler.shutdown(wait=False))
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize forecast scheduler: {str(e)}")


def get_scheduler_status():
    """
    Get the current status of the scheduler and its jobs.
    
    Returns:
        dict: Scheduler status information
    """
    global _scheduler
    
    if _scheduler is None:
        return {
            'running': False,
            'jobs': []
        }
    
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': str(job.next_run_time) if job.next_run_time else None,
            'trigger': str(job.trigger)
        })
    
    return {
        'running': _scheduler.running,
        'jobs': jobs
    }


def trigger_snapshot_now():
    """
    Manually trigger a mid-month snapshot capture.
    Useful for testing or manual captures.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        capture_mid_month_snapshot()
        return True
    except Exception as e:
        logger.error(f"Manual snapshot trigger failed: {str(e)}")
        return False
