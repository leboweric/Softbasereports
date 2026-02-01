"""
Department Metrics ETL
Extracts and pre-aggregates metrics for Service, Parts, Rental, Accounting, and Financial pages
Runs every 2 hours during business hours for instant page loading
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .base_etl import BaseETL

logger = logging.getLogger(__name__)


class DepartmentMetricsETL(BaseETL):
    """ETL job for Department page metrics from Softbase"""
    
    BENNETT_ORG_ID = 4
    BENNETT_SCHEMA = 'ben002'
    
    def __init__(self):
        """Initialize Department Metrics ETL"""
        super().__init__(
            job_name='etl_department_metrics',
            org_id=self.BENNETT_ORG_ID,
            source_system='softbase',
            target_table='mart_department_metrics'
        )
        self._azure_sql = None
        self.start_time = None
        self.current_date = datetime.now()
        
        # Fiscal year calculation (November 1st start)
        if self.current_date.month >= 11:
            self.fiscal_year_start = datetime(self.current_date.year, 11, 1)
        else:
            self.fiscal_year_start = datetime(self.current_date.year - 1, 11, 1)
        
        # Generate fiscal year months
        self.fiscal_months = []
        for i in range(12):
            month_date = self.fiscal_year_start + relativedelta(months=i)
            self.fiscal_months.append((month_date.year, month_date.month))
    
    @property
    def azure_sql(self):
        """Lazy load Azure SQL service"""
        if self._azure_sql is None:
            from src.services.azure_sql_service import AzureSQLService
            self._azure_sql = AzureSQLService()
        return self._azure_sql
    
    def extract(self) -> list:
        """Extract all department metrics from Softbase"""
        self.start_time = time.time()
        logger.info("Starting Department Metrics extraction...")
        
        all_metrics = []
        
        # Extract each department
        try:
            service_data = self._extract_service()
            all_metrics.append(('service', service_data))
            logger.info("✓ Service metrics extracted")
        except Exception as e:
            logger.error(f"Service extraction failed: {e}")
        
        try:
            parts_data = self._extract_parts()
            all_metrics.append(('parts', parts_data))
            logger.info("✓ Parts metrics extracted")
        except Exception as e:
            logger.error(f"Parts extraction failed: {e}")
        
        try:
            rental_data = self._extract_rental()
            all_metrics.append(('rental', rental_data))
            logger.info("✓ Rental metrics extracted")
        except Exception as e:
            logger.error(f"Rental extraction failed: {e}")
        
        try:
            accounting_data = self._extract_accounting()
            all_metrics.append(('accounting', accounting_data))
            logger.info("✓ Accounting metrics extracted")
        except Exception as e:
            logger.error(f"Accounting extraction failed: {e}")
        
        try:
            financial_data = self._extract_financial()
            all_metrics.append(('financial', financial_data))
            logger.info("✓ Financial metrics extracted")
        except Exception as e:
            import traceback
            logger.error(f"Financial extraction failed: {e}")
            logger.error(f"Financial traceback: {traceback.format_exc()}")
        
        return all_metrics
    
    def _extract_service(self) -> dict:
        """Extract Service department metrics"""
        schema = self.BENNETT_SCHEMA
        
        # Monthly Labor Revenue and Margins from GLDetail
        # Revenue: GL 410004 (Field) + GL 410005 (Shop)
        # Cost: GL 510004 (Field Cost) + GL 510005 (Shop Cost)
        query = f"""
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            ABS(SUM(CASE WHEN AccountNo IN ('410004', '410005') THEN Amount ELSE 0 END)) as labor_revenue,
            ABS(SUM(CASE WHEN AccountNo IN ('510004', '510005') THEN Amount ELSE 0 END)) as labor_cost,
            ABS(SUM(CASE WHEN AccountNo = '410004' THEN Amount ELSE 0 END)) as field_revenue,
            ABS(SUM(CASE WHEN AccountNo = '510004' THEN Amount ELSE 0 END)) as field_cost,
            ABS(SUM(CASE WHEN AccountNo = '410005' THEN Amount ELSE 0 END)) as shop_revenue,
            ABS(SUM(CASE WHEN AccountNo = '510005' THEN Amount ELSE 0 END)) as shop_cost
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('410004', '410005', '510004', '510005')
            AND EffectiveDate >= DATEADD(month, -25, GETDATE())
            AND Posted = 1
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        """
        
        results = self.azure_sql.execute_query(query)
        
        # Build lookup by year-month
        data_by_month = {}
        for row in results:
            key = (row['year'], row['month'])
            data_by_month[key] = row
        
        # Build monthly arrays for fiscal year
        monthly_revenue = []
        field_revenue = []
        shop_revenue = []
        
        for year, month in self.fiscal_months:
            key = (year, month)
            prior_key = (year - 1, month)
            
            row = data_by_month.get(key, {})
            prior_row = data_by_month.get(prior_key, {})
            
            labor_rev = float(row.get('labor_revenue', 0) or 0)
            labor_cost = float(row.get('labor_cost', 0) or 0)
            margin = round(((labor_rev - labor_cost) / labor_rev) * 100, 1) if labor_rev > 0 else None
            prior_labor = float(prior_row.get('labor_revenue', 0) or 0)
            
            field_rev = float(row.get('field_revenue', 0) or 0)
            field_cost = float(row.get('field_cost', 0) or 0)
            field_margin = round(((field_rev - field_cost) / field_rev) * 100, 1) if field_rev > 0 else None
            prior_field = float(prior_row.get('field_revenue', 0) or 0)
            
            shop_rev = float(row.get('shop_revenue', 0) or 0)
            shop_cost = float(row.get('shop_cost', 0) or 0)
            shop_margin = round(((shop_rev - shop_cost) / shop_rev) * 100, 1) if shop_rev > 0 else None
            prior_shop = float(prior_row.get('shop_revenue', 0) or 0)
            
            monthly_revenue.append({
                'year': year, 'month': month,
                'amount': labor_rev, 'margin': margin, 'prior_year_amount': prior_labor
            })
            field_revenue.append({
                'year': year, 'month': month,
                'amount': field_rev, 'margin': field_margin, 'prior_year_amount': prior_field
            })
            shop_revenue.append({
                'year': year, 'month': month,
                'amount': shop_rev, 'margin': shop_margin, 'prior_year_amount': prior_shop
            })
        
        # Calculate summary metrics
        current_month = monthly_revenue[-1]['amount'] if monthly_revenue else 0
        ytd_total = sum(m['amount'] for m in monthly_revenue)
        margins = [m['margin'] for m in monthly_revenue if m['margin'] is not None]
        avg_margin = sum(margins) / len(margins) if margins else 0
        
        return {
            'monthly_revenue': monthly_revenue,
            'sub_category_1': field_revenue,
            'sub_category_2': shop_revenue,
            'metric_1': current_month,
            'metric_2': ytd_total,
            'metric_3': avg_margin,
            'additional_data': {}
        }
    
    def _extract_parts(self) -> dict:
        """Extract Parts department metrics"""
        schema = self.BENNETT_SCHEMA
        
        # Monthly Parts Revenue and Margins from GLDetail
        # Revenue: GL 410003 (Counter) + GL 410012 (Customer Repair Order)
        # Cost: GL 510003 (Counter Cost) + GL 510012 (Customer Repair Order Cost)
        query = f"""
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            ABS(SUM(CASE WHEN AccountNo IN ('410003', '410012') THEN Amount ELSE 0 END)) as parts_revenue,
            ABS(SUM(CASE WHEN AccountNo IN ('510003', '510012') THEN Amount ELSE 0 END)) as parts_cost,
            ABS(SUM(CASE WHEN AccountNo = '410003' THEN Amount ELSE 0 END)) as counter_revenue,
            ABS(SUM(CASE WHEN AccountNo = '510003' THEN Amount ELSE 0 END)) as counter_cost,
            ABS(SUM(CASE WHEN AccountNo = '410012' THEN Amount ELSE 0 END)) as repair_order_revenue,
            ABS(SUM(CASE WHEN AccountNo = '510012' THEN Amount ELSE 0 END)) as repair_order_cost
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('410003', '410012', '510003', '510012')
            AND EffectiveDate >= DATEADD(month, -25, GETDATE())
            AND Posted = 1
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        """
        
        results = self.azure_sql.execute_query(query)
        
        # Build lookup by year-month
        data_by_month = {}
        for row in results:
            key = (row['year'], row['month'])
            data_by_month[key] = row
        
        # Build monthly arrays for fiscal year
        monthly_revenue = []
        counter_revenue = []
        repair_order_revenue = []
        
        for year, month in self.fiscal_months:
            key = (year, month)
            prior_key = (year - 1, month)
            
            row = data_by_month.get(key, {})
            prior_row = data_by_month.get(prior_key, {})
            
            parts_rev = float(row.get('parts_revenue', 0) or 0)
            parts_cost = float(row.get('parts_cost', 0) or 0)
            margin = round(((parts_rev - parts_cost) / parts_rev) * 100, 1) if parts_rev > 0 else None
            prior_parts = float(prior_row.get('parts_revenue', 0) or 0)
            
            counter_rev = float(row.get('counter_revenue', 0) or 0)
            counter_cost = float(row.get('counter_cost', 0) or 0)
            counter_margin = round(((counter_rev - counter_cost) / counter_rev) * 100, 1) if counter_rev > 0 else None
            prior_counter = float(prior_row.get('counter_revenue', 0) or 0)
            
            ro_rev = float(row.get('repair_order_revenue', 0) or 0)
            ro_cost = float(row.get('repair_order_cost', 0) or 0)
            ro_margin = round(((ro_rev - ro_cost) / ro_rev) * 100, 1) if ro_rev > 0 else None
            prior_ro = float(prior_row.get('repair_order_revenue', 0) or 0)
            
            monthly_revenue.append({
                'year': year, 'month': month,
                'amount': parts_rev, 'margin': margin, 'prior_year_amount': prior_parts
            })
            counter_revenue.append({
                'year': year, 'month': month,
                'amount': counter_rev, 'margin': counter_margin, 'prior_year_amount': prior_counter
            })
            repair_order_revenue.append({
                'year': year, 'month': month,
                'amount': ro_rev, 'margin': ro_margin, 'prior_year_amount': prior_ro
            })
        
        # Calculate summary metrics
        current_month = monthly_revenue[-1]['amount'] if monthly_revenue else 0
        ytd_total = sum(m['amount'] for m in monthly_revenue)
        margins = [m['margin'] for m in monthly_revenue if m['margin'] is not None]
        avg_margin = sum(margins) / len(margins) if margins else 0
        
        return {
            'monthly_revenue': monthly_revenue,
            'sub_category_1': counter_revenue,
            'sub_category_2': repair_order_revenue,
            'metric_1': current_month,
            'metric_2': ytd_total,
            'metric_3': avg_margin,
            'additional_data': {}
        }
    
    def _extract_rental(self) -> dict:
        """Extract Rental department metrics"""
        schema = self.BENNETT_SCHEMA
        
        # Summary metrics
        summary_query = f"""
        SELECT 
            (SELECT COUNT(*) FROM {schema}.Equipment WHERE WebRentalFlag = 1) as totalFleetSize,
            (SELECT COUNT(*) FROM {schema}.Equipment WHERE RentalStatus = 'Rented') as unitsOnRent,
            (SELECT SUM(GrandTotal) FROM {schema}.InvoiceReg 
             WHERE MONTH(InvoiceDate) = MONTH(GETDATE()) AND YEAR(InvoiceDate) = YEAR(GETDATE())) as monthlyRevenue
        """
        
        summary_result = self.azure_sql.execute_query(summary_query)
        
        total_fleet = int(summary_result[0]['totalFleetSize'] or 1)
        units_on_rent = int(summary_result[0]['unitsOnRent'] or 0)
        monthly_revenue = float(summary_result[0]['monthlyRevenue'] or 0)
        utilization = round((units_on_rent / total_fleet) * 100, 1) if total_fleet > 0 else 0
        
        # Fleet by category
        fleet_query = f"""
        SELECT 
            CASE 
                WHEN Model LIKE '%EXCAVATOR%' THEN 'Excavators'
                WHEN Model LIKE '%LOADER%' THEN 'Loaders'
                WHEN Model LIKE '%DOZER%' THEN 'Dozers'
                WHEN Model LIKE '%COMPACTOR%' THEN 'Compactors'
                ELSE 'Other'
            END as category,
            COUNT(*) as total,
            SUM(CASE WHEN RentalStatus = 'Rented' THEN 1 ELSE 0 END) as onRent
        FROM {schema}.Equipment
        WHERE WebRentalFlag = 1
        GROUP BY 
            CASE 
                WHEN Model LIKE '%EXCAVATOR%' THEN 'Excavators'
                WHEN Model LIKE '%LOADER%' THEN 'Loaders'
                WHEN Model LIKE '%DOZER%' THEN 'Dozers'
                WHEN Model LIKE '%COMPACTOR%' THEN 'Compactors'
                ELSE 'Other'
            END
        """
        
        fleet_result = self.azure_sql.execute_query(fleet_query)
        fleet_by_category = []
        for row in fleet_result:
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
        for row in trend_result:
            monthly_trend.append({
                'year': row['year'],
                'month': row['month'],
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
        for row in top_result:
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
            'metric_4': monthly_revenue,
            'count_1': total_fleet,
            'count_2': units_on_rent,
            'additional_data': {
                'summary': {
                    'totalFleetSize': total_fleet,
                    'unitsOnRent': units_on_rent,
                    'utilizationRate': utilization,
                    'monthlyRevenue': monthly_revenue
                },
                'topCustomers': top_customers
            }
        }
    
    def _extract_accounting(self) -> dict:
        """Extract Accounting department metrics"""
        schema = self.BENNETT_SCHEMA
        
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
        for row in expenses_result:
            monthly_expenses.append({
                'year': row['year'],
                'month': row['month'],
                'expenses': float(row['total_expenses'] or 0)
            })
        
        # Expense categories
        categories_query = f"""
        SELECT 
            CASE 
                WHEN AccountNo LIKE '600%' THEN 'Advertising & Marketing'
                WHEN AccountNo LIKE '601%' THEN 'Payroll & Benefits'
                WHEN AccountNo LIKE '602%' THEN 'Facilities & Rent'
                WHEN AccountNo LIKE '603%' THEN 'Insurance'
                WHEN AccountNo LIKE '604%' THEN 'Professional Services'
                WHEN AccountNo LIKE '605%' THEN 'IT & Computer'
                WHEN AccountNo LIKE '606%' THEN 'Depreciation'
                WHEN AccountNo LIKE '607%' THEN 'Interest & Finance'
                WHEN AccountNo LIKE '608%' THEN 'Travel & Entertainment'
                WHEN AccountNo LIKE '609%' THEN 'Office & Admin'
                ELSE 'Other Expenses'
            END as category,
            SUM(Amount) as amount
        FROM {schema}.GLDetail
        WHERE AccountNo LIKE '6%'
            AND EffectiveDate >= DATEADD(MONTH, -6, GETDATE())
        GROUP BY 
            CASE 
                WHEN AccountNo LIKE '600%' THEN 'Advertising & Marketing'
                WHEN AccountNo LIKE '601%' THEN 'Payroll & Benefits'
                WHEN AccountNo LIKE '602%' THEN 'Facilities & Rent'
                WHEN AccountNo LIKE '603%' THEN 'Insurance'
                WHEN AccountNo LIKE '604%' THEN 'Professional Services'
                WHEN AccountNo LIKE '605%' THEN 'IT & Computer'
                WHEN AccountNo LIKE '606%' THEN 'Depreciation'
                WHEN AccountNo LIKE '607%' THEN 'Interest & Finance'
                WHEN AccountNo LIKE '608%' THEN 'Travel & Entertainment'
                WHEN AccountNo LIKE '609%' THEN 'Office & Admin'
                ELSE 'Other Expenses'
            END
        HAVING SUM(Amount) > 0
        ORDER BY SUM(Amount) DESC
        """
        
        categories_result = self.azure_sql.execute_query(categories_query)
        expense_categories = []
        for row in categories_result:
            expense_categories.append({
                'category': row['category'],
                'amount': float(row['amount'] or 0)
            })
        
        # Calculate summary
        total_expenses = sum(m['expenses'] for m in monthly_expenses)
        complete_months = monthly_expenses[:-1] if len(monthly_expenses) > 1 else monthly_expenses
        avg_expenses = sum(m['expenses'] for m in complete_months) / len(complete_months) if complete_months else 0
        
        return {
            'monthly_revenue': monthly_expenses,  # Using revenue field for expenses
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
        """Extract Financial summary metrics"""
        schema = self.BENNETT_SCHEMA
        
        # AR Summary
        ar_query = f"""
        SELECT 
            COUNT(DISTINCT CustomerNo) as CustomersWithBalance,
            SUM(Balance) as TotalAR,
            SUM(CASE WHEN DaysPastDue > 0 THEN Balance ELSE 0 END) as PastDueAmount,
            SUM(CASE WHEN DaysPastDue > 30 THEN Balance ELSE 0 END) as Over30Days,
            SUM(CASE WHEN DaysPastDue > 60 THEN Balance ELSE 0 END) as Over60Days,
            SUM(CASE WHEN DaysPastDue > 90 THEN Balance ELSE 0 END) as Over90Days
        FROM {schema}.Customer
        WHERE Balance > 0
        """
        
        ar_result = self.azure_sql.execute_query(ar_query)
        ar_data = ar_result[0] if ar_result else {}
        
        total_ar = float(ar_data.get('TotalAR', 0) or 0)
        past_due = float(ar_data.get('PastDueAmount', 0) or 0)
        over_90 = float(ar_data.get('Over90Days', 0) or 0)
        customers_with_balance = int(ar_data.get('CustomersWithBalance', 0) or 0)
        
        # Top AR balances
        ar_detail_query = f"""
        SELECT TOP 20
            CustomerNo,
            Name,
            Balance,
            CreditLimit,
            DaysPastDue,
            LastPaymentDate,
            LastPaymentAmount
        FROM {schema}.Customer
        WHERE Balance > 0
        ORDER BY Balance DESC
        """
        
        ar_detail = self.azure_sql.execute_query(ar_detail_query)
        top_ar = []
        for row in ar_detail:
            top_ar.append({
                'customer_no': row['CustomerNo'],
                'name': row['Name'],
                'balance': float(row['Balance'] or 0),
                'credit_limit': float(row['CreditLimit'] or 0),
                'days_past_due': int(row['DaysPastDue'] or 0)
            })
        
        # Revenue by department (current month)
        revenue_query = f"""
        SELECT 
            DepartmentNo,
            COUNT(*) as TransactionCount,
            SUM(TotalAmount) as Revenue
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -1, GETDATE())
        GROUP BY DepartmentNo
        ORDER BY Revenue DESC
        """
        
        revenue_result = self.azure_sql.execute_query(revenue_query)
        revenue_by_dept = []
        for row in revenue_result:
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
        # Data is already in the right format from extract
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
                    'org_id': self.BENNETT_ORG_ID,
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
                
                # Insert new record
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
                logger.info(f"Loaded {department} metrics")
                
            except Exception as e:
                logger.error(f"Failed to load {department} metrics: {e}")
        
        return loaded_count


def run_department_metrics_etl():
    """Run the Department Metrics ETL job"""
    etl = DepartmentMetricsETL()
    return etl.run()
