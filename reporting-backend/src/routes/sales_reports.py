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
            combined_cost = 0.0
            combined_gp = 0.0
            combined_invoices = 0
            member_details = []
            remaining = []
            for r in results:
                name = (get_val(r, 'BillToName', '') or '').strip()
                if match_str in name.lower():
                    rev = float(get_val(r, 'total_revenue', 0) or 0)
                    cost = float(get_val(r, 'total_cost', 0) or 0)
                    gp = float(get_val(r, 'gross_profit', 0) or 0)
                    inv = int(get_val(r, 'invoice_count', 0) or 0)
                    combined_revenue += rev
                    combined_cost += cost
                    combined_gp += gp
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
                    'total_cost': combined_cost,
                    'gross_profit': combined_gp,
                    '_is_grouped': True,
                    '_grouped_customers': member_details,
                }
                remaining.append(combined_row)
            else:
                logger.warning(f"No customers matched pattern '{match_str}' for grouping")
            results = remaining

        # Calculate totals
        total_revenue = sum(float(get_val(r, 'total_revenue', 0) or 0) for r in results)
        total_cost = sum(float(get_val(r, 'total_cost', 0) or 0) for r in results)
        total_gross_profit = sum(float(get_val(r, 'gross_profit', 0) or 0) for r in results)

        # Sort by revenue descending and build response
        results.sort(key=lambda r: float(get_val(r, 'total_revenue', 0) or 0), reverse=True)

        customers = []
        for i, r in enumerate(results):
            revenue = float(get_val(r, 'total_revenue', 0) or 0)
            cost = float(get_val(r, 'total_cost', 0) or 0)
            gp = float(get_val(r, 'gross_profit', 0) or 0)
            entry = {
                'rank': i + 1,
                'name': get_val(r, 'BillToName', 'Unknown'),
                'invoice_count': int(get_val(r, 'invoice_count', 0) or 0),
                'total_revenue': round(revenue, 2),
                'total_cost': round(cost, 2),
                'gross_profit': round(gp, 2),
                'gross_margin_pct': round(gp * 100.0 / revenue, 1) if revenue > 0 else 0,
                'pct_of_total_revenue': round(revenue * 100.0 / total_revenue, 2) if total_revenue > 0 else 0,
                'pct_of_total_gp': round(gp * 100.0 / total_gross_profit, 2) if total_gross_profit > 0 else 0
            }
            if r.get('_is_grouped'):
                entry['is_grouped'] = True
                entry['grouped_customers'] = r['_grouped_customers']
            customers.append(entry)

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

        # Query 3: Check if there's an InvoiceSales table that links invoices to GL accounts
        gl_link_query = f"""
        SELECT TOP 50
            isales.InvoiceNo,
            isales.AccountNo,
            COALESCE(coa.Description, 'Unknown') as AccountDescription,
            isales.Amount
        FROM [{schema}].InvoiceSales isales
        LEFT JOIN [{schema}].ChartOfAccounts coa ON isales.AccountNo = coa.AccountNo
        WHERE isales.InvoiceNo IN (
            SELECT TOP 20 InvoiceNo 
            FROM [{schema}].InvoiceReg 
            WHERE BillToName LIKE '%{customer_name}%'
            AND InvoiceDate >= '{start_date}' AND InvoiceDate < '{end_date}'
            ORDER BY GrandTotal DESC
        )
        ORDER BY isales.InvoiceNo, isales.AccountNo
        """

        gl_details = []
        gl_error = None
        # First check if InvoiceSales table exists
        try:
            table_check = db.execute_query(f"""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = 'InvoiceSales'
            """)
            if table_check:
                # Table exists, try the actual query
                try:
                    # First check what columns InvoiceSales has
                    cols_check = db.execute_query(f"""
                    SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = 'InvoiceSales'
                    ORDER BY ORDINAL_POSITION
                    """)
                    gl_error = f"InvoiceSales columns: {[(r.get('COLUMN_NAME',''), r.get('DATA_TYPE','')) for r in (cols_check or [])]}"
                    gl_details = db.execute_query(gl_link_query)
                except Exception as e:
                    gl_error = f"InvoiceSales exists but query failed: {str(e)}. Columns: {gl_error}"
            else:
                gl_error = 'InvoiceSales table does NOT exist in this schema'
        except Exception as e:
            gl_error = f"Table check failed: {str(e)}"

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
            'gl_account_details': [
                {
                    'invoice_no': r.get('InvoiceNo', ''),
                    'account_no': r.get('AccountNo', ''),
                    'account_description': r.get('AccountDescription', ''),
                    'amount': round(float(r.get('Amount', 0) or 0), 2),
                }
                for r in (gl_details or [])
            ] if gl_details else gl_error or 'No GL details found',
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"Customer GL investigation error: {str(e)}")
        return jsonify({'error': str(e)}), 500
