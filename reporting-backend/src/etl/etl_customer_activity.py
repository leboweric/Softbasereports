"""
Customer Activity ETL
Extracts customer activity data from Softbase and loads into mart_customer_activity
for fast churn analysis queries
"""

import os
import json
import logging
from datetime import datetime, timedelta
from .base_etl import BaseETL

logger = logging.getLogger(__name__)


class CustomerActivityETL(BaseETL):
    """ETL job for customer activity from Softbase - used for churn analysis"""
    
    # Bennett org_id (from organization table)
    BENNETT_ORG_ID = 4
    BENNETT_SCHEMA = 'ben002'
    
    # Churn analysis periods (in days)
    RECENT_PERIOD_DAYS = 90   # Last 90 days = "recent period"
    PREVIOUS_PERIOD_DAYS = 90  # Days 91-180 = "previous period"
    
    def __init__(self):
        """Initialize Customer Activity ETL"""
        super().__init__(
            job_name='etl_customer_activity',
            org_id=self.BENNETT_ORG_ID,
            source_system='softbase',
            target_table='mart_customer_activity'
        )
        self._azure_sql = None
    
    @property
    def azure_sql(self):
        """Lazy load Azure SQL service"""
        if self._azure_sql is None:
            from src.services.azure_sql_service import AzureSQLService
            self._azure_sql = AzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """
        Extract customer activity data from Softbase InvoiceReg table
        Calculates metrics for recent period (0-90 days) and previous period (91-180 days)
        """
        
        today = datetime.now().date()
        
        # Main query to get customer activity with period breakdowns
        query = f"""
        WITH CustomerNormalized AS (
            SELECT 
                InvoiceNo,
                InvoiceDate,
                BillTo,
                -- Normalize customer names (consolidate variations)
                CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END as CustomerName,
                GrandTotal,
                COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0) as ServiceRevenue,
                COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0) as PartsRevenue,
                COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0) as RentalRevenue
            FROM {self.BENNETT_SCHEMA}.InvoiceReg
            WHERE BillToName IS NOT NULL
            AND BillToName != ''
            AND BillToName NOT LIKE '%Wells Fargo%'
            AND BillToName NOT LIKE '%Maintenance contract%'
            AND BillToName NOT LIKE '%Rental Fleet%'
        ),
        -- Recent period: last 90 days
        RecentActivity AS (
            SELECT 
                CustomerName,
                BillTo,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue,
                SUM(ServiceRevenue) as service_revenue,
                SUM(PartsRevenue) as parts_revenue,
                SUM(RentalRevenue) as rental_revenue,
                MIN(InvoiceDate) as first_invoice,
                MAX(InvoiceDate) as last_invoice
            FROM CustomerNormalized
            WHERE InvoiceDate >= DATEADD(day, -{self.RECENT_PERIOD_DAYS}, GETDATE())
            GROUP BY CustomerName, BillTo
        ),
        -- Previous period: days 91-180
        PreviousActivity AS (
            SELECT 
                CustomerName,
                BillTo,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue,
                SUM(ServiceRevenue) as service_revenue,
                SUM(PartsRevenue) as parts_revenue,
                SUM(RentalRevenue) as rental_revenue
            FROM CustomerNormalized
            WHERE InvoiceDate >= DATEADD(day, -{self.RECENT_PERIOD_DAYS + self.PREVIOUS_PERIOD_DAYS}, GETDATE())
            AND InvoiceDate < DATEADD(day, -{self.RECENT_PERIOD_DAYS}, GETDATE())
            GROUP BY CustomerName, BillTo
        ),
        -- Lifetime metrics
        LifetimeActivity AS (
            SELECT 
                CustomerName,
                BillTo,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue,
                MIN(InvoiceDate) as first_invoice,
                MAX(InvoiceDate) as last_invoice
            FROM CustomerNormalized
            GROUP BY CustomerName, BillTo
        )
        SELECT 
            COALESCE(l.CustomerName, r.CustomerName, p.CustomerName) as customer_name,
            COALESCE(l.BillTo, r.BillTo, p.BillTo) as bill_to,
            
            -- Recent period metrics
            ISNULL(r.invoice_count, 0) as recent_invoice_count,
            ISNULL(r.total_revenue, 0) as recent_revenue,
            ISNULL(r.service_revenue, 0) as recent_service_revenue,
            ISNULL(r.parts_revenue, 0) as recent_parts_revenue,
            ISNULL(r.rental_revenue, 0) as recent_rental_revenue,
            r.first_invoice as recent_first_invoice,
            r.last_invoice as recent_last_invoice,
            
            -- Previous period metrics
            ISNULL(p.invoice_count, 0) as previous_invoice_count,
            ISNULL(p.total_revenue, 0) as previous_revenue,
            ISNULL(p.service_revenue, 0) as previous_service_revenue,
            ISNULL(p.parts_revenue, 0) as previous_parts_revenue,
            ISNULL(p.rental_revenue, 0) as previous_rental_revenue,
            
            -- Lifetime metrics
            ISNULL(l.invoice_count, 0) as lifetime_invoice_count,
            ISNULL(l.total_revenue, 0) as lifetime_revenue,
            l.first_invoice as first_invoice_date,
            l.last_invoice as last_invoice_date,
            DATEDIFF(day, l.last_invoice, GETDATE()) as days_since_last_invoice
            
        FROM LifetimeActivity l
        LEFT JOIN RecentActivity r ON l.CustomerName = r.CustomerName AND l.BillTo = r.BillTo
        LEFT JOIN PreviousActivity p ON l.CustomerName = p.CustomerName AND l.BillTo = p.BillTo
        WHERE l.total_revenue > 100  -- Filter out tiny customers
        ORDER BY l.total_revenue DESC
        """
        
        logger.info(f"Extracting customer activity data")
        results = self.azure_sql.execute_query(query)
        
        return results if results else []
    
    def transform(self, data: list) -> list:
        """
        Transform extracted data and calculate churn status
        
        Churn criteria:
        - CHURNED: No invoices in last 90 days but had invoices in days 91-180
        - AT_RISK: 50%+ revenue drop between periods
        - ACTIVE: Normal activity
        - NEW: Only activity in recent period (new customer)
        """
        transformed = []
        today = datetime.now().date()
        
        for row in data:
            recent_revenue = float(row['recent_revenue'] or 0)
            previous_revenue = float(row['previous_revenue'] or 0)
            recent_count = int(row['recent_invoice_count'] or 0)
            previous_count = int(row['previous_invoice_count'] or 0)
            
            # Calculate revenue change percentage
            if previous_revenue > 0:
                revenue_change_percent = ((recent_revenue - previous_revenue) / previous_revenue) * 100
            elif recent_revenue > 0:
                revenue_change_percent = 100  # New customer
            else:
                revenue_change_percent = 0
            
            # Determine activity status
            if recent_count == 0 and previous_count > 0:
                # No recent activity but had previous activity = CHURNED
                activity_status = 'churned'
            elif previous_count > 0 and revenue_change_percent <= -50:
                # Significant revenue drop = AT_RISK
                activity_status = 'at_risk'
            elif previous_count == 0 and recent_count > 0:
                # Only recent activity = NEW customer
                activity_status = 'new'
            else:
                # Normal activity = ACTIVE
                activity_status = 'active'
            
            transformed.append({
                'org_id': self.org_id,
                'customer_name': row['customer_name'],
                'bill_to': row['bill_to'],
                
                # Recent period
                'recent_invoice_count': recent_count,
                'recent_revenue': recent_revenue,
                'recent_service_revenue': float(row['recent_service_revenue'] or 0),
                'recent_parts_revenue': float(row['recent_parts_revenue'] or 0),
                'recent_rental_revenue': float(row['recent_rental_revenue'] or 0),
                'recent_first_invoice': row['recent_first_invoice'],
                'recent_last_invoice': row['recent_last_invoice'],
                
                # Previous period
                'previous_invoice_count': previous_count,
                'previous_revenue': previous_revenue,
                'previous_service_revenue': float(row['previous_service_revenue'] or 0),
                'previous_parts_revenue': float(row['previous_parts_revenue'] or 0),
                'previous_rental_revenue': float(row['previous_rental_revenue'] or 0),
                
                # Lifetime
                'lifetime_invoice_count': int(row['lifetime_invoice_count'] or 0),
                'lifetime_revenue': float(row['lifetime_revenue'] or 0),
                'first_invoice_date': row['first_invoice_date'],
                'last_invoice_date': row['last_invoice_date'],
                'days_since_last_invoice': int(row['days_since_last_invoice'] or 0),
                
                # Status
                'activity_status': activity_status,
                'revenue_change_percent': round(revenue_change_percent, 2),
                
                # Metadata
                'source_system': self.source_system,
                'snapshot_date': today
            })
        
        return transformed
    
    def load(self, data: list) -> None:
        """Load transformed data into mart_customer_activity"""
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'customer_name', 'snapshot_date'])


# Convenience function to run the ETL
def run_customer_activity_etl():
    """Run the customer activity ETL job"""
    etl = CustomerActivityETL()
    return etl.run()


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run ETL
    success = run_customer_activity_etl()
    exit(0 if success else 1)
