"""
Forecast Scheduler Service
Runs background scheduled tasks within the Flask application.
- Captures mid-month forecast snapshots on the 15th of each month at 8 AM
- Captures end-of-month actual revenue on the last day of each month at 7 PM
"""

import logging
import atexit
import calendar
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


def capture_end_of_month_actual():
    """
    Capture the end-of-month actual revenue.
    Called automatically on the last day of each month at 7:00 PM.
    Updates the mid-month snapshot with actual revenue for comparison.
    """
    try:
        from src.services.azure_sql_service import AzureSQLService
        from src.services.postgres_service import get_postgres_db
        
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        logger.info(f"📊 Capturing end-of-month actual revenue for {current_year}-{current_month:02d}")
        
        # Get actual revenue for the month
        azure_db = AzureSQLService()
        postgres_db = get_postgres_db()
        
        if not postgres_db:
            logger.error("PostgreSQL not available - cannot save end-of-month actual")
            return
        
        # Query actual revenue for the month
        actual_query = f"""
        SELECT 
            SUM(GrandTotal) as actual_total,
            COUNT(*) as invoice_count
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = {current_year}
            AND MONTH(InvoiceDate) = {current_month}
        """
        
        result = azure_db.execute_query(actual_query)
        actual_total = float(result[0]['actual_total'] or 0) if result else 0
        invoice_count = int(result[0]['invoice_count'] or 0) if result else 0
        
        logger.info(f"📈 End-of-month actual: ${actual_total:,.2f} from {invoice_count} invoices")
        
        # Update the mid-month snapshot with actual revenue
        update_query = """
        UPDATE forecast_history
        SET actual_total = %s,
            actual_invoice_count = %s,
            is_end_of_month_actual = TRUE,
            end_of_month_captured_at = CURRENT_TIMESTAMP
        WHERE target_year = %s
            AND target_month = %s
            AND is_mid_month_snapshot = TRUE
            AND actual_total IS NULL
        """
        
        postgres_db.execute_query(update_query, (actual_total, invoice_count, current_year, current_month))
        
        # Also insert a separate end-of-month record for reference
        insert_query = """
        INSERT INTO forecast_history (
            forecast_date,
            forecast_timestamp,
            target_year,
            target_month,
            days_into_month,
            projected_total,
            forecast_low,
            forecast_high,
            confidence_level,
            mtd_sales,
            mtd_invoices,
            month_progress_pct,
            days_remaining,
            actual_total,
            is_mid_month_snapshot,
            is_end_of_month_actual
        ) VALUES (
            CURRENT_DATE,
            CURRENT_TIMESTAMP,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, TRUE
        )
        """
        
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        
        postgres_db.execute_query(insert_query, (
            current_year,
            current_month,
            days_in_month,  # days_into_month (last day)
            actual_total,   # projected_total = actual at end of month
            actual_total,   # forecast_low = actual
            actual_total,   # forecast_high = actual
            100,            # confidence_level = 100% (it's actual)
            actual_total,   # mtd_sales = actual
            invoice_count,  # mtd_invoices
            100.0,          # month_progress_pct = 100%
            0,              # days_remaining = 0
            actual_total    # actual_total
        ))
        
        logger.info(f"✅ End-of-month actual captured and linked to mid-month snapshot")
        
    except Exception as e:
        logger.error(f"❌ Failed to capture end-of-month actual: {str(e)}")


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
        _scheduler.add_job(
            func=capture_mid_month_snapshot,
            trigger=CronTrigger(day=15, hour=8, minute=0),
            id='mid_month_forecast_snapshot',
            name='Mid-Month Forecast Snapshot (15th at 8 AM)',
            replace_existing=True
        )
        
        # Schedule end-of-month actual capture on the last day at 7:00 PM
        # Using day='last' to run on the last day of each month
        _scheduler.add_job(
            func=capture_end_of_month_actual,
            trigger=CronTrigger(day='last', hour=19, minute=0),
            id='end_of_month_actual_capture',
            name='End-of-Month Actual Revenue (Last day at 7 PM)',
            replace_existing=True
        )
        
        # Start the scheduler
        _scheduler.start()
        logger.info("✅ Forecast scheduler started:")
        logger.info("   - Mid-month snapshots: 15th at 8:00 AM")
        logger.info("   - End-of-month actuals: Last day at 7:00 PM")
        
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


def trigger_end_of_month_now():
    """
    Manually trigger an end-of-month actual capture.
    Useful for testing or manual captures.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        capture_end_of_month_actual()
        return True
    except Exception as e:
        logger.error(f"Manual end-of-month trigger failed: {str(e)}")
        return False
