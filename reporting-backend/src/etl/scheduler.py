"""
AIOP ETL Scheduler
Runs all ETL jobs on a schedule using APScheduler
Can be run as a standalone process or integrated into the Flask app
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def run_all_etl():
    """Run all ETL jobs for all organizations"""
    from .etl_bennett_sales import run_bennett_etl
    from .etl_vital import run_vital_etl
    
    logger.info("=" * 60)
    logger.info(f"AIOP ETL Run Started: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    results = {
        'bennett': run_bennett_etl(),
        'vital': run_vital_etl()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("AIOP ETL Run Complete")
    logger.info(f"  Bennett: {'SUCCESS' if results['bennett'] else 'FAILED'}")
    logger.info(f"  VITAL: {'SUCCESS' if results['vital'] else 'FAILED'}")
    logger.info("=" * 60)
    
    return all(results.values())


def setup_scheduler():
    """Set up APScheduler for automated ETL runs"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BackgroundScheduler()
        
        # Run all ETL jobs daily at 2 AM
        scheduler.add_job(
            run_all_etl,
            CronTrigger(hour=2, minute=0),
            id='daily_etl',
            name='Daily ETL Run',
            replace_existing=True
        )
        
        logger.info("ETL Scheduler configured: Daily at 2:00 AM")
        return scheduler
        
    except ImportError:
        logger.warning("APScheduler not installed. Run: pip install apscheduler")
        return None


def start_scheduler():
    """Start the ETL scheduler"""
    scheduler = setup_scheduler()
    if scheduler:
        scheduler.start()
        logger.info("ETL Scheduler started")
        return scheduler
    return None


# Flask integration
def init_etl_scheduler(app):
    """Initialize ETL scheduler with Flask app"""
    if os.environ.get('ENABLE_ETL_SCHEDULER', 'false').lower() == 'true':
        scheduler = start_scheduler()
        if scheduler:
            # Store scheduler on app for cleanup
            app.etl_scheduler = scheduler
            logger.info("ETL Scheduler integrated with Flask app")
    else:
        logger.info("ETL Scheduler disabled (set ENABLE_ETL_SCHEDULER=true to enable)")


# Manual run endpoint for Flask
def register_etl_routes(app):
    """Register ETL management routes"""
    from flask import Blueprint, jsonify
    from flask_jwt_extended import jwt_required
    
    etl_bp = Blueprint('etl', __name__)
    
    @etl_bp.route('/api/admin/etl/run', methods=['POST'])
    @jwt_required()
    def trigger_etl():
        """Manually trigger ETL run (admin only)"""
        # TODO: Add admin role check
        try:
            success = run_all_etl()
            return jsonify({
                'success': success,
                'message': 'ETL run completed' if success else 'ETL run had failures'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @etl_bp.route('/api/admin/etl/status', methods=['GET'])
    @jwt_required()
    def get_etl_status():
        """Get recent ETL job status"""
        try:
            from src.services.postgres_service import PostgreSQLService
            pg = PostgreSQLService()
            
            query = """
            SELECT job_name, org_id, started_at, completed_at, status,
                   records_processed, records_inserted, records_updated, error_message
            FROM mart_etl_log
            ORDER BY started_at DESC
            LIMIT 50
            """
            
            results = pg.execute_query(query)
            
            return jsonify({
                'success': True,
                'jobs': [dict(r) for r in results]
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    app.register_blueprint(etl_bp)
    logger.info("ETL management routes registered")


if __name__ == '__main__':
    # Run ETL manually
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Running AIOP ETL manually...")
    success = run_all_etl()
    
    if success:
        print("\n✓ All ETL jobs completed successfully!")
    else:
        print("\n✗ Some ETL jobs failed. Check logs for details.")
