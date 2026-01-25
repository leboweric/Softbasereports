"""
VITAL WorkLife Financial Dashboard API Routes
Provides aggregated financial metrics for executive dashboard
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from decimal import Decimal
import json

vital_financial_dashboard_bp = Blueprint('vital_financial_dashboard', __name__)

# Import services
from src.services.postgres_service import get_postgres_db
from src.services.cache_service import CacheService

cache = CacheService()

def get_db():
    """Get PostgreSQL database connection"""
    return get_postgres_db()


@vital_financial_dashboard_bp.route('/api/vital/financial-dashboard/overview', methods=['GET'])
@jwt_required()
def get_financial_overview():
    """Get comprehensive financial overview for executive dashboard"""
    try:
        # Check cache first
        cache_key = f"financial_overview_{get_jwt_identity()}"
        cached = cache.get(cache_key)
        if cached and not request.args.get('refresh'):
            return jsonify(cached)
        
        db = get_db()
        current_user = get_jwt_identity()
        
        # Get user's org_id
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE id = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # 1. Total Book of Business (Annual Revenue)
        book_query = """
            SELECT 
                COUNT(DISTINCT fc.id) as total_clients,
                SUM(COALESCE(fph.population_count, 0)) as total_population,
                SUM(COALESCE(fph.population_count, 0) * COALESCE(
                    (SELECT pepm_rate FROM finance_rate_schedules frs
                     JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                     WHERE fcon.client_id = fc.id AND frs.effective_date <= CURRENT_DATE
                     ORDER BY frs.effective_date DESC LIMIT 1), 0
                )) as monthly_revenue
            FROM finance_clients fc
            LEFT JOIN LATERAL (
                SELECT population_count FROM finance_population_history
                WHERE client_id = fc.id ORDER BY effective_date DESC LIMIT 1
            ) fph ON true
            WHERE fc.org_id = %s AND fc.status = 'active'
        """
        book_result = db.execute_query(book_query, (org_id,))
        book_data = book_result[0] if book_result else {}
        
        monthly_revenue = float(book_data.get('monthly_revenue') or 0)
        arr = monthly_revenue * 12
        
        # 2. Revenue Trend (Last 12 months)
        trend_query = """
            SELECT 
                billing_year,
                billing_month,
                SUM(revenue_revrec) as revenue,
                SUM(revenue_cash) as cash_revenue,
                SUM(population_count) as population
            FROM finance_monthly_billing fmb
            JOIN finance_clients fc ON fmb.client_id = fc.id
            WHERE fc.org_id = %s
              AND (billing_year = %s OR billing_year = %s)
            GROUP BY billing_year, billing_month
            ORDER BY billing_year, billing_month
        """
        trend_result = db.execute_query(trend_query, (org_id, current_year - 1, current_year))
        
        # 3. Revenue by Service Line (Tier)
        tier_query = """
            SELECT 
                COALESCE(fc.tier, 'Unassigned') as tier,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(COALESCE(fph.population_count, 0)) as population,
                SUM(COALESCE(fph.population_count, 0) * COALESCE(
                    (SELECT pepm_rate FROM finance_rate_schedules frs
                     JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                     WHERE fcon.client_id = fc.id AND frs.effective_date <= CURRENT_DATE
                     ORDER BY frs.effective_date DESC LIMIT 1), 0
                ) * 12) as annual_revenue
            FROM finance_clients fc
            LEFT JOIN LATERAL (
                SELECT population_count FROM finance_population_history
                WHERE client_id = fc.id ORDER BY effective_date DESC LIMIT 1
            ) fph ON true
            WHERE fc.org_id = %s AND fc.status = 'active'
            GROUP BY fc.tier
            ORDER BY annual_revenue DESC
        """
        tier_result = db.execute_query(tier_query, (org_id,))
        
        # 4. Revenue by Solution Type
        solution_query = """
            SELECT 
                COALESCE(fc.session_product, fc.solution_type, 'Unassigned') as solution,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(COALESCE(fph.population_count, 0) * COALESCE(
                    (SELECT pepm_rate FROM finance_rate_schedules frs
                     JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                     WHERE fcon.client_id = fc.id AND frs.effective_date <= CURRENT_DATE
                     ORDER BY frs.effective_date DESC LIMIT 1), 0
                ) * 12) as annual_revenue
            FROM finance_clients fc
            LEFT JOIN LATERAL (
                SELECT population_count FROM finance_population_history
                WHERE client_id = fc.id ORDER BY effective_date DESC LIMIT 1
            ) fph ON true
            WHERE fc.org_id = %s AND fc.status = 'active'
            GROUP BY COALESCE(fc.session_product, fc.solution_type, 'Unassigned')
            ORDER BY annual_revenue DESC
        """
        solution_result = db.execute_query(solution_query, (org_id,))
        
        # 5. At-Risk Revenue
        at_risk_query = """
            SELECT 
                COUNT(DISTINCT fc.id) as at_risk_clients,
                SUM(COALESCE(fph.population_count, 0) * COALESCE(
                    (SELECT pepm_rate FROM finance_rate_schedules frs
                     JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                     WHERE fcon.client_id = fc.id AND frs.effective_date <= CURRENT_DATE
                     ORDER BY frs.effective_date DESC LIMIT 1), 0
                ) * 12) as at_risk_arr
            FROM finance_clients fc
            LEFT JOIN LATERAL (
                SELECT population_count FROM finance_population_history
                WHERE client_id = fc.id ORDER BY effective_date DESC LIMIT 1
            ) fph ON true
            WHERE fc.org_id = %s 
              AND fc.status = 'at_risk'
        """
        at_risk_result = db.execute_query(at_risk_query, (org_id,))
        at_risk_data = at_risk_result[0] if at_risk_result else {}
        
        # 6. Upcoming Renewals (Next 90 days)
        renewals_query = """
            SELECT 
                COUNT(DISTINCT fc.id) as renewal_count,
                SUM(COALESCE(fph.population_count, 0) * COALESCE(
                    (SELECT pepm_rate FROM finance_rate_schedules frs
                     JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                     WHERE fcon.client_id = fc.id AND frs.effective_date <= CURRENT_DATE
                     ORDER BY frs.effective_date DESC LIMIT 1), 0
                ) * 12) as renewal_arr
            FROM finance_clients fc
            LEFT JOIN LATERAL (
                SELECT population_count FROM finance_population_history
                WHERE client_id = fc.id ORDER BY effective_date DESC LIMIT 1
            ) fph ON true
            WHERE fc.org_id = %s 
              AND fc.renewal_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
        """
        renewals_result = db.execute_query(renewals_query, (org_id,))
        renewals_data = renewals_result[0] if renewals_result else {}
        
        # 7. Top 10 Clients by Revenue
        top_clients_query = """
            SELECT 
                fc.billing_name,
                fc.tier,
                fc.industry,
                COALESCE(fph.population_count, 0) as population,
                COALESCE(
                    (SELECT pepm_rate FROM finance_rate_schedules frs
                     JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                     WHERE fcon.client_id = fc.id AND frs.effective_date <= CURRENT_DATE
                     ORDER BY frs.effective_date DESC LIMIT 1), 0
                ) as pepm_rate,
                COALESCE(fph.population_count, 0) * COALESCE(
                    (SELECT pepm_rate FROM finance_rate_schedules frs
                     JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                     WHERE fcon.client_id = fc.id AND frs.effective_date <= CURRENT_DATE
                     ORDER BY frs.effective_date DESC LIMIT 1), 0
                ) * 12 as annual_revenue
            FROM finance_clients fc
            LEFT JOIN LATERAL (
                SELECT population_count FROM finance_population_history
                WHERE client_id = fc.id ORDER BY effective_date DESC LIMIT 1
            ) fph ON true
            WHERE fc.org_id = %s AND fc.status = 'active'
            ORDER BY annual_revenue DESC
            LIMIT 10
        """
        top_clients = db.execute_query(top_clients_query, (org_id,))
        
        # 8. YoY Growth Calculation
        last_year_query = """
            SELECT SUM(revenue_revrec) as total
            FROM finance_monthly_billing fmb
            JOIN finance_clients fc ON fmb.client_id = fc.id
            WHERE fc.org_id = %s AND billing_year = %s
        """
        last_year_result = db.execute_query(last_year_query, (org_id, current_year - 1))
        last_year_revenue = float(last_year_result[0]['total'] or 0) if last_year_result else 0
        
        this_year_result = db.execute_query(last_year_query, (org_id, current_year))
        this_year_revenue = float(this_year_result[0]['total'] or 0) if this_year_result else 0
        
        yoy_growth = ((this_year_revenue - last_year_revenue) / last_year_revenue * 100) if last_year_revenue > 0 else 0
        
        # 9. Revenue by Industry
        industry_query = """
            SELECT 
                COALESCE(fc.industry, 'Unassigned') as industry,
                COUNT(DISTINCT fc.id) as client_count,
                SUM(COALESCE(fph.population_count, 0) * COALESCE(
                    (SELECT pepm_rate FROM finance_rate_schedules frs
                     JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                     WHERE fcon.client_id = fc.id AND frs.effective_date <= CURRENT_DATE
                     ORDER BY frs.effective_date DESC LIMIT 1), 0
                ) * 12) as annual_revenue
            FROM finance_clients fc
            LEFT JOIN LATERAL (
                SELECT population_count FROM finance_population_history
                WHERE client_id = fc.id ORDER BY effective_date DESC LIMIT 1
            ) fph ON true
            WHERE fc.org_id = %s AND fc.status = 'active'
            GROUP BY fc.industry
            ORDER BY annual_revenue DESC
            LIMIT 10
        """
        industry_result = db.execute_query(industry_query, (org_id,))
        
        response = {
            'success': True,
            'overview': {
                'total_clients': int(book_data.get('total_clients') or 0),
                'total_population': int(book_data.get('total_population') or 0),
                'mrr': monthly_revenue,
                'arr': arr,
                'yoy_growth': round(yoy_growth, 1),
                'at_risk_clients': int(at_risk_data.get('at_risk_clients') or 0),
                'at_risk_arr': float(at_risk_data.get('at_risk_arr') or 0),
                'renewal_count': int(renewals_data.get('renewal_count') or 0),
                'renewal_arr': float(renewals_data.get('renewal_arr') or 0)
            },
            'revenue_trend': [
                {
                    'month': f"{r['billing_year']}-{str(r['billing_month']).zfill(2)}",
                    'revenue': float(r['revenue'] or 0),
                    'cash': float(r['cash_revenue'] or 0),
                    'population': int(r['population'] or 0)
                } for r in trend_result
            ],
            'by_tier': [
                {
                    'tier': r['tier'],
                    'clients': int(r['client_count'] or 0),
                    'population': int(r['population'] or 0),
                    'arr': float(r['annual_revenue'] or 0)
                } for r in tier_result
            ],
            'by_solution': [
                {
                    'solution': r['solution'],
                    'clients': int(r['client_count'] or 0),
                    'arr': float(r['annual_revenue'] or 0)
                } for r in solution_result
            ],
            'by_industry': [
                {
                    'industry': r['industry'],
                    'clients': int(r['client_count'] or 0),
                    'arr': float(r['annual_revenue'] or 0)
                } for r in industry_result
            ],
            'top_clients': [
                {
                    'name': r['billing_name'],
                    'tier': r['tier'],
                    'industry': r['industry'],
                    'population': int(r['population'] or 0),
                    'pepm': float(r['pepm_rate'] or 0),
                    'arr': float(r['annual_revenue'] or 0)
                } for r in top_clients
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, response, ttl=300)
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@vital_financial_dashboard_bp.route('/api/vital/financial-dashboard/budget-vs-actual', methods=['GET'])
@jwt_required()
def get_budget_vs_actual():
    """Get budget vs actual revenue comparison (placeholder for budget data)"""
    try:
        db = get_db()
        current_user = get_jwt_identity()
        
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE id = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        current_year = datetime.now().year
        
        # Get actual revenue by month
        actual_query = """
            SELECT 
                billing_month,
                SUM(revenue_revrec) as actual_revenue
            FROM finance_monthly_billing fmb
            JOIN finance_clients fc ON fmb.client_id = fc.id
            WHERE fc.org_id = %s AND billing_year = %s
            GROUP BY billing_month
            ORDER BY billing_month
        """
        actual_result = db.execute_query(actual_query, (org_id, current_year))
        
        # For now, budget is estimated as 10% growth over last year's actuals
        last_year_query = """
            SELECT 
                billing_month,
                SUM(revenue_revrec) * 1.10 as budget_revenue
            FROM finance_monthly_billing fmb
            JOIN finance_clients fc ON fmb.client_id = fc.id
            WHERE fc.org_id = %s AND billing_year = %s
            GROUP BY billing_month
            ORDER BY billing_month
        """
        budget_result = db.execute_query(last_year_query, (org_id, current_year - 1))
        
        # Combine into monthly comparison
        budget_map = {r['billing_month']: float(r['budget_revenue'] or 0) for r in budget_result}
        
        comparison = []
        for r in actual_result:
            month = r['billing_month']
            actual = float(r['actual_revenue'] or 0)
            budget = budget_map.get(month, actual)  # Default to actual if no budget
            variance = actual - budget
            variance_pct = (variance / budget * 100) if budget > 0 else 0
            
            comparison.append({
                'month': month,
                'actual': actual,
                'budget': budget,
                'variance': variance,
                'variance_pct': round(variance_pct, 1)
            })
        
        return jsonify({
            'success': True,
            'year': current_year,
            'comparison': comparison,
            'note': 'Budget is estimated as 10% growth over prior year. Upload actual budget for accurate comparison.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_financial_dashboard_bp.route('/api/vital/financial-dashboard/client-concentration', methods=['GET'])
@jwt_required()
def get_client_concentration():
    """Get client revenue concentration analysis"""
    try:
        db = get_db()
        current_user = get_jwt_identity()
        
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE id = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        # Get all clients with revenue, ordered by revenue
        query = """
            SELECT 
                fc.billing_name,
                COALESCE(fph.population_count, 0) * COALESCE(
                    (SELECT pepm_rate FROM finance_rate_schedules frs
                     JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                     WHERE fcon.client_id = fc.id AND frs.effective_date <= CURRENT_DATE
                     ORDER BY frs.effective_date DESC LIMIT 1), 0
                ) * 12 as annual_revenue
            FROM finance_clients fc
            LEFT JOIN LATERAL (
                SELECT population_count FROM finance_population_history
                WHERE client_id = fc.id ORDER BY effective_date DESC LIMIT 1
            ) fph ON true
            WHERE fc.org_id = %s AND fc.status = 'active'
            ORDER BY annual_revenue DESC
        """
        clients = db.execute_query(query, (org_id,))
        
        total_revenue = sum(float(c['annual_revenue'] or 0) for c in clients)
        
        # Calculate concentration metrics
        cumulative = 0
        top_10_revenue = 0
        top_20_revenue = 0
        
        for i, c in enumerate(clients):
            rev = float(c['annual_revenue'] or 0)
            cumulative += rev
            if i < 10:
                top_10_revenue += rev
            if i < 20:
                top_20_revenue += rev
        
        return jsonify({
            'success': True,
            'total_clients': len(clients),
            'total_revenue': total_revenue,
            'top_10_revenue': top_10_revenue,
            'top_10_pct': round(top_10_revenue / total_revenue * 100, 1) if total_revenue > 0 else 0,
            'top_20_revenue': top_20_revenue,
            'top_20_pct': round(top_20_revenue / total_revenue * 100, 1) if total_revenue > 0 else 0,
            'avg_revenue_per_client': round(total_revenue / len(clients), 2) if clients else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
