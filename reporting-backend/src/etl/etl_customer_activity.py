"""
Customer Activity ETL (Multi-Tenant)
Extracts customer activity data from Softbase and loads into mart_customer_activity
for fast churn analysis queries.

Supports all Softbase tenants - discovers them automatically via tenant_discovery.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from .base_etl import BaseETL

logger = logging.getLogger(__name__)


class CustomerActivityETL(BaseETL):
    """ETL job for customer activity from Softbase - used for churn analysis"""
    
    # Churn analysis periods (in days)
    RECENT_PERIOD_DAYS = 90   # Last 90 days = "recent period"
    PREVIOUS_PERIOD_DAYS = 90  # Days 91-180 = "previous period"
    
    def __init__(self, org_id=4, schema='ben002', azure_sql=None):
        """
        Initialize Customer Activity ETL for a specific tenant.
        
        Args:
            org_id: Organization ID from the organization table
            schema: Database schema for the tenant (e.g., 'ben002', 'ind004')
            azure_sql: Pre-configured AzureSQLService instance for the tenant
        """
        super().__init__(
            job_name='etl_customer_activity',
            org_id=org_id,
            source_system='softbase',
            target_table='mart_customer_activity'
        )
        self.schema = schema
        self._azure_sql = azure_sql
    
    @property
    def azure_sql(self):
        """Lazy load Azure SQL service if not provided"""
        if self._azure_sql is None:
            from src.services.azure_sql_service import AzureSQLService
            self._azure_sql = AzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """
        Extract customer activity data from Softbase InvoiceReg table.
        Calculates metrics for recent period (0-90 days) and previous period (91-180 days).
        Uses self.schema for tenant-specific table access.
        """
        
        schema = self.schema
        
        # Main query to get customer activity with period breakdowns
        query = f"""
        WITH CustomerNormalized AS (
            SELECT 
                InvoiceNo,
                InvoiceDate,
                BillTo,
                BillToName as CustomerName,
                GrandTotal,
                COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0) as ServiceRevenue,
                COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0) as PartsRevenue,
                COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0) as RentalRevenue
            FROM {schema}.InvoiceReg
            WHERE BillToName IS NOT NULL
            AND BillToName != ''
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
        
        logger.info(f"Extracting customer activity data for schema={schema}, org_id={self.org_id}")
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
                activity_status = 'churned'
            elif previous_count > 0 and revenue_change_percent <= -50:
                activity_status = 'at_risk'
            elif previous_count == 0 and recent_count > 0:
                activity_status = 'new'
            else:
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


def run_customer_activity_etl(org_id=None):
    """
    Run the customer activity ETL job.
    
    If org_id is provided, runs for that specific org only.
    Otherwise, runs for ALL discovered Softbase tenants.
    """
    if org_id is not None:
        # Run for a specific org (e.g., manual refresh from API)
        # Need to look up schema for this org
        try:
            from src.models.user import Organization
            org = Organization.query.get(org_id)
            if org and org.database_schema:
                from .tenant_discovery import TenantInfo
                tenant = TenantInfo(
                    org_id=org.id,
                    name=org.name,
                    schema=org.database_schema,
                    db_server=org.db_server,
                    db_name=org.db_name,
                    db_username=org.db_username,
                    db_password_encrypted=org.db_password_encrypted,
                    platform_type=org.platform_type
                )
                azure_sql = tenant.get_azure_sql_service()
                etl = CustomerActivityETL(
                    org_id=org_id,
                    schema=org.database_schema,
                    azure_sql=azure_sql
                )
                return etl.run()
            else:
                logger.error(f"Organization {org_id} not found or has no schema")
                return False
        except Exception as e:
            logger.error(f"Failed to run customer activity ETL for org_id={org_id}: {e}")
            return False
    else:
        # Run for all tenants
        from .tenant_discovery import run_etl_for_all_tenants
        results = run_etl_for_all_tenants(CustomerActivityETL, 'Customer Activity')
        return all(results.values()) if results else False


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = run_customer_activity_etl()
    exit(0 if success else 1)
