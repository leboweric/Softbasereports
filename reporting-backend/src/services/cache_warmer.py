"""
Dashboard Cache Warmer Service
Pre-warms the dashboard cache on server startup and maintains it with periodic refreshes.
This eliminates the ~30 second cold-start delay for dashboard loading.
"""
import logging
import atexit
import threading
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
logger = logging.getLogger(__name__)
# Global scheduler instance
_cache_warmer_scheduler = None
_warming_in_progress = False
_flask_app = None  # Store reference to Flask app for app context


def warm_dashboard_cache():
    """
    Pre-warm all dashboard cache entries by executing all queries and caching results.
    This runs in the background so it doesn't block server startup.
    """
    global _warming_in_progress
    
    if _warming_in_progress:
        logger.info("⏳ Cache warming already in progress, skipping...")
        return
    
    _warming_in_progress = True
    start_time = datetime.now()
    
    try:
        # Must run inside app context since we use SQLAlchemy models
        if _flask_app is None:
            logger.error("❌ Cache warmer: Flask app not set, cannot warm cache")
            return
        
        with _flask_app.app_context():
            _do_warm_cache(start_time)
        
    except Exception as e:
        logger.error(f"❌ Dashboard cache warm-up failed: {str(e)}")
    finally:
        _warming_in_progress = False


def _do_warm_cache(start_time):
    """Inner function that runs inside app context."""
    # Import here to avoid circular imports
    from src.services.azure_sql_service import AzureSQLService
    from src.services.cache_service import cache_service
    from src.routes.dashboard_optimized import DashboardQueries
    from src.models.user import Organization
    
    logger.info("🔥 Starting dashboard cache warm-up...")
    
    # Get all active organizations with database credentials
    orgs = Organization.query.filter(
        Organization.is_active == True,
        Organization.database_schema.isnot(None)
    ).all()
    
    if not orgs:
        logger.warning("No active organizations found for cache warming")
        return
    
    # Cache TTL settings (in seconds) - all set to 1 hour
    cache_ttl = 3600
    current_month = datetime.now().strftime('%Y-%m')
    
    total_success = 0
    total_error = 0
    
    for org in orgs:
        schema = org.database_schema
        if not schema:
            continue
        
        logger.info(f"  Warming cache for {org.name} (schema={schema})...")
        
        # Get org-specific settings to avoid needing Flask g context
        data_start_date = org.data_start_date.strftime('%Y-%m-%d') if org.data_start_date else '2000-01-01'
        fiscal_year_start_month = org.fiscal_year_start_month or 11
        
        try:
            db = AzureSQLService()
            queries = DashboardQueries(
                db, schema=schema,
                data_start_date=data_start_date,
                fiscal_year_start_month=fiscal_year_start_month
            )
        except Exception as e:
            logger.error(f"  ✗ Failed to init DashboardQueries for {org.name}: {str(e)}")
            continue
        
        # Define all queries to warm
        query_configs = [
            ('total_sales', queries.get_current_month_sales),
            ('ytd_sales', queries.get_ytd_sales),
            ('inventory_count', queries.get_inventory_count),
            ('active_customers', queries.get_active_customers),
            ('total_customers', queries.get_total_customers),
            ('monthly_sales', queries.get_monthly_sales),
            ('monthly_sales_no_equipment', queries.get_monthly_sales_excluding_equipment),
            ('monthly_equipment_sales', queries.get_monthly_equipment_sales),
            ('monthly_sales_by_stream', queries.get_monthly_sales_by_stream),
            ('uninvoiced', queries.get_uninvoiced_work_orders),
            ('monthly_quotes', queries.get_monthly_quotes),
            ('work_order_types', queries.get_work_order_types),
            ('top_customers', queries.get_top_customers),
            ('monthly_work_orders', queries.get_monthly_work_orders_by_type),
            ('department_margins', queries.get_department_margins),
            ('monthly_active_customers', queries.get_monthly_active_customers),
            ('monthly_open_work_orders', queries.get_monthly_open_work_orders),
            ('awaiting_invoice', queries.get_awaiting_invoice_work_orders),
            ('monthly_invoice_delays', queries.get_monthly_invoice_delay_avg),
        ]
        
        for key, query_func in query_configs:
            try:
                cache_key = f"dashboard:{key}:{current_month}:{schema}"
                result = cache_service.cache_query(cache_key, query_func, cache_ttl, force_refresh=True)
                total_success += 1
                logger.debug(f"    ✓ Warmed cache for {key}")
            except Exception as e:
                total_error += 1
                logger.error(f"    ✗ Failed to warm cache for {key}: {str(e)}")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"✅ Dashboard cache warm-up complete in {elapsed:.1f}s ({total_success} succeeded, {total_error} failed)")


def warm_cache_async():
    """
    Run cache warming in a separate thread to not block the main thread.
    """
    thread = threading.Thread(target=warm_dashboard_cache, daemon=True)
    thread.start()


def init_cache_warmer(app):
    """
    Initialize the cache warmer scheduler.
    Should be called once when the Flask app starts.
    
    Args:
        app: The Flask application instance
    """
    global _cache_warmer_scheduler, _flask_app
    
    # Store the Flask app reference for app context in background threads
    _flask_app = app
    
    # Only initialize once
    if _cache_warmer_scheduler is not None:
        logger.info("Cache warmer scheduler already initialized")
        return
    
    try:
        _cache_warmer_scheduler = BackgroundScheduler()
        
        # Schedule initial warm-up after 10 seconds (let server fully start)
        _cache_warmer_scheduler.add_job(
            func=warm_dashboard_cache,
            trigger='date',
            run_date=datetime.now().replace(microsecond=0),
            id='initial_cache_warmup',
            name='Initial Dashboard Cache Warm-up',
            replace_existing=True,
            misfire_grace_time=60
        )
        
        # Schedule periodic refresh every 55 minutes (before 1-hour TTL expires)
        _cache_warmer_scheduler.add_job(
            func=warm_dashboard_cache,
            trigger='interval',
            minutes=55,
            id='periodic_cache_refresh',
            name='Periodic Dashboard Cache Refresh (every 55 min)',
            replace_existing=True
        )
        
        # Schedule daily refresh at 5 AM to ensure fresh data for the day
        _cache_warmer_scheduler.add_job(
            func=warm_dashboard_cache,
            trigger='cron',
            hour=5,
            minute=0,
            id='daily_cache_refresh',
            name='Daily Dashboard Cache Refresh (5 AM)',
            replace_existing=True
        )
        
        # Start the scheduler
        _cache_warmer_scheduler.start()
        logger.info("✅ Cache warmer scheduler started:")
        logger.info("   - Initial warm-up: On startup")
        logger.info("   - Periodic refresh: Every 55 minutes")
        logger.info("   - Daily refresh: 5:00 AM")
        
        # Shut down the scheduler when the app exits
        atexit.register(lambda: _cache_warmer_scheduler.shutdown(wait=False))
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize cache warmer scheduler: {str(e)}")
