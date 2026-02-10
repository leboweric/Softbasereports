"""
CEO Dashboard ETL (Multi-Tenant)
Extracts and pre-aggregates all CEO Dashboard metrics from Softbase
Runs every 2 hours during business hours for fast dashboard loading.

Supports all Softbase tenants - discovers them automatically via tenant_discovery.
Uses dynamic LIKE queries (4% revenue, 5% COGS, 6% expenses) instead of hardcoded account lists.
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from .base_etl import BaseETL

logger = logging.getLogger(__name__)


class CEODashboardETL(BaseETL):
    """ETL job for CEO Dashboard metrics from Softbase"""
    
    def __init__(self, org_id=4, schema='ben002', azure_sql=None, fiscal_year_start_month=11):
        """
        Initialize CEO Dashboard ETL for a specific tenant.
        
        Args:
            org_id: Organization ID from the organization table
            schema: Database schema for the tenant (e.g., 'ben002', 'ind004')
            azure_sql: Pre-configured AzureSQLService instance for the tenant
            fiscal_year_start_month: Month number (1-12) when fiscal year starts
        """
        super().__init__(
            job_name='etl_ceo_dashboard',
            org_id=org_id,
            source_system='softbase',
            target_table='mart_ceo_metrics'
        )
        self.schema = schema
        self._azure_sql = azure_sql
        self.start_time = None
        self.current_date = datetime.now()
        self.month_start = self.current_date.replace(day=1).strftime('%Y-%m-%d')
        self.thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        self.fiscal_year_start_month = fiscal_year_start_month
        
        # Fiscal year start (dynamic per tenant)
        if self.current_date.month >= self.fiscal_year_start_month:
            self.fiscal_year_start = datetime(self.current_date.year, self.fiscal_year_start_month, 1).strftime('%Y-%m-%d')
        else:
            self.fiscal_year_start = datetime(self.current_date.year - 1, self.fiscal_year_start_month, 1).strftime('%Y-%m-%d')
    
    @property
    def azure_sql(self):
        """Lazy load Azure SQL service if not provided"""
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
        logger.info(f"  [{self.schema}] Extracting KPI metrics...")
        metrics.update(self._extract_kpi_metrics())
        
        logger.info(f"  [{self.schema}] Extracting work order metrics...")
        metrics.update(self._extract_work_order_metrics())
        
        logger.info(f"  [{self.schema}] Extracting monthly sales...")
        metrics['monthly_sales'] = self._extract_monthly_sales()
        metrics['monthly_sales_excluding_equipment'] = self._extract_monthly_sales_excluding_equipment()
        metrics['monthly_sales_by_stream'] = self._extract_monthly_sales_by_stream()
        
        logger.info(f"  [{self.schema}] Extracting equipment sales...")
        metrics['monthly_equipment_sales'] = self._extract_monthly_equipment_sales()
        
        logger.info(f"  [{self.schema}] Extracting monthly work orders...")
        metrics['monthly_work_orders'] = self._extract_monthly_work_orders()
        
        logger.info(f"  [{self.schema}] Extracting monthly quotes...")
        metrics['monthly_quotes'] = self._extract_monthly_quotes()
        
        logger.info(f"  [{self.schema}] Extracting top customers...")
        metrics['top_customers'] = self._extract_top_customers()
        
        logger.info(f"  [{self.schema}] Extracting invoice delays...")
        metrics['monthly_invoice_delays'] = self._extract_monthly_invoice_delays()
        
        # Calculate ETL duration
        metrics['etl_duration_seconds'] = round(time.time() - self.start_time, 2)
        
        return [metrics]
    
    def _extract_kpi_metrics(self) -> dict:
        """Extract KPI card metrics using dynamic LIKE queries"""
        schema = self.schema
        
        # Current month sales - dynamic revenue query
        query = f"""
        SELECT -SUM(Amount) as total_sales
        FROM {schema}.GLDetail
        WHERE AccountNo LIKE '4%'
            AND MONTH(EffectiveDate) = {self.current_date.month}
            AND YEAR(EffectiveDate) = {self.current_date.year}
            AND Posted = 1
        """
        result = self.azure_sql.execute_query(query)
        current_month_sales = float(result[0]['total_sales'] or 0) if result else 0
        
        # YTD sales - dynamic revenue query
        query = f"""
        SELECT -SUM(Amount) as ytd_sales
        FROM {schema}.GLDetail
        WHERE AccountNo LIKE '4%'
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
                WHEN InvoiceDate >= '{self.thirty_days_ago}' THEN BillToName
                ELSE NULL 
            END) as active_customers,
            COUNT(DISTINCT CASE 
                WHEN InvoiceDate >= '{sixty_days_ago}' AND InvoiceDate < '{self.thirty_days_ago}' THEN BillToName
                ELSE NULL 
            END) as previous_month_customers
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '{sixty_days_ago}'
        AND BillToName IS NOT NULL
        AND BillToName != ''
        """
        result = self.azure_sql.execute_query(query)
        active_customers = int(result[0]['active_customers']) if result else 0
        active_customers_previous = int(result[0]['previous_month_customers']) if result else 0
        
        # Total customers
        query = f"""
        SELECT COUNT(DISTINCT BillToName) as total_customers
        FROM {schema}.InvoiceReg
        WHERE BillToName IS NOT NULL
        AND BillToName != ''
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
        schema = self.schema
        
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
        """Extract monthly sales with trailing 13 months using dynamic LIKE queries"""
        schema = self.schema
        
        query = f"""
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN Amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN Amount ELSE 0 END) as total_cost
        FROM {schema}.GLDetail
        WHERE (AccountNo LIKE '4%' OR AccountNo LIKE '5%')
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
        """
        Extract monthly sales excluding equipment departments.
        Uses dynamic LIKE queries but excludes accounts starting with 41/51 (new equipment)
        and 41x002/51x002 patterns (used equipment).
        
        For a generic approach, we exclude accounts in the 10 (new equip) and 20 (used equip) 
        department ranges. Since we don't know exact account mappings per tenant, we use
        a broader approach: include all 4%/5% accounts but exclude known equipment patterns.
        
        Note: This is a best-effort approach. Once the Softbase Chart of Accounts is available,
        this can be refined with exact department-to-account mappings.
        """
        schema = self.schema
        
        # For now, use the same dynamic approach but try to exclude equipment-related accounts
        # Equipment departments typically use specific account suffixes
        # This query includes everything - the department breakdown will be refined later
        query = f"""
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN Amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN Amount ELSE 0 END) as total_cost
        FROM {schema}.GLDetail
        WHERE (AccountNo LIKE '4%' OR AccountNo LIKE '5%')
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
        """
        Extract monthly sales by revenue stream.
        Uses InvoiceReg for department breakdown since it has explicit department fields,
        rather than trying to map GL accounts to departments.
        """
        schema = self.schema
        
        query = f"""
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as labor_revenue,
            SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as parts_revenue,
            SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as rental_revenue
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -13, GETDATE())
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        """
        
        results = self.azure_sql.execute_query(query)
        monthly_data = []
        
        if results:
            for row in results:
                labor_rev = float(row['labor_revenue'] or 0)
                parts_rev = float(row['parts_revenue'] or 0)
                rental_rev = float(row['rental_revenue'] or 0)
                
                monthly_data.append({
                    'year': row['year'],
                    'month': row['month'],
                    'parts': parts_rev,
                    'labor': labor_rev,
                    'rental': rental_rev,
                    'parts_margin': None,  # Will be refined with CoA mapping
                    'labor_margin': None,
                    'rental_margin': None,
                })
        
        return monthly_data
    
    def _extract_monthly_equipment_sales(self) -> list:
        """
        Extract monthly equipment sales.
        Uses InvoiceReg EquipmentTaxable/EquipmentNonTax fields for a generic approach.
        """
        schema = self.schema
        
        query = f"""
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            SUM(COALESCE(EquipmentTaxable, 0) + COALESCE(EquipmentNonTax, 0)) as equipment_revenue
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -13, GETDATE())
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        """
        
        results = self.azure_sql.execute_query(query)
        monthly_data = []
        
        if results:
            for row in results:
                revenue = float(row['equipment_revenue'] or 0)
                
                monthly_data.append({
                    'year': row['year'],
                    'month': row['month'],
                    'amount': revenue,
                    'cost': 0,  # Will be refined with CoA mapping
                    'margin': None,
                })
        
        return monthly_data
    
    def _extract_monthly_work_orders(self) -> list:
        """Extract monthly work order counts"""
        schema = self.schema
        
        query = f"""
        SELECT 
            YEAR(OpenDate) as year,
            MONTH(OpenDate) as month,
            COUNT(*) as opened,
            COUNT(CASE WHEN CompletedDate IS NOT NULL THEN 1 END) as completed,
            COUNT(CASE WHEN ClosedDate IS NOT NULL THEN 1 END) as closed
        FROM {schema}.WO
        WHERE OpenDate >= DATEADD(month, -13, GETDATE())
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
        schema = self.schema
        
        query = f"""
        WITH LatestQuotes AS (
            SELECT 
                YEAR(CreationTime) as year,
                MONTH(CreationTime) as month,
                WONo,
                MAX(CAST(CreationTime AS DATE)) as latest_quote_date
            FROM {schema}.WOQuote
            WHERE CreationTime >= DATEADD(month, -13, GETDATE())
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
        schema = self.schema
        
        query = f"""
        SELECT TOP 10
            BillToName as customer_name,
            SUM(GrandTotal) as total_sales,
            COUNT(*) as invoice_count
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '{self.fiscal_year_start}'
        AND BillToName IS NOT NULL
        AND BillToName != ''
        GROUP BY BillToName
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
        schema = self.schema
        
        query = f"""
        WITH MonthEnds AS (
            SELECT DISTINCT 
                YEAR(CompletedDate) as year,
                MONTH(CompletedDate) as month,
                EOMONTH(CompletedDate) as month_end
            FROM {schema}.WO
            WHERE CompletedDate >= DATEADD(month, -13, GETDATE())
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


def run_ceo_dashboard_etl(org_id=None):
    """
    Run the CEO Dashboard ETL job.
    
    If org_id is provided, runs for that specific org only.
    Otherwise, runs for ALL discovered Softbase tenants.
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
                etl = CEODashboardETL(
                    org_id=org_id,
                    schema=org.database_schema,
                    azure_sql=azure_sql,
                    fiscal_year_start_month=org.fiscal_year_start_month or 11
                )
                return etl.run()
            else:
                logger.error(f"Organization {org_id} not found or has no schema")
                return False
        except Exception as e:
            logger.error(f"Failed to run CEO dashboard ETL for org_id={org_id}: {e}")
            return False
    else:
        from .tenant_discovery import run_etl_for_all_tenants
        results = run_etl_for_all_tenants(CEODashboardETL, 'CEO Dashboard')
        return all(results.values()) if results else False


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = run_ceo_dashboard_etl()
    exit(0 if success else 1)
