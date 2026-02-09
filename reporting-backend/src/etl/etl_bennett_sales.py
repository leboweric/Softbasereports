"""
Sales Daily ETL (Multi-Tenant)
Extracts daily sales data from Softbase and loads into mart_sales_daily.
Also includes Cash Flow ETL from GL data.

Supports all Softbase tenants - discovers them automatically via tenant_discovery.
Uses InvoiceReg fields (LaborTaxable, PartsTaxable, etc.) which are generic across all Softbase schemas.
Uses dynamic LIKE queries for GL-based cash flow data.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from calendar import monthrange
from .base_etl import BaseETL

logger = logging.getLogger(__name__)


class SalesDailyETL(BaseETL):
    """ETL job for daily sales from Softbase InvoiceReg"""
    
    def __init__(self, org_id=4, schema='ben002', azure_sql=None, days_back=7):
        """
        Initialize Sales Daily ETL for a specific tenant.
        
        Args:
            org_id: Organization ID from the organization table
            schema: Database schema for the tenant (e.g., 'ben002', 'ind004')
            azure_sql: Pre-configured AzureSQLService instance for the tenant
            days_back: Number of days to look back for data (default 7)
        """
        super().__init__(
            job_name='etl_sales_daily',
            org_id=org_id,
            source_system='softbase',
            target_table='mart_sales_daily'
        )
        self.schema = schema
        self._azure_sql = azure_sql
        self.days_back = days_back
    
    @property
    def azure_sql(self):
        """Lazy load Azure SQL service if not provided"""
        if self._azure_sql is None:
            from src.services.azure_sql_service import AzureSQLService
            self._azure_sql = AzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """Extract daily sales data from Softbase InvoiceReg table"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.days_back)
        
        query = f"""
        SELECT 
            CAST(InvoiceDate AS DATE) as sales_date,
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            DATEPART(WEEKDAY, InvoiceDate) - 1 as day_of_week,
            
            -- Service Revenue (Labor)
            SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as service_revenue,
            
            -- Parts Revenue
            SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as parts_revenue,
            
            -- Rental Revenue
            SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as rental_revenue,
            
            -- Sales/Equipment Revenue
            SUM(COALESCE(EquipmentTaxable, 0) + COALESCE(EquipmentNonTax, 0)) as sales_revenue,
            
            -- Total Revenue
            SUM(COALESCE(GrandTotal, 0)) as total_revenue,
            
            -- Cost of Goods Sold by department
            SUM(COALESCE(LaborCost, 0)) as service_cost,
            SUM(COALESCE(PartsCost, 0)) as parts_cost,
            SUM(COALESCE(RentalCost, 0)) as rental_cost,
            SUM(COALESCE(EquipmentCost, 0)) as sales_cost,
            SUM(COALESCE(LaborCost, 0) + COALESCE(PartsCost, 0) + COALESCE(RentalCost, 0) + COALESCE(EquipmentCost, 0)) as total_cost,
            
            -- Invoice Counts by type
            COUNT(CASE WHEN COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0) > 0 THEN 1 END) as service_invoices,
            COUNT(CASE WHEN COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0) > 0 THEN 1 END) as parts_invoices,
            COUNT(CASE WHEN COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0) > 0 THEN 1 END) as rental_invoices,
            COUNT(CASE WHEN COALESCE(EquipmentTaxable, 0) + COALESCE(EquipmentNonTax, 0) > 0 THEN 1 END) as sales_invoices,
            COUNT(*) as total_invoices
            
        FROM {self.schema}.InvoiceReg
        WHERE InvoiceDate >= '{start_date}'
          AND InvoiceDate <= '{end_date}'
        GROUP BY 
            CAST(InvoiceDate AS DATE),
            YEAR(InvoiceDate),
            MONTH(InvoiceDate),
            DATEPART(WEEKDAY, InvoiceDate)
        ORDER BY sales_date
        """
        
        logger.info(f"  [{self.schema}] Extracting sales data from {start_date} to {end_date}")
        results = self.azure_sql.execute_query(query)
        
        return results if results else []
    
    def transform(self, data: list) -> list:
        """Transform extracted data for loading"""
        transformed = []
        
        for row in data:
            transformed.append({
                'org_id': self.org_id,
                'sales_date': row['sales_date'],
                'year': row['year'],
                'month': row['month'],
                'day_of_week': row['day_of_week'],
                'service_revenue': float(row['service_revenue'] or 0),
                'parts_revenue': float(row['parts_revenue'] or 0),
                'rental_revenue': float(row['rental_revenue'] or 0),
                'sales_revenue': float(row['sales_revenue'] or 0),
                'total_revenue': float(row['total_revenue'] or 0),
                'service_cost': float(row['service_cost'] or 0),
                'parts_cost': float(row['parts_cost'] or 0),
                'rental_cost': float(row['rental_cost'] or 0),
                'sales_cost': float(row['sales_cost'] or 0),
                'total_cost': float(row['total_cost'] or 0),
                'service_invoices': int(row['service_invoices'] or 0),
                'parts_invoices': int(row['parts_invoices'] or 0),
                'rental_invoices': int(row['rental_invoices'] or 0),
                'sales_invoices': int(row['sales_invoices'] or 0),
                'total_invoices': int(row['total_invoices'] or 0),
                'open_work_orders': 0,
                'closed_work_orders': 0,
                'source_system': self.source_system
            })
        
        return transformed
    
    def load(self, data: list) -> None:
        """Load transformed data into mart_sales_daily"""
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'sales_date'])


