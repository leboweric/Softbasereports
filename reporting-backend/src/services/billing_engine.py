"""
Billing Calculation Engine for VITAL WorkLife Finance Module

This engine pulls billing data from the finance_monthly_billing table,
which contains pre-calculated monthly revenue values imported from the Excel spreadsheet.

The finance_monthly_billing table has:
- population_count: Correct population for each client
- pepm_rate: PEPM rate for each month
- revenue_revrec: Pre-calculated RevRec revenue (Pop × PEPM)
- revenue_cash: Pre-calculated Cash revenue (based on billing terms)
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import calendar


class BillingEngine:
    """Calculate billing amounts for Cash and Revenue Recognition"""
    
    BILLING_MULTIPLIERS = {
        'annual': 12,
        'semi': 6,
        'qtly': 3,
        'quarterly': 3,
        'monthly': 1
    }
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_spreadsheet_view(
        self,
        org_id: int,
        year: int,
        revenue_type: str = 'revrec'
    ) -> List[Dict]:
        """
        Generate spreadsheet-like view with all columns.
        Uses finance_monthly_billing table for correct population and revenue data.
        
        Args:
            org_id: Organization ID
            year: Year to display
            revenue_type: 'cash' or 'revrec' (determines which monthly values to show)
        
        Returns:
            List of dicts, each representing one row in the spreadsheet
        """
        cursor = self.db.cursor()
        
        # Get all clients with their monthly billing data
        cursor.execute("""
            SELECT 
                fc.id,
                fc.billing_name,
                fc.tier,
                fc.industry,
                fc.session_product,
                fc.billing_terms,
                fc.wpo_name,
                fc.wpo_product,
                fc.wpo_billing,
                fc.wpo_account_number,
                fc.solution_type,
                fc.applicable_law_state,
                fc.nexus_state,
                fc.status,
                fc.at_risk_reason,
                fc.at_risk_level,
                fc.inception_date,
                fc.renewal_date,
                fc.contract_length,
                fc.year_2026_months,
                fc.year_2027_months,
                fc.year_2028_months,
                fc.year_2029_months,
                fc.year_2030_months,
                fc.year_2031_months,
                fc.pepm_2025,
                fc.pepm_2026,
                fc.pepm_2027,
                fc.pepm_2028,
                fc.pepm_2029,
                fc.pepm_2030,
                fc.pepm_2031,
                fc.contract_value_total
            FROM finance_clients fc
            WHERE fc.org_id = %s
            ORDER BY fc.billing_name
        """, (org_id,))
        
        columns = [desc[0] for desc in cursor.description]
        clients = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        rows = []
        
        for client in clients:
            client_id = client['id']
            
            # Get monthly billing data for this client and year
            cursor.execute("""
                SELECT billing_month, population_count, pepm_rate, revenue_revrec, revenue_cash
                FROM finance_monthly_billing
                WHERE client_id = %s AND billing_year = %s
                ORDER BY billing_month
            """, (client_id, year))
            
            monthly_data = {row[0]: {
                'population': row[1],
                'pepm': float(row[2]) if row[2] else 0,
                'revrec': float(row[3]) if row[3] else 0,
                'cash': float(row[4]) if row[4] else 0
            } for row in cursor.fetchall()}
            
            if not monthly_data:
                continue  # Skip clients with no billing data for this year
            
            # Get population and PEPM from the first month with data
            first_month = min(monthly_data.keys()) if monthly_data else 1
            population = monthly_data.get(first_month, {}).get('population', 0)
            pepm = monthly_data.get(first_month, {}).get('pepm', 0)
            
            billing_terms = client['billing_terms'] or 'monthly'
            renewal_date = client['renewal_date']
            inception_date = client['inception_date']
            renewal_month = renewal_date.month if renewal_date else 1
            
            # Calculate monthly values and total
            monthly = {}
            total = Decimal('0')
            
            for month in range(1, 13):
                if month in monthly_data:
                    if revenue_type == 'cash':
                        value = monthly_data[month]['cash']
                    else:
                        value = monthly_data[month]['revrec']
                else:
                    value = 0
                
                monthly[month] = float(value)
                total += Decimal(str(value))
            
            # Build row matching spreadsheet columns (44 columns like Excel)
            row = {
                'id': client_id,
                'revenue_type': revenue_type.upper(),
                'wpo_name': client['wpo_name'],
                'at_risk': client['at_risk_level'],
                'billing_name': client['billing_name'],
                'inception_date': inception_date.isoformat() if inception_date else None,
                'renewal_date': renewal_date.isoformat() if renewal_date else None,
                'contract_length': client['contract_length'],
                # Year months active
                'year_2026': float(client['year_2026_months']) if client['year_2026_months'] else None,
                'year_2027': float(client['year_2027_months']) if client['year_2027_months'] else None,
                'year_2028': float(client['year_2028_months']) if client['year_2028_months'] else None,
                'year_2029': float(client['year_2029_months']) if client['year_2029_months'] else None,
                'year_2030': float(client['year_2030_months']) if client['year_2030_months'] else None,
                'year_2031': float(client['year_2031_months']) if client['year_2031_months'] else None,
                'session_product': client['session_product'],
                'billing_terms': billing_terms,
                # Monthly values
                'jan': monthly[1],
                'feb': monthly[2],
                'mar': monthly[3],
                'apr': monthly[4],
                'may': monthly[5],
                'jun': monthly[6],
                'jul': monthly[7],
                'aug': monthly[8],
                'sep': monthly[9],
                'oct': monthly[10],
                'nov': monthly[11],
                'dec': monthly[12],
                # Annual total
                'annual_total': float(total),
                'population': population,
                # PEPM rates by year
                'pepm_2025': float(client['pepm_2025']) if client['pepm_2025'] else None,
                'pepm_2026': float(client['pepm_2026']) if client['pepm_2026'] else pepm,
                'pepm_2027': float(client['pepm_2027']) if client['pepm_2027'] else None,
                'pepm_2028': float(client['pepm_2028']) if client['pepm_2028'] else None,
                'pepm_2029': float(client['pepm_2029']) if client['pepm_2029'] else None,
                'pepm_2030': float(client['pepm_2030']) if client['pepm_2030'] else None,
                'pepm_2031': float(client['pepm_2031']) if client['pepm_2031'] else None,
                'contract_value_total': float(client['contract_value_total']) if client['contract_value_total'] else None,
                'wpo_product': client['wpo_product'],
                'wpo_billing': float(client['wpo_billing']) if client['wpo_billing'] else None,
                'wpo_account_number': client['wpo_account_number'],
                'industry': client['industry'],
                'tier': client['tier'],
                'applicable_law_state': client['applicable_law_state'],
                'nexus_state': client['nexus_state'],
                # Legacy fields
                'solution_type': client['solution_type'],
                'status': client['status'],
                'at_risk_reason': client['at_risk_reason'],
                'renewal_month': renewal_month
            }
            
            rows.append(row)
        
        return rows
    
    def get_dual_entry_spreadsheet(
        self,
        org_id: int,
        year: int
    ) -> List[Dict]:
        """
        Generate dual-entry spreadsheet view with both Cash and RevRec rows per client.
        
        Returns:
            List of dicts with TWO rows per client (Cash and RevRec)
        """
        cash_rows = self.get_spreadsheet_view(org_id, year, 'cash')
        revrec_rows = self.get_spreadsheet_view(org_id, year, 'revrec')
        
        # Interleave Cash and RevRec rows
        result = []
        for i in range(len(cash_rows)):
            result.append(cash_rows[i])
            if i < len(revrec_rows):
                result.append(revrec_rows[i])
        
        return result
    
    def get_billing_summary(
        self,
        org_id: int,
        year: int
    ) -> Dict:
        """
        Get billing summary with totals by tier and industry.
        """
        cursor = self.db.cursor()
        
        # Get totals from finance_monthly_billing
        cursor.execute("""
            SELECT 
                fc.tier,
                fc.industry,
                SUM(fmb.revenue_revrec) as total_revrec,
                SUM(fmb.revenue_cash) as total_cash,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(fmb.population_count) / 12 as avg_population
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s AND fmb.billing_year = %s
            GROUP BY fc.tier, fc.industry
        """, (org_id, year))
        
        by_tier = {}
        by_industry = {}
        total_revrec = 0
        total_cash = 0
        client_count = 0
        
        for row in cursor.fetchall():
            tier = row[0] or 'Unknown'
            industry = row[1] or 'Unknown'
            revrec = float(row[2]) if row[2] else 0
            cash = float(row[3]) if row[3] else 0
            count = row[4] or 0
            population = int(row[5]) if row[5] else 0
            
            if tier not in by_tier:
                by_tier[tier] = {'revrec': 0, 'cash': 0, 'count': 0, 'population': 0}
            by_tier[tier]['revrec'] += revrec
            by_tier[tier]['cash'] += cash
            by_tier[tier]['count'] += count
            by_tier[tier]['population'] += population
            
            if industry not in by_industry:
                by_industry[industry] = {'revrec': 0, 'cash': 0, 'count': 0}
            by_industry[industry]['revrec'] += revrec
            by_industry[industry]['cash'] += cash
            by_industry[industry]['count'] += count
            
            total_revrec += revrec
            total_cash += cash
            client_count += count
        
        # Get monthly totals
        cursor.execute("""
            SELECT 
                fmb.billing_month,
                SUM(fmb.revenue_revrec) as month_revrec,
                SUM(fmb.revenue_cash) as month_cash
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s AND fmb.billing_year = %s
            GROUP BY fmb.billing_month
            ORDER BY fmb.billing_month
        """, (org_id, year))
        
        monthly_revrec = {}
        monthly_cash = {}
        for row in cursor.fetchall():
            month = row[0]
            monthly_revrec[month] = float(row[1]) if row[1] else 0
            monthly_cash[month] = float(row[2]) if row[2] else 0
        
        return {
            'year': year,
            'total_revrec': total_revrec,
            'total_cash': total_cash,
            'monthly_revrec': monthly_revrec,
            'monthly_cash': monthly_cash,
            'by_tier': by_tier,
            'by_industry': by_industry,
            'client_count': client_count
        }
    
    def get_client_billing_data(self, client_id: int) -> Optional[Dict]:
        """Get billing data for a single client"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT 
                fc.id, fc.billing_name, fc.tier, fc.industry, fc.session_product,
                fc.billing_terms, fc.wpo_name, fc.wpo_product, fc.wpo_billing,
                fc.solution_type, fc.applicable_law_state, fc.nexus_state, fc.status,
                fcon.renewal_date, fcon.contract_length_years
            FROM finance_clients fc
            LEFT JOIN finance_contracts fcon ON fc.id = fcon.client_id
            WHERE fc.id = %s
            ORDER BY fcon.id DESC
            LIMIT 1
        """, (client_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # Get population and PEPM from monthly billing
        cursor.execute("""
            SELECT population_count, pepm_rate
            FROM finance_monthly_billing
            WHERE client_id = %s
            ORDER BY billing_year DESC, billing_month DESC
            LIMIT 1
        """, (client_id,))
        
        billing_row = cursor.fetchone()
        population = billing_row[0] if billing_row else 0
        pepm = float(billing_row[1]) if billing_row and billing_row[1] else 0
        
        return {
            'id': row[0],
            'billing_name': row[1],
            'tier': row[2],
            'industry': row[3],
            'session_product': row[4],
            'billing_terms': row[5] or 'monthly',
            'wpo_name': row[6],
            'wpo_product': row[7],
            'wpo_billing': row[8],
            'solution_type': row[9],
            'applicable_law_state': row[10],
            'nexus_state': row[11],
            'status': row[12],
            'population': population,
            'pepm': pepm,
            'renewal_date': row[13],
            'contract_length': row[14]
        }
    
    def calculate_all_clients_billing(
        self,
        org_id: int,
        year: int
    ) -> List[Dict]:
        """Calculate billing for all clients in an organization"""
        return self.get_spreadsheet_view(org_id, year, 'revrec')

    def get_wpo_pivot(
        self,
        org_id: int,
        year: int,
        session_product: str = None,
        revenue_timing: str = 'cash'
    ) -> Dict:
        """
        Generate WPO Pivot table data.
        
        Replicates the Excel PIVOT WPO tab which shows:
        - Clients grouped by WPO Name
        - Sum of WPO Billing per client
        - Filterable by Session Product and Revenue Timing
        
        Args:
            org_id: Organization ID
            year: Year to analyze
            session_product: Filter by session product (e.g., 'PWR', 'EAP 3')
            revenue_timing: 'cash' or 'revrec'
        
        Returns:
            Dict with pivot data and totals
        """
        cursor = self.db.cursor()
        
        # Build query with optional session_product filter
        query = """
            SELECT 
                fc.wpo_name,
                fc.wpo_account_number,
                fc.session_product,
                fc.wpo_billing,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            AND fc.wpo_name IS NOT NULL
        """
        params = [revenue_timing, org_id, year]
        
        if session_product and session_product != 'all':
            query += " AND fc.session_product = %s"
            params.append(session_product)
        
        query += """
            GROUP BY fc.wpo_name, fc.wpo_account_number, fc.session_product, fc.wpo_billing
            ORDER BY fc.wpo_name
        """
        
        cursor.execute(query, params)
        
        rows = []
        total_wpo_billing = Decimal('0')
        total_revenue = Decimal('0')
        
        for row in cursor.fetchall():
            wpo_billing = Decimal(str(row[3])) if row[3] else Decimal('0')
            revenue = Decimal(str(row[4])) if row[4] else Decimal('0')
            
            rows.append({
                'wpo_name': row[0],
                'wpo_account_number': row[1],
                'session_product': row[2],
                'wpo_billing': float(wpo_billing),
                'total_revenue': float(revenue)
            })
            
            total_wpo_billing += wpo_billing
            total_revenue += revenue
        
        # Get distinct session products for filter dropdown
        cursor.execute("""
            SELECT DISTINCT session_product 
            FROM finance_clients 
            WHERE org_id = %s AND session_product IS NOT NULL
            ORDER BY session_product
        """, (org_id,))
        
        session_products = [row[0] for row in cursor.fetchall()]
        
        # Get revenue breakdown by session product (for summary cards and chart)
        cursor.execute("""
            SELECT 
                fc.session_product,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(fc.wpo_billing) as total_wpo_billing,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            AND fc.session_product IS NOT NULL
            GROUP BY fc.session_product
            ORDER BY total_revenue DESC
        """, (revenue_timing, org_id, year))
        
        revenue_by_product = []
        grand_total_revenue = Decimal('0')
        
        for row in cursor.fetchall():
            product_revenue = Decimal(str(row[3])) if row[3] else Decimal('0')
            grand_total_revenue += product_revenue
            revenue_by_product.append({
                'session_product': row[0],
                'client_count': row[1],
                'wpo_billing': float(Decimal(str(row[2])) if row[2] else Decimal('0')),
                'revenue': float(product_revenue)
            })
        
        # Calculate percentages
        for item in revenue_by_product:
            if grand_total_revenue > 0:
                item['percentage'] = round(float(Decimal(str(item['revenue'])) / grand_total_revenue * 100), 1)
            else:
                item['percentage'] = 0
        
        return {
            'year': year,
            'revenue_timing': revenue_timing,
            'session_product_filter': session_product,
            'rows': rows,
            'total_wpo_billing': float(total_wpo_billing),
            'total_revenue': float(total_revenue),
            'client_count': len(rows),
            'available_session_products': session_products,
            'revenue_by_product': revenue_by_product,
            'grand_total_revenue': float(grand_total_revenue)
        }

    def get_tier_product_pivot(
        self,
        org_id: int,
        year: int,
        revenue_timing: str = 'revrec'
    ) -> Dict:
        """
        Generate Tier & Product Pivot table data.
        
        Replicates the Excel 'PIVOT By Tier & Prod' tab which shows 4 pivot tables:
        1. Count of Company Name by Tier × Session Product
        2. Sum of Current Pop by Tier × Session Product
        3. Sum of Current Annual Revenue by Tier × Session Product
        4. Average of 2026 PEPM by Tier × Session Product
        
        Args:
            org_id: Organization ID
            year: Year to analyze
            revenue_timing: 'cash' or 'revrec'
        
        Returns:
            Dict with all 4 pivot tables and totals
        """
        cursor = self.db.cursor()
        
        # Get all data grouped by tier and session product
        cursor.execute("""
            SELECT 
                COALESCE(fc.tier, 'NA') as tier,
                COALESCE(fc.session_product, '(blank)') as session_product,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(DISTINCT fmb.population_count) as total_population,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue,
                AVG(fmb.pepm_rate) as avg_pepm
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            GROUP BY COALESCE(fc.tier, 'NA'), COALESCE(fc.session_product, '(blank)')
            ORDER BY tier, session_product
        """, (revenue_timing, org_id, year))
        
        # Initialize data structures
        tiers = set()
        products = set()
        data = {}  # {tier: {product: {count, population, revenue, avg_pepm}}}
        
        for row in cursor.fetchall():
            tier = row[0]
            product = row[1]
            
            tiers.add(tier)
            products.add(product)
            
            if tier not in data:
                data[tier] = {}
            
            data[tier][product] = {
                'count': row[2] or 0,
                'population': int(row[3]) if row[3] else 0,
                'revenue': float(row[4]) if row[4] else 0,
                'avg_pepm': float(row[5]) if row[5] else 0
            }
        
        # Sort tiers and products
        tier_order = ['A', 'B', 'C', 'D', 'NA', '(blank)']
        sorted_tiers = sorted(tiers, key=lambda x: tier_order.index(x) if x in tier_order else 99)
        
        product_order = ['Concierge', 'EAP 3', 'EAP 4', 'EAP 5', 'EAP 6', 'EAP 8', 'Nurseline', 'PWR', '(blank)']
        sorted_products = sorted(products, key=lambda x: product_order.index(x) if x in product_order else 99)
        
        # Build pivot tables
        count_pivot = []
        population_pivot = []
        revenue_pivot = []
        pepm_pivot = []
        
        # Grand totals by product
        product_totals = {p: {'count': 0, 'population': 0, 'revenue': 0, 'pepm_sum': 0, 'pepm_count': 0} for p in sorted_products}
        
        for tier in sorted_tiers:
            count_row = {'tier': tier}
            pop_row = {'tier': tier}
            rev_row = {'tier': tier}
            pepm_row = {'tier': tier}
            
            tier_total_count = 0
            tier_total_pop = 0
            tier_total_rev = 0
            tier_pepm_sum = 0
            tier_pepm_count = 0
            
            for product in sorted_products:
                cell_data = data.get(tier, {}).get(product, {'count': 0, 'population': 0, 'revenue': 0, 'avg_pepm': 0})
                
                count_row[product] = cell_data['count']
                pop_row[product] = cell_data['population']
                rev_row[product] = cell_data['revenue']
                pepm_row[product] = cell_data['avg_pepm']
                
                tier_total_count += cell_data['count']
                tier_total_pop += cell_data['population']
                tier_total_rev += cell_data['revenue']
                if cell_data['avg_pepm'] > 0:
                    tier_pepm_sum += cell_data['avg_pepm'] * cell_data['count']
                    tier_pepm_count += cell_data['count']
                
                # Update product totals
                product_totals[product]['count'] += cell_data['count']
                product_totals[product]['population'] += cell_data['population']
                product_totals[product]['revenue'] += cell_data['revenue']
                if cell_data['avg_pepm'] > 0:
                    product_totals[product]['pepm_sum'] += cell_data['avg_pepm'] * cell_data['count']
                    product_totals[product]['pepm_count'] += cell_data['count']
            
            # Add tier totals
            count_row['Grand Total'] = tier_total_count
            pop_row['Grand Total'] = tier_total_pop
            rev_row['Grand Total'] = tier_total_rev
            pepm_row['Grand Total'] = tier_pepm_sum / tier_pepm_count if tier_pepm_count > 0 else 0
            
            count_pivot.append(count_row)
            population_pivot.append(pop_row)
            revenue_pivot.append(rev_row)
            pepm_pivot.append(pepm_row)
        
        # Add Grand Total row
        grand_count_row = {'tier': 'Grand Total'}
        grand_pop_row = {'tier': 'Grand Total'}
        grand_rev_row = {'tier': 'Grand Total'}
        grand_pepm_row = {'tier': 'Grand Total'}
        
        grand_total_count = 0
        grand_total_pop = 0
        grand_total_rev = 0
        grand_pepm_sum = 0
        grand_pepm_count = 0
        
        for product in sorted_products:
            grand_count_row[product] = product_totals[product]['count']
            grand_pop_row[product] = product_totals[product]['population']
            grand_rev_row[product] = product_totals[product]['revenue']
            grand_pepm_row[product] = product_totals[product]['pepm_sum'] / product_totals[product]['pepm_count'] if product_totals[product]['pepm_count'] > 0 else 0
            
            grand_total_count += product_totals[product]['count']
            grand_total_pop += product_totals[product]['population']
            grand_total_rev += product_totals[product]['revenue']
            grand_pepm_sum += product_totals[product]['pepm_sum']
            grand_pepm_count += product_totals[product]['pepm_count']
        
        grand_count_row['Grand Total'] = grand_total_count
        grand_pop_row['Grand Total'] = grand_total_pop
        grand_rev_row['Grand Total'] = grand_total_rev
        grand_pepm_row['Grand Total'] = grand_pepm_sum / grand_pepm_count if grand_pepm_count > 0 else 0
        
        count_pivot.append(grand_count_row)
        population_pivot.append(grand_pop_row)
        revenue_pivot.append(grand_rev_row)
        pepm_pivot.append(grand_pepm_row)
        
        return {
            'year': year,
            'revenue_timing': revenue_timing,
            'tiers': sorted_tiers,
            'products': sorted_products,
            'count_pivot': count_pivot,
            'population_pivot': population_pivot,
            'revenue_pivot': revenue_pivot,
            'pepm_pivot': pepm_pivot,
            'grand_totals': {
                'count': grand_total_count,
                'population': grand_total_pop,
                'revenue': grand_total_rev,
                'avg_pepm': grand_pepm_sum / grand_pepm_count if grand_pepm_count > 0 else 0
            }
        }

    def get_current_value_renewals_pivot(
        self,
        org_id: int,
        year: int,
        revenue_timing: str = 'revrec'
    ) -> Dict:
        """
        Generate Current Value Renewals Pivot table data.
        
        Replicates the Excel 'PIVOT Current Value Renewals' tab which shows:
        - Revenue grouped by renewal year
        - Helps understand revenue concentration by renewal timing
        
        Args:
            org_id: Organization ID
            year: Base year for analysis
            revenue_timing: 'cash' or 'revrec'
        
        Returns:
            Dict with pivot data, charts, and insights
        """
        cursor = self.db.cursor()
        
        # Get revenue by renewal year
        cursor.execute("""
            SELECT 
                EXTRACT(YEAR FROM fc.renewal_date) as renewal_year,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(DISTINCT fmb.population_count) as total_population,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            AND fc.renewal_date IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM fc.renewal_date)
            ORDER BY renewal_year
        """, (revenue_timing, org_id, year))
        
        by_year = []
        grand_total_revenue = 0
        grand_total_clients = 0
        grand_total_population = 0
        
        for row in cursor.fetchall():
            renewal_year = int(row[0]) if row[0] else None
            client_count = row[1] or 0
            population = int(row[2]) if row[2] else 0
            revenue = float(row[3]) if row[3] else 0
            
            by_year.append({
                'renewal_year': renewal_year,
                'client_count': client_count,
                'population': population,
                'revenue': revenue
            })
            
            grand_total_revenue += revenue
            grand_total_clients += client_count
            grand_total_population += population
        
        # Get breakdown by tier for each renewal year
        cursor.execute("""
            SELECT 
                EXTRACT(YEAR FROM fc.renewal_date) as renewal_year,
                COALESCE(fc.tier, 'NA') as tier,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            AND fc.renewal_date IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM fc.renewal_date), COALESCE(fc.tier, 'NA')
            ORDER BY renewal_year, tier
        """, (revenue_timing, org_id, year))
        
        by_year_tier = {}
        tiers = set()
        for row in cursor.fetchall():
            renewal_year = int(row[0]) if row[0] else None
            tier = row[1]
            client_count = row[2] or 0
            revenue = float(row[3]) if row[3] else 0
            
            tiers.add(tier)
            if renewal_year not in by_year_tier:
                by_year_tier[renewal_year] = {}
            by_year_tier[renewal_year][tier] = {
                'client_count': client_count,
                'revenue': revenue
            }
        
        # Get breakdown by session product for each renewal year
        cursor.execute("""
            SELECT 
                EXTRACT(YEAR FROM fc.renewal_date) as renewal_year,
                COALESCE(fc.session_product, '(blank)') as session_product,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            AND fc.renewal_date IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM fc.renewal_date), COALESCE(fc.session_product, '(blank)')
            ORDER BY renewal_year, session_product
        """, (revenue_timing, org_id, year))
        
        by_year_product = {}
        products = set()
        for row in cursor.fetchall():
            renewal_year = int(row[0]) if row[0] else None
            product = row[1]
            client_count = row[2] or 0
            revenue = float(row[3]) if row[3] else 0
            
            products.add(product)
            if renewal_year not in by_year_product:
                by_year_product[renewal_year] = {}
            by_year_product[renewal_year][product] = {
                'client_count': client_count,
                'revenue': revenue
            }
        
        # Sort tiers and products
        tier_order = ['A', 'B', 'C', 'D', 'NA', '(blank)']
        sorted_tiers = sorted(tiers, key=lambda x: tier_order.index(x) if x in tier_order else 99)
        
        product_order = ['Concierge', 'EAP 3', 'EAP 4', 'EAP 5', 'EAP 6', 'EAP 8', 'Nurseline', 'PWR', '(blank)']
        sorted_products = sorted(products, key=lambda x: product_order.index(x) if x in product_order else 99)
        
        # Build stacked data for charts
        stacked_by_tier = []
        stacked_by_product = []
        
        for year_data in by_year:
            ry = year_data['renewal_year']
            
            # Tier breakdown
            tier_row = {'renewal_year': ry}
            for tier in sorted_tiers:
                tier_row[tier] = by_year_tier.get(ry, {}).get(tier, {}).get('revenue', 0)
            stacked_by_tier.append(tier_row)
            
            # Product breakdown
            product_row = {'renewal_year': ry}
            for product in sorted_products:
                product_row[product] = by_year_product.get(ry, {}).get(product, {}).get('revenue', 0)
            stacked_by_product.append(product_row)
        
        # Calculate insights
        # Find year with highest revenue
        max_year = max(by_year, key=lambda x: x['revenue']) if by_year else None
        
        # Revenue in next 2 years (current year and next)
        current_year = year
        near_term_revenue = sum(y['revenue'] for y in by_year if y['renewal_year'] and y['renewal_year'] <= current_year + 1)
        
        # Concentration - what % is in the largest year
        concentration_pct = (max_year['revenue'] / grand_total_revenue * 100) if max_year and grand_total_revenue > 0 else 0
        
        return {
            'year': year,
            'revenue_timing': revenue_timing,
            'by_year': by_year,
            'stacked_by_tier': stacked_by_tier,
            'stacked_by_product': stacked_by_product,
            'tiers': sorted_tiers,
            'products': sorted_products,
            'grand_totals': {
                'revenue': grand_total_revenue,
                'client_count': grand_total_clients,
                'population': grand_total_population
            },
            'insights': {
                'largest_renewal_year': max_year['renewal_year'] if max_year else None,
                'largest_renewal_revenue': max_year['revenue'] if max_year else 0,
                'near_term_revenue': near_term_revenue,
                'concentration_pct': concentration_pct
            }
        }


    def get_top_clients_pivot(
        self,
        org_id: int,
        year: int,
        revenue_timing: str = 'revrec',
        limit: int = 20
    ) -> Dict:
        """
        Generate Top Clients Pivot table data.
        
        Replicates the Excel 'PIVOT Top Client' tab which shows:
        - Clients ranked by annual revenue
        - Revenue concentration analysis
        
        Args:
            org_id: Organization ID
            year: Base year for analysis
            revenue_timing: 'cash' or 'revrec'
            limit: Number of top clients to return (default 20)
        
        Returns:
            Dict with pivot data, charts, and insights
        """
        cursor = self.db.cursor()
        
        # Get all clients with their total revenue for the year
        cursor.execute("""
            SELECT 
                fc.billing_name,
                fc.tier,
                fc.session_product,
                fc.industry,
                MAX(fmb.population_count) as population,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue,
                AVG(fmb.pepm_rate) as avg_pepm
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            GROUP BY fc.billing_name, fc.tier, fc.session_product, fc.industry
            ORDER BY total_revenue DESC
        """, (revenue_timing, org_id, year))
        
        all_clients = []
        grand_total_revenue = 0
        grand_total_population = 0
        
        for row in cursor.fetchall():
            billing_name = row[0]
            tier = row[1] or 'NA'
            session_product = row[2] or '(blank)'
            industry = row[3] or '(blank)'
            population = int(row[4]) if row[4] else 0
            revenue = float(row[5]) if row[5] else 0
            avg_pepm = float(row[6]) if row[6] else 0
            
            all_clients.append({
                'billing_name': billing_name,
                'tier': tier,
                'session_product': session_product,
                'industry': industry,
                'population': population,
                'revenue': revenue,
                'avg_pepm': avg_pepm
            })
            
            grand_total_revenue += revenue
            grand_total_population += population
        
        # Calculate cumulative percentages and add rank
        cumulative_revenue = 0
        for i, client in enumerate(all_clients):
            client['rank'] = i + 1
            client['pct_of_total'] = (client['revenue'] / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
            cumulative_revenue += client['revenue']
            client['cumulative_pct'] = (cumulative_revenue / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
        
        # Get top N clients
        top_clients = all_clients[:limit]
        
        # Calculate insights
        top_10_revenue = sum(c['revenue'] for c in all_clients[:10])
        top_10_pct = (top_10_revenue / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
        
        top_20_revenue = sum(c['revenue'] for c in all_clients[:20])
        top_20_pct = (top_20_revenue / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
        
        # Revenue by tier for top clients
        tier_breakdown = {}
        for client in all_clients:
            tier = client['tier']
            if tier not in tier_breakdown:
                tier_breakdown[tier] = {'count': 0, 'revenue': 0, 'population': 0}
            tier_breakdown[tier]['count'] += 1
            tier_breakdown[tier]['revenue'] += client['revenue']
            tier_breakdown[tier]['population'] += client['population']
        
        tier_data = [
            {
                'tier': tier,
                'count': data['count'],
                'revenue': data['revenue'],
                'population': data['population'],
                'pct_of_total': (data['revenue'] / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
            }
            for tier, data in sorted(tier_breakdown.items())
        ]
        
        # Revenue by industry for top clients
        industry_breakdown = {}
        for client in all_clients:
            industry = client['industry']
            if industry not in industry_breakdown:
                industry_breakdown[industry] = {'count': 0, 'revenue': 0}
            industry_breakdown[industry]['count'] += 1
            industry_breakdown[industry]['revenue'] += client['revenue']
        
        # Sort by revenue and take top 10 industries
        industry_data = sorted(
            [
                {
                    'industry': ind,
                    'count': data['count'],
                    'revenue': data['revenue'],
                    'pct_of_total': (data['revenue'] / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
                }
                for ind, data in industry_breakdown.items()
            ],
            key=lambda x: x['revenue'],
            reverse=True
        )[:10]
        
        return {
            'year': year,
            'revenue_timing': revenue_timing,
            'top_clients': top_clients,
            'all_clients_count': len(all_clients),
            'tier_breakdown': tier_data,
            'industry_breakdown': industry_data,
            'grand_totals': {
                'revenue': grand_total_revenue,
                'client_count': len(all_clients),
                'population': grand_total_population
            },
            'insights': {
                'largest_client': all_clients[0]['billing_name'] if all_clients else None,
                'largest_client_revenue': all_clients[0]['revenue'] if all_clients else 0,
                'largest_client_pct': all_clients[0]['pct_of_total'] if all_clients else 0,
                'top_10_revenue': top_10_revenue,
                'top_10_pct': top_10_pct,
                'top_20_revenue': top_20_revenue,
                'top_20_pct': top_20_pct
            }
        }


    def get_industry_stats_pivot(
        self,
        org_id: int,
        year: int,
        revenue_timing: str = 'revrec'
    ) -> Dict:
        """
        Generate Industry Stats Pivot table data.
        
        Replicates the Excel 'PIVOT Industry Stats' tab which shows:
        - Revenue and population breakdown by industry
        - Industry concentration analysis
        
        Args:
            org_id: Organization ID
            year: Base year for analysis
            revenue_timing: 'cash' or 'revrec'
        
        Returns:
            Dict with pivot data, charts, and insights
        """
        cursor = self.db.cursor()
        
        # Get revenue and population by industry
        cursor.execute("""
            SELECT 
                COALESCE(fc.industry, '(blank)') as industry,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(DISTINCT fmb.population_count) as total_population,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue,
                AVG(fmb.pepm_rate) as avg_pepm
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            GROUP BY COALESCE(fc.industry, '(blank)')
            ORDER BY total_revenue DESC
        """, (revenue_timing, org_id, year))
        
        industries = []
        grand_total_revenue = 0
        grand_total_population = 0
        grand_total_clients = 0
        
        for row in cursor.fetchall():
            industry = row[0]
            client_count = row[1] or 0
            population = int(row[2]) if row[2] else 0
            revenue = float(row[3]) if row[3] else 0
            avg_pepm = float(row[4]) if row[4] else 0
            
            industries.append({
                'industry': industry,
                'client_count': client_count,
                'population': population,
                'revenue': revenue,
                'avg_pepm': avg_pepm
            })
            
            grand_total_revenue += revenue
            grand_total_clients += client_count
            grand_total_population += population
        
        # Calculate percentages
        for ind in industries:
            ind['pct_of_revenue'] = (ind['revenue'] / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
            ind['pct_of_population'] = (ind['population'] / grand_total_population * 100) if grand_total_population > 0 else 0
        
        # Get breakdown by tier for each industry
        cursor.execute("""
            SELECT 
                COALESCE(fc.industry, '(blank)') as industry,
                COALESCE(fc.tier, 'NA') as tier,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            GROUP BY COALESCE(fc.industry, '(blank)'), COALESCE(fc.tier, 'NA')
            ORDER BY industry, tier
        """, (revenue_timing, org_id, year))
        
        by_industry_tier = {}
        tiers = set()
        for row in cursor.fetchall():
            industry = row[0]
            tier = row[1]
            client_count = row[2] or 0
            revenue = float(row[3]) if row[3] else 0
            
            tiers.add(tier)
            if industry not in by_industry_tier:
                by_industry_tier[industry] = {}
            by_industry_tier[industry][tier] = {
                'client_count': client_count,
                'revenue': revenue
            }
        
        sorted_tiers = sorted(list(tiers))
        
        # Build stacked data for charts
        stacked_by_tier = []
        for ind in industries:
            industry = ind['industry']
            tier_row = {'industry': industry}
            for tier in sorted_tiers:
                tier_row[tier] = by_industry_tier.get(industry, {}).get(tier, {}).get('revenue', 0)
            stacked_by_tier.append(tier_row)
        
        # Calculate insights
        # Top industry
        top_industry = industries[0] if industries else None
        
        # Healthcare concentration (Healthcare + Healthcare PWR)
        healthcare_revenue = sum(
            ind['revenue'] for ind in industries 
            if 'healthcare' in ind['industry'].lower()
        )
        healthcare_pct = (healthcare_revenue / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
        
        # Top 3 concentration
        top_3_revenue = sum(ind['revenue'] for ind in industries[:3])
        top_3_pct = (top_3_revenue / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
        
        # Diversification index (Herfindahl-Hirschman Index)
        hhi = sum((ind['pct_of_revenue'] / 100) ** 2 for ind in industries) * 10000
        
        return {
            'year': year,
            'revenue_timing': revenue_timing,
            'industries': industries,
            'stacked_by_tier': stacked_by_tier,
            'tiers': sorted_tiers,
            'grand_totals': {
                'revenue': grand_total_revenue,
                'client_count': grand_total_clients,
                'population': grand_total_population
            },
            'insights': {
                'top_industry': top_industry['industry'] if top_industry else None,
                'top_industry_revenue': top_industry['revenue'] if top_industry else 0,
                'top_industry_pct': top_industry['pct_of_revenue'] if top_industry else 0,
                'healthcare_pct': healthcare_pct,
                'top_3_pct': top_3_pct,
                'hhi_index': hhi,
                'industry_count': len(industries)
            }
        }


    def get_nexus_state_pivot(
        self,
        org_id: int,
        year: int,
        revenue_timing: str = 'revrec'
    ) -> Dict:
        """
        Generate Nexus State Pivot table data.
        
        Replicates the Excel 'PIVOT Nexus State' tab which shows:
        - Revenue grouped by nexus state (US states/regions)
        - Helps understand geographic revenue distribution
        
        Args:
            org_id: Organization ID
            year: Base year for analysis
            revenue_timing: 'cash' or 'revrec'
        
        Returns:
            Dict with pivot data, charts, and insights
        """
        cursor = self.db.cursor()
        
        # Get revenue by nexus state
        # NOTE: Excel PIVOT Nexus State filters to only include clients with valid Tier (A, B, C, D)
        # This excludes clients with blank Tier or 'NA' Tier to match Excel exactly
        cursor.execute("""
            SELECT 
                COALESCE(fc.nexus_state, '(blank)') as nexus_state,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(fmb.population_count) / 12 as avg_population,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            AND fc.tier IN ('A', 'B', 'C', 'D')
            GROUP BY COALESCE(fc.nexus_state, '(blank)')
            ORDER BY total_revenue DESC
        """, (revenue_timing, org_id, year))
        
        states = []
        grand_total_revenue = 0
        grand_total_clients = 0
        grand_total_population = 0
        
        for row in cursor.fetchall():
            nexus_state = row[0]
            client_count = row[1] or 0
            population = int(row[2]) if row[2] else 0
            revenue = float(row[3]) if row[3] else 0
            
            states.append({
                'nexus_state': nexus_state,
                'client_count': client_count,
                'population': population,
                'revenue': revenue
            })
            
            grand_total_revenue += revenue
            grand_total_clients += client_count
            grand_total_population += population
        
        # Calculate percentages
        for state in states:
            state['pct_of_revenue'] = (state['revenue'] / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
        
        # Get breakdown by tier for each state
        # Also filter by valid Tier to match Excel PIVOT
        cursor.execute("""
            SELECT 
                COALESCE(fc.nexus_state, '(blank)') as nexus_state,
                fc.tier as tier,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(CASE WHEN %s = 'cash' THEN fmb.revenue_cash ELSE fmb.revenue_revrec END) as total_revenue
            FROM finance_clients fc
            JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
            WHERE fc.org_id = %s 
            AND fmb.billing_year = %s
            AND fc.tier IN ('A', 'B', 'C', 'D')
            GROUP BY COALESCE(fc.nexus_state, '(blank)'), fc.tier
            ORDER BY nexus_state, tier
        """, (revenue_timing, org_id, year))
        
        by_state_tier = {}
        tiers = set()
        for row in cursor.fetchall():
            nexus_state = row[0]
            tier = row[1]
            client_count = row[2] or 0
            revenue = float(row[3]) if row[3] else 0
            
            tiers.add(tier)
            if nexus_state not in by_state_tier:
                by_state_tier[nexus_state] = {}
            by_state_tier[nexus_state][tier] = {
                'client_count': client_count,
                'revenue': revenue
            }
        
        # Sort tiers
        tier_order = ['A', 'B', 'C', 'D', 'NA', '(blank)']
        sorted_tiers = sorted(tiers, key=lambda x: tier_order.index(x) if x in tier_order else 99)
        
        # Build stacked data for charts
        stacked_by_tier = []
        for state_data in states:
            ns = state_data['nexus_state']
            tier_row = {'nexus_state': ns}
            for tier in sorted_tiers:
                tier_row[tier] = by_state_tier.get(ns, {}).get(tier, {}).get('revenue', 0)
            stacked_by_tier.append(tier_row)
        
        # Calculate insights
        top_state = states[0] if states else None
        
        # Top 5 concentration
        top_5_revenue = sum(s['revenue'] for s in states[:5])
        top_5_pct = (top_5_revenue / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
        
        # Count non-blank states
        state_count = len([s for s in states if s['nexus_state'] != '(blank)'])
        
        return {
            'year': year,
            'revenue_timing': revenue_timing,
            'states': states,
            'stacked_by_tier': stacked_by_tier,
            'tiers': sorted_tiers,
            'grand_totals': {
                'revenue': grand_total_revenue,
                'client_count': grand_total_clients,
                'population': grand_total_population
            },
            'insights': {
                'top_state': top_state['nexus_state'] if top_state else None,
                'top_state_revenue': top_state['revenue'] if top_state else 0,
                'top_state_pct': top_state['pct_of_revenue'] if top_state else 0,
                'top_5_pct': top_5_pct,
                'state_count': state_count
            }
        }
