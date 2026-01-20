"""
VITAL WorkLife ETL Jobs
Extracts data from HubSpot, QuickBooks, Zoom, Azure SQL, and BigQuery
"""

import os
import json
import logging
from datetime import datetime, timedelta
from .base_etl import BaseETL

logger = logging.getLogger(__name__)


# VITAL org_id (from organization table)
VITAL_ORG_ID = 6


class VitalHubSpotContactsETL(BaseETL):
    """ETL job for VITAL HubSpot contacts"""
    
    def __init__(self):
        super().__init__(
            job_name='etl_vital_hubspot_contacts',
            org_id=VITAL_ORG_ID,
            source_system='hubspot',
            target_table='mart_crm_contacts'
        )
        self._hubspot = None
    
    @property
    def hubspot(self):
        if self._hubspot is None:
            from src.services.hubspot_service import HubSpotService
            token = os.environ.get('VITAL_HUBSPOT_TOKEN')
            self._hubspot = HubSpotService(access_token=token)
        return self._hubspot
    
    def extract(self) -> list:
        """Extract contact data from HubSpot"""
        try:
            total_contacts = self.hubspot.get_contacts_count()
            lifecycle_data = self.hubspot.get_contacts_by_lifecycle_stage()
            new_contacts = self.hubspot.get_new_contacts_trend(days=30)
            
            return [{
                'total_contacts': total_contacts,
                'lifecycle_data': lifecycle_data,
                'new_contacts_30d': new_contacts.get('total_new', 0),
                'new_contacts_7d': 0  # Would need separate API call
            }]
        except Exception as e:
            logger.error(f"HubSpot extract error: {str(e)}")
            return []
    
    def transform(self, data: list) -> list:
        """Transform HubSpot contact data"""
        if not data:
            return []
        
        row = data[0]
        lifecycle = row.get('lifecycle_data', {})
        
        return [{
            'org_id': self.org_id,
            'snapshot_date': datetime.now().date(),
            'total_contacts': row.get('total_contacts', 0),
            'new_contacts_30d': row.get('new_contacts_30d', 0),
            'new_contacts_7d': row.get('new_contacts_7d', 0),
            'subscribers': lifecycle.get('subscriber', 0),
            'leads': lifecycle.get('lead', 0),
            'marketing_qualified': lifecycle.get('marketingqualifiedlead', 0),
            'sales_qualified': lifecycle.get('salesqualifiedlead', 0),
            'opportunities': lifecycle.get('opportunity', 0),
            'customers': lifecycle.get('customer', 0),
            'evangelists': lifecycle.get('evangelist', 0),
            'other_lifecycle': lifecycle.get('other', 0),
            'source_system': self.source_system
        }]
    
    def load(self, data: list) -> None:
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'snapshot_date'])


class VitalHubSpotDealsETL(BaseETL):
    """ETL job for VITAL HubSpot deals"""
    
    def __init__(self):
        super().__init__(
            job_name='etl_vital_hubspot_deals',
            org_id=VITAL_ORG_ID,
            source_system='hubspot',
            target_table='mart_crm_deals'
        )
        self._hubspot = None
    
    @property
    def hubspot(self):
        if self._hubspot is None:
            from src.services.hubspot_service import HubSpotService
            token = os.environ.get('VITAL_HUBSPOT_TOKEN')
            self._hubspot = HubSpotService(access_token=token)
        return self._hubspot
    
    def extract(self) -> list:
        """Extract deals data from HubSpot"""
        try:
            deals_summary = self.hubspot.get_deals_summary()
            deals_by_stage = self.hubspot.get_deals_by_stage()
            
            return [{
                'summary': deals_summary,
                'by_stage': deals_by_stage
            }]
        except Exception as e:
            logger.error(f"HubSpot deals extract error: {str(e)}")
            return []
    
    def transform(self, data: list) -> list:
        """Transform HubSpot deals data"""
        if not data:
            return []
        
        row = data[0]
        summary = row.get('summary', {})
        by_stage = row.get('by_stage', [])
        
        # Build stage breakdown JSON
        stage_breakdown = {}
        for stage in by_stage:
            stage_name = stage.get('stage_name', 'unknown')
            stage_breakdown[stage_name] = {
                'count': stage.get('count', 0),
                'value': stage.get('total_value', 0)
            }
        
        return [{
            'org_id': self.org_id,
            'snapshot_date': datetime.now().date(),
            'total_deals': summary.get('total_deals', 0),
            'open_deals': summary.get('open_deals', 0),
            'won_deals': summary.get('won_deals', 0),
            'lost_deals': summary.get('lost_deals', 0),
            'total_pipeline_value': float(summary.get('total_value', 0)),
            'won_value': float(summary.get('won_value', 0)),
            'lost_value': float(summary.get('lost_value', 0)),
            'average_deal_size': float(summary.get('average_deal_size', 0)),
            'deals_by_stage': json.dumps(stage_breakdown),
            'source_system': self.source_system
        }]
    
    def load(self, data: list) -> None:
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'snapshot_date'])


