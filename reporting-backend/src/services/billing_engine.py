"""
Billing Calculation Engine for VITAL WorkLife Finance Module

This engine replicates the logic from Nicole's billing spreadsheet:
- Cash: When money is actually received (based on billing terms)
- Revenue Recognition: When revenue is recognized (spread evenly across months)

Key formulas:
- RevRec: Monthly Revenue = Population × PEPM (spread evenly)
- Cash (annual): Full year billed in renewal month (Pop × PEPM × 12)
- Cash (quarterly): Quarterly billing (Pop × PEPM × 3)
- Cash (monthly): Same as RevRec (Pop × PEPM)
- Cash (semi): Semi-annual (Pop × PEPM × 6)
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
    
    def get_client_billing_data(self, client_id: int) -> Optional[Dict]:
        """Get all billing-related data for a client"""
        cursor = self.db.cursor()
        
        # Get client info
        cursor.execute("""
            SELECT fc.id, fc.billing_name, fc.tier, fc.industry, fc.session_product,
                   fph.population_count,
                   fcon.renewal_date, fcon.billing_frequency, fcon.contract_length_years,
                   fcon.months_2026, fcon.months_2027, fcon.months_2028
            FROM finance_clients fc
            LEFT JOIN finance_population_history fph ON fc.id = fph.client_id
            LEFT JOIN finance_contracts fcon ON fc.id = fcon.client_id
            WHERE fc.id = %s
            ORDER BY fph.effective_date DESC, fcon.id DESC
            LIMIT 1
        """, (client_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # Get rate schedules
        cursor.execute("""
            SELECT effective_date, pepm_rate
            FROM finance_rate_schedules frs
            JOIN finance_contracts fcon ON frs.contract_id = fcon.id
            WHERE fcon.client_id = %s
            ORDER BY effective_date
        """, (client_id,))
        
        rates = {str(r[0].year): float(r[1]) for r in cursor.fetchall()}
        
        return {
            'id': row[0],
            'billing_name': row[1],
            'tier': row[2],
            'industry': row[3],
            'session_product': row[4],
            'population': row[5] or 0,
            'renewal_date': row[6],
            'billing_frequency': row[7] or 'monthly',
            'contract_length': row[8],
            'months_2026': row[9] or 0,
            'months_2027': row[10] or 0,
            'months_2028': row[11] or 0,
            'rates': rates
        }
    
    def get_pepm_for_month(self, rates: Dict, year: int, month: int, renewal_date: date) -> float:
        """
        Get the correct PEPM rate for a given month.
        Before renewal date: use previous year's rate
        After renewal date: use current year's rate
        """
        current_date = date(year, month, 1)
        
        # If renewal is in this year and we're before renewal, use last year's rate
        if renewal_date and renewal_date.year == year:
            if current_date < renewal_date:
                return rates.get(str(year - 1), rates.get(str(year), 0))
        
        return rates.get(str(year), 0)
    
    def calculate_monthly_revenue_recognition(
        self, 
        population: int, 
        pepm: float
    ) -> Decimal:
        """
        Calculate Revenue Recognition for a month.
        Simple formula: Population × PEPM
        """
        return Decimal(str(population)) * Decimal(str(pepm))
    
    def calculate_monthly_cash(
        self,
        population: int,
        pepm: float,
        billing_frequency: str,
        month: int,
        renewal_month: int
    ) -> Decimal:
        """
        Calculate Cash billing for a month.
        
        - annual: Full year billed in renewal month only
        - semi: Half year billed in renewal month and 6 months later
        - qtly: Quarter billed in renewal month and every 3 months
        - monthly: Same as RevRec
        """
        multiplier = self.BILLING_MULTIPLIERS.get(billing_frequency.lower(), 1)
        base_amount = Decimal(str(population)) * Decimal(str(pepm))
        
        if billing_frequency.lower() == 'monthly':
            return base_amount
        
        if billing_frequency.lower() == 'annual':
            # Only bill in renewal month
            if month == renewal_month:
                return base_amount * 12
            return Decimal('0')
        
        if billing_frequency.lower() in ('semi', 'semiannual'):
            # Bill in renewal month and 6 months later
            semi_months = [renewal_month, (renewal_month + 5) % 12 + 1]
            if month in semi_months:
                return base_amount * 6
            return Decimal('0')
        
        if billing_frequency.lower() in ('qtly', 'quarterly'):
            # Bill every 3 months starting from renewal
            qtly_months = [
                renewal_month,
                (renewal_month + 2) % 12 + 1,
                (renewal_month + 5) % 12 + 1,
                (renewal_month + 8) % 12 + 1
            ]
            if month in qtly_months:
                return base_amount * 3
            return Decimal('0')
        
        return base_amount
    
    def calculate_year_billing(
        self,
        client_data: Dict,
        year: int,
        revenue_type: str = 'both'
    ) -> Dict:
        """
        Calculate full year billing for a client.
        
        Args:
            client_data: Client billing data from get_client_billing_data
            year: Year to calculate
            revenue_type: 'cash', 'revrec', or 'both'
        
        Returns:
            Dict with monthly breakdowns for cash and/or revrec
        """
        population = client_data['population']
        rates = client_data['rates']
        billing_frequency = client_data['billing_frequency']
        renewal_date = client_data['renewal_date']
        
        renewal_month = renewal_date.month if renewal_date else 1
        
        # Check if client is active in this year
        months_key = f'months_{year}'
        active_months = client_data.get(months_key, 12)
        
        result = {
            'client_id': client_data['id'],
            'billing_name': client_data['billing_name'],
            'year': year,
            'population': population,
            'billing_frequency': billing_frequency,
            'months': {}
        }
        
        total_cash = Decimal('0')
        total_revrec = Decimal('0')
        
        for month in range(1, 13):
            # Skip months where client is not active
            if active_months < 12:
                # Determine which months are active based on renewal
                if renewal_month <= month <= renewal_month + active_months - 1:
                    pass  # Active
                elif month < renewal_month and (month + 12 - renewal_month) < active_months:
                    pass  # Active (wrapped around year)
                else:
                    result['months'][month] = {'cash': 0, 'revrec': 0, 'pepm': 0}
                    continue
            
            pepm = self.get_pepm_for_month(rates, year, month, renewal_date)
            
            month_data = {'pepm': pepm}
            
            if revenue_type in ('cash', 'both'):
                cash = self.calculate_monthly_cash(
                    population, pepm, billing_frequency, month, renewal_month
                )
                month_data['cash'] = float(cash)
                total_cash += cash
            
            if revenue_type in ('revrec', 'both'):
                revrec = self.calculate_monthly_revenue_recognition(population, pepm)
                month_data['revrec'] = float(revrec)
                total_revrec += revrec
            
            result['months'][month] = month_data
        
        result['total_cash'] = float(total_cash)
        result['total_revrec'] = float(total_revrec)
        
        return result
    
    def calculate_all_clients_billing(
        self,
        org_id: int,
        year: int
    ) -> List[Dict]:
        """Calculate billing for all clients in an organization"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT id FROM finance_clients WHERE org_id = %s
        """, (org_id,))
        
        results = []
        for (client_id,) in cursor.fetchall():
            client_data = self.get_client_billing_data(client_id)
            if client_data:
                billing = self.calculate_year_billing(client_data, year)
                results.append(billing)
        
        return results
    
    def get_billing_summary(
        self,
        org_id: int,
        year: int,
        group_by: str = 'tier'
    ) -> Dict:
        """
        Get billing summary grouped by a dimension.
        
        Args:
            org_id: Organization ID
            year: Year to summarize
            group_by: 'tier', 'industry', 'session_product', or 'month'
        """
        all_billing = self.calculate_all_clients_billing(org_id, year)
        
        summary = {}
        
        for client in all_billing:
            client_data = self.get_client_billing_data(client['client_id'])
            if not client_data:
                continue
            
            if group_by == 'month':
                for month, values in client['months'].items():
                    if month not in summary:
                        summary[month] = {'cash': 0, 'revrec': 0, 'count': 0}
                    summary[month]['cash'] += values.get('cash', 0)
                    summary[month]['revrec'] += values.get('revrec', 0)
                    summary[month]['count'] += 1
            else:
                key = client_data.get(group_by, 'Unknown')
                if key not in summary:
                    summary[key] = {
                        'cash': 0, 
                        'revrec': 0, 
                        'count': 0, 
                        'population': 0
                    }
                summary[key]['cash'] += client['total_cash']
                summary[key]['revrec'] += client['total_revrec']
                summary[key]['count'] += 1
                summary[key]['population'] += client['population']
        
        return summary
    
    def generate_billing_report(
        self,
        org_id: int,
        year: int
    ) -> Dict:
        """
        Generate a comprehensive billing report similar to the spreadsheet.
        """
        all_billing = self.calculate_all_clients_billing(org_id, year)
        
        # Monthly totals
        monthly_cash = {m: 0 for m in range(1, 13)}
        monthly_revrec = {m: 0 for m in range(1, 13)}
        
        # By tier
        by_tier = {}
        
        # By industry
        by_industry = {}
        
        for client in all_billing:
            client_data = self.get_client_billing_data(client['client_id'])
            if not client_data:
                continue
            
            tier = client_data.get('tier', 'Unknown')
            industry = client_data.get('industry', 'Unknown')
            
            # Monthly totals
            for month, values in client['months'].items():
                monthly_cash[month] += values.get('cash', 0)
                monthly_revrec[month] += values.get('revrec', 0)
            
            # By tier
            if tier not in by_tier:
                by_tier[tier] = {'cash': 0, 'revrec': 0, 'count': 0, 'population': 0}
            by_tier[tier]['cash'] += client['total_cash']
            by_tier[tier]['revrec'] += client['total_revrec']
            by_tier[tier]['count'] += 1
            by_tier[tier]['population'] += client['population']
            
            # By industry
            if industry not in by_industry:
                by_industry[industry] = {'cash': 0, 'revrec': 0, 'count': 0}
            by_industry[industry]['cash'] += client['total_cash']
            by_industry[industry]['revrec'] += client['total_revrec']
            by_industry[industry]['count'] += 1
        
        return {
            'year': year,
            'total_cash': sum(monthly_cash.values()),
            'total_revrec': sum(monthly_revrec.values()),
            'monthly_cash': monthly_cash,
            'monthly_revrec': monthly_revrec,
            'by_tier': by_tier,
            'by_industry': by_industry,
            'client_count': len(all_billing)
        }
