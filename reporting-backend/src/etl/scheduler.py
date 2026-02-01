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
    from .etl_customer_activity import run_customer_activity_etl
    from .etl_vital import run_vital_etl
    
    logger.info("=" * 60)
    logger.info(f"AIOP ETL Run Started: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    results = {
        'bennett': run_bennett_etl(),
        'customer_activity': run_customer_activity_etl(),
        'vital': run_vital_etl()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("AIOP ETL Run Complete")
    logger.info(f"  Bennett: {'SUCCESS' if results['bennett'] else 'FAILED'}")
    logger.info(f"  Customer Activity: {'SUCCESS' if results['customer_activity'] else 'FAILED'}")
    logger.info(f"  VITAL: {'SUCCESS' if results['vital'] else 'FAILED'}")
    logger.info("=" * 60)
    
    return all(results.values())


def run_hubspot_sync():
    """Run HubSpot population sync for VITAL Finance clients"""
    import requests
    
    logger.info("=" * 60)
    logger.info(f"HubSpot Sync Started: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        # Get VITAL org credentials from environment
        hubspot_token = os.environ.get('VITAL_HUBSPOT_TOKEN')
        if not hubspot_token:
            logger.warning("VITAL_HUBSPOT_TOKEN not configured, skipping HubSpot sync")
            return False
        
        # Import the sync function
        from fuzzywuzzy import fuzz
        from src.services.postgres_service import PostgreSQLService
        
        db = PostgreSQLService()
        
        # Get VITAL org_id (hardcoded for now, could be made configurable)
        VITAL_ORG_ID = 6
        
        # Get all Finance clients
        clients = db.execute_query("""
            SELECT id, billing_name, hubspot_company_id, hubspot_company_name
            FROM finance_clients
            WHERE org_id = %s
        """, (VITAL_ORG_ID,))
        
        # Get HubSpot companies
        hubspot_url = "https://api.hubapi.com/crm/v3/objects/companies"
        headers = {"Authorization": f"Bearer {hubspot_token}"}
        params = {"limit": 100, "properties": "name,numberofemployees,domain"}
        
        all_companies = []
        after = None
        
        while True:
            if after:
                params['after'] = after
            
            resp = requests.get(hubspot_url, headers=headers, params=params, timeout=30)
            if resp.status_code != 200:
                logger.error(f"HubSpot API error: {resp.text}")
                return False
            
            data = resp.json()
            all_companies.extend(data.get('results', []))
            
            paging = data.get('paging', {})
            if paging.get('next'):
                after = paging['next'].get('after')
            else:
                break
            
            if len(all_companies) > 5000:
                break
        
        logger.info(f"Fetched {len(all_companies)} HubSpot companies")
        
        # Match and sync
        synced_count = 0
        
        for client in clients:
            client_name = client['billing_name'].lower().strip()
            best_match = None
            best_score = 0
            
            # If already linked, use that
            if client['hubspot_company_id']:
                for company in all_companies:
                    if str(company['id']) == str(client['hubspot_company_id']):
                        best_match = company
                        best_score = 100
                        break
            
            # Otherwise fuzzy match
            if not best_match:
                for company in all_companies:
                    company_name = (company.get('properties', {}).get('name') or '').lower().strip()
                    if not company_name:
                        continue
                    
                    if client_name == company_name:
                        best_match = company
                        best_score = 100
                        break
                    
                    score = fuzz.ratio(client_name, company_name)
                    if score > best_score and score >= 80:
                        best_match = company
                        best_score = score
            
            if best_match:
                props = best_match.get('properties', {})
                employees = props.get('numberofemployees')
                
                if employees and str(employees).isdigit():
                    employee_count = int(employees)
                    
                    # Update client
                    db.execute_update("""
                        UPDATE finance_clients 
                        SET hubspot_company_id = %s, hubspot_company_name = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (best_match['id'], props.get('name'), client['id']))
                    
                    # Upsert population
                    db.execute_update("""
                        INSERT INTO finance_population_history 
                        (client_id, population_count, effective_date, source, created_at)
                        VALUES (%s, %s, CURRENT_DATE, 'hubspot_sync_scheduled', NOW())
                        ON CONFLICT (client_id, effective_date) 
                        DO UPDATE SET population_count = EXCLUDED.population_count,
                                      source = EXCLUDED.source, created_at = NOW()
                    """, (client['id'], employee_count))
                    
                    synced_count += 1
        
        logger.info(f"HubSpot Sync Complete: {synced_count} clients synced")
        return True
        
    except Exception as e:
        logger.error(f"HubSpot sync failed: {str(e)}")
        return False


def run_high_fives_sync():
    """Sync High Fives recognition data from Microsoft Teams"""
    logger.info("=" * 60)
    logger.info(f"High Fives Sync Started: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        # Check if Teams credentials are configured
        tenant_id = os.environ.get('VITAL_TEAMS_TENANT_ID')
        client_id = os.environ.get('VITAL_TEAMS_CLIENT_ID')
        client_secret = os.environ.get('VITAL_TEAMS_CLIENT_SECRET')
        
        if not all([tenant_id, client_id, client_secret]):
            logger.warning("VITAL Teams credentials not configured, skipping High Fives sync")
            return False
        
        from src.services.vital_teams_service import VitalTeamsService
        
        teams_service = VitalTeamsService()
        
        # Get High Fives channel
        channel_info = teams_service.find_high_fives_channel()
        if not channel_info.get('found'):
            logger.warning("High Fives channel not found")
            return False
        
        # Get recognition summary (this triggers message parsing)
        summary = teams_service.get_recognition_summary(days=30)
        
        logger.info(f"High Fives Sync Complete: {summary.get('total_recognitions', 0)} recognitions found")
        return True
        
    except Exception as e:
        logger.error(f"High Fives sync failed: {str(e)}")
        return False


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
        
        # Run HubSpot sync weekly on Monday at 3 AM
        scheduler.add_job(
            run_hubspot_sync,
            CronTrigger(day_of_week='mon', hour=3, minute=0),
            id='weekly_hubspot_sync',
            name='Weekly HubSpot Population Sync',
            replace_existing=True
        )
        
        # Run High Fives sync daily at 6 AM
        scheduler.add_job(
            run_high_fives_sync,
            CronTrigger(hour=6, minute=0),
            id='daily_high_fives_sync',
            name='Daily High Fives Recognition Sync',
            replace_existing=True
        )
        
        logger.info("ETL Scheduler configured: Daily ETL at 2:00 AM, HubSpot sync weekly Monday 3:00 AM, High Fives daily 6:00 AM")
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
