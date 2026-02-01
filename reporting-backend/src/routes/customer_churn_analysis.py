"""
Customer Churn Analysis API
Analyzes customer activity patterns to identify churned customers and provide AI-powered insights
For Bennett organization
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
import os
from openai import OpenAI
from src.services.azure_sql_service import AzureSQLService
from src.utils.tenant_utils import get_tenant_schema

logger = logging.getLogger(__name__)

customer_churn_bp = Blueprint('customer_churn', __name__)


@customer_churn_bp.route('/api/customer-churn/analysis', methods=['GET'])
@jwt_required()
def get_churn_analysis():
    """
    Get comprehensive customer churn analysis
    Returns churned customers, their history, and patterns
    """
    try:
        # Get tenant schema (should be ben002 for Bennett)
        try:
            schema = get_tenant_schema()
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        db = AzureSQLService()
        
        # Get the analysis period (default: compare last 3 months vs previous 3 months)
        months_back = int(request.args.get('months', 3))
        
        # Calculate date ranges
        today = datetime.now()
        current_period_start = today - relativedelta(months=months_back)
        previous_period_start = current_period_start - relativedelta(months=months_back)
        previous_period_end = current_period_start - timedelta(days=1)
        
        # Query to find customers who were active in previous period but not in current period
        churn_query = f"""
        WITH CustomerNormalized AS (
            SELECT 
                InvoiceNo,
                InvoiceDate,
                CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END as CustomerName,
                TotalSale
            FROM {schema}.InvoiceReg
            WHERE BillToName IS NOT NULL
            AND BillToName != ''
            AND BillToName NOT LIKE '%Wells Fargo%'
            AND BillToName NOT LIKE '%Maintenance contract%'
            AND BillToName NOT LIKE '%Rental Fleet%'
        ),
        PreviousPeriodCustomers AS (
            SELECT DISTINCT CustomerName
            FROM CustomerNormalized
            WHERE InvoiceDate >= '{previous_period_start.strftime('%Y-%m-%d')}'
            AND InvoiceDate < '{current_period_start.strftime('%Y-%m-%d')}'
        ),
        CurrentPeriodCustomers AS (
            SELECT DISTINCT CustomerName
            FROM CustomerNormalized
            WHERE InvoiceDate >= '{current_period_start.strftime('%Y-%m-%d')}'
        ),
        ChurnedCustomers AS (
            SELECT p.CustomerName
            FROM PreviousPeriodCustomers p
            LEFT JOIN CurrentPeriodCustomers c ON p.CustomerName = c.CustomerName
            WHERE c.CustomerName IS NULL
        )
        SELECT 
            ch.CustomerName,
            COUNT(DISTINCT cn.InvoiceNo) as total_invoices,
            SUM(cn.TotalSale) as total_revenue,
            MIN(cn.InvoiceDate) as first_invoice,
            MAX(cn.InvoiceDate) as last_invoice,
            DATEDIFF(day, MAX(cn.InvoiceDate), GETDATE()) as days_since_last_invoice
        FROM ChurnedCustomers ch
        JOIN CustomerNormalized cn ON ch.CustomerName = cn.CustomerName
        GROUP BY ch.CustomerName
        ORDER BY total_revenue DESC
        """
        
        churned_customers = db.execute_query(churn_query)
        
        # Get detailed history for churned customers
        churned_list = []
        if churned_customers:
            for customer in churned_customers[:50]:  # Limit to top 50 for performance
                customer_name = customer['CustomerName']
                
                # Get work order breakdown by type
                wo_query = f"""
                SELECT 
                    WOType,
                    COUNT(*) as wo_count,
                    SUM(ISNULL(TotalInvoiced, 0)) as wo_revenue
                FROM {schema}.WO
                WHERE (BillTo LIKE '%{customer_name.replace("'", "''")}%' 
                       OR ShipTo LIKE '%{customer_name.replace("'", "''")}%')
                GROUP BY WOType
                """
                wo_breakdown = db.execute_query(wo_query)
                
                # Get monthly revenue trend for this customer (last 12 months before churn)
                trend_query = f"""
                WITH CustomerNormalized AS (
                    SELECT 
                        InvoiceDate,
                        CASE 
                            WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                            WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                            ELSE BillToName
                        END as CustomerName,
                        TotalSale
                    FROM {schema}.InvoiceReg
                )
                SELECT 
                    YEAR(InvoiceDate) as year,
                    MONTH(InvoiceDate) as month,
                    SUM(TotalSale) as monthly_revenue,
                    COUNT(*) as invoice_count
                FROM CustomerNormalized
                WHERE CustomerName = '{customer_name.replace("'", "''")}'
                AND InvoiceDate >= DATEADD(month, -12, '{customer['last_invoice'].strftime('%Y-%m-%d')}')
                GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
                ORDER BY year, month
                """
                revenue_trend = db.execute_query(trend_query)
                
                churned_list.append({
                    'customer_name': customer_name,
                    'total_invoices': int(customer['total_invoices']),
                    'total_revenue': float(customer['total_revenue'] or 0),
                    'first_invoice': customer['first_invoice'].strftime('%Y-%m-%d') if customer['first_invoice'] else None,
                    'last_invoice': customer['last_invoice'].strftime('%Y-%m-%d') if customer['last_invoice'] else None,
                    'days_since_last_invoice': int(customer['days_since_last_invoice'] or 0),
                    'work_order_breakdown': [
                        {
                            'type': wo['WOType'],
                            'count': int(wo['wo_count']),
                            'revenue': float(wo['wo_revenue'] or 0)
                        } for wo in (wo_breakdown or [])
                    ],
                    'revenue_trend': [
                        {
                            'month': f"{row['year']}-{row['month']:02d}",
                            'revenue': float(row['monthly_revenue'] or 0),
                            'invoices': int(row['invoice_count'])
                        } for row in (revenue_trend or [])
                    ]
                })
        
        # Get summary statistics
        total_churned = len(churned_list)
        total_lost_revenue = sum(c['total_revenue'] for c in churned_list)
        avg_customer_value = total_lost_revenue / total_churned if total_churned > 0 else 0
        
        # Get current active customer count for comparison
        active_query = f"""
        SELECT COUNT(DISTINCT CASE 
            WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
            WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
            ELSE BillToName
        END) as active_count
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '{current_period_start.strftime('%Y-%m-%d')}'
        AND BillToName IS NOT NULL
        AND BillToName != ''
        AND BillToName NOT LIKE '%Wells Fargo%'
        AND BillToName NOT LIKE '%Maintenance contract%'
        AND BillToName NOT LIKE '%Rental Fleet%'
        """
        active_result = db.execute_query(active_query)
        current_active = active_result[0]['active_count'] if active_result else 0
        
        # Calculate churn rate
        previous_active = current_active + total_churned
        churn_rate = (total_churned / previous_active * 100) if previous_active > 0 else 0
        
        response = {
            'summary': {
                'total_churned_customers': total_churned,
                'total_lost_revenue': round(total_lost_revenue, 2),
                'average_customer_value': round(avg_customer_value, 2),
                'current_active_customers': current_active,
                'churn_rate_percent': round(churn_rate, 2),
                'analysis_period': {
                    'current_start': current_period_start.strftime('%Y-%m-%d'),
                    'current_end': today.strftime('%Y-%m-%d'),
                    'previous_start': previous_period_start.strftime('%Y-%m-%d'),
                    'previous_end': previous_period_end.strftime('%Y-%m-%d')
                }
            },
            'churned_customers': churned_list,
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Churn analysis failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@customer_churn_bp.route('/api/customer-churn/ai-insights', methods=['POST'])
@jwt_required()
def get_ai_insights():
    """
    Generate AI-powered insights from churn data
    Uses Claude to analyze patterns and suggest actions
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Prepare the analysis prompt
        summary = data.get('summary', {})
        churned_customers = data.get('churned_customers', [])
        
        # Build customer profiles for analysis
        customer_profiles = []
        for c in churned_customers[:20]:  # Limit to top 20 for API efficiency
            wo_types = ', '.join([f"{wo['type']} (${wo['revenue']:,.0f})" for wo in c.get('work_order_breakdown', [])])
            profile = f"- {c['customer_name']}: ${c['total_revenue']:,.0f} lifetime revenue, {c['total_invoices']} invoices, last active {c['last_invoice']}, work types: {wo_types or 'N/A'}"
            customer_profiles.append(profile)
        
        prompt = f"""Analyze this customer churn data for Bennett Equipment, a forklift and material handling equipment dealership, and provide actionable insights.

## Summary Statistics
- Total Churned Customers: {summary.get('total_churned_customers', 0)}
- Total Lost Revenue: ${summary.get('total_lost_revenue', 0):,.2f}
- Average Customer Value: ${summary.get('average_customer_value', 0):,.2f}
- Current Active Customers: {summary.get('current_active_customers', 0)}
- Churn Rate: {summary.get('churn_rate_percent', 0):.1f}%
- Analysis Period: {summary.get('analysis_period', {}).get('previous_start', 'N/A')} to {summary.get('analysis_period', {}).get('current_end', 'N/A')}

## Churned Customer Profiles (Top by Revenue)
{chr(10).join(customer_profiles)}

Work Order Types Key:
- S = Service/Repair
- PM = Preventive Maintenance
- R = Rental
- P = Parts
- I = Internal

Please provide:
1. **Key Trends**: What patterns do you see in the churned customers? (e.g., customer size, service types, timing)
2. **Risk Factors**: What characteristics might indicate a customer is at risk of churning?
3. **High-Priority Win-Back Targets**: Which 3-5 customers should be prioritized for outreach and why?
4. **Recommended Actions**: Specific steps Bennett should take to reduce churn and win back customers
5. **Questions to Investigate**: What additional data would help understand the churn better?

Format your response in clear sections with actionable recommendations."""

        # Call AI API
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a business analyst specializing in customer retention for equipment dealerships. Provide clear, actionable insights based on data analysis. Be specific about which customers to contact and what actions to take."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        ai_analysis = response.choices[0].message.content
        
        return jsonify({
            'insights': ai_analysis,
            'generated_at': datetime.now().isoformat(),
            'model': 'gpt-4.1-mini'
        })
        
    except Exception as e:
        logger.error(f"AI insights generation failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@customer_churn_bp.route('/api/customer-churn/at-risk', methods=['GET'])
@jwt_required()
def get_at_risk_customers():
    """
    Identify customers who are at risk of churning based on declining activity
    """
    try:
        # Get tenant schema
        try:
            schema = get_tenant_schema()
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        db = AzureSQLService()
        
        # Find customers with declining activity (active in past but reduced recent activity)
        at_risk_query = f"""
        WITH CustomerNormalized AS (
            SELECT 
                InvoiceDate,
                CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END as CustomerName,
                TotalSale
            FROM {schema}.InvoiceReg
            WHERE BillToName IS NOT NULL
            AND BillToName != ''
            AND BillToName NOT LIKE '%Wells Fargo%'
            AND BillToName NOT LIKE '%Maintenance contract%'
            AND BillToName NOT LIKE '%Rental Fleet%'
        ),
        RecentActivity AS (
            SELECT 
                CustomerName,
                SUM(TotalSale) as recent_revenue,
                COUNT(*) as recent_invoices,
                MAX(InvoiceDate) as last_invoice
            FROM CustomerNormalized
            WHERE InvoiceDate >= DATEADD(month, -3, GETDATE())
            GROUP BY CustomerName
        ),
        PreviousActivity AS (
            SELECT 
                CustomerName,
                SUM(TotalSale) as previous_revenue,
                COUNT(*) as previous_invoices
            FROM CustomerNormalized
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            AND InvoiceDate < DATEADD(month, -3, GETDATE())
            GROUP BY CustomerName
        )
        SELECT 
            COALESCE(r.CustomerName, p.CustomerName) as CustomerName,
            ISNULL(r.recent_revenue, 0) as recent_revenue,
            ISNULL(r.recent_invoices, 0) as recent_invoices,
            ISNULL(p.previous_revenue, 0) as previous_revenue,
            ISNULL(p.previous_invoices, 0) as previous_invoices,
            r.last_invoice,
            CASE 
                WHEN p.previous_revenue > 0 AND r.recent_revenue IS NULL THEN -100
                WHEN p.previous_revenue > 0 THEN ((ISNULL(r.recent_revenue, 0) - p.previous_revenue) / p.previous_revenue * 100)
                ELSE 0
            END as revenue_change_percent,
            DATEDIFF(day, ISNULL(r.last_invoice, DATEADD(month, -3, GETDATE())), GETDATE()) as days_since_activity
        FROM PreviousActivity p
        LEFT JOIN RecentActivity r ON p.CustomerName = r.CustomerName
        WHERE p.previous_revenue > 1000  -- Only consider customers with meaningful previous activity
        AND (r.recent_revenue IS NULL OR r.recent_revenue < p.previous_revenue * 0.5)  -- Revenue dropped by 50% or more
        ORDER BY p.previous_revenue DESC
        """
        
        at_risk_customers = db.execute_query(at_risk_query)
        
        at_risk_list = []
        if at_risk_customers:
            for customer in at_risk_customers:
                at_risk_list.append({
                    'customer_name': customer['CustomerName'],
                    'recent_revenue': float(customer['recent_revenue'] or 0),
                    'recent_invoices': int(customer['recent_invoices'] or 0),
                    'previous_revenue': float(customer['previous_revenue'] or 0),
                    'previous_invoices': int(customer['previous_invoices'] or 0),
                    'revenue_change_percent': round(float(customer['revenue_change_percent'] or 0), 1),
                    'last_invoice': customer['last_invoice'].strftime('%Y-%m-%d') if customer['last_invoice'] else None,
                    'days_since_activity': int(customer['days_since_activity'] or 0),
                    'risk_level': 'High' if customer['revenue_change_percent'] <= -75 else 'Medium'
                })
        
        return jsonify({
            'at_risk_customers': at_risk_list,
            'total_at_risk': len(at_risk_list),
            'total_at_risk_previous_revenue': sum(c['previous_revenue'] for c in at_risk_list),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"At-risk analysis failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
