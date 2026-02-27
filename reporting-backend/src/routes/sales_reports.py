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

        # Apply account groupings if configured for this tenant (case-insensitive schema match)
        groupings = []
        schema_lower = schema.lower().strip() if schema else ''
        for cfg_schema, cfg_val in ACCOUNT_GROUPINGS.items():
            if cfg_schema.lower() == schema_lower:
                groupings = cfg_val
                break
        logger.info(f"Sales breakdown - schema: '{schema}', groupings found: {len(groupings)}")
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

        # Main query: split revenue into rental vs non-rental using SaleDept
        # Rental = SaleDept 60, everything else = non-rental
        query = f"""
        SELECT 
            BillToName,
            COUNT(*) as invoice_count,
            SUM(GrandTotal) as total_revenue,
            SUM(COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + COALESCE(MiscCost, 0) + COALESCE(RentalCost, 0) + COALESCE(EquipmentCost, 0)) as direct_cost,
            SUM(CASE WHEN SaleDept = 60 THEN GrandTotal ELSE 0 END) as rental_revenue,
            SUM(CASE WHEN SaleDept != 60 OR SaleDept IS NULL THEN GrandTotal ELSE 0 END) as non_rental_revenue,
            SUM(CASE WHEN SaleDept != 60 OR SaleDept IS NULL THEN 
                COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + COALESCE(MiscCost, 0) + COALESCE(RentalCost, 0) + COALESCE(EquipmentCost, 0)
            ELSE 0 END) as non_rental_cost
        FROM [{schema}].InvoiceReg
        WHERE InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
        AND BillToName IS NOT NULL AND BillToName != ''
        GROUP BY BillToName
        ORDER BY SUM(GrandTotal) DESC
        """

        results = db.execute_query(query)

        # Query fleet-wide rental costs from GLDetail for proportional allocation
        # These are the COS accounts for the rental department that don't flow through InvoiceReg
        RENTAL_COS_ACCOUNTS = ('537001', '539000', '541000', '510008', '511001', '519000', '521008', '534014', '545000')
        fleet_cost_query = f"""
        SELECT 
            SUM(Amount) as total_fleet_cost
        FROM [{schema}].GLDetail
        WHERE AccountNo IN {RENTAL_COS_ACCOUNTS}
        AND EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
        AND Posted = 1
        """

        fleet_cost_result = None
        total_fleet_rental_cost = 0
        try:
            fleet_cost_result = db.execute_query(fleet_cost_query)
            if fleet_cost_result:
                total_fleet_rental_cost = abs(float(fleet_cost_result[0].get('total_fleet_cost', 0) or 0))
                logger.info(f"Sales by customer - total fleet rental cost from GLDetail: ${total_fleet_rental_cost:,.2f}")
        except Exception as e:
            logger.warning(f"Could not query fleet rental costs from GLDetail: {str(e)}")
            total_fleet_rental_cost = 0

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

        # Normalize DB result keys to handle case variations from different SQL drivers
        # pymssql may return keys matching SQL aliases exactly, but we want consistent access
        def normalize_row(row):
            """Create a case-insensitive lookup for a row dict"""
            normalized = {}
            for k, v in row.items():
                normalized[k] = v
                normalized[k.lower()] = v
            return normalized

        results = [normalize_row(r) for r in results]

        # Log first result keys for debugging
        if results:
            logger.info(f"Sales by customer - schema: '{schema}', first row keys: {list(results[0].keys())[:10]}")

        # Helper to get value from row with case-insensitive fallback
        def get_val(row, key, default=None):
            return row.get(key, row.get(key.lower(), default))

        # Tenant-specific customer configurations
        # exclude_patterns: customers matching these substrings (case-insensitive) are removed
        # group_patterns: customers matching a substring are combined into one row
        CUSTOMER_CONFIG = {
            'ben002': {
                'exclude_patterns': [],
                'group_patterns': [
                    {
                        'match': 'polaris',   # case-insensitive substring match
                        'label': 'Polaris',    # combined row display name
                    },
                ],
            },
        }

        # Look up config with case-insensitive schema matching
        config = {}
        schema_lower = schema.lower().strip() if schema else ''
        for cfg_schema, cfg_val in CUSTOMER_CONFIG.items():
            if cfg_schema.lower() == schema_lower:
                config = cfg_val
                break

        logger.info(f"Sales by customer - schema: '{schema}', config found: {bool(config)}, group_patterns: {len(config.get('group_patterns', []))}")

        # Step 1: Exclude unwanted customers
        exclude_patterns = config.get('exclude_patterns', [])
        if exclude_patterns:
            results = [
                r for r in results
                if not any(
                    pat in (get_val(r, 'BillToName', '') or '').lower()
                    for pat in exclude_patterns
                )
            ]

        # Step 2: Group customers by pattern
        group_patterns = config.get('group_patterns', [])
        for group in group_patterns:
            match_str = group['match'].lower()
            label = group['label']
            combined_revenue = 0.0
            combined_direct_cost = 0.0
            combined_rental_rev = 0.0
            combined_non_rental_rev = 0.0
            combined_non_rental_cost = 0.0
            combined_invoices = 0
            member_details = []
            remaining = []
            for r in results:
                name = (get_val(r, 'BillToName', '') or '').strip()
                if match_str in name.lower():
                    rev = float(get_val(r, 'total_revenue', 0) or 0)
                    dc = float(get_val(r, 'direct_cost', 0) or 0)
                    rr = float(get_val(r, 'rental_revenue', 0) or 0)
                    nrr = float(get_val(r, 'non_rental_revenue', 0) or 0)
                    nrc = float(get_val(r, 'non_rental_cost', 0) or 0)
                    inv = int(get_val(r, 'invoice_count', 0) or 0)
                    combined_revenue += rev
                    combined_direct_cost += dc
                    combined_rental_rev += rr
                    combined_non_rental_rev += nrr
                    combined_non_rental_cost += nrc
                    combined_invoices += inv
                    member_details.append({
                        'name': name,
                        'total_revenue': round(rev, 2),
                        'invoice_count': inv,
                    })
                    logger.info(f"Grouped customer '{name}' into '{label}' (rev: {rev})")
                else:
                    remaining.append(r)
            if member_details:
                logger.info(f"Created combined '{label}' row with {len(member_details)} members, total rev: {combined_revenue}")
                combined_row = {
                    'BillToName': label,
                    'billtoname': label,
                    'invoice_count': combined_invoices,
                    'total_revenue': combined_revenue,
                    'direct_cost': combined_direct_cost,
                    'rental_revenue': combined_rental_rev,
                    'non_rental_revenue': combined_non_rental_rev,
                    'non_rental_cost': combined_non_rental_cost,
                    '_is_grouped': True,
                    '_grouped_customers': member_details,
                }
                remaining.append(combined_row)
            else:
                logger.warning(f"No customers matched pattern '{match_str}' for grouping")
            results = remaining

        # Step 3: Calculate blended margins
        # - Non-rental: use direct costs from InvoiceReg (accurate per-customer)
        # - Rental: allocate fleet-wide rental costs proportionally by rental revenue share
        total_rental_revenue_all_customers = sum(
            float(get_val(r, 'rental_revenue', 0) or 0) for r in results
        )
        logger.info(f"Sales by customer - total rental revenue across all customers: ${total_rental_revenue_all_customers:,.2f}, fleet cost to allocate: ${total_fleet_rental_cost:,.2f}")

        # Sort by revenue descending
        results.sort(key=lambda r: float(get_val(r, 'total_revenue', 0) or 0), reverse=True)

        customers = []
        running_total_revenue = 0
        running_total_cost = 0
        running_total_gp = 0

        for i, r in enumerate(results):
            revenue = float(get_val(r, 'total_revenue', 0) or 0)
            rental_rev = float(get_val(r, 'rental_revenue', 0) or 0)
            non_rental_rev = float(get_val(r, 'non_rental_revenue', 0) or 0)
            non_rental_cost = float(get_val(r, 'non_rental_cost', 0) or 0)

            # Allocate fleet rental costs proportionally
            if total_rental_revenue_all_customers > 0 and rental_rev > 0:
                rental_share = rental_rev / total_rental_revenue_all_customers
                allocated_rental_cost = total_fleet_rental_cost * rental_share
            else:
                rental_share = 0
                allocated_rental_cost = 0

            # Blended cost = direct non-rental cost + proportionally allocated rental cost
            blended_cost = non_rental_cost + allocated_rental_cost
            blended_gp = revenue - blended_cost

            running_total_revenue += revenue
            running_total_cost += blended_cost
            running_total_gp += blended_gp

            entry = {
                'rank': i + 1,
                'name': get_val(r, 'BillToName', 'Unknown'),
                'invoice_count': int(get_val(r, 'invoice_count', 0) or 0),
                'total_revenue': round(revenue, 2),
                'total_cost': round(blended_cost, 2),
                'gross_profit': round(blended_gp, 2),
                'gross_margin_pct': round(blended_gp * 100.0 / revenue, 1) if revenue > 0 else 0,
                'rental_revenue': round(rental_rev, 2),
                'non_rental_revenue': round(non_rental_rev, 2),
                'rental_cost_allocated': round(allocated_rental_cost, 2),
                'non_rental_cost': round(non_rental_cost, 2),
            }
            if r.get('_is_grouped'):
                entry['is_grouped'] = True
                entry['grouped_customers'] = r['_grouped_customers']
            customers.append(entry)

        # Now calculate pct_of_total fields with final totals
        total_revenue = running_total_revenue
        total_cost = running_total_cost
        total_gross_profit = running_total_gp

        for c in customers:
            c['pct_of_total_revenue'] = round(c['total_revenue'] * 100.0 / total_revenue, 2) if total_revenue > 0 else 0
            c['pct_of_total_gp'] = round(c['gross_profit'] * 100.0 / total_gross_profit, 2) if total_gross_profit > 0 else 0

        return jsonify({
            'customers': customers,
            'total_revenue': round(total_revenue, 2),
            'total_cost': round(total_cost, 2),
            'total_gross_profit': round(total_gross_profit, 2),
            'overall_margin_pct': round(total_gross_profit * 100.0 / total_revenue, 1) if total_revenue > 0 else 0,
            'customer_count': len(customers),
            'start_date': start_date,
            'end_date': end_date,
            'rental_cost_allocation': {
                'total_fleet_rental_cost': round(total_fleet_rental_cost, 2),
                'total_rental_revenue': round(total_rental_revenue_all_customers, 2),
                'method': 'Proportional allocation of fleet-wide rental COS (537001, 539000, 541000, etc.) from GLDetail based on customer share of total rental revenue (SaleDept=60)'
            }
        })

    except Exception as e:
        logger.error(f"Sales by customer error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sales_reports_bp.route('/api/reports/customer-gl-investigation', methods=['GET'])
def investigate_customer_gl():
    """
    Diagnostic (TEMPORARY - no auth): Investigate what GL accounts are associated with specific customers.
    Shows how their invoices post to the GL to determine if they're real revenue
    or internal transfers / finance partner transactions.
    
    Query params:
        customer_name: Customer name to investigate (substring match)
        schema: Schema to query (default: ben002)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    try:
        from src.services.azure_sql_service import AzureSQLService
        schema = request.args.get('schema', 'ben002')
        db = AzureSQLService()

        customer_name = request.args.get('customer_name', '')
        start_date = request.args.get('start_date', '2024-01-01')
        end_date = request.args.get('end_date', '2026-12-31')

        if not customer_name:
            return jsonify({'error': 'customer_name parameter is required'}), 400

        # Query 1: Get all invoices for this customer with their details
        invoice_query = f"""
        SELECT TOP 50
            InvoiceNo,
            InvoiceDate,
            BillToName,
            BillTo,
            GrandTotal
        FROM [{schema}].InvoiceReg
        WHERE BillToName LIKE '%{customer_name}%'
        AND InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
        ORDER BY GrandTotal DESC
        """

        invoices = db.execute_query(invoice_query)

        # Query 2: Get summary stats
        summary_query = f"""
        SELECT 
            COUNT(*) as invoice_count,
            SUM(GrandTotal) as total_grand,
            MIN(GrandTotal) as min_grand,
            MAX(GrandTotal) as max_grand,
            AVG(GrandTotal) as avg_grand,
            SUM(CASE WHEN GrandTotal < 0 THEN 1 ELSE 0 END) as negative_count,
            SUM(CASE WHEN GrandTotal < 0 THEN GrandTotal ELSE 0 END) as negative_total
        FROM [{schema}].InvoiceReg
        WHERE BillToName LIKE '%{customer_name}%'
        AND InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
        """

        summary = db.execute_query(summary_query)

        # Query 3: Use GLDetail table to find GL account postings for this customer's invoices
        # GLDetail has: AccountNo, Amount, EffectiveDate, InvoiceNo, Posted, Branch, Dept
        gl_link_query = f"""
        SELECT TOP 100
            gld.InvoiceNo,
            gld.AccountNo,
            COALESCE(coa.Description, 'Unknown') as AccountDescription,
            gld.Amount,
            gld.EffectiveDate,
            gld.Branch,
            gld.Dept
        FROM [{schema}].GLDetail gld
        LEFT JOIN [{schema}].ChartOfAccounts coa ON gld.AccountNo = coa.AccountNo
        WHERE gld.InvoiceNo IN (
            SELECT TOP 20 InvoiceNo 
            FROM [{schema}].InvoiceReg 
            WHERE BillToName LIKE '%{customer_name}%'
            AND InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
            ORDER BY GrandTotal DESC
        )
        AND gld.Posted = 1
        ORDER BY gld.InvoiceNo, gld.AccountNo
        """

        # Query 3b: Summarize GL accounts for ALL matching invoices (not just top 20)
        gl_summary_query = f"""
        SELECT 
            gld.AccountNo,
            COALESCE(coa.Description, 'Unknown') as AccountDescription,
            COUNT(*) as posting_count,
            SUM(gld.Amount) as total_amount,
            MIN(gld.Amount) as min_amount,
            MAX(gld.Amount) as max_amount
        FROM [{schema}].GLDetail gld
        LEFT JOIN [{schema}].ChartOfAccounts coa ON gld.AccountNo = coa.AccountNo
        WHERE gld.InvoiceNo IN (
            SELECT InvoiceNo 
            FROM [{schema}].InvoiceReg 
            WHERE BillToName LIKE '%{customer_name}%'
            AND InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
        )
        AND gld.Posted = 1
        GROUP BY gld.AccountNo, coa.Description
        ORDER BY ABS(SUM(gld.Amount)) DESC
        """

        gl_details = []
        gl_summary = []
        gl_error = None
        try:
            gl_details = db.execute_query(gl_link_query)
            gl_summary = db.execute_query(gl_summary_query)
        except Exception as e:
            gl_error = f"GLDetail query failed: {str(e)}"

        # Query 4: Get distinct BillToName variations matching the pattern
        names_query = f"""
        SELECT DISTINCT BillToName, COUNT(*) as cnt, SUM(GrandTotal) as total
        FROM [{schema}].InvoiceReg
        WHERE BillToName LIKE '%{customer_name}%'
        AND InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
        GROUP BY BillToName
        ORDER BY SUM(GrandTotal) DESC
        """

        name_variations = db.execute_query(names_query)

        # Format response
        result = {
            'customer_search': customer_name,
            'schema': schema,
            'date_range': {'start': start_date, 'end': end_date},
            'name_variations': [
                {
                    'name': r.get('BillToName', ''),
                    'invoice_count': int(r.get('cnt', 0) or 0),
                    'total_revenue': round(float(r.get('total', 0) or 0), 2)
                }
                for r in (name_variations or [])
            ],
            'summary': {
                'invoice_count': int(summary[0].get('invoice_count', 0) or 0) if summary else 0,
                'total_grand': round(float(summary[0].get('total_grand', 0) or 0), 2) if summary else 0,
                'min_grand': round(float(summary[0].get('min_grand', 0) or 0), 2) if summary else 0,
                'max_grand': round(float(summary[0].get('max_grand', 0) or 0), 2) if summary else 0,
                'avg_grand': round(float(summary[0].get('avg_grand', 0) or 0), 2) if summary else 0,
                'negative_count': int(summary[0].get('negative_count', 0) or 0) if summary else 0,
                'negative_total': round(float(summary[0].get('negative_total', 0) or 0), 2) if summary else 0,
            },
            'sample_invoices': [
                {
                    'invoice_no': r.get('InvoiceNo', ''),
                    'date': str(r.get('InvoiceDate', '')),
                    'bill_to_name': r.get('BillToName', ''),
                    'bill_to': r.get('BillTo', ''),
                    'grand_total': round(float(r.get('GrandTotal', 0) or 0), 2),
                }
                for r in (invoices or [])
            ],
            'gl_account_summary': [
                {
                    'account_no': r.get('AccountNo', ''),
                    'account_description': r.get('AccountDescription', ''),
                    'posting_count': int(r.get('posting_count', 0) or 0),
                    'total_amount': round(float(r.get('total_amount', 0) or 0), 2),
                    'min_amount': round(float(r.get('min_amount', 0) or 0), 2),
                    'max_amount': round(float(r.get('max_amount', 0) or 0), 2),
                }
                for r in (gl_summary or [])
            ] if gl_summary else gl_error or 'No GL summary found',
            'gl_account_details': [
                {
                    'invoice_no': r.get('InvoiceNo', ''),
                    'account_no': r.get('AccountNo', ''),
                    'account_description': r.get('AccountDescription', ''),
                    'amount': round(float(r.get('Amount', 0) or 0), 2),
                    'date': str(r.get('EffectiveDate', '')),
                    'branch': r.get('Branch', ''),
                    'dept': r.get('Dept', ''),
                }
                for r in (gl_details or [])
            ] if gl_details else gl_error or 'No GL details found',
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"Customer GL investigation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sales_reports_bp.route('/api/reports/rental-cost-investigation', methods=['GET'])
def get_rental_cost_investigation():
    """Investigate rental cost allocation via ControlNo - NO AUTH for diagnostic use"""
    try:
        from src.services.azure_sql_service import AzureSQLService
        schema = request.args.get('schema', 'ben002')
        db = AzureSQLService()

        customer_name = request.args.get('customer_name', 'POLARIS')
        start_date = request.args.get('start_date', '2025-03-01')
        end_date = request.args.get('end_date', '2026-03-01')

        # Query 1: How many rental invoices have ControlNo populated vs empty?
        control_coverage_query = f"""
        SELECT 
            COUNT(*) as total_invoices,
            COUNT(CASE WHEN ControlNo IS NOT NULL AND ControlNo != '' THEN 1 END) as with_control_no,
            COUNT(CASE WHEN ControlNo IS NULL OR ControlNo = '' THEN 1 END) as without_control_no,
            SUM(GrandTotal) as total_revenue,
            SUM(CASE WHEN ControlNo IS NOT NULL AND ControlNo != '' THEN GrandTotal ELSE 0 END) as revenue_with_control,
            SUM(CASE WHEN ControlNo IS NULL OR ControlNo = '' THEN GrandTotal ELSE 0 END) as revenue_without_control,
            COUNT(DISTINCT CASE WHEN ControlNo IS NOT NULL AND ControlNo != '' THEN ControlNo END) as unique_control_nos
        FROM [{schema}].InvoiceReg
        WHERE BillToName LIKE '%{customer_name}%'
        AND InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
        """

        coverage = db.execute_query(control_coverage_query)

        # Query 2: Top control numbers for this customer with revenue
        top_controls_query = f"""
        SELECT TOP 20
            ir.ControlNo,
            COUNT(*) as invoice_count,
            SUM(ir.GrandTotal) as total_revenue,
            MIN(ir.InvoiceDate) as first_invoice,
            MAX(ir.InvoiceDate) as last_invoice,
            e.Make,
            e.Model,
            e.SerialNo,
            e.Cost as equipment_cost
        FROM [{schema}].InvoiceReg ir
        LEFT JOIN [{schema}].Equipment e ON ir.ControlNo = e.ControlNo
        WHERE ir.BillToName LIKE '%{customer_name}%'
        AND ir.InvoiceDate >= '{start_date}' AND ir.InvoiceDate < '{end_date}'
        AND ir.ControlNo IS NOT NULL AND ir.ControlNo != ''
        GROUP BY ir.ControlNo, e.Make, e.Model, e.SerialNo, e.Cost
        ORDER BY SUM(ir.GrandTotal) DESC
        """

        top_controls = db.execute_query(top_controls_query)

        # Query 3: For those control numbers, check if depreciation (537001) exists in GLDetail
        depreciation_query = f"""
        SELECT 
            gld.ControlNo,
            gld.AccountNo,
            COALESCE(coa.Description, 'Unknown') as AccountDescription,
            COUNT(*) as posting_count,
            SUM(gld.Amount) as total_amount
        FROM [{schema}].GLDetail gld
        LEFT JOIN [{schema}].ChartOfAccounts coa ON gld.AccountNo = coa.AccountNo
        WHERE gld.ControlNo IN (
            SELECT DISTINCT ControlNo 
            FROM [{schema}].InvoiceReg
            WHERE BillToName LIKE '%{customer_name}%'
            AND InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
            AND ControlNo IS NOT NULL AND ControlNo != ''
        )
        AND gld.AccountNo IN ('537001', '539000', '541000', '510008', '511001', '519000', '521008', '534014', '545000')
        AND gld.EffectiveDate >= '{start_date}' AND gld.EffectiveDate < '{end_date}'
        AND gld.Posted = 1
        GROUP BY gld.ControlNo, gld.AccountNo, coa.Description
        ORDER BY gld.ControlNo, ABS(SUM(gld.Amount)) DESC
        """

        depreciation_data = []
        dep_error = None
        try:
            depreciation_data = db.execute_query(depreciation_query)
        except Exception as e:
            dep_error = f"Depreciation query failed: {str(e)}"

        # Query 4: Total rental fleet depreciation (537001) across ALL control numbers for the period
        fleet_depreciation_query = f"""
        SELECT 
            gld.AccountNo,
            COALESCE(coa.Description, 'Unknown') as AccountDescription,
            COUNT(DISTINCT gld.ControlNo) as unique_units,
            COUNT(*) as posting_count,
            SUM(gld.Amount) as total_amount
        FROM [{schema}].GLDetail gld
        LEFT JOIN [{schema}].ChartOfAccounts coa ON gld.AccountNo = coa.AccountNo
        WHERE gld.AccountNo IN ('537001', '539000', '541000', '510008', '545000', '600901')
        AND gld.EffectiveDate >= '{start_date}' AND gld.EffectiveDate < '{end_date}'
        AND gld.Posted = 1
        GROUP BY gld.AccountNo, coa.Description
        ORDER BY ABS(SUM(gld.Amount)) DESC
        """

        fleet_dep = []
        fleet_dep_error = None
        try:
            fleet_dep = db.execute_query(fleet_depreciation_query)
        except Exception as e:
            fleet_dep_error = f"Fleet depreciation query failed: {str(e)}"

        # Format response
        c = coverage[0] if coverage else {}
        result = {
            'customer_search': customer_name,
            'schema': schema,
            'date_range': {'start': start_date, 'end': end_date},
            'control_number_coverage': {
                'total_invoices': int(c.get('total_invoices', 0) or 0),
                'with_control_no': int(c.get('with_control_no', 0) or 0),
                'without_control_no': int(c.get('without_control_no', 0) or 0),
                'coverage_pct': round(int(c.get('with_control_no', 0) or 0) * 100.0 / max(int(c.get('total_invoices', 0) or 0), 1), 1),
                'total_revenue': round(float(c.get('total_revenue', 0) or 0), 2),
                'revenue_with_control': round(float(c.get('revenue_with_control', 0) or 0), 2),
                'revenue_without_control': round(float(c.get('revenue_without_control', 0) or 0), 2),
                'revenue_coverage_pct': round(float(c.get('revenue_with_control', 0) or 0) * 100.0 / max(float(c.get('total_revenue', 0) or 0), 1), 1),
                'unique_control_nos': int(c.get('unique_control_nos', 0) or 0),
            },
            'top_control_numbers': [
                {
                    'control_no': r.get('ControlNo', ''),
                    'invoice_count': int(r.get('invoice_count', 0) or 0),
                    'total_revenue': round(float(r.get('total_revenue', 0) or 0), 2),
                    'first_invoice': str(r.get('first_invoice', '')),
                    'last_invoice': str(r.get('last_invoice', '')),
                    'make': r.get('Make', ''),
                    'model': r.get('Model', ''),
                    'serial_no': r.get('SerialNo', ''),
                    'equipment_cost': round(float(r.get('equipment_cost', 0) or 0), 2),
                }
                for r in (top_controls or [])
            ],
            'depreciation_by_control_no': [
                {
                    'control_no': r.get('ControlNo', ''),
                    'account_no': r.get('AccountNo', ''),
                    'account_description': r.get('AccountDescription', ''),
                    'posting_count': int(r.get('posting_count', 0) or 0),
                    'total_amount': round(float(r.get('total_amount', 0) or 0), 2),
                }
                for r in (depreciation_data or [])
            ] if depreciation_data else dep_error or 'No depreciation data found',
            'total_fleet_costs': [
                {
                    'account_no': r.get('AccountNo', ''),
                    'account_description': r.get('AccountDescription', ''),
                    'unique_units': int(r.get('unique_units', 0) or 0),
                    'posting_count': int(r.get('posting_count', 0) or 0),
                    'total_amount': round(float(r.get('total_amount', 0) or 0), 2),
                }
                for r in (fleet_dep or [])
            ] if fleet_dep else fleet_dep_error or 'No fleet depreciation data found',
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"Rental cost investigation error: {str(e)}")
        return jsonify({'error': str(e)}), 500
