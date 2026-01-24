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