class CashFlowETL(BaseETL):
    """ETL job for cash flow from Softbase GL - uses dynamic LIKE queries"""
    
    def __init__(self, org_id=4, schema='ben002', azure_sql=None, months_back=12):
        """
        Initialize Cash Flow ETL for a specific tenant.
        
        Args:
            org_id: Organization ID from the organization table
            schema: Database schema for the tenant (e.g., 'ben002', 'ind004')
            azure_sql: Pre-configured AzureSQLService instance for the tenant
            months_back: Number of months to look back (default 12)
        """
        super().__init__(
            job_name='etl_cash_flow',
            org_id=org_id,
            source_system='softbase_gl',
            target_table='mart_cash_flow'
        )
        self.schema = schema
        self._azure_sql = azure_sql
        self.months_back = months_back
    
    @property
    def azure_sql(self):
        """Lazy load Azure SQL service if not provided"""
        if self._azure_sql is None:
            from src.services.azure_sql_service import AzureSQLService
            self._azure_sql = AzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """Extract cash flow data from GL table using dynamic LIKE queries"""
        now = datetime.now()
        
        # Cash accounts: 1xxxxx starting with 11 (cash & equivalents)
        # Operating: 4% revenue + 5% COGS + 6% expenses
        # Working capital: 12% AR, 13% inventory, 20% AP
        query = f"""
        WITH CashAccounts AS (
            SELECT 
                Year, Month,
                SUM(YTD) as cash_balance,
                SUM(MTD) as cash_change_mtd
            FROM {self.schema}.GL
            WHERE AccountNo LIKE '11%'
            GROUP BY Year, Month
        ),
        OperatingCF AS (
            SELECT 
                Year, Month,
                SUM(MTD) as operating_cf
            FROM {self.schema}.GL
            WHERE AccountNo LIKE '4%' OR AccountNo LIKE '5%' OR AccountNo LIKE '6%'
            GROUP BY Year, Month
        ),
        WorkingCapital AS (
            SELECT 
                Year, Month,
                SUM(CASE WHEN AccountNo LIKE '12%' THEN MTD ELSE 0 END) as ar_change,
                SUM(CASE WHEN AccountNo LIKE '13%' THEN MTD ELSE 0 END) as inventory_change,
                SUM(CASE WHEN AccountNo LIKE '20%' THEN MTD ELSE 0 END) as ap_change
            FROM {self.schema}.GL
            GROUP BY Year, Month
        )
        SELECT 
            c.Year as year,
            c.Month as month,
            c.cash_balance,
            c.cash_change_mtd,
            COALESCE(o.operating_cf, 0) as operating_cash_flow,
            COALESCE(w.ar_change, 0) as ar_change,
            COALESCE(w.inventory_change, 0) as inventory_change,
            COALESCE(w.ap_change, 0) as ap_change
        FROM CashAccounts c
        LEFT JOIN OperatingCF o ON c.Year = o.Year AND c.Month = o.Month
        LEFT JOIN WorkingCapital w ON c.Year = w.Year AND c.Month = w.Month
        WHERE c.Year >= {now.year - 1}
        ORDER BY c.Year DESC, c.Month DESC
        """
        
        logger.info(f"  [{self.schema}] Extracting cash flow data")
        results = self.azure_sql.execute_query(query)
        return results if results else []
    
    def transform(self, data: list) -> list:
        """Transform cash flow data"""
        transformed = []
        
        for row in data:
            year = row['year']
            month = row['month']
            _, last_day = monthrange(year, month)
            period_end = datetime(year, month, last_day).date()
            
            operating_cf = float(row['operating_cash_flow'] or 0)
            
            if operating_cf > 0:
                health_status = 'healthy'
            elif operating_cf > -50000:
                health_status = 'warning'
            else:
                health_status = 'critical'
            
            transformed.append({
                'org_id': self.org_id,
                'year': year,
                'month': month,
                'period_end': period_end,
                'cash_balance': float(row['cash_balance'] or 0),
                'cash_change_mtd': float(row['cash_change_mtd'] or 0),
                'operating_cash_flow': operating_cf,
                'ar_change': float(row['ar_change'] or 0),
                'inventory_change': float(row['inventory_change'] or 0),
                'ap_change': float(row['ap_change'] or 0),
                'investing_cash_flow': 0,
                'financing_cash_flow': 0,
                'health_status': health_status,
                'non_operating_breakdown': json.dumps({}),
                'source_system': self.source_system
            })
        
        return transformed
    
    def load(self, data: list) -> None:
        """Load cash flow data"""
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'year', 'month'])


