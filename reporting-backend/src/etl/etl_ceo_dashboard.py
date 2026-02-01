"""
CEO Dashboard ETL
Extracts and pre-aggregates all CEO Dashboard metrics from Softbase
Runs every 2 hours during business hours for fast dashboard loading
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from .base_etl import BaseETL

logger = logging.getLogger(__name__)

# GL Account Mappings by Department (Source: Softbase P&L)
GL_ACCOUNTS = {
    'new_equipment': {
        'dept_code': 10,
        'dept_name': 'New Equipment',
        'revenue': ['410001', '412001', '413001', '414001', '421001', '426001', '431001', '434001'],
        'cogs': ['510001', '513001', '514001', '521001', '525001', '526001', '531001', '534001', '534013', '538000']
    },
    'used_equipment': {
        'dept_code': 20,
        'dept_name': 'Used Equipment',
        'revenue': ['410002', '412002', '413002', '414002', '421002', '426002', '431002', '434002', '436001'],
        'cogs': ['510002', '512002', '513002', '514002', '521002', '525002', '526002', '531002', '534002', '536001']
    },
    'parts': {
        'dept_code': 30,
        'dept_name': 'Parts',
        'revenue': ['410003', '410012', '410014', '410015', '421003', '424000', '429001', '430000', '433000', '434003', '436002', '439000'],
        'cogs': ['510003', '510012', '510013', '510014', '510015', '521003', '522001', '524000', '529002', '530000', '533000', '534003', '536002', '542000', '543000', '544000']
    },
    'service': {
        'dept_code': 40,
        'dept_name': 'Service',
        'revenue': ['410004', '410005', '410007', '410016', '421004', '421005', '421006', '421007', '423000', '425000', '428000', '429002', '432000', '435000', '435001', '435002', '435003', '435004'],
        'cogs': ['510004', '510005', '510007', '512001', '521004', '521005', '521006', '521007', '522000', '523000', '528000', '529001', '534015', '535001', '535002', '535003', '535004', '535005']
    },
    'rental': {
        'dept_code': 60,
        'dept_name': 'Rental',
        'revenue': ['410008', '411001', '419000', '420000', '421000', '434012'],
        'cogs': ['510008', '511001', '519000', '520000', '521008', '534014', '537001', '539000', '545000']
    },
    'transportation': {
        'dept_code': 80,
        'dept_name': 'Transportation',
        'revenue': ['410010', '421010', '434010', '434013'],
        'cogs': ['510010', '521010', '534010', '534012']
    },
    'administrative': {
        'dept_code': 90,
        'dept_name': 'Administrative',
        'revenue': ['410011', '421011', '422100', '427000', '434011'],
        'cogs': ['510011', '521011', '522100', '525000', '527000', '532000', '534011', '540000', '541000']
    }
}

OTHER_INCOME_ACCOUNTS = ['701000', '702000', '703000', '704000', '705000']


class CEODashboardETL(BaseETL):
    """ETL job for CEO Dashboard metrics from Softbase"""
    
    BENNETT_ORG_ID = 4
    BENNETT_SCHEMA = 'ben002'
    
    def __init__(self):
        """Initialize CEO Dashboard ETL"""
        super().__init__(
            job_name='etl_ceo_dashboard',
            org_id=self.BENNETT_ORG_ID,
            source_system='softbase',
            target_table='mart_ceo_metrics'
        )
        self._azure_sql = None
        self.start_time = None
        self.current_date = datetime.now()
        self.month_start = self.current_date.replace(day=1).strftime('%Y-%m-%d')
        self.thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Fiscal year start (November 1st)
        if self.current_date.month >= 11:
            self.fiscal_year_start = datetime(self.current_date.year, 11, 1).strftime('%Y-%m-%d')
        else:
            self.fiscal_year_start = datetime(self.current_date.year - 1, 11, 1).strftime('%Y-%m-%d')
    
    @property
    def azure_sql(self):
        """Lazy load Azure SQL service"""
        if self._azure_sql is None:
            from src.services.azure_sql_service import AzureSQLService
            self._azure_sql = AzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """Extract all CEO Dashboard metrics from Softbase"""
        self.start_time = time.time()
        
        metrics = {
            'org_id': self.org_id,
            'snapshot_timestamp': datetime.now(),
            'snapshot_date': datetime.now().date(),
            'fiscal_year_start': self.fiscal_year_start,
        }
        
        # Extract each metric set
        logger.info("  Extracting KPI metrics...")
        metrics.update(self._extract_kpi_metrics())
        
        logger.info("  Extracting work order metrics...")
        metrics.update(self._extract_work_order_metrics())
        
        logger.info("  Extracting monthly sales...")
        metrics['monthly_sales'] = self._extract_monthly_sales()
        metrics['monthly_sales_excluding_equipment'] = self._extract_monthly_sales_excluding_equipment()
        metrics['monthly_sales_by_stream'] = self._extract_monthly_sales_by_stream()
        
        logger.info("  Extracting equipment sales...")
        metrics['monthly_equipment_sales'] = self._extract_monthly_equipment_sales()
        
        logger.info("  Extracting monthly work orders...")
        metrics['monthly_work_orders'] = self._extract_monthly_work_orders()
        
        logger.info("  Extracting monthly quotes...")
        metrics['monthly_quotes'] = self._extract_monthly_quotes()
        
        logger.info("  Extracting top customers...")
        metrics['top_customers'] = self._extract_top_customers()
        
        logger.info("  Extracting invoice delays...")
        metrics['monthly_invoice_delays'] = self._extract_monthly_invoice_delays()
        
        # Calculate ETL duration
        metrics['etl_duration_seconds'] = round(time.time() - self.start_time, 2)
        
        return [metrics]
    
    def _extract_kpi_metrics(self) -> dict:
        """Extract KPI card metrics"""
        schema = self.BENNETT_SCHEMA
        
        # Build revenue account list
        all_revenue_accounts = []
        for dept in GL_ACCOUNTS.values():
            all_revenue_accounts.extend(dept['revenue'])
        all_revenue_accounts.extend(OTHER_INCOME_ACCOUNTS)
        revenue_list = "', '".join(all_revenue_accounts)
        
        # Current month sales
        query = f"""
        SELECT -SUM(Amount) as total_sales
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('{revenue_list}')
            AND MONTH(EffectiveDate) = {self.current_date.month}
            AND YEAR(EffectiveDate) = {self.current_date.year}
            AND Posted = 1
        """
        result = self.azure_sql.execute_query(query)
        current_month_sales = float(result[0]['total_sales'] or 0) if result else 0
        
        # YTD sales
        query = f"""
        SELECT -SUM(Amount) as ytd_sales
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('{revenue_list}')
            AND EffectiveDate >= '{self.fiscal_year_start}'
            AND EffectiveDate < DATEADD(DAY, 1, GETDATE())
            AND Posted = 1
        """
        result = self.azure_sql.execute_query(query)
        ytd_sales = float(result[0]['ytd_sales'] or 0) if result else 0
        
        # Inventory count
        query = f"""
        SELECT COUNT(*) as inventory_count
        FROM {schema}.Equipment
        WHERE RentalStatus = 'Ready To Rent'
        """
        result = self.azure_sql.execute_query(query)
        inventory_count = int(result[0]['inventory_count']) if result else 0
        
        # Active customers (last 30 days vs previous 30 days)
        sixty_days_ago = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        query = f"""
        SELECT 
            COUNT(DISTINCT CASE 
                WHEN InvoiceDate >= '{self.thirty_days_ago}' 
                THEN CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END
                ELSE NULL 
            END) as active_customers,
            COUNT(DISTINCT CASE 
                WHEN InvoiceDate >= '{sixty_days_ago}' AND InvoiceDate < '{self.thirty_days_ago}' 
                THEN CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END
                ELSE NULL 
            END) as previous_month_customers
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '{sixty_days_ago}'
        AND BillToName IS NOT NULL
        AND BillToName != ''
        AND BillToName NOT LIKE '%Wells Fargo%'
        AND BillToName NOT LIKE '%Maintenance contract%'
        AND BillToName NOT LIKE '%Rental Fleet%'
        """
        result = self.azure_sql.execute_query(query)
        active_customers = int(result[0]['active_customers']) if result else 0
        active_customers_previous = int(result[0]['previous_month_customers']) if result else 0
        
        # Total customers
        query = f"""
        SELECT COUNT(DISTINCT CASE 
            WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
            WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
            ELSE BillToName
        END) as total_customers
        FROM {schema}.InvoiceReg
        WHERE BillToName IS NOT NULL
        AND BillToName != ''
        AND BillToName NOT LIKE '%Wells Fargo%'
        AND BillToName NOT LIKE '%Maintenance contract%'
        AND BillToName NOT LIKE '%Rental Fleet%'
        """
        result = self.azure_sql.execute_query(query)
        total_customers = int(result[0]['total_customers']) if result else 0
        
        return {
            'current_month_sales': current_month_sales,
            'ytd_sales': ytd_sales,
            'inventory_count': inventory_count,
            'active_customers': active_customers,
            'active_customers_previous': active_customers_previous,
            'total_customers': total_customers,
        }
    
    def _extract_work_order_metrics(self) -> dict:
        """Extract work order metrics"""
        schema = self.BENNETT_SCHEMA
        
        # Open work orders with value
        query = f"""
        WITH LaborTotals AS (
            SELECT WONo, SUM(Sell) as labor_total FROM {schema}.WOLabor GROUP BY WONo
        ),
        PartsTotals AS (
            SELECT WONo, SUM(Sell * Qty) as parts_total FROM {schema}.WOParts GROUP BY WONo
        ),
        MiscTotals AS (
            SELECT WONo, SUM(Sell) as misc_total FROM {schema}.WOMisc GROUP BY WONo
        )
        SELECT 
            COUNT(*) as count,
            SUM(COALESCE(l.labor_total, 0) + COALESCE(p.parts_total, 0) + COALESCE(m.misc_total, 0)) as total_value
        FROM {schema}.WO w
        LEFT JOIN LaborTotals l ON w.WONo = l.WONo
        LEFT JOIN PartsTotals p ON w.WONo = p.WONo
        LEFT JOIN MiscTotals m ON w.WONo = m.WONo
        WHERE w.CompletedDate IS NULL AND w.ClosedDate IS NULL
        """
        result = self.azure_sql.execute_query(query)
        open_wo_count = int(result[0]['count']) if result else 0
        open_wo_value = float(result[0]['total_value'] or 0) if result else 0
        
        # Previous month open WO value (for comparison)
        previous_month_end = (self.current_date.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        query = f"""
        WITH LaborTotals AS (
            SELECT WONo, SUM(Sell) as labor_total FROM {schema}.WOLabor GROUP BY WONo
        ),
        PartsTotals AS (
            SELECT WONo, SUM(Sell * Qty) as parts_total FROM {schema}.WOParts GROUP BY WONo
        ),
        MiscTotals AS (
            SELECT WONo, SUM(Sell) as misc_total FROM {schema}.WOMisc GROUP BY WONo
        )
        SELECT SUM(COALESCE(l.labor_total, 0) + COALESCE(p.parts_total, 0) + COALESCE(m.misc_total, 0)) as previous_total
        FROM {schema}.WO w
        LEFT JOIN LaborTotals l ON w.WONo = l.WONo
        LEFT JOIN PartsTotals p ON w.WONo = p.WONo
        LEFT JOIN MiscTotals m ON w.WONo = m.WONo
        WHERE w.OpenDate <= '{previous_month_end}'
        AND (w.CompletedDate IS NULL OR w.CompletedDate > '{previous_month_end}')
        AND (w.ClosedDate IS NULL OR w.ClosedDate > '{previous_month_end}')
        """
        result = self.azure_sql.execute_query(query)
        open_wo_previous_value = float(result[0]['previous_total'] or 0) if result else 0
        
        # Work order types breakdown
        query = f"""
        WITH LaborTotals AS (
            SELECT WONo, SUM(Sell) as labor_total FROM {schema}.WOLabor GROUP BY WONo
        ),
        PartsTotals AS (
            SELECT WONo, SUM(Sell * Qty) as parts_total FROM {schema}.WOParts GROUP BY WONo
        ),
        MiscTotals AS (
            SELECT WONo, SUM(Sell) as misc_total FROM {schema}.WOMisc GROUP BY WONo
        )
        SELECT 
            CASE 
                WHEN w.Type = 'S' THEN 'Service'
                WHEN w.Type = 'R' THEN 'Rental'
                WHEN w.Type = 'P' THEN 'Parts'
                WHEN w.Type = 'PM' THEN 'Preventive Maintenance'
                WHEN w.Type = 'SH' THEN 'Shop'
                WHEN w.Type = 'E' THEN 'Equipment'
                WHEN w.Type IS NULL THEN 'Unspecified'
                ELSE w.Type
            END as type_name,
            COUNT(*) as count,
            SUM(COALESCE(l.labor_total, 0) + COALESCE(p.parts_total, 0) + COALESCE(m.misc_total, 0)) as total_value
        FROM {schema}.WO w
        LEFT JOIN LaborTotals l ON w.WONo = l.WONo
        LEFT JOIN PartsTotals p ON w.WONo = p.WONo
        LEFT JOIN MiscTotals m ON w.WONo = m.WONo
        WHERE w.CompletedDate IS NULL AND w.ClosedDate IS NULL
        GROUP BY w.Type
        ORDER BY total_value DESC
        """
        result = self.azure_sql.execute_query(query)
        work_order_types = [{'type': r['type_name'], 'count': int(r['count']), 'value': float(r['total_value'] or 0)} for r in result] if result else []
        
        # Uninvoiced work orders
        query = f"""
        WITH LaborTotals AS (
            SELECT WONo, SUM(Sell) as labor_total FROM {schema}.WOLabor GROUP BY WONo
        ),
        PartsTotals AS (
            SELECT WONo, SUM(Sell * Qty) as parts_total FROM {schema}.WOParts GROUP BY WONo
        ),
        MiscTotals AS (
            SELECT WONo, SUM(Sell) as misc_total FROM {schema}.WOMisc GROUP BY WONo
        )
        SELECT COUNT(*) as count, SUM(COALESCE(l.labor_total, 0) + COALESCE(p.parts_total, 0) + COALESCE(m.misc_total, 0)) as total_value
        FROM {schema}.WO w
        LEFT JOIN LaborTotals l ON w.WONo = l.WONo
        LEFT JOIN PartsTotals p ON w.WONo = p.WONo
        LEFT JOIN MiscTotals m ON w.WONo = m.WONo
        WHERE w.CompletedDate IS NOT NULL AND w.InvoiceDate IS NULL
        """
        result = self.azure_sql.execute_query(query)
        uninvoiced_count = int(result[0]['count']) if result else 0
        uninvoiced_value = float(result[0]['total_value'] or 0) if result else 0
        
        # Awaiting invoice (Service, Shop, PM)
        query = f"""
        WITH LaborTotals AS (
            SELECT WONo, SUM(Sell) as labor_total FROM {schema}.WOLabor GROUP BY WONo
        ),
        PartsTotals AS (
            SELECT WONo, SUM(Sell * Qty) as parts_total FROM {schema}.WOParts GROUP BY WONo
        ),
        MiscTotals AS (
            SELECT WONo, SUM(Sell) as misc_total FROM {schema}.WOMisc GROUP BY WONo
        )
        SELECT 
            COUNT(*) as count, 
            SUM(COALESCE(l.labor_total, 0) + COALESCE(p.parts_total, 0) + COALESCE(m.misc_total, 0)) as total_value,
            AVG(DATEDIFF(day, w.CompletedDate, GETDATE())) as avg_days
        FROM {schema}.WO w
        LEFT JOIN LaborTotals l ON w.WONo = l.WONo
        LEFT JOIN PartsTotals p ON w.WONo = p.WONo
        LEFT JOIN MiscTotals m ON w.WONo = m.WONo
        WHERE w.CompletedDate IS NOT NULL 
        AND w.ClosedDate IS NULL 
        AND w.InvoiceDate IS NULL
        AND w.Type IN ('S', 'SH', 'PM')
        """
        result = self.azure_sql.execute_query(query)
        awaiting_count = int(result[0]['count']) if result else 0
        awaiting_value = float(result[0]['total_value'] or 0) if result else 0
        awaiting_avg_days = float(result[0]['avg_days'] or 0) if result else 0
        
        return {
            'open_work_orders_count': open_wo_count,
            'open_work_orders_value': open_wo_value,
            'open_work_orders_previous_value': open_wo_previous_value,
            'work_order_types': work_order_types,
            'uninvoiced_wo_count': uninvoiced_count,
            'uninvoiced_wo_value': uninvoiced_value,
            'awaiting_invoice_count': awaiting_count,
            'awaiting_invoice_value': awaiting_value,
            'awaiting_invoice_avg_days': awaiting_avg_days,
        }
    
    def _extract_monthly_sales(self) -> list:
        """Extract monthly sales with trailing 13 months"""
        schema = self.BENNETT_SCHEMA
        
        all_revenue_accounts = []
        all_cost_accounts = []
        for dept in GL_ACCOUNTS.values():
            all_revenue_accounts.extend(dept['revenue'])
            all_cost_accounts.extend(dept['cogs'])
        all_revenue_accounts.extend(OTHER_INCOME_ACCOUNTS)
        
        revenue_list = "', '".join(all_revenue_accounts)
        cost_list = "', '".join(all_cost_accounts)
        all_accounts_list = "', '".join(all_revenue_accounts + all_cost_accounts)
        
        query = f"""
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            -SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN AccountNo IN ('{cost_list}') THEN Amount ELSE 0 END) as total_cost
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('{all_accounts_list}')
            AND EffectiveDate >= DATEADD(month, -13, GETDATE())
            AND Posted = 1
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        """
        
        results = self.azure_sql.execute_query(query)
        monthly_sales = []
        
        if results:
            for row in results:
                revenue = float(row['total_revenue'] or 0)
                cost = float(row['total_cost'] or 0)
                margin = round(((revenue - cost) / revenue) * 100, 1) if revenue > 0 else None
                
                monthly_sales.append({
                    'year': row['year'],
                    'month': row['month'],
                    'amount': revenue,
                    'cost': cost,
                    'margin': margin,
                    'gross_margin_dollars': revenue - cost
                })
        
        return monthly_sales
    
    def _extract_monthly_sales_excluding_equipment(self) -> list:
        """Extract monthly sales excluding equipment departments"""
        schema = self.BENNETT_SCHEMA
        
        all_revenue_accounts = []
        all_cost_accounts = []
        include_depts = ['service', 'parts', 'rental', 'transportation', 'administrative']
        
        for dept_key in include_depts:
            if dept_key in GL_ACCOUNTS:
                dept = GL_ACCOUNTS[dept_key]
                all_revenue_accounts.extend(dept['revenue'])
                all_cost_accounts.extend(dept['cogs'])
        all_revenue_accounts.extend(OTHER_INCOME_ACCOUNTS)
        
        revenue_list = "', '".join(all_revenue_accounts)
        cost_list = "', '".join(all_cost_accounts)
        all_accounts_list = "', '".join(all_revenue_accounts + all_cost_accounts)
        
        query = f"""
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            -SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN AccountNo IN ('{cost_list}') THEN Amount ELSE 0 END) as total_cost
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('{all_accounts_list}')
            AND EffectiveDate >= DATEADD(month, -13, GETDATE())
            AND Posted = 1
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        """
        
        results = self.azure_sql.execute_query(query)
        monthly_sales = []
        
        if results:
            for row in results:
                revenue = float(row['total_revenue'] or 0)
                cost = float(row['total_cost'] or 0)
                margin = round(((revenue - cost) / revenue) * 100, 1) if revenue > 0 else None
                
                monthly_sales.append({
                    'year': row['year'],
                    'month': row['month'],
                    'amount': revenue,
                    'cost': cost,
                    'margin': margin,
                    'gross_margin_dollars': revenue - cost
                })
        
        return monthly_sales
    
    def _extract_monthly_sales_by_stream(self) -> list:
        """Extract monthly sales by revenue stream (Service, Parts, Rental)"""
        schema = self.BENNETT_SCHEMA
        
        service_rev = GL_ACCOUNTS['service']['revenue']
        service_cost = GL_ACCOUNTS['service']['cogs']
        parts_rev = GL_ACCOUNTS['parts']['revenue']
        parts_cost = GL_ACCOUNTS['parts']['cogs']
        rental_rev = GL_ACCOUNTS['rental']['revenue']
        rental_cost = GL_ACCOUNTS['rental']['cogs']
        
        service_rev_list = "', '".join(service_rev)
        service_cost_list = "', '".join(service_cost)
        parts_rev_list = "', '".join(parts_rev)
        parts_cost_list = "', '".join(parts_cost)
        rental_rev_list = "', '".join(rental_rev)
        rental_cost_list = "', '".join(rental_cost)
        
        all_accounts = service_rev + service_cost + parts_rev + parts_cost + rental_rev + rental_cost
        all_accounts_list = "', '".join(all_accounts)
        
        query = f"""
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            -SUM(CASE WHEN AccountNo IN ('{service_rev_list}') THEN Amount ELSE 0 END) as labor_revenue,
            SUM(CASE WHEN AccountNo IN ('{service_cost_list}') THEN Amount ELSE 0 END) as labor_cost,
            -SUM(CASE WHEN AccountNo IN ('{parts_rev_list}') THEN Amount ELSE 0 END) as parts_revenue,
            SUM(CASE WHEN AccountNo IN ('{parts_cost_list}') THEN Amount ELSE 0 END) as parts_cost,
            -SUM(CASE WHEN AccountNo IN ('{rental_rev_list}') THEN Amount ELSE 0 END) as rental_revenue,
            SUM(CASE WHEN AccountNo IN ('{rental_cost_list}') THEN Amount ELSE 0 END) as rental_cost
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('{all_accounts_list}')
            AND EffectiveDate >= DATEADD(month, -13, GETDATE())
            AND Posted = 1
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        """
        
        results = self.azure_sql.execute_query(query)
        monthly_data = []
        
        if results:
            for row in results:
                parts_rev = float(row['parts_revenue'] or 0)
                parts_cost = float(row['parts_cost'] or 0)
                labor_rev = float(row['labor_revenue'] or 0)
                labor_cost = float(row['labor_cost'] or 0)
                rental_rev = float(row['rental_revenue'] or 0)
                rental_cost = float(row['rental_cost'] or 0)
                
                monthly_data.append({
                    'year': row['year'],
                    'month': row['month'],
                    'parts': parts_rev,
                    'labor': labor_rev,
                    'rental': rental_rev,
                    'parts_margin': round(((parts_rev - parts_cost) / parts_rev) * 100, 1) if parts_rev > 0 else None,
                    'labor_margin': round(((labor_rev - labor_cost) / labor_rev) * 100, 1) if labor_rev > 0 else None,
                    'rental_margin': round(((rental_rev - rental_cost) / rental_rev) * 100, 1) if rental_rev > 0 else None,
                })
        
        return monthly_data
    
    def _extract_monthly_equipment_sales(self) -> list:
        """Extract monthly Linde new truck sales"""
        schema = self.BENNETT_SCHEMA
        
        query = f"""
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            ABS(SUM(CASE WHEN AccountNo = '413001' THEN Amount ELSE 0 END)) as equipment_revenue,
            ABS(SUM(CASE WHEN AccountNo = '513001' THEN Amount ELSE 0 END)) as equipment_cost
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('413001', '513001')
            AND EffectiveDate >= DATEADD(month, -13, GETDATE())
            AND Posted = 1
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        """
        
        results = self.azure_sql.execute_query(query)
        monthly_data = []
        
        if results:
            for row in results:
                revenue = float(row['equipment_revenue'] or 0)
                cost = float(row['equipment_cost'] or 0)
                margin = round(((revenue - cost) / revenue) * 100, 1) if revenue > 0 else None
                
                monthly_data.append({
                    'year': row['year'],
                    'month': row['month'],
                    'amount': revenue,
                    'cost': cost,
                    'margin': margin,
                })
        
        return monthly_data
    
    def _extract_monthly_work_orders(self) -> list:
        """Extract monthly work order counts"""
        schema = self.BENNETT_SCHEMA
        
        query = f"""
        SELECT 
            YEAR(OpenDate) as year,
            MONTH(OpenDate) as month,
            COUNT(*) as opened,
            COUNT(CASE WHEN CompletedDate IS NOT NULL THEN 1 END) as completed,
            COUNT(CASE WHEN ClosedDate IS NOT NULL THEN 1 END) as closed
        FROM {schema}.WO
        WHERE OpenDate >= '2025-03-01'
        GROUP BY YEAR(OpenDate), MONTH(OpenDate)
        ORDER BY YEAR(OpenDate), MONTH(OpenDate)
        """
        
        results = self.azure_sql.execute_query(query)
        monthly_data = []
        
        if results:
            for row in results:
                monthly_data.append({
                    'year': row['year'],
                    'month': row['month'],
                    'opened': int(row['opened']),
                    'completed': int(row['completed']),
                    'closed': int(row['closed']),
                })
        
        return monthly_data
    
    def _extract_monthly_quotes(self) -> list:
        """Extract monthly quote values"""
        schema = self.BENNETT_SCHEMA
        
        query = f"""
        WITH LatestQuotes AS (
            SELECT 
                YEAR(CreationTime) as year,
                MONTH(CreationTime) as month,
                WONo,
                MAX(CAST(CreationTime AS DATE)) as latest_quote_date
            FROM {schema}.WOQuote
            WHERE CreationTime >= '2025-03-01'
            AND Amount > 0
            GROUP BY YEAR(CreationTime), MONTH(CreationTime), WONo
        ),
        QuoteTotals AS (
            SELECT 
                lq.year,
                lq.month,
                lq.WONo,
                SUM(wq.Amount) as wo_total
            FROM LatestQuotes lq
            INNER JOIN {schema}.WOQuote wq
                ON lq.WONo = wq.WONo
                AND lq.year = YEAR(wq.CreationTime)
                AND lq.month = MONTH(wq.CreationTime)
                AND CAST(wq.CreationTime AS DATE) = lq.latest_quote_date
            WHERE wq.Amount > 0
            GROUP BY lq.year, lq.month, lq.WONo
        )
        SELECT year, month, SUM(wo_total) as amount
        FROM QuoteTotals
        GROUP BY year, month
        ORDER BY year, month
        """
        
        results = self.azure_sql.execute_query(query)
        monthly_data = []
        
        if results:
            for row in results:
                monthly_data.append({
                    'year': row['year'],
                    'month': row['month'],
                    'amount': float(row['amount']),
                })
        
        return monthly_data
    
    def _extract_top_customers(self) -> list:
        """Extract top 10 customers by fiscal YTD sales"""
        schema = self.BENNETT_SCHEMA
        
        query = f"""
        SELECT TOP 10
            CASE 
                WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                ELSE BillToName
            END as customer_name,
            SUM(GrandTotal) as total_sales,
            COUNT(*) as invoice_count
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '{self.fiscal_year_start}'
        AND BillToName IS NOT NULL
        AND BillToName != ''
        AND BillToName NOT LIKE '%Wells Fargo%'
        AND BillToName NOT LIKE '%Maintenance contract%'
        AND BillToName NOT LIKE '%Rental Fleet%'
        GROUP BY CASE 
            WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
            WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
            ELSE BillToName
        END
        ORDER BY total_sales DESC
        """
        
        results = self.azure_sql.execute_query(query)
        top_customers = []
        
        if results:
            for row in results:
                top_customers.append({
                    'customer_name': row['customer_name'],
                    'total_sales': float(row['total_sales']),
                    'invoice_count': int(row['invoice_count']),
                })
        
        return top_customers
    
    def _extract_monthly_invoice_delays(self) -> list:
        """Extract monthly average invoice delay"""
        schema = self.BENNETT_SCHEMA
        
        query = f"""
        WITH MonthEnds AS (
            SELECT DISTINCT 
                YEAR(CompletedDate) as year,
                MONTH(CompletedDate) as month,
                EOMONTH(CompletedDate) as month_end
            FROM {schema}.WO
            WHERE CompletedDate >= '2025-03-01'
                AND CompletedDate <= GETDATE()
                AND Type IN ('S', 'SH', 'PM')
        ),
        MonthlyDelays AS (
            SELECT 
                me.year,
                me.month,
                CASE 
                    WHEN COALESCE(w.InvoiceDate, w.ClosedDate) <= me.month_end 
                    THEN DATEDIFF(day, w.CompletedDate, COALESCE(w.InvoiceDate, w.ClosedDate))
                    ELSE DATEDIFF(day, w.CompletedDate, me.month_end)
                END as DaysWaiting
            FROM MonthEnds me
            INNER JOIN {schema}.WO w 
                ON YEAR(w.CompletedDate) = me.year 
                AND MONTH(w.CompletedDate) = me.month
            WHERE w.CompletedDate IS NOT NULL
                AND w.Type IN ('S', 'SH', 'PM')
        )
        SELECT 
            year,
            month,
            COUNT(*) as completed_count,
            AVG(CAST(DaysWaiting as FLOAT)) as avg_days_waiting
        FROM MonthlyDelays
        GROUP BY year, month
        ORDER BY year, month
        """
        
        results = self.azure_sql.execute_query(query)
        monthly_data = []
        
        if results:
            for row in results:
                monthly_data.append({
                    'year': row['year'],
                    'month': row['month'],
                    'avg_days': round(float(row['avg_days_waiting']), 1),
                    'completed_count': int(row['completed_count']),
                })
        
        return monthly_data
    
    def transform(self, data: list) -> list:
        """Transform - convert JSON fields to strings for PostgreSQL"""
        for record in data:
            # Convert list/dict fields to JSON strings
            for key in ['work_order_types', 'monthly_sales', 'monthly_sales_excluding_equipment',
                        'monthly_sales_by_stream', 'monthly_equipment_sales', 'monthly_work_orders',
                        'monthly_quotes', 'top_customers', 'monthly_invoice_delays', 'department_margins']:
                if key in record and record[key] is not None:
                    record[key] = json.dumps(record[key])
        return data
    
    def load(self, data: list) -> None:
        """Load transformed data into mart_ceo_metrics"""
        for record in data:
            # Build insert query
            columns = list(record.keys())
            values = list(record.values())
            placeholders = ', '.join(['%s'] * len(columns))
            column_list = ', '.join(columns)
            
            query = f"""
            INSERT INTO {self.target_table} ({column_list})
            VALUES ({placeholders})
            """
            
            self.pg.execute_update(query, tuple(values))
            self.records_inserted += 1


def run_ceo_dashboard_etl():
    """Run the CEO Dashboard ETL job"""
    etl = CEODashboardETL()
    return etl.run()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = run_ceo_dashboard_etl()
    exit(0 if success else 1)