class VitalZoomETL(BaseETL):
    """ETL job for VITAL Zoom metrics"""
    
    def __init__(self):
        super().__init__(
            job_name='etl_vital_zoom',
            org_id=VITAL_ORG_ID,
            source_system='zoom',
            target_table='mart_zoom_metrics'
        )
        self._zoom = None
    
    @property
    def zoom(self):
        if self._zoom is None:
            from src.services.vital_zoom_service import VitalZoomService
            self._zoom = VitalZoomService()
        return self._zoom
    
    def extract(self) -> list:
        """Extract Zoom data"""
        try:
            dashboard = self.zoom.get_call_center_dashboard()
            users = self.zoom.get_users()
            phone_users = self.zoom.get_phone_users()
            
            return [{
                'dashboard': dashboard,
                'total_users': len(users) if users else 0,
                'phone_users': len(phone_users) if phone_users else 0
            }]
        except Exception as e:
            logger.error(f"Zoom extract error: {str(e)}")
            return []
    
    def transform(self, data: list) -> list:
        """Transform Zoom data"""
        if not data:
            return []
        
        row = data[0]
        dashboard = row.get('dashboard', {})
        
        return [{
            'org_id': self.org_id,
            'metric_date': datetime.now().date(),
            'total_users': row.get('total_users', 0),
            'phone_users': row.get('phone_users', 0),
            'total_meetings': dashboard.get('total_meetings', 0),
            'total_meeting_minutes': dashboard.get('total_meeting_minutes', 0),
            'total_participants': dashboard.get('total_participants', 0),
            'avg_meeting_duration_mins': float(dashboard.get('avg_meeting_duration', 0)),
            'total_calls': dashboard.get('total_calls', 0),
            'inbound_calls': dashboard.get('inbound_calls', 0),
            'outbound_calls': dashboard.get('outbound_calls', 0),
            'missed_calls': dashboard.get('missed_calls', 0),
            'total_call_minutes': dashboard.get('total_call_minutes', 0),
            'avg_call_duration_mins': float(dashboard.get('avg_call_duration', 0)),
            'queue_count': dashboard.get('queue_count', 0),
            'source_system': self.source_system
        }]
    
    def load(self, data: list) -> None:
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'metric_date'])


class VitalCaseDataETL(BaseETL):
    """ETL job for VITAL Azure SQL case data"""
    
    def __init__(self):
        super().__init__(
            job_name='etl_vital_case_data',
            org_id=VITAL_ORG_ID,
            source_system='azure_sql',
            target_table='mart_case_metrics'
        )
        self._azure_sql = None
    
    @property
    def azure_sql(self):
        if self._azure_sql is None:
            from src.services.vital_azure_sql_service import VitalAzureSQLService
            self._azure_sql = VitalAzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """Extract case data from Azure SQL"""
        try:
            # Get total count
            total_cases = self.azure_sql.get_row_count()
            
            # Get summary stats
            stats = self.azure_sql.get_summary_stats()
            
            return [{
                'total_cases': total_cases,
                'stats': stats
            }]
        except Exception as e:
            logger.error(f"Azure SQL extract error: {str(e)}")
            return []
    
    def transform(self, data: list) -> list:
        """Transform case data"""
        if not data:
            return []
        
        row = data[0]
        
        return [{
            'org_id': self.org_id,
            'snapshot_date': datetime.now().date(),
            'total_cases': row.get('total_cases', 0),
            'new_cases_30d': 0,  # Would need date-based query
            'closed_cases_30d': 0,  # Would need status-based query
            'cases_by_type': json.dumps({}),
            'cases_by_status': json.dumps({}),
            'cases_by_category': json.dumps({}),
            'source_system': self.source_system,
            'source_table': 'Case_Data_Summary_NOPHI'
        }]
    
    def load(self, data: list) -> None:
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'snapshot_date'])