def run_bennett_etl(org_id=None):
    """
    Run Sales Daily and Cash Flow ETL jobs.
    
    If org_id is provided, runs for that specific org only.
    Otherwise, runs for ALL discovered Softbase tenants.
    
    Note: Kept as run_bennett_etl for backward compatibility with scheduler.
    """
    if org_id is not None:
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
                
                sales_etl = SalesDailyETL(
                    org_id=org_id,
                    schema=org.database_schema,
                    azure_sql=azure_sql,
                    days_back=30
                )
                cash_etl = CashFlowETL(
                    org_id=org_id,
                    schema=org.database_schema,
                    azure_sql=azure_sql,
                    months_back=12
                )
                
                sales_ok = sales_etl.run()
                cash_ok = cash_etl.run()
                return sales_ok and cash_ok
            else:
                logger.error(f"Organization {org_id} not found or has no schema")
                return False
        except Exception as e:
            logger.error(f"Failed to run sales ETL for org_id={org_id}: {e}")
            return False
    else:
        # Run for all tenants
        from .tenant_discovery import discover_softbase_tenants
        
        tenants = discover_softbase_tenants()
        if not tenants:
            logger.warning("No Softbase tenants found")
            return False
        
        all_success = True
        for tenant in tenants:
            logger.info(f"Running Sales/CashFlow ETL for {tenant.name} ({tenant.schema})")
            try:
                azure_sql = tenant.get_azure_sql_service()
                
                sales_etl = SalesDailyETL(
                    org_id=tenant.org_id,
                    schema=tenant.schema,
                    azure_sql=azure_sql,
                    days_back=30
                )
                cash_etl = CashFlowETL(
                    org_id=tenant.org_id,
                    schema=tenant.schema,
                    azure_sql=azure_sql,
                    months_back=12
                )
                
                sales_ok = sales_etl.run()
                cash_ok = cash_etl.run()
                
                if not (sales_ok and cash_ok):
                    all_success = False
                    
            except Exception as e:
                logger.error(f"Failed Sales/CashFlow ETL for {tenant.name}: {e}")
                all_success = False
        
        return all_success


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_bennett_etl()
