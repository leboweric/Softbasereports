"""
Mart Service - Provides fast queries against pre-aggregated Mart tables
This service queries PostgreSQL Mart tables instead of Azure SQL for dashboard data.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MartService:
    """Service for querying pre-aggregated Mart tables in PostgreSQL"""
    
    def __init__(self, postgres_service, org_id: int):
        """
        Initialize MartService
        
        Args:
            postgres_service: PostgreSQLService instance
            org_id: Organization ID for multi-tenant filtering
        """
        self.pg = postgres_service
        self.org_id = org_id
    
    def get_daily_sales(self, start_date: str, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Get daily sales data from mart_sales_daily
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: Optional end date (defaults to today)
        
        Returns:
            List of daily sales records
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        query = """
        SELECT 
            sales_date,
            year,
            month,
            day_of_week,
            service_revenue,
            parts_revenue,
            rental_revenue,
            sales_revenue,
            total_revenue,
            service_invoices,
            parts_invoices,
            rental_invoices,
            sales_invoices,
            total_invoices
        FROM mart_sales_daily
        WHERE org_id = %s
          AND sales_date >= %s
          AND sales_date <= %s
        ORDER BY sales_date
        """
        
        try:
            results = self.pg.execute_query(query, (self.org_id, start_date, end_date))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"MartService.get_daily_sales failed: {str(e)}")
            return []
    
    def get_monthly_sales_summary(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get monthly sales summary aggregated from daily data
        
        Args:
            months: Number of months to retrieve
        
        Returns:
            List of monthly sales summaries
        """
        query = """
        SELECT 
            year,
            month,
            SUM(service_revenue) as service_revenue,
            SUM(parts_revenue) as parts_revenue,
            SUM(rental_revenue) as rental_revenue,
            SUM(sales_revenue) as equipment_revenue,
            SUM(total_revenue) as total_revenue,
            SUM(service_invoices) as service_invoices,
            SUM(parts_invoices) as parts_invoices,
            SUM(rental_invoices) as rental_invoices,
            SUM(sales_invoices) as equipment_invoices,
            SUM(total_invoices) as total_invoices
        FROM mart_sales_daily
        WHERE org_id = %s
          AND sales_date >= CURRENT_DATE - INTERVAL '%s months'
        GROUP BY year, month
        ORDER BY year, month
        """
        
        try:
            results = self.pg.execute_query(query, (self.org_id, months))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"MartService.get_monthly_sales_summary failed: {str(e)}")
            return []
    
    def get_cash_flow(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get cash flow data from mart_cash_flow
        
        Args:
            months: Number of months to retrieve
        
        Returns:
            List of monthly cash flow records
        """
        query = """
        SELECT 
            year,
            month,
            period_end,
            cash_balance,
            cash_change_mtd,
            operating_cash_flow,
            ar_change,
            inventory_change,
            ap_change,
            investing_cash_flow,
            financing_cash_flow,
            health_status
        FROM mart_cash_flow
        WHERE org_id = %s
        ORDER BY year DESC, month DESC
        LIMIT %s
        """
        
        try:
            results = self.pg.execute_query(query, (self.org_id, months))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"MartService.get_cash_flow failed: {str(e)}")
            return []
    
    def get_department_margins_from_mart(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Calculate department margins from mart_sales_daily
        Note: This requires cost data which isn't in the current Mart schema.
        For now, returns revenue breakdown. Full margin calculation needs ETL enhancement.
        
        Args:
            months: Number of months to retrieve
        
        Returns:
            List of monthly department data
        """
        query = """
        SELECT 
            year,
            month,
            SUM(service_revenue) as labor_revenue,
            SUM(parts_revenue) as parts_revenue,
            SUM(rental_revenue) as rental_revenue,
            SUM(sales_revenue) as equipment_revenue,
            SUM(total_revenue) as total_revenue
        FROM mart_sales_daily
        WHERE org_id = %s
          AND sales_date >= CURRENT_DATE - INTERVAL '%s months'
        GROUP BY year, month
        ORDER BY year, month
        """
        
        try:
            results = self.pg.execute_query(query, (self.org_id, months))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"MartService.get_department_margins_from_mart failed: {str(e)}")
            return []
    
    def get_etl_status(self) -> List[Dict[str, Any]]:
        """
        Get recent ETL job status
        
        Returns:
            List of recent ETL job records
        """
        query = """
        SELECT 
            job_name,
            org_id,
            started_at,
            completed_at,
            status,
            records_processed,
            records_inserted,
            records_updated,
            error_message
        FROM mart_etl_log
        WHERE org_id = %s OR org_id IS NULL
        ORDER BY started_at DESC
        LIMIT 20
        """
        
        try:
            results = self.pg.execute_query(query, (self.org_id,))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"MartService.get_etl_status failed: {str(e)}")
            return []
    
    def has_recent_data(self, max_age_hours: int = 48) -> bool:
        """
        Check if Mart tables have recent data
        
        Args:
            max_age_hours: Maximum age of data in hours
        
        Returns:
            True if data is fresh, False otherwise
        """
        query = """
        SELECT MAX(sales_date) as latest_date
        FROM mart_sales_daily
        WHERE org_id = %s
        """
        
        try:
            results = self.pg.execute_query(query, (self.org_id,))
            if results and results[0]['latest_date']:
                latest = results[0]['latest_date']
                if isinstance(latest, str):
                    latest = datetime.strptime(latest, '%Y-%m-%d')
                age = datetime.now() - datetime.combine(latest, datetime.min.time())
                return age.total_seconds() < (max_age_hours * 3600)
            return False
        except Exception as e:
            logger.error(f"MartService.has_recent_data failed: {str(e)}")
            return False


def get_mart_service(org_id: int) -> Optional[MartService]:
    """
    Factory function to get a MartService instance
    
    Args:
        org_id: Organization ID
    
    Returns:
        MartService instance or None if PostgreSQL not available
    """
    from src.services.postgres_service import get_postgres_db
    
    pg = get_postgres_db()
    if pg:
        return MartService(pg, org_id)
    return None
