"""
Softbase Evolution ERP Adapter

Extracts financial data from Softbase Evolution SQL Server databases.
Based on the proven queries from the existing Currie Report implementation.
"""
import logging
from typing import List, Dict, Any
from datetime import date
import pymssql

from .base_adapter import BaseERPAdapter

logger = logging.getLogger(__name__)


class SoftbaseEvolutionAdapter(BaseERPAdapter):
    """
    Adapter for Softbase Evolution dealer management system.
    Connects to Azure SQL Server databases.
    """

    # GL Account mappings for financial data extraction
    # These can be customized per dealer if their chart of accounts differs
    GL_ACCOUNTS = {
        'new_equipment': {
            'revenue': ['413001', '426001', '412001', '414001'],
            'cost': ['513001', '526001', '512001', '514001']
        },
        'used_equipment': {
            'revenue': ['412002', '413002', '414002', '426002', '431002', '410002'],
            'cost': ['512002', '513002', '514002', '526002', '531002', '510002']
        },
        'rental': {
            'revenue': ['411001', '419000', '420000', '421000', '434012', '410008'],
            'cost': ['510008', '511001', '519000', '520000', '521008', '537001', '539000', '534014', '545000']
        },
        'service': {
            'revenue': ['432001', '432003', '434001', '434005', '434010', '434013', '433001', '410003'],
            'cost': ['510003', '532001', '532002', '532003', '534001', '534003', '534005', '534010', '534013']
        },
        'parts': {
            'revenue': ['430001', '430002', '430003', '430004', '434002', '434003', '434004', '410006'],
            'cost': ['510006', '530001', '530002', '530003', '530004', '534002', '534004']
        },
        'trucking': {
            'revenue': ['435001'],
            'cost': ['535001', '535002']
        }
    }

    @property
    def erp_type(self) -> str:
        return 'softbase_evolution'

    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize with database connection details.

        Args:
            connection_config: Dict with keys:
                - server: Azure SQL server hostname
                - database: Database name
                - username: SQL username
                - password: SQL password
                - schema: Schema name (default: 'ben002')
        """
        super().__init__(connection_config)
        self.schema = connection_config.get('schema', 'ben002')
        self._connection = None

    def _get_connection(self):
        """Get or create database connection."""
        if self._connection is None:
            self._connection = pymssql.connect(
                server=self.config['server'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database']
            )
        return self._connection

    def test_connection(self) -> Dict[str, Any]:
        """Test database connectivity."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return {'success': True, 'message': 'Connection successful'}
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {'success': False, 'message': str(e)}

    def _execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dicts."""
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results

    def get_department_financials(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Extract financial data by department from GLDetail table.
        """
        results = []

        for department, accounts in self.GL_ACCOUNTS.items():
            revenue_accounts = accounts['revenue']
            cost_accounts = accounts['cost']
            all_accounts = revenue_accounts + cost_accounts

            # Build query for this department's accounts
            placeholders = ','.join(['%s'] * len(all_accounts))
            query = f"""
            SELECT
                AccountNo,
                SUM(Amount) as total_amount
            FROM {self.schema}.GLDetail
            WHERE EffectiveDate >= %s
              AND EffectiveDate <= %s
              AND Posted = 1
              AND AccountNo IN ({placeholders})
            GROUP BY AccountNo
            """

            params = (start_date, end_date) + tuple(all_accounts)
            rows = self._execute_query(query, params)

            # Calculate totals
            gross_sales = 0
            cost_of_goods_sold = 0

            for row in rows:
                account = row['AccountNo']
                amount = float(row['total_amount'] or 0)

                if account in revenue_accounts:
                    gross_sales += -amount  # Revenue is credit (negative in GL)
                elif account in cost_accounts:
                    cost_of_goods_sold += amount  # COGS is debit (positive)

            results.append({
                'department': department,
                'gross_sales': gross_sales,
                'discounts': 0,  # TODO: Add discount account tracking if needed
                'cost_of_goods_sold': cost_of_goods_sold,
                'units_sold': self._get_unit_count(department, start_date, end_date)
            })

        return results

    def _get_unit_count(
        self,
        department: str,
        start_date: date,
        end_date: date
    ) -> int:
        """Get unit count for equipment departments from InvoiceReg."""
        if department not in ('new_equipment', 'used_equipment'):
            return 0

        try:
            sale_code = 'N' if department == 'new_equipment' else 'U'
            query = f"""
            SELECT COUNT(*) as unit_count
            FROM {self.schema}.InvoiceReg
            WHERE InvoiceDate >= %s
              AND InvoiceDate <= %s
              AND SaleCode = %s
            """
            results = self._execute_query(query, (start_date, end_date, sale_code))
            return results[0]['unit_count'] if results else 0
        except Exception as e:
            logger.warning(f"Could not get unit count for {department}: {e}")
            return 0

    def get_expense_allocations(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Extract expense data from GL accounts.
        """
        # Define expense account ranges
        expense_categories = {
            'personnel': ('600000', '699999'),
            'operating': ('700000', '799999'),
            'occupancy': ('800000', '899999'),
            'ga': ('900000', '949999')
        }

        results = []

        for category, (start_acct, end_acct) in expense_categories.items():
            query = f"""
            SELECT SUM(Amount) as total_amount
            FROM {self.schema}.GLDetail
            WHERE EffectiveDate >= %s
              AND EffectiveDate <= %s
              AND Posted = 1
              AND AccountNo >= %s
              AND AccountNo <= %s
            """

            rows = self._execute_query(query, (start_date, end_date, start_acct, end_acct))
            amount = float(rows[0]['total_amount'] or 0) if rows else 0

            # Note: Department allocation is typically done at the platform level
            # based on dealer-specific allocation percentages
            results.append({
                'expense_category': category,
                'department': None,  # Allocated at platform level
                'amount': amount,
                'allocation_method': 'pending_allocation'
            })

        return results

    def get_operational_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Extract operational KPIs from various tables.
        """
        metrics = []

        # Technician count
        try:
            query = f"""
            SELECT COUNT(*) as tech_count
            FROM {self.schema}.Employee
            WHERE Department = '40' AND IsActive = 1
            """
            results = self._execute_query(query)
            metrics.append({
                'metric_name': 'technician_count',
                'metric_category': 'service',
                'metric_value': results[0]['tech_count'] if results else 0,
                'metric_unit': 'count'
            })
        except Exception as e:
            logger.warning(f"Could not get technician count: {e}")

        # Open work orders
        try:
            query = f"""
            SELECT COUNT(*) as wo_count
            FROM {self.schema}.WO
            WHERE Type = 'S' AND ClosedDate IS NULL
            """
            results = self._execute_query(query)
            metrics.append({
                'metric_name': 'work_orders_open',
                'metric_category': 'service',
                'metric_value': results[0]['wo_count'] if results else 0,
                'metric_unit': 'count'
            })
        except Exception as e:
            logger.warning(f"Could not get work order count: {e}")

        # AR Aging
        try:
            ar_metrics = self._get_ar_aging()
            metrics.extend(ar_metrics)
        except Exception as e:
            logger.warning(f"Could not get AR aging: {e}")

        return metrics

    def _get_ar_aging(self) -> List[Dict[str, Any]]:
        """Get AR aging breakdown."""
        query = f"""
        SELECT
            SUM(CASE WHEN DATEDIFF(day, DueDate, GETDATE()) <= 30 THEN AmountDue ELSE 0 END) as current_ar,
            SUM(CASE WHEN DATEDIFF(day, DueDate, GETDATE()) BETWEEN 31 AND 60 THEN AmountDue ELSE 0 END) as ar_30_60,
            SUM(CASE WHEN DATEDIFF(day, DueDate, GETDATE()) BETWEEN 61 AND 90 THEN AmountDue ELSE 0 END) as ar_60_90,
            SUM(CASE WHEN DATEDIFF(day, DueDate, GETDATE()) > 90 THEN AmountDue ELSE 0 END) as ar_over_90,
            SUM(AmountDue) as ar_total
        FROM {self.schema}.AR
        WHERE AmountDue > 0
        """

        results = self._execute_query(query)
        if not results:
            return []

        row = results[0]
        return [
            {'metric_name': 'ar_current', 'metric_category': 'ar', 'metric_value': float(row['current_ar'] or 0), 'metric_unit': 'dollars'},
            {'metric_name': 'ar_30_60', 'metric_category': 'ar', 'metric_value': float(row['ar_30_60'] or 0), 'metric_unit': 'dollars'},
            {'metric_name': 'ar_60_90', 'metric_category': 'ar', 'metric_value': float(row['ar_60_90'] or 0), 'metric_unit': 'dollars'},
            {'metric_name': 'ar_over_90', 'metric_category': 'ar', 'metric_value': float(row['ar_over_90'] or 0), 'metric_unit': 'dollars'},
            {'metric_name': 'ar_total', 'metric_category': 'ar', 'metric_value': float(row['ar_total'] or 0), 'metric_unit': 'dollars'},
        ]

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        self.connected = False
