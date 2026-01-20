"""
Bennett Sales Daily ETL
Extracts daily sales data from Softbase and loads into mart_sales_daily
"""

import os
import logging
from datetime import datetime, timedelta
from .base_etl import BaseETL

logger = logging.getLogger(__name__)


class BennettSalesETL(BaseETL):
    """ETL job for Bennett daily sales from Softbase"""
    
    # Bennett org_id (from organization table)
    BENNETT_ORG_ID = 4
    BENNETT_SCHEMA = 'ben002'
    
    def __init__(self, days_back: int = 7):
        """
        Initialize Bennett Sales ETL
        
        Args:
            days_back: Number of days to look back for data (default 7)
        """
        super().__init__(
            job_name='etl_bennett_sales_daily',
            org_id=self.BENNETT_ORG_ID,
            source_system='softbase',
            target_table='mart_sales_daily'
        )
        self.days_back = days_back
        self._azure_sql = None
    
    @property
    def azure_sql(self):
        """Lazy load Azure SQL service"""
        if self._azure_sql is None:
            from src.services.azure_sql_service import AzureSQLService
            self._azure_sql = AzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """Extract daily sales data from Softbase InvoiceReg table"""
        
        # Calculate date range
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
            
        FROM {self.BENNETT_SCHEMA}.InvoiceReg
        WHERE InvoiceDate >= '{start_date}'
          AND InvoiceDate <= '{end_date}'
        GROUP BY 
            CAST(InvoiceDate AS DATE),
            YEAR(InvoiceDate),
            MONTH(InvoiceDate),
            DATEPART(WEEKDAY, InvoiceDate)
        ORDER BY sales_date
        """
        
        logger.info(f"Extracting sales data from {start_date} to {end_date}")
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
                'open_work_orders': 0,  # Will be populated separately
                'closed_work_orders': 0,  # Will be populated separately
                'source_system': self.source_system
            })
        
        return transformed
    
    def load(self, data: list) -> None:
        """Load transformed data into mart_sales_daily"""
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'sales_date'])


class BennettCashFlowETL(BaseETL):
    """ETL job for Bennett cash flow from Softbase GL"""
    
    BENNETT_ORG_ID = 4
    BENNETT_SCHEMA = 'ben002'
    
    def __init__(self, months_back: int = 12):
        super().__init__(
            job_name='etl_bennett_cash_flow',
            org_id=self.BENNETT_ORG_ID,
            source_system='softbase_gl',
            target_table='mart_cash_flow'
        )
        self.months_back = months_back
        self._azure_sql = None
    
    @property
    def azure_sql(self):
        if self._azure_sql is None:
            from src.services.azure_sql_service import AzureSQLService
            self._azure_sql = AzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """Extract cash flow data from GL table"""
        
        # Get last N months of data
        now = datetime.now()
        
        query = f"""
        WITH CashAccounts AS (
            SELECT 
                Year, Month,
                SUM(YTD) as cash_balance,
                SUM(MTD) as cash_change_mtd
            FROM {self.BENNETT_SCHEMA}.GL
            WHERE AccountNo IN ('110000', '113000', '114000')
            GROUP BY Year, Month
        ),
        OperatingCF AS (
            SELECT 
                Year, Month,
                SUM(MTD) as operating_cf
            FROM {self.BENNETT_SCHEMA}.GL
            WHERE AccountNo LIKE '4%' OR AccountNo LIKE '5%' OR AccountNo LIKE '6%'
            GROUP BY Year, Month
        ),
        WorkingCapital AS (
            SELECT 
                Year, Month,
                SUM(CASE WHEN AccountNo LIKE '12%' THEN MTD ELSE 0 END) as ar_change,
                SUM(CASE WHEN AccountNo LIKE '13%' THEN MTD ELSE 0 END) as inventory_change,
                SUM(CASE WHEN AccountNo LIKE '20%' THEN MTD ELSE 0 END) as ap_change
            FROM {self.BENNETT_SCHEMA}.GL
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
        
        results = self.azure_sql.execute_query(query)
        return results if results else []
    
    def transform(self, data: list) -> list:
        """Transform cash flow data"""
        import json
        from calendar import monthrange
        
        transformed = []
        
        for row in data:
            year = row['year']
            month = row['month']
            _, last_day = monthrange(year, month)
            period_end = datetime(year, month, last_day).date()
            
            operating_cf = float(row['operating_cash_flow'] or 0)
            
            # Determine health status
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
                'investing_cash_flow': 0,  # Would need additional query
                'financing_cash_flow': 0,  # Would need additional query
                'health_status': health_status,
                'non_operating_breakdown': json.dumps({}),
                'source_system': self.source_system
            })
        
        return transformed
    
    def load(self, data: list) -> None:
        """Load cash flow data"""
        for record in data:
            self.upsert_record(record, unique_columns=['org_id', 'year', 'month'])


def run_bennett_etl():
    """Run all Bennett ETL jobs"""
    logger.info("=" * 50)
    logger.info("Starting Bennett ETL Jobs")
    logger.info("=" * 50)
    
    jobs = [
        BennettSalesETL(days_back=30),
        BennettCashFlowETL(months_back=12),
    ]
    
    results = {}
    for job in jobs:
        success = job.run()
        results[job.job_name] = 'success' if success else 'failed'
    
    logger.info("\n" + "=" * 50)
    logger.info("Bennett ETL Summary:")
    for job_name, status in results.items():
        logger.info(f"  {job_name}: {status}")
    logger.info("=" * 50)
    
    return all(s == 'success' for s in results.values())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_bennett_etl()