class VitalQuickBooksETL(BaseETL):
    """ETL job for VITAL QuickBooks financial data"""
    
    def __init__(self):
        super().__init__(
            job_name='etl_vital_quickbooks',
            org_id=VITAL_ORG_ID,
            source_system='quickbooks',
            target_table='mart_financial_metrics'
        )
        self._qb = None
    
    @property
    def qb(self):
        if self._qb is None:
            from src.services.quickbooks_service import QuickBooksService
            self._qb = QuickBooksService(
                client_id=os.environ.get('QB_CLIENT_ID'),
                client_secret=os.environ.get('QB_CLIENT_SECRET'),
                redirect_uri=os.environ.get('QB_REDIRECT_URI')
            )
        return self._qb
    
    def extract(self) -> list:
        """Extract financial data from QuickBooks"""
        try:
            # Get tokens from environment
            access_token = os.environ.get('VITAL_QB_ACCESS_TOKEN')
            realm_id = os.environ.get('VITAL_QB_REALM_ID')
            
            if not access_token or not realm_id:
                logger.warning("QuickBooks tokens not configured")
                return []
            
            dashboard = self.qb.get_financial_dashboard(access_token, realm_id)
            return [dashboard] if dashboard else []
            
        except Exception as e:
            logger.error(f"QuickBooks extract error: {str(e)}")
            return []
    
    def transform(self, data: list) -> list:
        """Transform QuickBooks data"""
        if not data:
            return []
        
        row = data[0]
        now = datetime.now()
        
        # Get last day of current month
        from calendar import monthrange
        _, last_day = monthrange(now.year, now.month)
        
        return [{
            'org_id': self.org_id,
            'year': now.year,
            'month': now.month,
            'period_start': datetime(now.year, now.month, 1).date(),
            'period_end': datetime(now.year, now.month, last_day).date(),
            'total_revenue': float(row.get('total_income', 0)),
            'total_expenses': float(row.get('total_expenses', 0)),
            'net_income': float(row.get('net_income', 0)),
            'gross_profit': float(row.get('gross_profit', 0)),
            'gross_margin_pct': 0,  # Calculate if needed
            'total_assets': float(row.get('total_assets', 0)),
            'total_liabilities': float(row.get('total_liabilities', 0)),
            'total_equity': float(row.get('total_equity', 0)),
            'cash_balance': float(row.get('cash_balance', 0)),
            'accounts_receivable': float(row.get('accounts_receivable', 0)),
            'accounts_payable': float(row.get('accounts_payable', 0)),
            'operating_cash_flow': 0,  # Would need cash flow report
            'source_system': self.source_system
        }]
    
    def load(self, data: list) -> None:
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'year', 'month'])


class VitalAppAnalyticsETL(BaseETL):
    """ETL job for VITAL BigQuery/GA4 mobile app analytics"""
    
    def __init__(self):
        super().__init__(
            job_name='etl_vital_app_analytics',
            org_id=VITAL_ORG_ID,
            source_system='bigquery_ga4',
            target_table='mart_app_analytics'
        )
    
    def extract(self) -> list:
        """Extract app analytics from BigQuery"""
        try:
            # BigQuery integration pending dataViewer permission
            # This is a placeholder that will be filled in once permissions are granted
            
            logger.info("BigQuery integration pending - using placeholder data")
            return [{
                'dau': 0,
                'wau': 0,
                'mau': 0,
                'new_users': 0,
                'sessions': 0
            }]
            
        except Exception as e:
            logger.error(f"BigQuery extract error: {str(e)}")
            return []
    
    def transform(self, data: list) -> list:
        """Transform app analytics data"""
        if not data:
            return []
        
        row = data[0]
        
        return [{
            'org_id': self.org_id,
            'metric_date': datetime.now().date(),
            'daily_active_users': row.get('dau', 0),
            'weekly_active_users': row.get('wau', 0),
            'monthly_active_users': row.get('mau', 0),
            'new_users': row.get('new_users', 0),
            'returning_users': 0,
            'total_sessions': row.get('sessions', 0),
            'avg_session_duration_secs': 0,
            'screens_per_session': 0,
            'ios_downloads': 0,
            'android_downloads': 0,
            'top_screens': json.dumps([]),
            'source_system': self.source_system
        }]
    
    def load(self, data: list) -> None:
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'metric_date'])


def run_vital_etl():
    """Run all VITAL ETL jobs"""
    logger.info("=" * 50)
    logger.info("Starting VITAL WorkLife ETL Jobs")
    logger.info("=" * 50)
    
    jobs = [
        VitalHubSpotContactsETL(),
        VitalHubSpotDealsETL(),
        VitalZoomETL(),
        VitalCaseDataETL(),
        VitalQuickBooksETL(),
        VitalAppAnalyticsETL(),
    ]
    
    results = {}
    for job in jobs:
        try:
            success = job.run()
            results[job.job_name] = 'success' if success else 'failed'
        except Exception as e:
            logger.error(f"Job {job.job_name} crashed: {str(e)}")
            results[job.job_name] = 'crashed'
    
    logger.info("\n" + "=" * 50)
    logger.info("VITAL ETL Summary:")
    for job_name, status in results.items():
        logger.info(f"  {job_name}: {status}")
    logger.info("=" * 50)
    
    return all(s == 'success' for s in results.values())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_vital_etl()
