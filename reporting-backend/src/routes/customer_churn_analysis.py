"""
Customer Churn Analysis API
Analyzes customer activity patterns to identify churned customers and provide AI-powered insights
Multi-tenant: uses the current user's organization for data isolation

Now uses pre-computed mart_customer_activity table for fast queries (ETL runs nightly)
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
import os
from openai import OpenAI
from src.services.postgres_service import PostgreSQLService
from src.utils.tenant_utils import get_tenant_schema
from src.models.user import User

logger = logging.getLogger(__name__)

customer_churn_bp = Blueprint('customer_churn', __name__)


def get_current_org_id():
    """Get the organization ID for the current authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if user and user.organization_id:
            return user.organization_id
        return None
    except Exception as e:
        logger.error(f"Error getting org_id: {e}")
        return None


def get_current_org_name():
    """Get the organization name for the current authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if user and user.organization:
            return user.organization.name
        return 'the company'
    except Exception:
        return 'the company'


def get_work_order_breakdown(db, schema, customer_name):
    """Get work order breakdown by type for a customer from Azure SQL"""
    try:
        wo_query = f"""
        SELECT 
            Type,
            COUNT(*) as wo_count
        FROM {schema}.WO
        WHERE (BillTo LIKE '%{customer_name.replace("'", "''")}%' 
               OR ShipTo LIKE '%{customer_name.replace("'", "''")}%')
        GROUP BY Type
        """
        return db.execute_query(wo_query) or []
    except Exception as e:
        logger.warning(f"Could not get WO breakdown for {customer_name}: {e}")
        return []


@customer_churn_bp.route('/api/customer-churn/analysis', methods=['GET'])
@jwt_required()
def get_churn_analysis():
    """
    Get comprehensive customer churn analysis
    Returns churned customers from pre-computed mart table
    
    Churn criteria: No invoices in last 90 days but had invoices in days 91-180
    """
    try:
        org_id = get_current_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        
        pg = PostgreSQLService()
        
        # Get churned customers from mart table
        churned_query = """
        SELECT 
            customer_name,
            bill_to,
            recent_invoice_count,
            recent_revenue,
            recent_service_revenue,
            recent_parts_revenue,
            recent_rental_revenue,
            previous_invoice_count,
            previous_revenue,
            previous_service_revenue,
            previous_parts_revenue,
            previous_rental_revenue,
            lifetime_invoice_count,
            lifetime_revenue,
            first_invoice_date,
            last_invoice_date,
            days_since_last_invoice,
            revenue_change_percent,
            monthly_revenue_trend,
            work_order_breakdown,
            snapshot_date
        FROM mart_customer_activity
        WHERE org_id = %s
        AND activity_status = 'churned'
        AND snapshot_date = (SELECT MAX(snapshot_date) FROM mart_customer_activity WHERE org_id = %s)
        ORDER BY previous_revenue DESC
        LIMIT 100
        """
        
        churned_customers = pg.execute_query(churned_query, (org_id, org_id))
        
        # Format churned customers
        churned_list = []
        if churned_customers:
            for customer in churned_customers:
                churned_list.append({
                    'customer_name': customer['customer_name'],
                    'bill_to': customer['bill_to'],
                    'total_invoices': int(customer['lifetime_invoice_count'] or 0),
                    'total_revenue': float(customer['lifetime_revenue'] or 0),
                    'first_invoice': customer['first_invoice_date'].strftime('%Y-%m-%d') if customer['first_invoice_date'] else None,
                    'last_invoice': customer['last_invoice_date'].strftime('%Y-%m-%d') if customer['last_invoice_date'] else None,
                    'days_since_last_invoice': int(customer['days_since_last_invoice'] or 0),
                    'previous_period_revenue': float(customer['previous_revenue'] or 0),
                    'previous_period_invoices': int(customer['previous_invoice_count'] or 0),
                    'work_order_breakdown': customer['work_order_breakdown'] if customer['work_order_breakdown'] else [],
                    'revenue_trend': customer['monthly_revenue_trend'] if customer['monthly_revenue_trend'] else []
                })
        
        # Get summary statistics
        total_churned = len(churned_list)
        total_lost_revenue = sum(c['previous_period_revenue'] for c in churned_list)
        avg_customer_value = total_lost_revenue / total_churned if total_churned > 0 else 0
        
        # Get current active customer count
        active_query = """
        SELECT COUNT(*) as active_count
        FROM mart_customer_activity
        WHERE org_id = %s
        AND activity_status = 'active'
        AND snapshot_date = (SELECT MAX(snapshot_date) FROM mart_customer_activity WHERE org_id = %s)
        """
        active_result = pg.execute_query(active_query, (org_id, org_id))
        current_active = active_result[0]['active_count'] if active_result else 0
        
        # Calculate churn rate
        previous_active = current_active + total_churned
        churn_rate = (total_churned / previous_active * 100) if previous_active > 0 else 0
        
        # Get snapshot date for analysis period info
        snapshot_query = """
        SELECT MAX(snapshot_date) as snapshot_date
        FROM mart_customer_activity
        WHERE org_id = %s
        """
        snapshot_result = pg.execute_query(snapshot_query, (org_id,))
        snapshot_date = None
        if snapshot_result and snapshot_result[0].get('snapshot_date'):
            snapshot_date = snapshot_result[0]['snapshot_date']
        
        if not snapshot_date:
            # No mart data for this tenant yet - return empty response
            return jsonify({
                'summary': {
                    'total_churned_customers': 0,
                    'total_lost_revenue': 0,
                    'average_customer_value': 0,
                    'churn_rate': 0,
                    'total_customers': 0,
                    'active_customers': 0
                },
                'churned_customers': [],
                'analysis_period': {
                    'message': 'No customer activity data available yet. ETL has not run for this tenant.'
                }
            })
        
        # Calculate period dates (90-day periods)
        current_end = snapshot_date
        current_start = current_end - timedelta(days=90)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=89)
        
        response = {
            'summary': {
                'total_churned_customers': total_churned,
                'total_lost_revenue': round(total_lost_revenue, 2),
                'average_customer_value': round(avg_customer_value, 2),
                'current_active_customers': current_active,
                'churn_rate_percent': round(churn_rate, 2),
                'analysis_period': {
                    'current_start': current_start.strftime('%Y-%m-%d'),
                    'current_end': current_end.strftime('%Y-%m-%d'),
                    'previous_start': previous_start.strftime('%Y-%m-%d'),
                    'previous_end': previous_end.strftime('%Y-%m-%d')
                }
            },
            'churned_customers': churned_list,
            'data_freshness': snapshot_date.strftime('%Y-%m-%d') if snapshot_date else None,
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
    Uses AI to analyze patterns and suggest actions
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get org name for context in the AI prompt
        org_name = get_current_org_name()
        
        # Prepare the analysis prompt
        summary = data.get('summary', {})
        churned_customers = data.get('churned_customers', [])
        
        # Build customer profiles for analysis
        customer_profiles = []
        for c in churned_customers[:20]:  # Limit to top 20 for API efficiency
            wo_breakdown = c.get('work_order_breakdown', [])
            if isinstance(wo_breakdown, list):
                wo_types = ', '.join([f"{wo.get('type', 'N/A')}" for wo in wo_breakdown])
            else:
                wo_types = 'N/A'
            
            profile = f"- {c['customer_name']}: ${c['total_revenue']:,.0f} lifetime revenue, {c['total_invoices']} invoices, last active {c['last_invoice']}, ${c.get('previous_period_revenue', 0):,.0f} in previous 90 days"
            customer_profiles.append(profile)
        
        prompt = f"""Analyze this customer churn data for {org_name}, an equipment and industrial services company, and provide actionable insights.

## Summary Statistics
- Total Churned Customers: {summary.get('total_churned_customers', 0)}
- Total Lost Revenue (Previous 90-day Period): ${summary.get('total_lost_revenue', 0):,.2f}
- Average Customer Value: ${summary.get('average_customer_value', 0):,.2f}
- Current Active Customers: {summary.get('current_active_customers', 0)}
- Churn Rate: {summary.get('churn_rate_percent', 0):.1f}%
- Analysis Period: {summary.get('analysis_period', {}).get('previous_start', 'N/A')} to {summary.get('analysis_period', {}).get('current_end', 'N/A')}

## Churned Customer Profiles (Top by Revenue)
{chr(10).join(customer_profiles)}

## Churn Definition
A customer is considered "churned" if they had invoices in the previous 90-day period (days 91-180 ago) but NO invoices in the recent 90-day period (last 90 days).

Please provide:
1. **Key Trends**: What patterns do you see in the churned customers? (e.g., customer size, service types, timing)
2. **Risk Factors**: What characteristics might indicate a customer is at risk of churning?
3. **High-Priority Win-Back Targets**: Which 3-5 customers should be prioritized for outreach and why?
4. **Recommended Actions**: Specific steps {org_name} should take to reduce churn and win back customers
5. **Questions to Investigate**: What additional data would help understand the churn better?

Format your response in clear sections with actionable recommendations."""

        # Call AI API
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a business analyst specializing in customer retention for equipment dealerships and industrial service companies. Provide clear, actionable insights based on data analysis. Be specific about which customers to contact and what actions to take."
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
    
    At-risk criteria: 50%+ revenue drop between 90-day periods
    """
    try:
        org_id = get_current_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        
        pg = PostgreSQLService()
        
        # Get at-risk customers from mart table
        at_risk_query = """
        SELECT 
            customer_name,
            bill_to,
            recent_invoice_count,
            recent_revenue,
            recent_service_revenue,
            recent_parts_revenue,
            recent_rental_revenue,
            recent_last_invoice as last_invoice,
            previous_invoice_count,
            previous_revenue,
            previous_service_revenue,
            previous_parts_revenue,
            previous_rental_revenue,
            days_since_last_invoice,
            revenue_change_percent
        FROM mart_customer_activity
        WHERE org_id = %s
        AND activity_status = 'at_risk'
        AND snapshot_date = (SELECT MAX(snapshot_date) FROM mart_customer_activity WHERE org_id = %s)
        ORDER BY previous_revenue DESC
        LIMIT 100
        """
        
        at_risk_customers = pg.execute_query(at_risk_query, (org_id, org_id))
        
        at_risk_list = []
        if at_risk_customers:
            for customer in at_risk_customers:
                revenue_change = float(customer['revenue_change_percent'] or 0)
                at_risk_list.append({
                    'customer_name': customer['customer_name'],
                    'bill_to': customer['bill_to'],
                    'recent_revenue': float(customer['recent_revenue'] or 0),
                    'recent_invoices': int(customer['recent_invoice_count'] or 0),
                    'previous_revenue': float(customer['previous_revenue'] or 0),
                    'previous_invoices': int(customer['previous_invoice_count'] or 0),
                    'revenue_change_percent': round(revenue_change, 1),
                    'last_invoice': customer['last_invoice'].strftime('%Y-%m-%d') if customer['last_invoice'] else None,
                    'days_since_activity': int(customer['days_since_last_invoice'] or 0),
                    'risk_level': 'High' if revenue_change <= -75 else 'Medium'
                })
        
        # Get snapshot date
        snapshot_query = """
        SELECT MAX(snapshot_date) as snapshot_date
        FROM mart_customer_activity
        WHERE org_id = %s
        """
        snapshot_result = pg.execute_query(snapshot_query, (org_id,))
        snapshot_date = None
        if snapshot_result and snapshot_result[0].get('snapshot_date'):
            snapshot_date = snapshot_result[0]['snapshot_date']
        
        return jsonify({
            'at_risk_customers': at_risk_list,
            'total_at_risk': len(at_risk_list),
            'total_at_risk_previous_revenue': sum(c['previous_revenue'] for c in at_risk_list),
            'data_freshness': snapshot_date.strftime('%Y-%m-%d') if snapshot_date else None,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"At-risk analysis failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@customer_churn_bp.route('/api/customer-churn/refresh', methods=['POST'])
@jwt_required()
def refresh_churn_data():
    """
    Manually trigger a refresh of the customer activity ETL
    Admin endpoint for on-demand data refresh
    """
    try:
        org_id = get_current_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        
        from src.etl.etl_customer_activity import run_customer_activity_etl
        
        logger.info(f"Manual customer activity ETL triggered for org_id={org_id}")
        success = run_customer_activity_etl(org_id=org_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Customer activity data refreshed successfully',
                'refreshed_at': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'ETL job completed with errors'
            }), 500
            
    except Exception as e:
        logger.error(f"Manual ETL refresh failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@customer_churn_bp.route('/api/customer-churn/summary', methods=['GET'])
@jwt_required()
def get_churn_summary():
    """
    Get a quick summary of churn metrics without full customer details
    Useful for dashboard widgets
    """
    try:
        org_id = get_current_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        
        pg = PostgreSQLService()
        
        summary_query = """
        SELECT 
            activity_status,
            COUNT(*) as customer_count,
            SUM(previous_revenue) as total_previous_revenue,
            SUM(recent_revenue) as total_recent_revenue,
            AVG(revenue_change_percent) as avg_revenue_change
        FROM mart_customer_activity
        WHERE org_id = %s
        AND snapshot_date = (SELECT MAX(snapshot_date) FROM mart_customer_activity WHERE org_id = %s)
        GROUP BY activity_status
        """
        
        results = pg.execute_query(summary_query, (org_id, org_id))
        
        summary = {
            'active': {'count': 0, 'revenue': 0},
            'at_risk': {'count': 0, 'revenue': 0},
            'churned': {'count': 0, 'revenue': 0},
            'new': {'count': 0, 'revenue': 0}
        }
        
        if results:
            for row in results:
                status = row['activity_status']
                if status in summary:
                    summary[status] = {
                        'count': int(row['customer_count'] or 0),
                        'previous_revenue': float(row['total_previous_revenue'] or 0),
                        'recent_revenue': float(row['total_recent_revenue'] or 0),
                        'avg_revenue_change': round(float(row['avg_revenue_change'] or 0), 1)
                    }
        
        # Calculate totals
        total_customers = sum(s['count'] for s in summary.values())
        churn_rate = (summary['churned']['count'] / (total_customers - summary['new']['count']) * 100) if (total_customers - summary['new']['count']) > 0 else 0
        
        return jsonify({
            'by_status': summary,
            'total_customers': total_customers,
            'churn_rate_percent': round(churn_rate, 2),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Churn summary failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
