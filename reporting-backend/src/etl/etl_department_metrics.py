"""
Department Metrics ETL (Multi-Tenant)
Extracts and pre-aggregates metrics for Service, Parts, Rental, Accounting, and Financial pages
Runs every 2 hours during business hours for instant page loading.

Supports all Softbase tenants - discovers them automatically via tenant_discovery.
Uses dynamic LIKE queries where possible for consolidated totals.
Department-level breakdowns use InvoiceReg fields (LaborTaxable, PartsTaxable, etc.)
which are generic across all Softbase tenants.
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .base_etl import BaseETL

logger = logging.getLogger(__name__)


def format_month_label(year: int, month: int) -> str:
    """Format year/month as 'Nov '25' style label"""
    month_date = datetime(year, month, 1)
    return month_date.strftime("%b '%y")


class DepartmentMetricsETL(BaseETL):
    """ETL job for Department page metrics from Softbase"""
    
    def __init__(self, org_id=4, schema='ben002', azure_sql=None, fiscal_year_start_month=11):
        """
        Initialize Department Metrics ETL for a specific tenant.
        
        Args:
            org_id: Organization ID from the organization table
            schema: Database schema for the tenant (e.g., 'ben002', 'ind004')
            azure_sql: Pre-configured AzureSQLService instance for the tenant
            fiscal_year_start_month: Month number (1-12) when fiscal year starts
        """
        super().__init__(
            job_name='etl_department_metrics',
            org_id=org_id,
            source_system='softbase',
            target_table='mart_department_metrics'
        )
        self.schema = schema
        self._azure_sql = azure_sql
        self.start_time = None
        self.current_date = datetime.now()
        self.fiscal_year_start_month = fiscal_year_start_month
        
        # Fiscal year calculation (dynamic per tenant)
        if self.current_date.month >= self.fiscal_year_start_month:
            self.fiscal_year_start = datetime(self.current_date.year, self.fiscal_year_start_month, 1)
        else:
            self.fiscal_year_start = datetime(self.current_date.year - 1, self.fiscal_year_start_month, 1)
        
        # Generate fiscal year months - ONLY up to current month (no future months)
        self.fiscal_months = []
        for i in range(12):
            month_date = self.fiscal_year_start + relativedelta(months=i)
            if month_date > self.current_date:
                break
            self.fiscal_months.append((month_date.year, month_date.month))
    
    @property
    def azure_sql(self):
        """Lazy load Azure SQL service if not provided"""
        if self._azure_sql is None:
            from src.services.azure_sql_service import AzureSQLService
            self._azure_sql = AzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """Extract all department metrics from Softbase"""
        self.start_time = time.time()
        logger.info(f"Starting Department Metrics extraction for {self.schema} (org_id={self.org_id})...")
        
        all_metrics = []
        
        # Extract each department
        try:
            service_data = self._extract_service()
            all_metrics.append(('service', service_data))
            logger.info(f"  [{self.schema}] ✓ Service metrics extracted")
        except Exception as e:
            logger.error(f"  [{self.schema}] Service extraction failed: {e}")
        
        try:
            parts_data = self._extract_parts()
            all_metrics.append(('parts', parts_data))
            logger.info(f"  [{self.schema}] ✓ Parts metrics extracted")
        except Exception as e:
            logger.error(f"  [{self.schema}] Parts extraction failed: {e}")
        
        try:
            rental_data = self._extract_rental()
            all_metrics.append(('rental', rental_data))
            logger.info(f"  [{self.schema}] ✓ Rental metrics extracted")
        except Exception as e:
            logger.error(f"  [{self.schema}] Rental extraction failed: {e}")
        
        try:
            accounting_data = self._extract_accounting()
            all_metrics.append(('accounting', accounting_data))
            logger.info(f"  [{self.schema}] ✓ Accounting metrics extracted")
        except Exception as e:
            logger.error(f"  [{self.schema}] Accounting extraction failed: {e}")
        
        try:
            financial_data = self._extract_financial()
            all_metrics.append(('financial', financial_data))
            logger.info(f"  [{self.schema}] ✓ Financial metrics extracted")
        except Exception as e:
            import traceback
            logger.error(f"  [{self.schema}] Financial extraction failed: {e}")
            logger.error(f"  [{self.schema}] Financial traceback: {traceback.format_exc()}")
        
        return all_metrics
    
    def _extract_service(self) -> dict:
        """
        Extract Service department metrics using InvoiceReg for generic tenant support.
        Uses LaborTaxable/LaborNonTax fields which are available across all Softbase schemas.
        """
        schema = self.schema
        
        # Monthly Labor Revenue from InvoiceReg
        query = f"""
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as labor_revenue
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -25, GETDATE())
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        """
        
        results = self.azure_sql.execute_query(query)
        
        # Build lookup by year-month
        data_by_month = {}
        for row in results:
            key = (row['year'], row['month'])
            data_by_month[key] = row
        
        # Build monthly arrays for fiscal year
        monthly_revenue = []
        
        for year, month in self.fiscal_months:
            key = (year, month)
            prior_key = (year - 1, month)
            month_label = format_month_label(year, month)
            
            row = data_by_month.get(key, {})
            prior_row = data_by_month.get(prior_key, {})
            
            labor_rev = float(row.get('labor_revenue', 0) or 0)
            prior_labor = float(prior_row.get('labor_revenue', 0) or 0)
            
            monthly_revenue.append({
                'month': month_label, 'year': year, 'month_num': month,
                'amount': labor_rev, 'margin': None, 'prior_year_amount': prior_labor
            })
        
        # Calculate summary metrics
        current_month = monthly_revenue[-1]['amount'] if monthly_revenue else 0
        ytd_total = sum(m['amount'] for m in monthly_revenue)
        
        return {
            'monthly_revenue': monthly_revenue,
            'sub_category_1': [],  # Field/Shop breakdown not available generically
            'sub_category_2': [],
            'metric_1': current_month,
            'metric_2': ytd_total,
            'metric_3': 0,  # Margin not available without GL COGS mapping
            'additional_data': {}
        }
    
    def _extract_parts(self) -> dict:
        """
        Extract Parts department metrics using InvoiceReg for generic tenant support.
        Uses PartsTaxable/PartsNonTax fields which are available across all Softbase schemas.
        """
        schema = self.schema
        
        # Monthly Parts Revenue from InvoiceReg
        query = f"""
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as parts_revenue
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -25, GETDATE())
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        """
        
        results = self.azure_sql.execute_query(query)
        
        # Build lookup by year-month
        data_by_month = {}
        for row in results:
            key = (row['year'], row['month'])
            data_by_month[key] = row
        
        # Build monthly arrays for fiscal year
        monthly_revenue = []
        
        for year, month in self.fiscal_months:
            key = (year, month)
            prior_key = (year - 1, month)
            month_label = format_month_label(year, month)
            
            row = data_by_month.get(key, {})
            prior_row = data_by_month.get(prior_key, {})
            
            parts_rev = float(row.get('parts_revenue', 0) or 0)
            prior_parts = float(prior_row.get('parts_revenue', 0) or 0)
            
            monthly_revenue.append({
                'month': month_label, 'year': year, 'month_num': month,
                'amount': parts_rev, 'margin': None, 'prior_year_amount': prior_parts
            })
        
        # Calculate summary metrics
        current_month = monthly_revenue[-1]['amount'] if monthly_revenue else 0
        ytd_total = sum(m['amount'] for m in monthly_revenue)
        
        return {
            'monthly_revenue': monthly_revenue,
            'sub_category_1': [],  # Counter/Repair breakdown not available generically
            'sub_category_2': [],
            'metric_1': current_month,
            'metric_2': ytd_total,
            'metric_3': 0,  # Margin not available without GL COGS mapping
            'additional_data': {}
        }
    
    def _extract_rental(self) -> dict:
        """Extract Rental department metrics"""
        schema = self.schema
        
        # Summary metrics
        summary_query = f"""
        SELECT 
            (SELECT COUNT(*) FROM {schema}.Equipment WHERE WebRentalFlag = 1) as totalFleetSize,
            (SELECT COUNT(*) FROM {schema}.Equipment WHERE RentalStatus = 'Rented') as unitsOnRent,
            (SELECT SUM(GrandTotal) FROM {schema}.InvoiceReg 
             WHERE MONTH(InvoiceDate) = MONTH(GETDATE()) AND YEAR(InvoiceDate) = YEAR(GETDATE())) as monthlyRevenue
        """
        
        summary_result = self.azure_sql.execute_query(summary_query)
        
        total_fleet = int(summary_result[0]['totalFleetSize'] or 1) if summary_result else 1
        units_on_rent = int(summary_result[0]['unitsOnRent'] or 0) if summary_result else 0
        monthly_revenue_val = float(summary_result[0]['monthlyRevenue'] or 0) if summary_result else 0
        utilization = round((units_on_rent / total_fleet) * 100, 1) if total_fleet > 0 else 0
        
        # Fleet by category - generic approach using Make/Model
        fleet_query = f"""
        SELECT 
            COALESCE(Make, 'Other') as category,
            COUNT(*) as total,
            SUM(CASE WHEN RentalStatus = 'Rented' THEN 1 ELSE 0 END) as onRent
        FROM {schema}.Equipment
        WHERE WebRentalFlag = 1
        GROUP BY Make
        ORDER BY COUNT(*) DESC
        """
        
        fleet_result = self.azure_sql.execute_query(fleet_query)
        fleet_by_category = []
        for row in (fleet_result or []):
            total = int(row['total'] or 0)
            on_rent = int(row['onRent'] or 0)
            fleet_by_category.append({
                'category': row['category'],
                'total': total,
                'onRent': on_rent,
                'available': total - on_rent
            })
        
        # Monthly trend
        trend_query = f"""
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            SUM(GrandTotal) as revenue,
            COUNT(*) as rentals
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        """
        
        trend_result = self.azure_sql.execute_query(trend_query)
        monthly_trend = []
        for row in (trend_result or []):
            month_label = format_month_label(row['year'], row['month'])
            monthly_trend.append({
                'month': month_label,
                'year': row['year'],
                'month_num': row['month'],
                'revenue': float(row['revenue'] or 0),
                'rentals': int(row['rentals'] or 0)
            })
        
        # Top customers
        top_customers_query = f"""
        SELECT TOP 10
            BillToName as customer,
            COUNT(*) as rental_count,
            SUM(GrandTotal) as total_revenue
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
            AND BillToName IS NOT NULL AND BillToName != ''
        GROUP BY BillToName
        ORDER BY total_revenue DESC
        """
        
        top_result = self.azure_sql.execute_query(top_customers_query)
        top_customers = []
        for row in (top_result or []):
            top_customers.append({
                'customer': row['customer'],
                'rental_count': int(row['rental_count'] or 0),
                'total_revenue': float(row['total_revenue'] or 0)
            })
        
        return {
            'monthly_revenue': monthly_trend,
            'sub_category_1': fleet_by_category,
            'sub_category_2': None,
            'metric_1': total_fleet,
            'metric_2': units_on_rent,
            'metric_3': utilization,
            'metric_4': monthly_revenue_val,
            'count_1': total_fleet,
            'count_2': units_on_rent,
            'additional_data': {
                'summary': {
                    'totalFleetSize': total_fleet,
                    'unitsOnRent': units_on_rent,
                    'utilizationRate': utilization,
                    'monthlyRevenue': monthly_revenue_val
                },
                'topCustomers': top_customers
            }
        }
    
    def _extract_accounting(self) -> dict:
        """Extract Accounting department metrics using dynamic LIKE '6%' query"""
        schema = self.schema
        
        # G&A expenses from GLDetail
        expenses_query = f"""
        SELECT
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            SUM(Amount) as total_expenses
        FROM {schema}.GLDetail
        WHERE AccountNo LIKE '6%'
            AND EffectiveDate >= DATEADD(month, -13, GETDATE())
            AND EffectiveDate < DATEADD(DAY, 1, GETDATE())
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        """
        
        expenses_result = self.azure_sql.execute_query(expenses_query)
        
        monthly_expenses = []
        for row in (expenses_result or []):
            month_label = format_month_label(row['year'], row['month'])
            monthly_expenses.append({
                'month': month_label,
                'year': row['year'],
                'month_num': row['month'],
                'expenses': float(row['total_expenses'] or 0)
            })
        
        # Expense categories - generic grouping by first 3 digits
        categories_query = f"""
        SELECT 
            LEFT(AccountNo, 3) as account_prefix,
            SUM(Amount) as amount
        FROM {schema}.GLDetail
        WHERE AccountNo LIKE '6%'
            AND EffectiveDate >= DATEADD(MONTH, -6, GETDATE())
        GROUP BY LEFT(AccountNo, 3)
        HAVING SUM(Amount) > 0
        ORDER BY SUM(Amount) DESC
        """
        
        categories_result = self.azure_sql.execute_query(categories_query)
        expense_categories = []
        for row in (categories_result or []):
            expense_categories.append({
                'category': f"Account {row['account_prefix']}xxx",
                'amount': float(row['amount'] or 0)
            })
        
        # Calculate summary
        total_expenses = sum(m['expenses'] for m in monthly_expenses)
        complete_months = monthly_expenses[:-1] if len(monthly_expenses) > 1 else monthly_expenses
        avg_expenses = sum(m['expenses'] for m in complete_months) / len(complete_months) if complete_months else 0
        
        return {
            'monthly_revenue': monthly_expenses,
            'sub_category_1': expense_categories,
            'sub_category_2': None,
            'metric_1': total_expenses,
            'metric_2': avg_expenses,
            'metric_3': None,
            'additional_data': {
                'expense_categories': expense_categories
            }
        }
    
    def _extract_financial(self) -> dict:
        """Extract Financial summary metrics using ARDetail table"""
        schema = self.schema
        
        # AR Summary using ARDetail (Customer table does NOT have Balance/DaysPastDue columns)
        ar_query = f"""
        WITH CustomerBalances AS (
            SELECT 
                ar.CustomerNo,
                SUM(ar.Amount) as Balance,
                MIN(ar.Due) as EarliestDue
            FROM {schema}.ARDetail ar
            WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                AND ar.DeletionTime IS NULL
                AND ar.InvoiceNo IS NOT NULL
            GROUP BY ar.CustomerNo
            HAVING SUM(ar.Amount) > 0.01
        )
        SELECT 
            COUNT(DISTINCT CustomerNo) as CustomersWithBalance,
            SUM(Balance) as TotalAR,
            SUM(CASE WHEN DATEDIFF(day, EarliestDue, GETDATE()) > 0 THEN Balance ELSE 0 END) as PastDueAmount,
            SUM(CASE WHEN DATEDIFF(day, EarliestDue, GETDATE()) > 30 THEN Balance ELSE 0 END) as Over30Days,
            SUM(CASE WHEN DATEDIFF(day, EarliestDue, GETDATE()) > 60 THEN Balance ELSE 0 END) as Over60Days,
            SUM(CASE WHEN DATEDIFF(day, EarliestDue, GETDATE()) > 90 THEN Balance ELSE 0 END) as Over90Days
        FROM CustomerBalances
        """
        
        try:
            ar_result = self.azure_sql.execute_query(ar_query)
            ar_data = ar_result[0] if ar_result else {}
        except Exception as e:
            logger.error(f"  [{schema}] AR query failed: {e}")
            ar_data = {}
        
        total_ar = float(ar_data.get('TotalAR', 0) or 0)
        past_due = float(ar_data.get('PastDueAmount', 0) or 0)
        over_90 = float(ar_data.get('Over90Days', 0) or 0)
        customers_with_balance = int(ar_data.get('CustomersWithBalance', 0) or 0)
        
        # Top AR balances using ARDetail
        ar_detail_query = f"""
        WITH CustomerBalances AS (
            SELECT 
                ar.CustomerNo,
                SUM(ar.Amount) as Balance
            FROM {schema}.ARDetail ar
            WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                AND ar.DeletionTime IS NULL
                AND ar.InvoiceNo IS NOT NULL
            GROUP BY ar.CustomerNo
            HAVING SUM(ar.Amount) > 0.01
        )
        SELECT TOP 20
            cb.CustomerNo,
            c.Name,
            cb.Balance
        FROM CustomerBalances cb
        LEFT JOIN {schema}.Customer c ON cb.CustomerNo = c.Number
        ORDER BY cb.Balance DESC
        """
        
        try:
            ar_detail = self.azure_sql.execute_query(ar_detail_query)
        except Exception as e:
            logger.error(f"  [{schema}] AR detail query failed: {e}")
            ar_detail = []
        top_ar = []
        for row in (ar_detail or []):
            top_ar.append({
                'customer_no': row.get('CustomerNo', ''),
                'name': row.get('Name', 'Unknown'),
                'balance': float(row.get('Balance', 0) or 0),
                'credit_limit': 0,
                'days_past_due': 0
            })
        
        # Revenue by department (current month)
        revenue_query = f"""
        SELECT 
            SaleDept as DepartmentNo,
            COUNT(*) as TransactionCount,
            SUM(GrandTotal) as Revenue
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -1, GETDATE())
        GROUP BY SaleDept
        ORDER BY Revenue DESC
        """
        
        revenue_result = self.azure_sql.execute_query(revenue_query)
        revenue_by_dept = []
        for row in (revenue_result or []):
            revenue_by_dept.append({
                'department': row['DepartmentNo'],
                'transaction_count': int(row['TransactionCount'] or 0),
                'revenue': float(row['Revenue'] or 0)
            })
        
        return {
            'monthly_revenue': None,
            'sub_category_1': top_ar,
            'sub_category_2': revenue_by_dept,
            'metric_1': total_ar,
            'metric_2': past_due,
            'metric_3': over_90,
            'count_1': customers_with_balance,
            'additional_data': {
                'ar_summary': {
                    'total_ar': total_ar,
                    'past_due': past_due,
                    'over_30': float(ar_data.get('Over30Days', 0) or 0),
                    'over_60': float(ar_data.get('Over60Days', 0) or 0),
                    'over_90': over_90,
                    'customers_with_balance': customers_with_balance
                },
                'revenue_by_department': revenue_by_dept
            }
        }
    
    def transform(self, raw_data: list) -> list:
        """Transform extracted data for loading"""
        return raw_data
    
    def load(self, transformed_data: list) -> int:
        """Load transformed data into mart_department_metrics"""
        if not transformed_data:
            logger.warning("No data to load")
            return 0
        
        etl_duration = time.time() - self.start_time
        loaded_count = 0
        snapshot_time = datetime.now()
        
        for department, data in transformed_data:
            try:
                record = {
                    'org_id': self.org_id,
                    'department': department,
                    'snapshot_timestamp': snapshot_time,
                    'monthly_revenue': json.dumps(data.get('monthly_revenue')) if data.get('monthly_revenue') else None,
                    'sub_category_1': json.dumps(data.get('sub_category_1')) if data.get('sub_category_1') else None,
                    'sub_category_2': json.dumps(data.get('sub_category_2')) if data.get('sub_category_2') else None,
                    'metric_1': data.get('metric_1'),
                    'metric_2': data.get('metric_2'),
                    'metric_3': data.get('metric_3'),
                    'metric_4': data.get('metric_4'),
                    'count_1': data.get('count_1'),
                    'count_2': data.get('count_2'),
                    'additional_data': json.dumps(data.get('additional_data')) if data.get('additional_data') else None,
                    'etl_duration_seconds': etl_duration
                }
                
                insert_query = """
                INSERT INTO mart_department_metrics 
                (org_id, department, snapshot_timestamp, monthly_revenue, sub_category_1, sub_category_2,
                 metric_1, metric_2, metric_3, metric_4, count_1, count_2, additional_data, etl_duration_seconds)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                self.pg.execute_update(insert_query, (
                    record['org_id'], record['department'], record['snapshot_timestamp'],
                    record['monthly_revenue'], record['sub_category_1'], record['sub_category_2'],
                    record['metric_1'], record['metric_2'], record['metric_3'], record['metric_4'],
                    record['count_1'], record['count_2'], record['additional_data'], record['etl_duration_seconds']
                ))
                
                loaded_count += 1
                logger.info(f"  [{self.schema}] Loaded {department} metrics")
                
            except Exception as e:
                logger.error(f"  [{self.schema}] Failed to load {department} metrics: {e}")
        
        return loaded_count


def run_department_metrics_etl(org_id=None):
    """
    Run the Department Metrics ETL job.
    
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
                etl = DepartmentMetricsETL(
                    org_id=org_id,
                    schema=org.database_schema,
                    azure_sql=azure_sql
                )
                return etl.run()
            else:
                logger.error(f"Organization {org_id} not found or has no schema")
                return False
        except Exception as e:
            logger.error(f"Failed to run department metrics ETL for org_id={org_id}: {e}")
            return False
    else:
        from .tenant_discovery import run_etl_for_all_tenants
        results = run_etl_for_all_tenants(DepartmentMetricsETL, 'Department Metrics')
        return all(results.values()) if results else False
