"""
QBR Service - Business Logic for Quarterly Business Reviews
Handles metric calculations, data aggregation, and recommendation generation

Adapted for Softbase database schema:
- Customer table uses 'Number' field (not CustomerID)
- Equipment uses 'UnitNo' and 'SerialNo'
- Work Orders (WO table) for service data
- InvoiceReg for financial data
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class QBRService:
    """Service class for QBR business logic"""

    def __init__(self, sql_service, postgres_service=None):
        """
        Initialize QBR Service
        Args:
            sql_service: AzureSQLService for Softbase data (customers, WOs, invoices)
            postgres_service: PostgreSQLService for QBR session storage (optional)
        """
        self.sql_service = sql_service  # Azure SQL for Softbase data
        self.postgres_service = postgres_service  # PostgreSQL for QBR sessions

    def get_quarter_date_range(self, quarter: str, year: int) -> tuple:
        """
        Convert quarter string to date range
        Args:
            quarter: 'Q1', 'Q2', 'Q3', or 'Q4'
            year: fiscal year
        Returns:
            (start_date, end_date) tuple
        """
        quarter_map = {
            'Q1': (1, 3),
            'Q2': (4, 6),
            'Q3': (7, 9),
            'Q4': (10, 12)
        }

        if quarter not in quarter_map:
            raise ValueError(f"Invalid quarter: {quarter}")

        start_month, end_month = quarter_map[quarter]
        start_date = datetime(year, start_month, 1)

        # Get last day of end month
        if end_month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, end_month + 1, 1) - timedelta(days=1)

        return (start_date, end_date)

    def _convert_decimal(self, value):
        """Convert Decimal to float for JSON serialization"""
        if isinstance(value, Decimal):
            return float(value)
        return value

    def get_customers_for_qbr(self) -> List[Dict]:
        """
        Get list of customers for QBR dropdown
        Returns customers with recent invoice activity (last 2 years)
        Uses same pattern as dashboard top_customers
        """
        try:
            query = """
            WITH NormalizedCustomers AS (
                SELECT 
                    CASE 
                        WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                        WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                        ELSE BillToName
                    END as customer_name,
                    InvoiceNo,
                    InvoiceDate
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= DATEADD(year, -2, GETDATE())
                  AND BillToName IS NOT NULL
                  AND BillToName != ''
                  AND BillToName NOT LIKE '%Wells Fargo%'
                  AND BillToName NOT LIKE '%Maintenance contract%'
                  AND BillToName NOT LIKE '%Rental Fleet%'
            )
            SELECT 
                customer_name,
                customer_name as customer_number,
                COUNT(DISTINCT InvoiceNo) as total_invoices,
                MAX(InvoiceDate) as last_invoice_date
            FROM NormalizedCustomers
            GROUP BY customer_name
            HAVING COUNT(DISTINCT InvoiceNo) > 0
            ORDER BY customer_name
            """

            results = self.sql_service.execute_query(query)

            return [{
                'customer_number': row['customer_number'],
                'customer_name': row['customer_name'],
                'total_invoices': row.get('total_invoices', 0) or 0
            } for row in results] if results else []

        except Exception as e:
            logger.error(f"Error getting customers for QBR: {str(e)}")
            return []

    def get_fleet_overview(self, customer_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get fleet overview metrics
        Returns total units serviced, equipment types breakdown
        customer_name: The normalized customer name from BillToName
        """
        try:
            # BillTo subquery for customer name lookup
            billto_subquery = """
                SELECT DISTINCT BillTo FROM ben002.InvoiceReg
                WHERE CASE
                    WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END = %s
            """

            # Get equipment serviced for this customer
            query = f"""
            SELECT
                COUNT(DISTINCT wo.UnitNo) as total_units,
                e.Make,
                e.Model
            FROM ben002.WO wo
            LEFT JOIN ben002.Equipment e ON wo.UnitNo = e.UnitNo
            WHERE wo.BillTo IN ({billto_subquery})
              AND wo.OpenDate >= %s
              AND wo.OpenDate <= %s
              AND wo.Type IN ('S', 'R', 'P')
            GROUP BY e.Make, e.Model
            ORDER BY COUNT(DISTINCT wo.UnitNo) DESC
            """

            mix_results = self.sql_service.execute_query(query, (customer_name, start_date, end_date))

            # Get total unique units
            total_query = f"""
            SELECT COUNT(DISTINCT UnitNo) as total_units
            FROM ben002.WO
            WHERE BillTo IN ({billto_subquery})
              AND OpenDate >= %s
              AND OpenDate <= %s
              AND Type IN ('S', 'R', 'P')
            """

            total_result = self.sql_service.execute_query(total_query, (customer_name, start_date, end_date))
            total_units = total_result[0]['total_units'] if total_result else 0

            # Format equipment mix
            equipment_mix = []
            for row in (mix_results or []):
                make = row.get('Make', 'Unknown') or 'Unknown'
                model = row.get('Model', '') or ''
                equipment_mix.append({
                    'equipment_type': f"{make} {model}".strip() or 'Unknown',
                    'count': row.get('total_units', 0) or 0
                })

            return {
                'total_units': total_units or 0,
                'owned': 0,  # Would need ownership tracking
                'leased': 0,
                'rented': 0,
                'equipment_mix': equipment_mix[:10]  # Top 10
            }

        except Exception as e:
            logger.error(f"Error getting fleet overview: {str(e)}")
            return {
                'total_units': 0,
                'owned': 0,
                'leased': 0,
                'rented': 0,
                'equipment_mix': []
            }

    def get_fleet_health(self, customer_number: str, assessment_date: datetime) -> Dict:
        """
        Get fleet health metrics from equipment_condition_history (PostgreSQL)
        Returns equipment condition breakdown and average age
        """
        try:
            good_count = 0
            monitor_count = 0
            replace_count = 0
            avg_fleet_age = 0

            # Try to get condition history from PostgreSQL if available
            if self.postgres_service:
                query = """
                WITH LatestAssessments AS (
                    SELECT
                        unit_no,
                        condition_status,
                        age_years,
                        ROW_NUMBER() OVER (PARTITION BY unit_no ORDER BY assessment_date DESC) as rn
                    FROM equipment_condition_history
                    WHERE customer_number = %s
                      AND assessment_date <= %s
                )
                SELECT
                    condition_status,
                    COUNT(*) as count,
                    AVG(age_years) as avg_age
                FROM LatestAssessments
                WHERE rn = 1
                GROUP BY condition_status
                """

                try:
                    conditions = self.postgres_service.execute_query(query, (customer_number, assessment_date))

                    total_age = 0
                    total_count = 0

                    if conditions:
                        for row in conditions:
                            count = row['count'] or 0
                            total_count += count
                            total_age += (self._convert_decimal(row['avg_age']) or 0) * count

                            if row['condition_status'] == 'good':
                                good_count = count
                            elif row['condition_status'] == 'monitor':
                                monitor_count = count
                            elif row['condition_status'] == 'replace':
                                replace_count = count

                    avg_fleet_age = round(total_age / total_count, 1) if total_count > 0 else 0
                except Exception as pg_error:
                    logger.warning(f"Could not query condition history from PostgreSQL: {pg_error}")

            # Age distribution (placeholder - would need actual equipment age data)
            age_distribution = [
                {'age_range': '0-2 years', 'count': 0},
                {'age_range': '3-5 years', 'count': 0},
                {'age_range': '6-8 years', 'count': 0},
                {'age_range': '9-11 years', 'count': 0},
                {'age_range': '12+ years', 'count': 0}
            ]

            return {
                'good_condition': good_count,
                'monitor': monitor_count,
                'replace_soon': replace_count,
                'avg_fleet_age': avg_fleet_age,
                'age_distribution': age_distribution
            }

        except Exception as e:
            logger.error(f"Error getting fleet health: {str(e)}")
            return {
                'good_condition': 0,
                'monitor': 0,
                'replace_soon': 0,
                'avg_fleet_age': 0,
                'age_distribution': []
            }

    def get_service_performance(self, customer_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get service performance metrics from WO table
        Returns service calls, PM completion, response time
        customer_name: The normalized customer name from BillToName
        """
        try:
            # BillTo subquery for customer name lookup
            billto_subquery = """
                SELECT DISTINCT BillTo FROM ben002.InvoiceReg
                WHERE CASE
                    WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END = %s
            """

            # Service calls and metrics from WO table
            query = f"""
            SELECT
                COUNT(*) as total_calls,
                SUM(CASE WHEN Type = 'S' AND WONo LIKE 'PM%' THEN 1 ELSE 0 END) as pm_count,
                SUM(CASE WHEN Type = 'S' AND WONo LIKE 'PM%' AND ClosedDate IS NOT NULL THEN 1 ELSE 0 END) as pm_completed,
                SUM(CASE WHEN ClosedDate IS NOT NULL THEN 1 ELSE 0 END) as completed_calls
            FROM ben002.WO
            WHERE BillTo IN ({billto_subquery})
              AND OpenDate >= %s
              AND OpenDate <= %s
              AND Type IN ('S', 'R')
              AND WONo NOT LIKE '9%%'
            """

            result = self.sql_service.execute_query(query, (customer_name, start_date, end_date))
            metrics = result[0] if result else {}

            total_calls = metrics.get('total_calls', 0) or 0
            pm_count = metrics.get('pm_count', 0) or 0
            pm_completed = metrics.get('pm_completed', 0) or 0
            completed_calls = metrics.get('completed_calls', 0) or 0

            pm_completion_rate = round((pm_completed / pm_count * 100), 1) if pm_count > 0 else 0
            first_time_fix_rate = round((completed_calls / total_calls * 100), 1) if total_calls > 0 else 0

            # Service type breakdown
            breakdown_query = f"""
            SELECT
                CASE
                    WHEN WONo LIKE 'PM%%' THEN 'Planned Maintenance'
                    WHEN Type = 'S' THEN 'Service/Repair'
                    WHEN Type = 'R' THEN 'Rental Service'
                    ELSE 'Other'
                END as service_type,
                COUNT(*) as count
            FROM ben002.WO
            WHERE BillTo IN ({billto_subquery})
              AND OpenDate >= %s
              AND OpenDate <= %s
              AND Type IN ('S', 'R')
              AND WONo NOT LIKE '9%%'
            GROUP BY
                CASE
                    WHEN WONo LIKE 'PM%%' THEN 'Planned Maintenance'
                    WHEN Type = 'S' THEN 'Service/Repair'
                    WHEN Type = 'R' THEN 'Rental Service'
                    ELSE 'Other'
                END
            """

            breakdown = self.sql_service.execute_query(breakdown_query, (customer_name, start_date, end_date))

            # Calculate percentages
            service_breakdown = {}
            for row in (breakdown or []):
                service_type = row['service_type']
                count = row['count'] or 0
                percentage = round((count / total_calls * 100), 1) if total_calls > 0 else 0
                key = service_type.lower().replace(' ', '_').replace('/', '_')
                service_breakdown[key] = percentage

            # Monthly trend
            trend_query = f"""
            SELECT
                MONTH(OpenDate) as month,
                COUNT(*) as calls
            FROM ben002.WO
            WHERE BillTo IN ({billto_subquery})
              AND OpenDate >= %s
              AND OpenDate <= %s
              AND Type IN ('S', 'R')
              AND WONo NOT LIKE '9%%'
            GROUP BY MONTH(OpenDate)
            ORDER BY MONTH(OpenDate)
            """

            monthly_trend = self.sql_service.execute_query(trend_query, (customer_name, start_date, end_date))

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            trend_data = []
            for row in (monthly_trend or []):
                month_num = row['month']
                if month_num and 1 <= month_num <= 12:
                    trend_data.append({
                        'month': month_num,
                        'month_name': month_names[month_num - 1],
                        'calls': row['calls'] or 0
                    })

            return {
                'service_calls': total_calls,
                'pm_completion_rate': pm_completion_rate,
                'avg_response_time': 0,  # Would need timestamp data
                'first_time_fix_rate': first_time_fix_rate,
                'service_breakdown': service_breakdown,
                'monthly_trend': trend_data
            }

        except Exception as e:
            logger.error(f"Error getting service performance: {str(e)}")
            return {
                'service_calls': 0,
                'pm_completion_rate': 0,
                'avg_response_time': 0,
                'first_time_fix_rate': 0,
                'service_breakdown': {},
                'monthly_trend': []
            }

    def get_service_costs(self, customer_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get service cost analysis from InvoiceReg
        Returns total spend and breakdown by category
        customer_name: The normalized customer name from BillToName
        """
        try:
            # Total spend from InvoiceReg for service invoices using BillToName normalization
            query = """
            SELECT
                SUM(GrandTotal) as total_spend,
                SUM(LaborTaxable + LaborNonTaxable) as labor_total,
                SUM(PartsTaxable + PartsNonTaxable) as parts_total,
                COUNT(*) as invoice_count
            FROM ben002.InvoiceReg
            WHERE CASE
                WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                ELSE BillToName
            END = %s
              AND InvoiceDate >= %s
              AND InvoiceDate <= %s
              AND SaleCode = 'SVE'
            """

            result = self.sql_service.execute_query(query, (customer_name, start_date, end_date))
            costs = result[0] if result else {}

            total_spend = self._convert_decimal(costs.get('total_spend', 0)) or 0
            labor_total = self._convert_decimal(costs.get('labor_total', 0)) or 0
            parts_total = self._convert_decimal(costs.get('parts_total', 0)) or 0

            # Quarterly trend (last 4 quarters)
            year = start_date.year
            quarter_num = (start_date.month - 1) // 3 + 1

            quarters = []
            for i in range(3, -1, -1):
                q_num = quarter_num - i
                q_year = year
                if q_num <= 0:
                    q_num += 4
                    q_year -= 1

                q_start, q_end = self.get_quarter_date_range(f'Q{q_num}', q_year)

                q_query = """
                SELECT SUM(GrandTotal) as cost
                FROM ben002.InvoiceReg
                WHERE CASE
                    WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END = %s
                  AND InvoiceDate >= %s
                  AND InvoiceDate <= %s
                  AND SaleCode = 'SVE'
                """

                q_result = self.sql_service.execute_query(q_query, (customer_name, q_start, q_end))
                q_cost = self._convert_decimal(q_result[0]['cost']) if q_result and q_result[0]['cost'] else 0

                quarters.append({
                    'quarter': f'Q{q_num} {q_year}',
                    'cost': float(q_cost)
                })

            return {
                'total_spend': float(total_spend),
                'planned_maintenance': {
                    'cost': float(labor_total * 0.4),  # Estimate PM as 40% of labor
                    'services': 0
                },
                'unplanned_repairs': {
                    'cost': float(labor_total * 0.6),  # Estimate repairs as 60%
                    'services': 0
                },
                'damage_accidents': {
                    'cost': 0,
                    'incidents': 0
                },
                'quarterly_trend': quarters
            }

        except Exception as e:
            logger.error(f"Error getting service costs: {str(e)}")
            return {
                'total_spend': 0,
                'planned_maintenance': {'cost': 0, 'services': 0},
                'unplanned_repairs': {'cost': 0, 'services': 0},
                'damage_accidents': {'cost': 0, 'incidents': 0},
                'quarterly_trend': []
            }

    def get_parts_rentals(self, customer_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get parts and rental activity from InvoiceReg
        customer_name: The normalized customer name from BillToName
        """
        try:
            # Parts from InvoiceReg using BillToName normalization
            parts_query = """
            SELECT
                COUNT(*) as orders,
                SUM(PartsTaxable + PartsNonTaxable) as total_spend
            FROM ben002.InvoiceReg
            WHERE CASE
                WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                ELSE BillToName
            END = %s
              AND InvoiceDate >= %s
              AND InvoiceDate <= %s
              AND SaleCode = 'PRT'
            """

            parts_result = self.sql_service.execute_query(parts_query, (customer_name, start_date, end_date))
            parts = parts_result[0] if parts_result else {'orders': 0, 'total_spend': 0}

            # Rental from InvoiceReg using BillToName normalization
            rental_query = """
            SELECT
                COUNT(*) as rental_invoices,
                SUM(RentalTaxable + RentalNonTaxable) as rental_spend
            FROM ben002.InvoiceReg
            WHERE CASE
                WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                ELSE BillToName
            END = %s
              AND InvoiceDate >= %s
              AND InvoiceDate <= %s
              AND (RentalTaxable > 0 OR RentalNonTaxable > 0)
            """

            rental_result = self.sql_service.execute_query(rental_query, (customer_name, start_date, end_date))
            rentals = rental_result[0] if rental_result else {'rental_invoices': 0, 'rental_spend': 0}

            # Monthly rental trend using BillToName normalization
            rental_trend_query = """
            SELECT
                MONTH(InvoiceDate) as month,
                SUM(RentalTaxable + RentalNonTaxable) as amount
            FROM ben002.InvoiceReg
            WHERE CASE
                WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                ELSE BillToName
            END = %s
              AND InvoiceDate >= %s
              AND InvoiceDate <= %s
              AND (RentalTaxable > 0 OR RentalNonTaxable > 0)
            GROUP BY MONTH(InvoiceDate)
            ORDER BY MONTH(InvoiceDate)
            """

            rental_trend = self.sql_service.execute_query(rental_trend_query, (customer_name, start_date, end_date))

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            trend_data = []
            for row in (rental_trend or []):
                month_num = row['month']
                if month_num and 1 <= month_num <= 12:
                    trend_data.append({
                        'month': month_num,
                        'month_name': month_names[month_num - 1],
                        'amount': float(self._convert_decimal(row['amount']) or 0)
                    })

            return {
                'parts': {
                    'orders': int(parts['orders'] or 0),
                    'total_spend': float(self._convert_decimal(parts['total_spend']) or 0),
                    'top_categories': []  # Would need parts detail data
                },
                'rentals': {
                    'active_rentals': int(rentals['rental_invoices'] or 0),
                    'rental_days': 0,  # Would need rental detail data
                    'rental_spend': float(self._convert_decimal(rentals['rental_spend']) or 0),
                    'monthly_trend': trend_data
                }
            }

        except Exception as e:
            logger.error(f"Error getting parts/rentals: {str(e)}")
            return {
                'parts': {'orders': 0, 'total_spend': 0, 'top_categories': []},
                'rentals': {'active_rentals': 0, 'rental_days': 0, 'rental_spend': 0, 'monthly_trend': []}
            }

    def get_value_delivered(self, customer_name: str, start_date: datetime, end_date: datetime,
                            service_costs: Dict, parts_rentals: Dict) -> Dict:
        """
        Calculate value delivered / ROI metrics
        customer_name: The normalized customer name from BillToName
        """
        try:
            # Calculate estimated savings (25% savings estimate from preventive maintenance)
            total_service_spend = service_costs['total_spend']
            estimated_savings = total_service_spend * 0.25

            # Uptime estimate (95% baseline)
            uptime_percentage = 95.0

            # Spend breakdown
            service_labor = service_costs['total_spend']
            parts_spend = parts_rentals['parts']['total_spend']
            rental_spend = parts_rentals['rentals'].get('rental_spend', 0)

            total_spend = service_labor + parts_spend + rental_spend

            # Rolling 4 quarters trend
            year = start_date.year
            quarter_num = (start_date.month - 1) // 3 + 1

            quarters = []
            for i in range(3, -1, -1):
                q_num = quarter_num - i
                q_year = year
                if q_num <= 0:
                    q_num += 4
                    q_year -= 1

                q_start, q_end = self.get_quarter_date_range(f'Q{q_num}', q_year)

                # Get total spend for quarter using BillToName normalization
                q_query = """
                SELECT SUM(GrandTotal) as total
                FROM ben002.InvoiceReg
                WHERE CASE
                    WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END = %s
                  AND InvoiceDate >= %s
                  AND InvoiceDate <= %s
                """

                q_result = self.sql_service.execute_query(q_query, (customer_name, q_start, q_end))
                q_total = self._convert_decimal(q_result[0]['total']) if q_result and q_result[0]['total'] else 0

                quarters.append({
                    'quarter': f'Q{q_num} {q_year}',
                    'spend': float(q_total)
                })

            return {
                'estimated_savings': round(estimated_savings, 2),
                'uptime_achieved': uptime_percentage,
                'downtime_avoided': 0,
                'spend_breakdown': {
                    'service_labor': round(service_labor, 2),
                    'parts': round(parts_spend, 2),
                    'rentals': round(rental_spend, 2),
                    'total': round(total_spend, 2)
                },
                'rolling_4q_trend': quarters
            }

        except Exception as e:
            logger.error(f"Error calculating value delivered: {str(e)}")
            return {
                'estimated_savings': 0,
                'uptime_achieved': 0,
                'downtime_avoided': 0,
                'spend_breakdown': {'service_labor': 0, 'parts': 0, 'rentals': 0, 'total': 0},
                'rolling_4q_trend': []
            }

    def generate_recommendations(self, customer_name: str, fleet_health: Dict, service_costs: Dict) -> List[Dict]:
        """
        Generate auto-recommendations based on data patterns
        customer_name: The normalized customer name from BillToName (not currently used but kept for consistency)
        """
        recommendations = []

        try:
            # Recommendation 1: Equipment replacement
            if fleet_health['replace_soon'] > 0:
                recommendations.append({
                    'category': 'equipment_refresh',
                    'title': f"Replace {fleet_health['replace_soon']} aging equipment units",
                    'description': "These units have high maintenance costs relative to replacement value",
                    'estimated_impact': f"${fleet_health['replace_soon'] * 5000} estimated annual savings",
                    'is_auto_generated': True
                })

            # Recommendation 2: High repair costs
            pm_cost = service_costs['planned_maintenance']['cost']
            repair_cost = service_costs['unplanned_repairs']['cost']
            if repair_cost > pm_cost and repair_cost > 0:
                savings = (repair_cost - pm_cost) * 0.3
                recommendations.append({
                    'category': 'optimization',
                    'title': "Increase preventive maintenance frequency",
                    'description': "Unplanned repairs exceed planned maintenance costs",
                    'estimated_impact': f"${round(savings, 0)} potential savings",
                    'is_auto_generated': True
                })

            # Recommendation 3: Safety/training (if high damage costs)
            if service_costs['damage_accidents']['incidents'] > 2:
                recommendations.append({
                    'category': 'safety_training',
                    'title': "Implement operator safety training",
                    'description': f"{service_costs['damage_accidents']['incidents']} damage incidents this quarter",
                    'estimated_impact': "50% reduction in damage incidents",
                    'is_auto_generated': True
                })

            # Default recommendation if none generated
            if len(recommendations) == 0:
                recommendations.append({
                    'category': 'optimization',
                    'title': "Continue current maintenance program",
                    'description': "Equipment performance metrics are on target",
                    'estimated_impact': "Maintain current efficiency levels",
                    'is_auto_generated': True
                })

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")

        return recommendations

    # === QBR Session Management (PostgreSQL) ===

    def save_qbr_session(self, qbr_data: Dict, created_by: str = None) -> str:
        """Save a new QBR session to PostgreSQL database"""
        try:
            import uuid
            qbr_id = f"QBR-{qbr_data['quarter'].replace(' ', '-')}-{qbr_data['customer_number']}-{uuid.uuid4().hex[:8]}"

            if not self.postgres_service:
                logger.warning("PostgreSQL service not available, QBR session not saved")
                return qbr_id

            # Parse quarter (e.g., "Q4 2025" -> quarter="Q4", fiscal_year=2025)
            quarter_parts = qbr_data['quarter'].split(' ')
            quarter = quarter_parts[0] if quarter_parts else 'Q4'
            fiscal_year = int(quarter_parts[1]) if len(quarter_parts) > 1 else 2025

            insert_query = """
            INSERT INTO qbr_sessions (
                qbr_id, customer_number, customer_name, quarter, fiscal_year,
                meeting_date, created_by, status, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING qbr_id
            """

            result = self.postgres_service.execute_insert_returning(
                insert_query,
                (
                    qbr_id,
                    qbr_data['customer_number'],
                    qbr_data.get('customer_name', 'Unknown'),
                    quarter,
                    fiscal_year,
                    qbr_data.get('meeting_date'),
                    created_by,
                    qbr_data.get('status', 'draft'),
                    qbr_data.get('notes')
                )
            )

            logger.info(f"Saved QBR session: {qbr_id}")

            # Save business priorities if provided
            if qbr_data.get('business_priorities'):
                for i, priority in enumerate(qbr_data['business_priorities'][:3], 1):
                    self._save_business_priority(qbr_id, i, priority)

            # Save recommendations if provided
            if qbr_data.get('recommendations'):
                for rec in qbr_data['recommendations']:
                    self._save_recommendation(qbr_id, rec)

            # Save action items if provided
            if qbr_data.get('action_items'):
                for item in qbr_data['action_items']:
                    self._save_action_item(qbr_id, item)

            return qbr_id

        except Exception as e:
            logger.error(f"Error saving QBR session: {str(e)}")
            raise

    def _save_business_priority(self, qbr_id: str, priority_number: int, priority: Dict):
        """Save a business priority to PostgreSQL"""
        if not self.postgres_service:
            return

        query = """
        INSERT INTO qbr_business_priorities (qbr_id, priority_number, title, description)
        VALUES (%s, %s, %s, %s)
        """
        self.postgres_service.execute_update(
            query,
            (qbr_id, priority_number, priority.get('title', ''), priority.get('description'))
        )

    def _save_recommendation(self, qbr_id: str, recommendation: Dict):
        """Save a recommendation to PostgreSQL"""
        if not self.postgres_service:
            return

        query = """
        INSERT INTO qbr_recommendations (qbr_id, category, title, description, estimated_impact, is_auto_generated, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.postgres_service.execute_update(
            query,
            (
                qbr_id,
                recommendation.get('category', 'optimization'),
                recommendation.get('title', ''),
                recommendation.get('description'),
                recommendation.get('estimated_impact'),
                recommendation.get('is_auto_generated', False),
                recommendation.get('status', 'proposed')
            )
        )

    def _save_action_item(self, qbr_id: str, action_item: Dict):
        """Save an action item to PostgreSQL"""
        if not self.postgres_service:
            return

        query = """
        INSERT INTO qbr_action_items (qbr_id, party, description, owner_name, due_date)
        VALUES (%s, %s, %s, %s, %s)
        """
        self.postgres_service.execute_update(
            query,
            (
                qbr_id,
                action_item.get('party', 'BMH'),
                action_item.get('description', ''),
                action_item.get('owner_name'),
                action_item.get('due_date')
            )
        )

    def get_qbr_session(self, qbr_id: str) -> Optional[Dict]:
        """Retrieve a saved QBR session from PostgreSQL"""
        try:
            if not self.postgres_service:
                logger.warning("PostgreSQL service not available")
                return None

            # Get main session
            query = "SELECT * FROM qbr_sessions WHERE qbr_id = %s"
            result = self.postgres_service.execute_query(query, (qbr_id,))

            if not result:
                return None

            session = dict(result[0])

            # Get business priorities
            priorities_query = """
            SELECT * FROM qbr_business_priorities
            WHERE qbr_id = %s ORDER BY priority_number
            """
            session['business_priorities'] = self.postgres_service.execute_query(priorities_query, (qbr_id,))

            # Get recommendations
            recommendations_query = "SELECT * FROM qbr_recommendations WHERE qbr_id = %s"
            session['recommendations'] = self.postgres_service.execute_query(recommendations_query, (qbr_id,))

            # Get action items
            actions_query = "SELECT * FROM qbr_action_items WHERE qbr_id = %s ORDER BY due_date"
            session['action_items'] = self.postgres_service.execute_query(actions_query, (qbr_id,))

            return session

        except Exception as e:
            logger.error(f"Error getting QBR session: {str(e)}")
            return None

    def get_qbr_sessions_list(self, customer_number: str = None, status: str = None) -> List[Dict]:
        """Get list of QBR sessions from PostgreSQL"""
        try:
            if not self.postgres_service:
                return []

            query = "SELECT * FROM qbr_sessions WHERE 1=1"
            params = []

            if customer_number:
                query += " AND customer_number = %s"
                params.append(customer_number)

            if status:
                query += " AND status = %s"
                params.append(status)

            query += " ORDER BY created_date DESC"

            return self.postgres_service.execute_query(query, tuple(params) if params else None) or []

        except Exception as e:
            logger.error(f"Error getting QBR sessions list: {str(e)}")
            return []
