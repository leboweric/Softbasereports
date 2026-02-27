"""
Sales Reports API
Report 1: Sales Breakdown by GL Account - Revenue by GL account with descriptions
Report 2: Sales by Customer - Stack-ranked customer revenue with % of total
Multi-tenant: uses the current user's organization for data isolation
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
from src.models.user import User

logger = logging.getLogger(__name__)
sales_reports_bp = Blueprint('sales_reports', __name__)


def get_current_org():
    """Get the organization for the current authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if user and user.organization:
            return user.organization
        return None
    except Exception as e:
        logger.error(f"Error getting organization: {e}")
        return None


@sales_reports_bp.route('/api/reports/sales-breakdown', methods=['GET'])
@jwt_required()
def get_sales_breakdown():
    """
    Get revenue breakdown by GL account for a given date range.
    
    Query params:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns each GL 4xxx account with description and revenue amount.
    """
    try:
        org = get_current_org()
        if not org:
            return jsonify({'error': 'Could not determine organization'}), 400

        schema = get_tenant_schema()
        db = get_tenant_db()

        # Get date range from query params
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400

        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Parse dates to get year/month ranges for GL table
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        # Build year/month conditions for the GL table
        # GL stores data by Year and Month columns
        date_conditions = []
        current = start_dt.replace(day=1)
        while current <= end_dt:
            date_conditions.append(f"(gl.Year = {current.year} AND gl.Month = {current.month})")
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        if not date_conditions:
            return jsonify({'error': 'No months in the specified date range'}), 400

        date_filter = " OR ".join(date_conditions)

        query = f"""
        SELECT 
            gl.AccountNo,
            COALESCE(coa.Description, 'Unknown Account') as AccountDescription,
            -SUM(gl.MTD) as Revenue
        FROM [{schema}].GL gl
        LEFT JOIN [{schema}].ChartOfAccounts coa ON gl.AccountNo = coa.AccountNo
        WHERE gl.AccountNo LIKE '4%'
        AND ({date_filter})
        GROUP BY gl.AccountNo, coa.Description
        HAVING ABS(SUM(gl.MTD)) > 0
        ORDER BY -SUM(gl.MTD) DESC
        """

        results = db.execute_query(query)

        if not results:
            return jsonify({
                'accounts': [],
                'total_revenue': 0,
                'start_date': start_date,
                'end_date': end_date
            })

        # Tenant-specific account groupings
        # Each entry: { 'accounts': [list of account numbers to combine],
        #               'label': 'Display name for the combined row' }
        ACCOUNT_GROUPINGS = {
            'ben002': [
                {
                    'accounts': ['410001', '413001', '426001'],
                    'label': 'New Equipment',
                },
            ],
        }

        # Apply account groupings if configured for this tenant
        groupings = ACCOUNT_GROUPINGS.get(schema, [])
        if groupings:
            for group in groupings:
                group_accounts = set(group['accounts'])
                combined_revenue = 0.0
                member_details = []  # track individual accounts for tooltip
                remaining = []
                for r in results:
                    acct = r.get('AccountNo', '').strip()
                    if acct in group_accounts:
                        rev = float(r.get('Revenue', 0) or 0)
                        combined_revenue += rev
                        member_details.append({
                            'account_no': acct,
                            'description': r.get('AccountDescription', 'Unknown'),
                            'revenue': round(rev, 2),
                        })
                    else:
                        remaining.append(r)
                if member_details:
                    # Insert the combined row as a synthetic result
                    combined_row = {
                        'AccountNo': ', '.join(group['accounts']),
                        'AccountDescription': group['label'],
                        'Revenue': combined_revenue,
                        '_is_grouped': True,
                        '_grouped_accounts': member_details,
                    }
                    remaining.append(combined_row)
                results = remaining

        # Calculate total revenue
        total_revenue = sum(float(r.get('Revenue', 0) or 0) for r in results)

        # Build response with percentages
        accounts = []
        for r in results:
            revenue = float(r.get('Revenue', 0) or 0)
            entry = {
                'account_no': r.get('AccountNo', ''),
                'description': r.get('AccountDescription', 'Unknown'),
                'revenue': round(revenue, 2),
                'pct_of_total': round(revenue * 100.0 / total_revenue, 2) if total_revenue > 0 else 0
            }
            # Include grouping metadata if this is a combined row
            if r.get('_is_grouped'):
                entry['is_grouped'] = True
                entry['grouped_accounts'] = r['_grouped_accounts']
            accounts.append(entry)

        # Sort by revenue descending
        accounts.sort(key=lambda a: a['revenue'], reverse=True)

        return jsonify({
            'accounts': accounts,
            'total_revenue': round(total_revenue, 2),
            'start_date': start_date,
            'end_date': end_date,
            'account_count': len(accounts)
        })

    except Exception as e:
        logger.error(f"Sales breakdown error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sales_reports_bp.route('/api/reports/sales-by-customer', methods=['GET'])
@jwt_required()
def get_sales_by_customer():
    """
    Get stack-ranked customer revenue for a given date range.
    
    Query params:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns all customers ranked by total revenue with % of total.
    """
    try:
        org = get_current_org()
        if not org:
            return jsonify({'error': 'Could not determine organization'}), 400

        schema = get_tenant_schema()
        db = get_tenant_db()

        # Get date range from query params
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400

        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        query = f"""
        SELECT 
            BillToName,
            COUNT(*) as invoice_count,
            SUM(GrandTotal) as total_revenue,
            SUM(COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + COALESCE(MiscCost, 0) + COALESCE(RentalCost, 0) + COALESCE(EquipmentCost, 0)) as total_cost,
            SUM(GrandTotal) - SUM(COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + COALESCE(MiscCost, 0) + COALESCE(RentalCost, 0) + COALESCE(EquipmentCost, 0)) as gross_profit
        FROM [{schema}].InvoiceReg
        WHERE InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
        AND BillToName IS NOT NULL AND BillToName != ''
        GROUP BY BillToName
        ORDER BY SUM(GrandTotal) DESC
        """

        results = db.execute_query(query)

        if not results:
            return jsonify({
                'customers': [],
                'total_revenue': 0,
                'total_cost': 0,
                'total_gross_profit': 0,
                'customer_count': 0,
                'start_date': start_date,
                'end_date': end_date
            })

        # Calculate totals
        total_revenue = sum(float(r.get('total_revenue', 0) or 0) for r in results)
        total_cost = sum(float(r.get('total_cost', 0) or 0) for r in results)
        total_gross_profit = sum(float(r.get('gross_profit', 0) or 0) for r in results)

        # Build response with percentages and rank
        customers = []
        for i, r in enumerate(results):
            revenue = float(r.get('total_revenue', 0) or 0)
            cost = float(r.get('total_cost', 0) or 0)
            gp = float(r.get('gross_profit', 0) or 0)
            customers.append({
                'rank': i + 1,
                'name': r.get('BillToName', 'Unknown'),
                'invoice_count': int(r.get('invoice_count', 0) or 0),
                'total_revenue': round(revenue, 2),
                'total_cost': round(cost, 2),
                'gross_profit': round(gp, 2),
                'gross_margin_pct': round(gp * 100.0 / revenue, 1) if revenue > 0 else 0,
                'pct_of_total_revenue': round(revenue * 100.0 / total_revenue, 2) if total_revenue > 0 else 0,
                'pct_of_total_gp': round(gp * 100.0 / total_gross_profit, 2) if total_gross_profit > 0 else 0
            })

        return jsonify({
            'customers': customers,
            'total_revenue': round(total_revenue, 2),
            'total_cost': round(total_cost, 2),
            'total_gross_profit': round(total_gross_profit, 2),
            'overall_margin_pct': round(total_gross_profit * 100.0 / total_revenue, 1) if total_revenue > 0 else 0,
            'customer_count': len(customers),
            'start_date': start_date,
            'end_date': end_date
        })

    except Exception as e:
        logger.error(f"Sales by customer error: {str(e)}")
        return jsonify({'error': str(e)}), 500
