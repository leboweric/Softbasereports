"""
BigQuery Service for Mobile App Analytics
Connects to GA4 BigQuery export for VITAL WorkLife mobile app
"""

import os
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BigQueryService:
    """Service for querying GA4 data from BigQuery"""
    
    def __init__(self, credentials_json=None):
        """Initialize BigQuery client with service account credentials"""
        self._client = None
        self._credentials_json = credentials_json or os.environ.get('VITAL_BIGQUERY_CREDENTIALS')
        self.project_id = 'prd-vwl'
        self.dataset_id = 'analytics_514267662'
    
    @property
    def client(self):
        """Lazy-load BigQuery client"""
        if self._client is None:
            try:
                from google.cloud import bigquery
                from google.oauth2 import service_account
                
                if not self._credentials_json:
                    raise ValueError("BigQuery credentials not configured")
                
                creds_dict = json.loads(self._credentials_json) if isinstance(self._credentials_json, str) else self._credentials_json
                credentials = service_account.Credentials.from_service_account_info(creds_dict)
                self._client = bigquery.Client(project=self.project_id, credentials=credentials)
                logger.info("BigQuery client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize BigQuery client: {str(e)}")
                raise
        return self._client
    
    def _run_query(self, query):
        """Execute a query and return results as list of dicts"""
        try:
            results = self.client.query(query).result()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"BigQuery query error: {str(e)}")
            raise
    
    def get_dau_mau_metrics(self, days=30):
        """Get DAU, MAU, and stickiness metrics"""
        query = f"""
        WITH daily_users AS (
            SELECT 
                event_date,
                COUNT(DISTINCT user_pseudo_id) as dau
            FROM `{self.project_id}.{self.dataset_id}.events_*`
            WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY))
            GROUP BY event_date
        ),
        monthly_users AS (
            SELECT COUNT(DISTINCT user_pseudo_id) as mau
            FROM `{self.project_id}.{self.dataset_id}.events_*`
            WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY))
        ),
        today_users AS (
            SELECT COUNT(DISTINCT user_pseudo_id) as today_dau
            FROM `{self.project_id}.{self.dataset_id}.events_*`
            WHERE _TABLE_SUFFIX = FORMAT_DATE('%Y%m%d', CURRENT_DATE())
        )
        SELECT 
            (SELECT today_dau FROM today_users) as dau,
            (SELECT AVG(dau) FROM daily_users) as avg_dau,
            (SELECT MAX(dau) FROM daily_users) as max_dau,
            (SELECT MIN(dau) FROM daily_users) as min_dau,
            (SELECT mau FROM monthly_users) as mau,
            ROUND((SELECT AVG(dau) FROM daily_users) / NULLIF((SELECT mau FROM monthly_users), 0) * 100, 2) as stickiness
        """
        results = self._run_query(query)
        return results[0] if results else {}
    
    def get_daily_trend(self, days=30):
        """Get daily active users trend"""
        query = f"""
        SELECT 
            event_date as date,
            COUNT(DISTINCT user_pseudo_id) as dau,
            COUNT(*) as events,
            COUNT(DISTINCT CASE WHEN event_name = 'session_start' THEN CONCAT(user_pseudo_id, CAST(event_timestamp AS STRING)) END) as sessions
        FROM `{self.project_id}.{self.dataset_id}.events_*`
        WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY))
        GROUP BY event_date
        ORDER BY event_date ASC
        """
        results = self._run_query(query)
        # Format dates for frontend
        for row in results:
            if row.get('date'):
                row['date'] = f"{row['date'][:4]}-{row['date'][4:6]}-{row['date'][6:]}"
        return results
    
    def get_new_vs_returning(self, days=30):
        """Get new vs returning user counts"""
        query = f"""
        SELECT 
            COUNT(DISTINCT CASE WHEN event_name = 'first_open' THEN user_pseudo_id END) as new_users,
            COUNT(DISTINCT user_pseudo_id) as total_users
        FROM `{self.project_id}.{self.dataset_id}.events_*`
        WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY))
        """
        results = self._run_query(query)
        if results:
            row = results[0]
            row['returning_users'] = row['total_users'] - row['new_users']
            row['new_user_pct'] = round(row['new_users'] / max(row['total_users'], 1) * 100, 1)
            row['returning_user_pct'] = round(row['returning_users'] / max(row['total_users'], 1) * 100, 1)
            return row
        return {}
    
    def get_platform_breakdown(self, days=30):
        """Get users by platform/OS"""
        query = f"""
        SELECT 
            device.operating_system as platform,
            COUNT(DISTINCT user_pseudo_id) as users,
            COUNT(*) as events
        FROM `{self.project_id}.{self.dataset_id}.events_*`
        WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY))
        GROUP BY platform
        ORDER BY users DESC
        """
        return self._run_query(query)
    
    def get_top_screens(self, days=30, limit=10):
        """Get most viewed screens"""
        query = f"""
        SELECT 
            (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'firebase_screen') as screen,
            COUNT(*) as views,
            COUNT(DISTINCT user_pseudo_id) as users
        FROM `{self.project_id}.{self.dataset_id}.events_*`
        WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY))
          AND event_name = 'screen_view'
        GROUP BY screen
        HAVING screen IS NOT NULL
        ORDER BY views DESC
        LIMIT {limit}
        """
        return self._run_query(query)
    
    def get_hourly_activity(self, days=30):
        """Get user activity by hour of day"""
        query = f"""
        SELECT 
            EXTRACT(HOUR FROM TIMESTAMP_MICROS(event_timestamp)) as hour,
            COUNT(DISTINCT user_pseudo_id) as users,
            COUNT(*) as events
        FROM `{self.project_id}.{self.dataset_id}.events_*`
        WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY))
        GROUP BY hour
        ORDER BY hour
        """
        return self._run_query(query)
    
    def get_key_actions(self, days=30):
        """Get counts of key user actions"""
        query = f"""
        SELECT 
            event_name as action,
            COUNT(*) as count,
            COUNT(DISTINCT user_pseudo_id) as unique_users
        FROM `{self.project_id}.{self.dataset_id}.events_*`
        WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY))
          AND event_name IN ('user_login', 'user_registered', 'content_accessed', 'assessment_completed', 'onboarding_completed', 'first_open')
        GROUP BY event_name
        ORDER BY count DESC
        """
        return self._run_query(query)
    
    def get_session_metrics(self, days=30):
        """Get session-related metrics"""
        query = f"""
        WITH session_data AS (
            SELECT 
                user_pseudo_id,
                (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') as session_id,
                (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') as engagement_time
            FROM `{self.project_id}.{self.dataset_id}.events_*`
            WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY))
              AND event_name = 'user_engagement'
        )
        SELECT 
            COUNT(DISTINCT CONCAT(user_pseudo_id, CAST(session_id AS STRING))) as total_sessions,
            ROUND(AVG(engagement_time) / 1000, 1) as avg_engagement_secs,
            ROUND(SUM(engagement_time) / 1000 / 60, 1) as total_engagement_mins
        FROM session_data
        WHERE session_id IS NOT NULL
        """
        results = self._run_query(query)
        return results[0] if results else {}
    
    def get_weekly_trend(self, weeks=8):
        """Get weekly active users trend"""
        query = f"""
        SELECT 
            FORMAT_DATE('%Y-%m-%d', DATE_TRUNC(PARSE_DATE('%Y%m%d', event_date), WEEK)) as week,
            COUNT(DISTINCT user_pseudo_id) as wau,
            COUNT(*) as events,
            COUNT(DISTINCT CASE WHEN event_name = 'first_open' THEN user_pseudo_id END) as new_users
        FROM `{self.project_id}.{self.dataset_id}.events_*`
        WHERE _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {weeks * 7} DAY))
        GROUP BY week
        ORDER BY week ASC
        """
        return self._run_query(query)
    
    def get_dashboard_summary(self, days=30):
        """Get complete dashboard summary"""
        try:
            # Get all metrics
            dau_mau = self.get_dau_mau_metrics(days)
            new_returning = self.get_new_vs_returning(days)
            session_metrics = self.get_session_metrics(days)
            daily_trend = self.get_daily_trend(days)
            platforms = self.get_platform_breakdown(days)
            top_screens = self.get_top_screens(days)
            hourly = self.get_hourly_activity(days)
            key_actions = self.get_key_actions(days)
            weekly = self.get_weekly_trend()
            
            # Calculate additional metrics
            total_events = sum(d.get('events', 0) for d in daily_trend)
            avg_hourly_users = sum(h.get('users', 0) for h in hourly) / max(len(hourly), 1)
            sessions_per_user = round(session_metrics.get('total_sessions', 0) / max(dau_mau.get('mau', 1), 1), 1)
            
            return {
                # Core metrics
                'dau': dau_mau.get('dau') or dau_mau.get('avg_dau', 0),
                'avg_dau': dau_mau.get('avg_dau', 0),
                'mau': dau_mau.get('mau', 0),
                'stickiness': dau_mau.get('stickiness', 0),
                
                # User breakdown
                'new_users': new_returning.get('new_users', 0),
                'returning_users': new_returning.get('returning_users', 0),
                'new_user_pct': new_returning.get('new_user_pct', 0),
                'returning_user_pct': new_returning.get('returning_user_pct', 0),
                
                # Session metrics
                'total_sessions': session_metrics.get('total_sessions', 0),
                'avg_engagement_secs': session_metrics.get('avg_engagement_secs', 0),
                'sessions_per_user': sessions_per_user,
                
                # Totals
                'total_events': total_events,
                'avg_hourly_users': avg_hourly_users,
                
                # Trend data
                'daily_trend': daily_trend,
                'weekly_trend': weekly,
                'platforms': platforms,
                'top_screens': top_screens,
                'hourly_activity': hourly,
                'key_actions': key_actions
            }
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {str(e)}")
            raise
