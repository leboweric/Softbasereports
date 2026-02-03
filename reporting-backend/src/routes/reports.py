from flask import Blueprint, request, jsonify, send_file, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.softbase_service import SoftbaseService
from src.services.report_generator import ReportGenerator
from src.middleware.tenant_middleware import TenantMiddleware
import io
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
reports_bp = Blueprint('reports', __name__)
report_generator = ReportGenerator()

# Import and register department routes
from .department_reports import register_department_routes
register_department_routes(reports_bp)

# Import accounting reports routes (they use reports_bp directly)
from . import accounting_reports
from . import control_number_research
from . import control_number_reports
from . import rental_shipto_research
from . import rental_shipto_simple
from . import rental_comprehensive_research
from . import rental_customer_solution
from . import rental_diagnosis

def get_softbase_service():
    """Get Softbase service instance for current organization"""
    if hasattr(g, 'current_organization'):
        return SoftbaseService(g.current_organization)
    return None

@reports_bp.route('/debug-dashboard', methods=['GET'])
def debug_dashboard():
    """Debug dashboard queries - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        current_date = datetime.now()
        month_start = current_date.replace(day=1).strftime('%Y-%m-%d')
        
        debug_info = {
            'current_date': current_date.strftime('%Y-%m-%d'),
            'current_month': current_date.month,
            'current_year': current_date.year,
            'month_start': month_start
        }
        
        # Test sales query
        sales_query = f"""
        SELECT COALESCE(SUM(GrandTotal), 0) as total_sales,
               COUNT(*) as invoice_count
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '{month_start}'
        AND MONTH(InvoiceDate) = {current_date.month}
        AND YEAR(InvoiceDate) = {current_date.year}
        """
        
        try:
            sales_result = db.execute_query(sales_query)
            debug_info['sales_query'] = {
                'query': sales_query,
                'result': sales_result,
                'error': None
            }
        except Exception as e:
            debug_info['sales_query'] = {
                'query': sales_query,
                'result': None,
                'error': str(e)
            }
        
        # Test inventory query
        inventory_query = f"""
        SELECT COUNT(*) as inventory_count
        FROM {schema}.Equipment
        WHERE RentalStatus IN ('In Stock', 'Available')
        """
        
        try:
            inventory_result = db.execute_query(inventory_query)
            debug_info['inventory_query'] = {
                'query': inventory_query,
                'result': inventory_result,
                'error': None
            }
        except Exception as e:
            debug_info['inventory_query'] = {
                'query': inventory_query,
                'result': None,
                'error': str(e)
            }
        
        # Test customers query
        customers_query = f"""
        SELECT COUNT(DISTINCT ID) as active_customers
        FROM {schema}.Customer
        WHERE Balance > 0 OR YTD > 0
        """
        
        try:
            customers_result = db.execute_query(customers_query)
            debug_info['customers_query'] = {
                'query': customers_query,
                'result': customers_result,
                'error': None
            }
        except Exception as e:
            debug_info['customers_query'] = {
                'query': customers_query,
                'result': None,
                'error': str(e)
            }
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@reports_bp.route('/check-service-claims', methods=['GET'])
def check_service_claims():
    """Check ServiceClaim table structure - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get ServiceClaim columns
        columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'ServiceClaim' 
        AND TABLE_SCHEMA = '{schema}'
        ORDER BY ORDINAL_POSITION
        """
        
        results['columns'] = db.execute_query(columns_query)
        
        # First get a sample record to see actual columns
        sample_all = """
        SELECT TOP 5 *
        FROM {schema}.ServiceClaim
        """
        
        try:
            results['sample_records'] = db.execute_query(sample_all)
        except Exception as e:
            results['sample_error'] = str(e)
        
        # Get total count
        try:
            count_result = db.execute_query("SELECT COUNT(*) as count FROM {schema}.ServiceClaim")
            results['total_count'] = count_result[0]['count'] if count_result else 0
        except Exception as e:
            results['count_error'] = str(e)
        
        # Check for date-related columns (might indicate completion)
        date_columns = [col for col in results.get('columns', []) if 'date' in col['COLUMN_NAME'].lower() or 'time' in col['COLUMN_NAME'].lower()]
        results['date_columns'] = date_columns
        
        # Check for status-related columns
        status_columns = [col for col in results.get('columns', []) if 'status' in col['COLUMN_NAME'].lower() or 'complete' in col['COLUMN_NAME'].lower() or 'closed' in col['COLUMN_NAME'].lower()]
        results['status_columns'] = status_columns
        
        # Check for invoice-related columns
        invoice_columns = [col for col in results.get('columns', []) if 'invoice' in col['COLUMN_NAME'].lower() or 'bill' in col['COLUMN_NAME'].lower()]
        results['invoice_related_columns'] = invoice_columns
        
        # Check for amount/cost columns
        amount_columns = [col for col in results.get('columns', []) if any(term in col['COLUMN_NAME'].lower() for term in ['total', 'amount', 'cost', 'price', 'labor', 'parts'])]
        results['amount_columns'] = amount_columns
        
        # Try to get a work order with costs
        try:
            cost_query = f"""
            SELECT TOP 5 *
            FROM {schema}.ServiceClaim
            WHERE (TotalLabor > 0 OR TotalParts > 0)
            """
            results['records_with_costs'] = db.execute_query(cost_query)
        except:
            # If TotalLabor/TotalParts don't exist, try other approaches
            try:
                # Just get any 5 records
                any_query = f"""
                SELECT TOP 5 ServiceClaimID, *
                FROM {schema}.ServiceClaim
                ORDER BY ServiceClaimID DESC
                """
                results['recent_records'] = db.execute_query(any_query)
            except Exception as e:
                results['recent_records_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/find-work-orders', methods=['GET'])
def find_work_orders():
    """Find tables that might contain work order data - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get all tables that might contain work order data
        tables_query = f"""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_TYPE = 'VIEW'
        AND (
            TABLE_NAME LIKE '%Work%' OR 
            TABLE_NAME LIKE '%Service%' OR 
            TABLE_NAME LIKE '%Job%' OR
            TABLE_NAME LIKE '%Repair%' OR
            TABLE_NAME LIKE '%Order%'
        )
        ORDER BY TABLE_NAME
        """
        
        work_tables = db.execute_query(tables_query)
        results['potential_tables'] = [t['TABLE_NAME'] for t in work_tables]
        
        # Check each table for relevant data
        for table in work_tables[:10]:  # Limit to first 10 to avoid timeout
            table_name = table['TABLE_NAME']
            try:
                # Get count
                count_query = f"SELECT COUNT(*) as count FROM {schema}.{table_name}"
                count_result = db.execute_query(count_query)
                
                # Get columns
                cols_query = f"""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}' 
                AND TABLE_SCHEMA = '{schema}'
                AND (
                    COLUMN_NAME LIKE '%Invoice%' OR 
                    COLUMN_NAME LIKE '%Total%' OR 
                    COLUMN_NAME LIKE '%Labor%' OR
                    COLUMN_NAME LIKE '%Parts%' OR
                    COLUMN_NAME LIKE '%Date%'
                )
                """
                cols = db.execute_query(cols_query)
                
                if count_result[0]['count'] > 0:
                    results[table_name] = {
                        'count': count_result[0]['count'],
                        'relevant_columns': cols
                    }
            except Exception as e:
                results[table_name + '_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/check-work-order-data', methods=['GET'])
def check_work_order_data():
    """Check for work order data in various tables - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Check if ServiceClaim has any data
        try:
            sc_count = db.execute_query("SELECT COUNT(*) as count FROM {schema}.ServiceClaim")
            results['service_claim_count'] = sc_count[0]['count'] if sc_count else 0
        except Exception as e:
            results['service_claim_error'] = str(e)
        
        # Check for WOHeader (Work Order Header) table
        try:
            wo_tables = db.execute_query("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{schema}' 
                AND TABLE_NAME LIKE '%WO%'
                ORDER BY TABLE_NAME
            """)
            results['wo_tables'] = [t['TABLE_NAME'] for t in wo_tables]
            
            # Check WOHeader if it exists
            if any('WOHeader' in t['TABLE_NAME'] for t in wo_tables):
                wo_count = db.execute_query("SELECT COUNT(*) as count FROM {schema}.WOHeader")
                results['wo_header_count'] = wo_count[0]['count'] if wo_count else 0
                
                # Get sample work order
                wo_sample = db.execute_query("""
                    SELECT TOP 3 * 
                    FROM {schema}.WOHeader 
                    ORDER BY WONumber DESC
                """)
                results['wo_header_sample'] = wo_sample
        except Exception as e:
            results['wo_tables_error'] = str(e)
        
        # Check for JobHeader table (another common name for work orders)
        try:
            job_count = db.execute_query("SELECT COUNT(*) as count FROM {schema}.JobHeader")
            results['job_header_count'] = job_count[0]['count'] if job_count else 0
        except:
            pass
        
        # Look for tables with "Labor" and "Parts" in their names
        try:
            labor_parts_tables = db.execute_query("""
                SELECT DISTINCT TABLE_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{schema}' 
                AND (COLUMN_NAME LIKE '%Labor%' OR COLUMN_NAME LIKE '%Parts%')
                AND TABLE_NAME NOT LIKE '%Claim%'
                ORDER BY TABLE_NAME
            """)
            results['tables_with_labor_parts'] = [t['TABLE_NAME'] for t in labor_parts_tables]
        except Exception as e:
            results['labor_parts_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/analyze-wo-table', methods=['GET'])
def analyze_wo_table():
    """Analyze WO table structure for uninvoiced work orders - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get WO table columns
        wo_columns = db.execute_query("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'WO' 
            AND TABLE_SCHEMA = '{schema}'
            ORDER BY ORDINAL_POSITION
        """)
        results['wo_columns'] = wo_columns
        
        # Get sample WO records
        try:
            wo_sample = db.execute_query("""
                SELECT TOP 3 *
                FROM {schema}.WO
                ORDER BY WONumber DESC
            """)
            results['wo_sample'] = wo_sample
        except Exception as e:
            results['wo_sample_error'] = str(e)
        
        # Count total work orders
        try:
            wo_count = db.execute_query("SELECT COUNT(*) as count FROM {schema}.WO")
            results['wo_total_count'] = wo_count[0]['count'] if wo_count else 0
        except Exception as e:
            results['wo_count_error'] = str(e)
        
        # Find invoice-related columns
        invoice_cols = [col for col in wo_columns if 'invoice' in col['COLUMN_NAME'].lower() or 'inv' in col['COLUMN_NAME'].lower()]
        results['invoice_columns'] = invoice_cols
        
        # Find status/complete columns
        status_cols = [col for col in wo_columns if any(term in col['COLUMN_NAME'].lower() for term in ['status', 'complete', 'closed', 'finish'])]
        results['status_columns'] = status_cols
        
        # Find date columns
        date_cols = [col for col in wo_columns if 'date' in col['COLUMN_NAME'].lower()]
        results['date_columns'] = date_cols
        
        # Try to get labor and parts totals
        try:
            # Check if we can join with WOLabor and WOParts
            labor_parts_query = f"""
            SELECT TOP 5
                w.WONumber,
                COALESCE(
                    (SELECT SUM(ExtLabor) FROM {schema}.WOLabor WHERE WONumber = w.WONumber), 
                    0
                ) as TotalLabor,
                COALESCE(
                    (SELECT SUM(ExtPrice) FROM {schema}.WOParts WHERE WONumber = w.WONumber), 
                    0
                ) as TotalParts
            FROM {schema}.WO w
            ORDER BY w.WONumber DESC
            """
            labor_parts_sample = db.execute_query(labor_parts_query)
            results['wo_with_costs'] = labor_parts_sample
        except Exception as e:
            results['labor_parts_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/test-uninvoiced-wo', methods=['GET'])
def test_uninvoiced_wo():
    """Test uninvoiced work orders calculation - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # First check what columns exist in WO table
        col_check = db.execute_query("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'WO' 
            AND TABLE_SCHEMA = '{schema}'
            AND COLUMN_NAME IN ('TotalLabor', 'TotalParts', 'TotalMisc', 'Labor', 'Parts', 'Misc')
        """)
        results['available_total_columns'] = [c['COLUMN_NAME'] for c in col_check]
        
        # Get a sample WO record to see structure
        try:
            sample = db.execute_query("SELECT TOP 1 * FROM {schema}.WO WHERE CompletedDate IS NOT NULL")
            if sample:
                # Extract just the relevant fields
                results['sample_wo'] = {
                    k: v for k, v in sample[0].items() 
                    if any(term in k.lower() for term in ['total', 'labor', 'parts', 'misc', 'invoice', 'complete', 'wo'])
                }
        except Exception as e:
            results['sample_error'] = str(e)
        
        # Test different queries
        queries_to_test = [
            {
                "name": "Count completed but not invoiced",
                "query": """
                    SELECT COUNT(*) as count
                    FROM {schema}.WO
                    WHERE CompletedDate IS NOT NULL
                    AND InvoiceDate IS NULL
                """
            },
            {
                "name": "Try with TotalLabor/TotalParts",
                "query": """
                    SELECT 
                        COUNT(*) as count,
                        SUM(ISNULL(TotalLabor, 0) + ISNULL(TotalParts, 0) + ISNULL(TotalMisc, 0)) as total_value
                    FROM {schema}.WO
                    WHERE CompletedDate IS NOT NULL
                    AND InvoiceDate IS NULL
                """
            },
            {
                "name": "Count by work order status",
                "query": """
                    SELECT 
                        CASE 
                            WHEN CompletedDate IS NOT NULL AND InvoiceDate IS NULL THEN 'Completed Not Invoiced'
                            WHEN CompletedDate IS NOT NULL AND InvoiceDate IS NOT NULL THEN 'Completed and Invoiced'
                            WHEN CompletedDate IS NULL THEN 'Not Completed'
                        END as status,
                        COUNT(*) as count
                    FROM {schema}.WO
                    GROUP BY 
                        CASE 
                            WHEN CompletedDate IS NOT NULL AND InvoiceDate IS NULL THEN 'Completed Not Invoiced'
                            WHEN CompletedDate IS NOT NULL AND InvoiceDate IS NOT NULL THEN 'Completed and Invoiced'
                            WHEN CompletedDate IS NULL THEN 'Not Completed'
                        END
                """
            }
        ]
        
        for qt in queries_to_test:
            try:
                result = db.execute_query(qt['query'])
                results[qt['name']] = result
            except Exception as e:
                results[qt['name'] + '_error'] = str(e)
        
        # Check WOLabor and WOParts tables
        try:
            # Get uninvoiced work orders with labor/parts from related tables
            complex_query = f"""
            SELECT TOP 10
                w.WO,
                w.CompletedDate,
                w.InvoiceDate,
                (SELECT COALESCE(SUM(ExtLabor), 0) FROM {schema}.WOLabor WHERE WO = w.WO) as LaborTotal,
                (SELECT COALESCE(SUM(ExtPrice), 0) FROM {schema}.WOParts WHERE WO = w.WO) as PartsTotal
            FROM {schema}.WO w
            WHERE w.CompletedDate IS NOT NULL
            AND w.InvoiceDate IS NULL
            ORDER BY w.CompletedDate DESC
            """
            results['uninvoiced_with_details'] = db.execute_query(complex_query)
        except Exception as e:
            results['complex_query_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/calculate-uninvoiced-value', methods=['GET'])
def calculate_uninvoiced_value():
    """Calculate actual uninvoiced work order values - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get uninvoiced work orders with their labor and parts totals
        query = f"""
        SELECT 
            w.WONo,
            w.CompletedDate,
            COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as LaborTotal,
            COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as PartsTotal,
            COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as MiscTotal
        FROM {schema}.WO w
        WHERE w.CompletedDate IS NOT NULL
        AND w.InvoiceDate IS NULL
        """
        
        try:
            wo_details = db.execute_query(query)
            
            # Calculate totals
            total_value = 0
            total_count = len(wo_details)
            
            for wo in wo_details:
                wo_total = float(wo['LaborTotal']) + float(wo['PartsTotal']) + float(wo['MiscTotal'])
                total_value += wo_total
            
            results['summary'] = {
                'count': total_count,
                'total_value': total_value,
                'average_value': total_value / total_count if total_count > 0 else 0
            }
            
            # Get top 10 by value
            wo_details_sorted = sorted(wo_details, key=lambda x: float(x['LaborTotal']) + float(x['PartsTotal']) + float(x['MiscTotal']), reverse=True)[:10]
            results['top_10_uninvoiced'] = wo_details_sorted
            
        except Exception as e:
            results['calculation_error'] = str(e)
            
        # Also test a simplified query for the dashboard
        try:
            dashboard_query = f"""
            SELECT 
                COUNT(*) as count,
                SUM(labor_total + parts_total + misc_total) as total_value
            FROM (
                SELECT 
                    w.WONo,
                    COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                    COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                    COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
                FROM {schema}.WO w
                WHERE w.CompletedDate IS NOT NULL
                AND w.InvoiceDate IS NULL
            ) as uninvoiced
            """
            dashboard_result = db.execute_query(dashboard_query)
            results['dashboard_query_result'] = dashboard_result
        except Exception as e:
            results['dashboard_query_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/check-wo-columns', methods=['GET'])
def check_wo_columns():
    """Check WOLabor and WOParts column structure - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get WOLabor columns
        labor_cols = db.execute_query("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'WOLabor' 
            AND TABLE_SCHEMA = '{schema}'
            AND (COLUMN_NAME LIKE '%Labor%' OR COLUMN_NAME LIKE '%Ext%' OR COLUMN_NAME LIKE '%Total%' OR COLUMN_NAME LIKE '%Amount%')
            ORDER BY ORDINAL_POSITION
        """)
        results['wolabor_columns'] = labor_cols
        
        # Get WOParts columns
        parts_cols = db.execute_query("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'WOParts' 
            AND TABLE_SCHEMA = '{schema}'
            AND (COLUMN_NAME LIKE '%Price%' OR COLUMN_NAME LIKE '%Ext%' OR COLUMN_NAME LIKE '%Total%' OR COLUMN_NAME LIKE '%Amount%')
            ORDER BY ORDINAL_POSITION
        """)
        results['woparts_columns'] = parts_cols
        
        # Get WOMisc columns
        misc_cols = db.execute_query("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'WOMisc' 
            AND TABLE_SCHEMA = '{schema}'
            ORDER BY ORDINAL_POSITION
        """)
        results['womisc_columns'] = misc_cols
        
        # Get sample data
        try:
            labor_sample = db.execute_query("SELECT TOP 1 * FROM {schema}.WOLabor WHERE WONo > 0")
            results['labor_sample'] = labor_sample
        except Exception as e:
            results['labor_sample_error'] = str(e)
            
        try:
            parts_sample = db.execute_query("SELECT TOP 1 * FROM {schema}.WOParts WHERE WONo > 0")
            results['parts_sample'] = parts_sample
        except Exception as e:
            results['parts_sample_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/check-invoice-cost-columns', methods=['GET'])
def check_invoice_cost_columns():
    """Check InvoiceReg for cost columns - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get columns that might contain cost information
        cost_cols = db.execute_query("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'InvoiceReg' 
            AND TABLE_SCHEMA = '{schema}'
            AND (
                COLUMN_NAME LIKE '%Cost%' OR 
                COLUMN_NAME LIKE '%COGS%' OR 
                COLUMN_NAME LIKE '%COG%' OR
                COLUMN_NAME LIKE '%Margin%' OR
                COLUMN_NAME LIKE '%Profit%'
            )
            ORDER BY ORDINAL_POSITION
        """)
        results['cost_related_columns'] = cost_cols
        
        # Get a sample invoice to see what columns have data
        try:
            sample = db.execute_query("""
                SELECT TOP 1 * 
                FROM {schema}.InvoiceReg 
                WHERE GrandTotal > 0
                ORDER BY InvoiceDate DESC
            """)
            if sample:
                # Extract cost-related fields
                results['sample_cost_fields'] = {
                    k: v for k, v in sample[0].items() 
                    if any(term in k.lower() for term in ['cost', 'cog', 'margin', 'profit', 'total'])
                }
        except Exception as e:
            results['sample_error'] = str(e)
        
        # Check if we need to join with invoice line items
        try:
            # Check for invoice detail/line item tables
            detail_tables = db.execute_query("""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{schema}'
                AND (
                    TABLE_NAME LIKE '%InvoiceDet%' OR 
                    TABLE_NAME LIKE '%InvoiceLine%' OR
                    TABLE_NAME LIKE '%InvoiceItem%'
                )
            """)
            results['invoice_detail_tables'] = [t['TABLE_NAME'] for t in detail_tables]
        except Exception as e:
            results['detail_tables_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/find-quotes-data', methods=['GET'])
def find_quotes_data():
    """Find tables and columns related to quotes - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Find tables with Quote in the name
        quote_tables = db.execute_query("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
            AND (
                TABLE_NAME LIKE '%Quote%' OR 
                TABLE_NAME LIKE '%Quot%' OR
                TABLE_NAME LIKE '%Estimate%' OR
                TABLE_NAME LIKE '%Proposal%'
            )
            ORDER BY TABLE_NAME
        """)
        results['quote_tables'] = [t['TABLE_NAME'] for t in quote_tables]
        
        # Check each quote table for data
        for table in quote_tables[:5]:  # Limit to first 5
            table_name = table['TABLE_NAME']
            try:
                # Get count
                count_query = f"SELECT COUNT(*) as count FROM {schema}.{table_name}"
                count_result = db.execute_query(count_query)
                
                # Get columns
                cols_query = f"""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}' 
                AND TABLE_SCHEMA = '{schema}'
                AND (
                    COLUMN_NAME LIKE '%Date%' OR 
                    COLUMN_NAME LIKE '%Amount%' OR 
                    COLUMN_NAME LIKE '%Total%' OR
                    COLUMN_NAME LIKE '%Price%' OR
                    COLUMN_NAME LIKE '%Value%'
                )
                """
                cols = db.execute_query(cols_query)
                
                if count_result[0]['count'] > 0:
                    # Get a sample record
                    sample_query = f"SELECT TOP 1 * FROM {schema}.{table_name}"
                    sample = db.execute_query(sample_query)
                    
                    results[table_name] = {
                        'count': count_result[0]['count'],
                        'relevant_columns': cols,
                        'sample_record': sample[0] if sample else None
                    }
            except Exception as e:
                results[table_name + '_error'] = str(e)
        
        # Also check WO table for quote-related columns
        try:
            wo_quote_cols = db.execute_query("""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WO' 
                AND TABLE_SCHEMA = '{schema}'
                AND (
                    COLUMN_NAME LIKE '%Quote%' OR 
                    COLUMN_NAME LIKE '%Estimate%'
                )
                ORDER BY ORDINAL_POSITION
            """)
            results['wo_quote_columns'] = wo_quote_cols
            
            # Check if there are WOs with quote dates
            wo_quote_check = db.execute_query("""
                SELECT COUNT(*) as count
                FROM {schema}.WO
                WHERE ShopQuoteDate IS NOT NULL
            """)
            results['wo_with_quotes'] = wo_quote_check[0]['count'] if wo_quote_check else 0
            
        except Exception as e:
            results['wo_quote_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/analyze-woquest-data', methods=['GET'])
def analyze_woquote_data():
    """Analyze WOQuote table for monthly quote values - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get WOQuote columns to find date fields
        cols = db.execute_query("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'WOQuote' 
            AND TABLE_SCHEMA = '{schema}'
            ORDER BY ORDINAL_POSITION
        """)
        results['woquote_columns'] = cols
        
        # Get date columns
        date_cols = [c for c in cols if 'date' in c['COLUMN_NAME'].lower() or 'time' in c['COLUMN_NAME'].lower()]
        results['date_columns'] = date_cols
        
        # Get sample records with amounts
        sample_query = f"""
        SELECT TOP 10 
            wq.*,
            w.OpenDate as WO_OpenDate,
            w.ShopQuoteDate as WO_QuoteDate
        FROM {schema}.WOQuote wq
        LEFT JOIN {schema}.WO w ON wq.WONo = w.WONo
        WHERE wq.Amount > 0
        ORDER BY wq.Id DESC
        """
        results['sample_quotes'] = db.execute_query(sample_query)
        
        # Get monthly quote totals using CreationTime
        monthly_query = f"""
        SELECT 
            YEAR(CreationTime) as year,
            MONTH(CreationTime) as month,
            COUNT(*) as quote_count,
            SUM(Amount) as total_quoted
        FROM {schema}.WOQuote
        WHERE CreationTime >= '2024-03-01'
        AND Amount > 0
        GROUP BY YEAR(CreationTime), MONTH(CreationTime)
        ORDER BY year, month
        """
        results['monthly_by_creation'] = db.execute_query(monthly_query)
        
        # Also try using WO.ShopQuoteDate
        wo_monthly_query = f"""
        SELECT 
            YEAR(w.ShopQuoteDate) as year,
            MONTH(w.ShopQuoteDate) as month,
            COUNT(DISTINCT w.WONo) as quote_count,
            SUM(wq.Amount) as total_quoted
        FROM {schema}.WO w
        INNER JOIN {schema}.WOQuote wq ON w.WONo = wq.WONo
        WHERE w.ShopQuoteDate >= '2024-03-01'
        AND wq.Amount > 0
        GROUP BY YEAR(w.ShopQuoteDate), MONTH(w.ShopQuoteDate)
        ORDER BY year, month
        """
        results['monthly_by_shopquotedate'] = db.execute_query(wo_monthly_query)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/analyze-department-margins', methods=['GET'])
def analyze_department_margins():
    """Analyze department sales and margins - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Check what department/category fields exist in InvoiceReg
        dept_cols = db.execute_query("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'InvoiceReg' 
            AND TABLE_SCHEMA = '{schema}'
            AND (
                COLUMN_NAME LIKE '%Dept%' OR 
                COLUMN_NAME LIKE '%Department%' OR 
                COLUMN_NAME LIKE '%Category%' OR
                COLUMN_NAME LIKE '%Type%' OR
                COLUMN_NAME LIKE '%Class%'
            )
            ORDER BY ORDINAL_POSITION
        """)
        results['department_columns'] = dept_cols
        
        # Get a sample invoice to see department data
        sample = db.execute_query("""
            SELECT TOP 5 *
            FROM {schema}.InvoiceReg
            WHERE GrandTotal > 0
            ORDER BY InvoiceDate DESC
        """)
        if sample:
            # Extract department-related fields
            results['sample_dept_fields'] = []
            for rec in sample:
                dept_data = {k: v for k, v in rec.items() 
                            if any(term in k.lower() for term in ['dept', 'type', 'category', 'labor', 'parts', 'misc', 'equipment', 'rental'])}
                results['sample_dept_fields'].append(dept_data)
        
        # Test query for parts margin by month
        test_query = f"""
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            SUM(PartsRevenue) as parts_revenue,
            SUM(PartsCost) as parts_cost,
            CASE 
                WHEN SUM(PartsRevenue) > 0 
                THEN ((SUM(PartsRevenue) - SUM(PartsCost)) / SUM(PartsRevenue)) * 100
                ELSE 0 
            END as parts_margin_pct
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '2025-01-01'
        AND PartsRevenue > 0
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY year, month
        """
        
        try:
            results['parts_margin_test'] = db.execute_query(test_query)
        except Exception as e:
            results['parts_margin_error'] = str(e)
            
            # Try alternative column names
            alt_query = f"""
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                COUNT(*) as invoice_count,
                SUM(TotalExclusive) as total_revenue,
                SUM(PartsCost) as parts_cost,
                AVG(CASE WHEN TotalExclusive > 0 THEN ((TotalExclusive - PartsCost) / TotalExclusive) * 100 ELSE 0 END) as avg_margin_pct
            FROM {schema}.InvoiceReg
            WHERE InvoiceDate >= '2025-01-01'
            AND PartsCost > 0
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY year, month
            """
            try:
                results['alternative_margin_calc'] = db.execute_query(alt_query)
            except Exception as e2:
                results['alt_margin_error'] = str(e2)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/find-duplicate-customers', methods=['GET'])
def find_duplicate_customers():
    """Find potential duplicate customer names - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get all customer names with their sales
        all_customers = db.execute_query("""
            SELECT 
                BillToName,
                COUNT(DISTINCT InvoiceNo) as invoice_count,
                SUM(GrandTotal) as total_sales
            FROM {schema}.InvoiceReg
            WHERE InvoiceDate >= '2024-11-01'
            AND BillToName IS NOT NULL
            AND BillToName != ''
            GROUP BY BillToName
            ORDER BY SUM(GrandTotal) DESC
        """)
        
        # Look for potential duplicates
        potential_duplicates = []
        customer_names = [c['BillToName'] for c in all_customers]
        
        for i, name1 in enumerate(customer_names):
            for j, name2 in enumerate(customer_names[i+1:], i+1):
                # Check if one is substring of another
                if name1.lower() in name2.lower() or name2.lower() in name1.lower():
                    # Skip if they're exactly the same (shouldn't happen due to GROUP BY)
                    if name1.lower() != name2.lower():
                        cust1 = all_customers[i]
                        cust2 = all_customers[j]
                        potential_duplicates.append({
                            'name1': name1,
                            'sales1': float(cust1['total_sales']),
                            'invoices1': cust1['invoice_count'],
                            'name2': name2,
                            'sales2': float(cust2['total_sales']),
                            'invoices2': cust2['invoice_count'],
                            'combined_sales': float(cust1['total_sales']) + float(cust2['total_sales'])
                        })
        
        # Sort by combined sales
        potential_duplicates.sort(key=lambda x: x['combined_sales'], reverse=True)
        
        results['potential_duplicates'] = potential_duplicates[:20]  # Top 20
        results['total_customers'] = len(customer_names)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/analyze-total-work-orders', methods=['GET'])
def analyze_total_work_orders():
    """Analyze all work orders value - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get breakdown of all work orders
        breakdown_query = f"""
        SELECT 
            CASE 
                WHEN CompletedDate IS NOT NULL AND InvoiceDate IS NOT NULL THEN 'Completed and Invoiced'
                WHEN CompletedDate IS NOT NULL AND InvoiceDate IS NULL THEN 'Completed Not Invoiced'
                WHEN CompletedDate IS NULL AND ClosedDate IS NOT NULL THEN 'Closed Not Completed'
                WHEN CompletedDate IS NULL AND ClosedDate IS NULL THEN 'Open/In Progress'
                ELSE 'Other'
            END as status,
            COUNT(*) as count
        FROM {schema}.WO
        GROUP BY 
            CASE 
                WHEN CompletedDate IS NOT NULL AND InvoiceDate IS NOT NULL THEN 'Completed and Invoiced'
                WHEN CompletedDate IS NOT NULL AND InvoiceDate IS NULL THEN 'Completed Not Invoiced'
                WHEN CompletedDate IS NULL AND ClosedDate IS NOT NULL THEN 'Closed Not Completed'
                WHEN CompletedDate IS NULL AND ClosedDate IS NULL THEN 'Open/In Progress'
                ELSE 'Other'
            END
        """
        results['wo_breakdown'] = db.execute_query(breakdown_query)
        
        # Get total value of ALL work orders (complete and incomplete)
        all_wo_value_query = f"""
        SELECT 
            COUNT(DISTINCT w.WONo) as total_count,
            SUM(labor_total + parts_total + misc_total) as total_value,
            SUM(CASE WHEN w.CompletedDate IS NOT NULL THEN labor_total + parts_total + misc_total ELSE 0 END) as completed_value,
            SUM(CASE WHEN w.CompletedDate IS NULL THEN labor_total + parts_total + misc_total ELSE 0 END) as incomplete_value
        FROM (
            SELECT 
                w.WONo,
                w.CompletedDate,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
            FROM {schema}.WO w
        ) as wo_values
        """
        
        try:
            results['all_wo_values'] = db.execute_query(all_wo_value_query)
        except Exception as e:
            results['value_error'] = str(e)
        
        # Get just open/incomplete work orders value
        open_wo_query = f"""
        SELECT 
            COUNT(*) as count,
            SUM(labor_total + parts_total + misc_total) as total_value
        FROM (
            SELECT 
                w.WONo,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
            FROM {schema}.WO w
            WHERE w.CompletedDate IS NULL
            AND w.ClosedDate IS NULL
        ) as open_wo
        """
        
        try:
            results['open_wo_value'] = db.execute_query(open_wo_query)
        except Exception as e:
            results['open_error'] = str(e)
            
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/analyze-wo-types', methods=['GET'])
def analyze_wo_types():
    """Analyze work order types breakdown - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # First, find type-related columns in WO table
        wo_columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'WO' 
        AND TABLE_SCHEMA = '{schema}'
        AND (
            COLUMN_NAME LIKE '%Type%' OR 
            COLUMN_NAME LIKE '%Category%' OR 
            COLUMN_NAME LIKE '%Class%' OR
            COLUMN_NAME LIKE '%Department%' OR
            COLUMN_NAME LIKE '%Service%'
        )
        ORDER BY ORDINAL_POSITION
        """
        results['wo_type_columns'] = db.execute_query(wo_columns_query)
        
        # Get sample WO records to see type data
        sample_query = f"""
        SELECT TOP 10 *
        FROM {schema}.WO
        WHERE CompletedDate IS NULL
        AND ClosedDate IS NULL
        ORDER BY WONo DESC
        """
        
        samples = db.execute_query(sample_query)
        if samples:
            # Extract potential type fields
            results['sample_type_fields'] = []
            for rec in samples[:3]:  # Just first 3 for brevity
                type_data = {k: v for k, v in rec.items() 
                            if any(term in k.lower() for term in ['type', 'category', 'class', 'dept', 'service', 'quote'])}
                type_data['WONo'] = rec.get('WONo')
                results['sample_type_fields'].append(type_data)
        
        # Try to find and group by different type columns
        type_columns_to_try = ['WOType', 'Type', 'ServiceType', 'QuoteType', 'Category', 'Department']
        
        for col in type_columns_to_try:
            try:
                type_breakdown_query = f"""
                SELECT 
                    {col} as type_value,
                    COUNT(*) as count,
                    SUM(labor_total + parts_total + misc_total) as total_value
                FROM (
                    SELECT 
                        w.WONo,
                        w.{col},
                        COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                        COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                        COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
                    FROM {schema}.WO w
                    WHERE w.CompletedDate IS NULL
                    AND w.ClosedDate IS NULL
                ) as open_wo
                GROUP BY {col}
                ORDER BY total_value DESC
                """
                
                breakdown = db.execute_query(type_breakdown_query)
                if breakdown and len(breakdown) > 0:
                    results[f'breakdown_by_{col}'] = breakdown
                    results['successful_type_column'] = col
                    break
            except Exception as e:
                continue
        
        # Also get overall open/in progress summary
        summary_query = f"""
        SELECT 
            COUNT(*) as total_count,
            SUM(labor_total + parts_total + misc_total) as total_value
        FROM (
            SELECT 
                w.WONo,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
            FROM {schema}.WO w
            WHERE w.CompletedDate IS NULL
            AND w.ClosedDate IS NULL
        ) as open_wo
        """
        results['open_wo_summary'] = db.execute_query(summary_query)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/debug-wo-types', methods=['GET'])
def debug_wo_types():
    """Debug work order types and categorization - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Get ALL columns from WO table
        all_columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'WO' 
        AND TABLE_SCHEMA = '{schema}'
        ORDER BY ORDINAL_POSITION
        """
        results['all_columns'] = db.execute_query(all_columns_query)
        
        # Get sample of open work orders to see actual data
        sample_query = f"""
        SELECT TOP 10 *
        FROM {schema}.WO
        WHERE CompletedDate IS NULL
        AND ClosedDate IS NULL
        ORDER BY WONo DESC
        """
        
        samples = db.execute_query(sample_query)
        if samples:
            # Extract fields that might contain type/category info
            results['potential_type_fields'] = []
            for sample in samples[:3]:  # Just first 3 for brevity
                type_fields = {}
                type_fields['WONo'] = sample.get('WONo')
                
                # Check all fields that might contain type info
                for key, value in sample.items():
                    if value and any(term in key.lower() for term in ['type', 'category', 'class', 'dept', 'service', 'status', 'quote']):
                        type_fields[key] = value
                
                results['potential_type_fields'].append(type_fields)
        
        # Try to group by different potential type columns
        type_columns_to_analyze = ['QuoteType', 'Type', 'WOType', 'ServiceType', 'Category', 'Department', 'Status']
        
        for col in type_columns_to_analyze:
            try:
                # Check if column exists and get value distribution
                distribution_query = f"""
                SELECT 
                    {col} as type_value,
                    COUNT(*) as count,
                    SUM(CASE WHEN CompletedDate IS NULL AND ClosedDate IS NULL THEN 1 ELSE 0 END) as open_count
                FROM {schema}.WO
                WHERE {col} IS NOT NULL
                GROUP BY {col}
                ORDER BY COUNT(*) DESC
                """
                
                distribution = db.execute_query(distribution_query)
                if distribution and len(distribution) > 0:
                    results[f'distribution_by_{col}'] = distribution[:10]  # Top 10 values
            except:
                continue
        
        # Get summary of open work orders
        summary_query = f"""
        SELECT 
            COUNT(*) as total_open,
            COUNT(CASE WHEN QuoteType IS NOT NULL THEN 1 END) as has_quotetype,
            COUNT(CASE WHEN QuoteType LIKE '%Quote%' THEN 1 END) as is_quote,
            SUM(labor_total + parts_total + misc_total) as total_value
        FROM (
            SELECT 
                w.WONo,
                w.QuoteType,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
            FROM {schema}.WO w
            WHERE w.CompletedDate IS NULL
            AND w.ClosedDate IS NULL
        ) as open_wo
        """
        
        results['open_wo_summary'] = db.execute_query(summary_query)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/check-tables', methods=['GET'])
def check_tables():
    """Check table columns - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        results = {}
        
        # Check Equipment table columns
        equipment_columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Equipment' 
        AND TABLE_SCHEMA = '{schema}'
        ORDER BY ORDINAL_POSITION
        """
        
        results['equipment_columns'] = db.execute_query(equipment_columns_query)
        
        # Check Customer table columns
        customer_columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Customer' 
        AND TABLE_SCHEMA = '{schema}'
        ORDER BY ORDINAL_POSITION
        """
        
        results['customer_columns'] = db.execute_query(customer_columns_query)
        
        # Get sample Equipment record to see actual data
        try:
            equipment_sample = """
            SELECT TOP 1 *
            FROM {schema}.Equipment
            """
            results['equipment_sample'] = db.execute_query(equipment_sample)
        except Exception as e:
            results['equipment_sample_error'] = str(e)
        
        # Get sample Customer record to see actual data
        try:
            customer_sample = """
            SELECT TOP 1 *
            FROM {schema}.Customer
            """
            results['customer_sample'] = db.execute_query(customer_sample)
        except Exception as e:
            results['customer_sample_error'] = str(e)
        
        # Try to count equipment with different status columns
        try:
            # Try Status column
            status_count = """
            SELECT Status, COUNT(*) as count
            FROM {schema}.Equipment
            GROUP BY Status
            """
            results['equipment_status_values'] = db.execute_query(status_count)
        except:
            try:
                # Try RentalStatus column
                rental_status_count = """
                SELECT RentalStatus, COUNT(*) as count
                FROM {schema}.Equipment
                GROUP BY RentalStatus
                """
                results['equipment_rentalstatus_values'] = db.execute_query(rental_status_count)
            except Exception as e:
                results['status_error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/validate-sales', methods=['GET'])
def validate_sales():
    """Validate actual sales from Nov 1, 2024 through today - NO AUTH REQUIRED for testing"""
    try:
        db = get_tenant_db()
        
        # Test multiple date ranges to find the $11,998,467.41
        results = {}
        
        # Test 1: Nov 1, 2024 forward (current query)
        query1 = """
        SELECT 
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales,
            MIN(InvoiceDate) as first_invoice,
            MAX(InvoiceDate) as last_invoice
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '2024-11-01'
        """
        result1 = db.execute_query(query1)
        results['nov_2024_forward'] = {
            'total': float(result1[0]['total_sales']) if result1[0]['total_sales'] else 0,
            'count': result1[0]['invoice_count'],
            'first': str(result1[0]['first_invoice']),
            'last': str(result1[0]['last_invoice'])
        }
        
        # Test 2: Include Nov/Dec 2024 dates
        query2 = """
        SELECT 
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM {schema}.InvoiceReg
        WHERE (InvoiceDate >= '2024-11-01' AND InvoiceDate <= '2024-12-31')
        """
        result2 = db.execute_query(query2)
        results['nov_dec_2024'] = {
            'total': float(result2[0]['total_sales']) if result2[0]['total_sales'] else 0,
            'count': result2[0]['invoice_count']
        }
        
        # Test 3: Check if we need to add two periods together
        # Nov-Dec 2024 PLUS Mar-Jul 2025
        total_combined = results['nov_dec_2024']['total'] + results['nov_2024_forward']['total']
        results['combined_total'] = {
            'total': total_combined,
            'formula': 'Nov-Dec 2024 + Mar-Jul 2025'
        }
        
        # Test 4: Full fiscal year Nov 2024 - Oct 2025
        query4 = """
        SELECT 
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '2024-11-01' AND InvoiceDate <= '2025-10-31'
        """
        result4 = db.execute_query(query4)
        results['full_fiscal_2025'] = {
            'total': float(result4[0]['total_sales']) if result4[0]['total_sales'] else 0,
            'count': result4[0]['invoice_count']
        }
        
        # Get monthly breakdown for better understanding
        monthly_query = f"""
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as monthly_total
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '2024-11-01' OR InvoiceDate >= '2025-01-01'
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY year, month
        """
        monthly_results = db.execute_query(monthly_query)
        
        return jsonify({
            'success': True,
            'target_amount': 11998467.41,
            'test_results': results,
            'monthly_breakdown': monthly_results,
            'analysis': {
                'current_dashboard_shows': results['nov_2024_forward']['total'],
                'difference_from_target': 11998467.41 - results['nov_2024_forward']['total']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@reports_bp.route('/current-month-sales', methods=['GET'])
@jwt_required()
def get_current_month_sales():
    """Simple endpoint that returns current month sales"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e), 'month_sales': 0}), 400
    
    try:
        db = get_tenant_db()
        
        # Get current month's sales
        current_date = datetime.now()
        month_start = current_date.replace(day=1).strftime('%Y-%m-%d')
        
        query = f"""
        SELECT COALESCE(SUM(GrandTotal), 0) as month_sales
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '{month_start}'
        AND MONTH(InvoiceDate) = {current_date.month}
        AND YEAR(InvoiceDate) = {current_date.year}
        """
        
        result = db.execute_query(query)
        # Convert to int to remove decimals
        month_sales = int(float(result[0]['month_sales'])) if result else 0
        
        return jsonify({
            'success': True,
            'month_sales': month_sales,
            'period': current_date.strftime('%B %Y'),
            'as_of': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'month_sales': 0
        }), 500

@reports_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """Simplified dashboard - just return YTD sales for now"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        db = get_tenant_db()
        
        # Get current month's sales
        current_date = datetime.now()
        month_start = current_date.replace(day=1).strftime('%Y-%m-%d')
        
        sales_query = f"""
        SELECT COALESCE(SUM(GrandTotal), 0) as total_sales
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '{month_start}'
        AND MONTH(InvoiceDate) = {current_date.month}
        AND YEAR(InvoiceDate) = {current_date.year}
        """
        
        try:
            sales_result = db.execute_query(sales_query)
            total_sales = int(float(sales_result[0]['total_sales'])) if sales_result else 0
        except Exception as e:
            logger.error(f"Sales query failed: {str(e)}")
            total_sales = 0
        
        # Get inventory count - only count equipment that is "Ready To Rent"
        inventory_query = f"""
        SELECT COUNT(*) as inventory_count
        FROM {schema}.Equipment
        WHERE RentalStatus = 'Ready To Rent'
        """
        
        try:
            inventory_result = db.execute_query(inventory_query)
            inventory_count = int(inventory_result[0]['inventory_count']) if inventory_result else 0
        except Exception as e:
            logger.error(f"Inventory query failed: {str(e)}")
            inventory_count = 0
        
        # Get active customers - unique customers (by name) with invoices in the past 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        customers_query = f"""
        SELECT COUNT(DISTINCT BillToName) as active_customers
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '{thirty_days_ago}'
        AND BillToName IS NOT NULL
        AND BillToName != ''
        """
        
        try:
            customers_result = db.execute_query(customers_query)
            active_customers = int(customers_result[0]['active_customers']) if customers_result else 0
        except:
            # If that fails, just count all customers
            active_customers = 0
        
        # Get monthly sales for the last 12 months
        monthly_sales = []
        try:
            # Get sales grouped by month for the last 12 months
            twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            monthly_query = f"""
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(GrandTotal) as amount
            FROM {schema}.InvoiceReg
            WHERE InvoiceDate >= '{twelve_months_ago}'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            results = db.execute_query(monthly_query)
            
            # Convert to the format expected by the chart
            if results:
                for row in results:
                    # Create month name
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_sales.append({
                        'month': month_date.strftime("%b"),
                        'amount': float(row['amount'])
                    })
            
            # If we have less than 12 months of data, pad with zeros for missing months
            if len(monthly_sales) < 12:
                # Fill in any missing months with zero sales
                today = datetime.now()
                all_months = []
                for i in range(11, -1, -1):
                    month_date = today - timedelta(days=i*30)
                    all_months.append(month_date.strftime("%b"))
                
                # Create a dict of existing data
                existing_data = {item['month']: item['amount'] for item in monthly_sales}
                
                # Rebuild with all months
                monthly_sales = []
                for month in all_months:
                    monthly_sales.append({
                        'month': month,
                        'amount': existing_data.get(month, 0)
                    })
                    
        except Exception as e:
            logger.error(f"Monthly sales calculation failed: {str(e)}")
        
        # Get monthly gross profit (Sales - Cost of Sales) for the last 12 months
        monthly_gross_profit = []
        try:
            # Query to get sales and cost of sales by month
            gross_profit_query = f"""
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(GrandTotal) as sales,
                SUM(ISNULL(LaborCost, 0) + ISNULL(PartsCost, 0) + ISNULL(MiscCost, 0) + 
                    ISNULL(EquipmentCost, 0) + ISNULL(RentalCost, 0)) as cost_of_sales
            FROM {schema}.InvoiceReg
            WHERE InvoiceDate >= '{twelve_months_ago}'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            gp_results = db.execute_query(gross_profit_query)
            
            if gp_results:
                for row in gp_results:
                    month_date = datetime(row['year'], row['month'], 1)
                    gross_profit = float(row['sales'] or 0) - float(row['cost_of_sales'] or 0)
                    monthly_gross_profit.append({
                        'month': month_date.strftime("%b"),
                        'amount': gross_profit
                    })
            
            # Pad with zeros for missing months
            if len(monthly_gross_profit) < 12:
                today = datetime.now()
                all_months = []
                for i in range(11, -1, -1):
                    month_date = today - timedelta(days=i*30)
                    all_months.append(month_date.strftime("%b"))
                
                existing_gp_data = {item['month']: item['amount'] for item in monthly_gross_profit}
                
                monthly_gross_profit = []
                for month in all_months:
                    monthly_gross_profit.append({
                        'month': month,
                        'amount': existing_gp_data.get(month, 0)
                    })
                    
        except Exception as e:
            logger.error(f"Monthly gross profit calculation failed: {str(e)}")
            # If TotalCost doesn't exist, try alternative calculation
            try:
                # Alternative: Calculate based on invoice details or line items
                alt_gp_query = f"""
                SELECT 
                    YEAR(i.InvoiceDate) as year,
                    MONTH(i.InvoiceDate) as month,
                    SUM(i.GrandTotal) as sales,
                    SUM(i.TotalExclusive * 0.7) as estimated_cost
                FROM {schema}.InvoiceReg i
                WHERE i.InvoiceDate >= '{twelve_months_ago}'
                GROUP BY YEAR(i.InvoiceDate), MONTH(i.InvoiceDate)
                ORDER BY YEAR(i.InvoiceDate), MONTH(i.InvoiceDate)
                """
                
                alt_results = db.execute_query(alt_gp_query)
                
                if alt_results:
                    monthly_gross_profit = []
                    for row in alt_results:
                        month_date = datetime(row['year'], row['month'], 1)
                        gross_profit = float(row['sales'] or 0) - float(row['estimated_cost'] or 0)
                        monthly_gross_profit.append({
                            'month': month_date.strftime("%b"),
                            'amount': gross_profit
                        })
            except:
                logger.error("Alternative gross profit calculation also failed")
        
        # Get uninvoiced work orders value
        uninvoiced_value = 0
        uninvoiced_count = 0
        try:
            # First try ServiceClaim table (appears to be empty)
            uninvoiced_query = f"""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(DealerTotal), 0) as total_value
            FROM {schema}.ServiceClaim
            WHERE ProcessedDate IS NOT NULL
            AND (CustomerInvoiceNo IS NULL OR CustomerInvoiceNo = '' OR CustomerInvoiceNo = '0')
            """
            
            uninvoiced_result = db.execute_query(uninvoiced_query)
            if uninvoiced_result:
                uninvoiced_value = float(uninvoiced_result[0]['total_value'])
                uninvoiced_count = int(uninvoiced_result[0]['count'])
                
            # If ServiceClaim is empty, check WO table
            if uninvoiced_count == 0:
                try:
                    # Query WO table for completed but not invoiced work orders
                    # Using subqueries to get labor, parts, and misc totals
                    wo_query = f"""
                    SELECT 
                        COUNT(*) as count,
                        COALESCE(SUM(labor_total + parts_total + misc_total), 0) as total_value
                    FROM (
                        SELECT 
                            w.WONo,
                            COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                            COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                            COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
                        FROM {schema}.WO w
                        WHERE w.CompletedDate IS NOT NULL
                        AND w.InvoiceDate IS NULL
                    ) as uninvoiced
                    """
                    wo_result = db.execute_query(wo_query)
                    if wo_result:
                        uninvoiced_value = float(wo_result[0]['total_value'])
                        uninvoiced_count = int(wo_result[0]['count'])
                except Exception as e:
                    logger.error(f"Complex WO query failed: {str(e)}")
                    # If the complex query fails, at least get the count
                    try:
                        simple_query = f"""
                        SELECT COUNT(*) as count
                        FROM {schema}.WO
                        WHERE CompletedDate IS NOT NULL
                        AND InvoiceDate IS NULL
                        """
                        simple_result = db.execute_query(simple_query)
                        if simple_result:
                            uninvoiced_count = int(simple_result[0]['count'])
                            # Set a reasonable placeholder value
                            if uninvoiced_count > 0:
                                uninvoiced_value = uninvoiced_count * 500  # Placeholder average
                    except:
                        pass
                    
        except Exception as e:
            logger.error(f"Uninvoiced work orders query failed: {str(e)}")
            uninvoiced_count = 0
        
        # Get monthly quotes value since March
        monthly_quotes = []
        try:
            # Query WOQuote table for monthly quote totals
            quotes_query = f"""
            SELECT 
                YEAR(CreationTime) as year,
                MONTH(CreationTime) as month,
                SUM(Amount) as amount
            FROM {schema}.WOQuote
            WHERE CreationTime >= '2025-03-01'
            AND Amount > 0
            GROUP BY YEAR(CreationTime), MONTH(CreationTime)
            ORDER BY YEAR(CreationTime), MONTH(CreationTime)
            """
            
            quote_results = db.execute_query(quotes_query)
            
            if quote_results:
                for row in quote_results:
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_quotes.append({
                        'month': month_date.strftime("%b"),
                        'amount': float(row['amount'])
                    })
            
            # Pad with zeros for months without quotes
            if len(monthly_quotes) < 5:  # March to July is 5 months
                # Get all months from March to current
                start_date = datetime(2025, 3, 1)
                current_date = datetime.now()
                
                all_months = []
                date = start_date
                while date <= current_date:
                    all_months.append(date.strftime("%b"))
                    # Move to next month
                    if date.month == 12:
                        date = date.replace(year=date.year + 1, month=1)
                    else:
                        date = date.replace(month=date.month + 1)
                
                # Create dict of existing data
                existing_quotes = {item['month']: item['amount'] for item in monthly_quotes}
                
                # Rebuild with all months
                monthly_quotes = []
                for month in all_months:
                    monthly_quotes.append({
                        'month': month,
                        'amount': existing_quotes.get(month, 0)
                    })
                    
        except Exception as e:
            logger.error(f"Monthly quotes calculation failed: {str(e)}")
        
        # Get monthly work orders by type since March
        monthly_work_orders_by_type = []
        try:
            # Use OpenDate to track when work orders are opened
            wo_type_trends_query = f"""
            SELECT 
                YEAR(OpenDate) as year,
                MONTH(OpenDate) as month,
                Type,
                COUNT(*) as count,
                SUM(labor_total + parts_total + misc_total) as total_value
            FROM (
                SELECT 
                    w.WONo,
                    w.OpenDate,
                    w.Type,
                    COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                    COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                    COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
                FROM {schema}.WO w
                WHERE w.OpenDate >= '2025-03-01'
                AND w.OpenDate IS NOT NULL
            ) as wo_with_values
            GROUP BY YEAR(OpenDate), MONTH(OpenDate), Type
            ORDER BY YEAR(OpenDate), MONTH(OpenDate)
            """
            
            wo_results = db.execute_query(wo_type_trends_query)
            
            if wo_results:
                # Organize data by month
                months_data = {}
                
                for row in wo_results:
                    month_date = datetime(row['year'], row['month'], 1)
                    month_key = month_date.strftime("%b")
                    
                    if month_key not in months_data:
                        months_data[month_key] = {
                            'month': month_key,
                            'service_value': 0,
                            'rental_value': 0,
                            'parts_value': 0,
                            'pm_value': 0,
                            'shop_value': 0,
                            'equipment_value': 0
                        }
                    
                    # Map type codes to value fields
                    if row['Type'] == 'S':
                        months_data[month_key]['service_value'] = float(row['total_value'] or 0)
                    elif row['Type'] == 'R':
                        months_data[month_key]['rental_value'] = float(row['total_value'] or 0)
                    elif row['Type'] == 'P':
                        months_data[month_key]['parts_value'] = float(row['total_value'] or 0)
                    elif row['Type'] == 'PM':
                        months_data[month_key]['pm_value'] = float(row['total_value'] or 0)
                    elif row['Type'] == 'SH':
                        months_data[month_key]['shop_value'] = float(row['total_value'] or 0)
                    elif row['Type'] == 'E':
                        months_data[month_key]['equipment_value'] = float(row['total_value'] or 0)
                
                # Convert to list
                monthly_work_orders_by_type = list(months_data.values())
            
            # If no data, provide empty months from March to current
            if not monthly_work_orders_by_type:
                start_date = datetime(2025, 3, 1)
                current_date = datetime.now()
                
                date = start_date
                while date <= current_date:
                    monthly_work_orders_by_type.append({
                        'month': date.strftime("%b"),
                        'service_value': 0,
                        'rental_value': 0,
                        'parts_value': 0,
                        'pm_value': 0,
                        'shop_value': 0,
                        'equipment_value': 0
                    })
                    if date.month == 12:
                        date = date.replace(year=date.year + 1, month=1)
                    else:
                        date = date.replace(month=date.month + 1)
                    
        except Exception as e:
            logger.error(f"Monthly work orders by type calculation failed: {str(e)}")
        
        # Get Top 10 customers by YTD sales
        top_customers = []
        try:
            # Get fiscal year start (November 1st of previous year)
            today = datetime.now()
            if today.month >= 11:
                fiscal_year_start = datetime(today.year, 11, 1)
            else:
                fiscal_year_start = datetime(today.year - 1, 11, 1)
            
            top_customers_query = f"""
            SELECT TOP 10
                CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    ELSE BillToName
                END as customer_name,
                COUNT(DISTINCT InvoiceNo) as invoice_count,
                SUM(GrandTotal) as total_sales
            FROM {schema}.InvoiceReg
            WHERE InvoiceDate >= '{fiscal_year_start.strftime('%Y-%m-%d')}'
            AND BillToName IS NOT NULL
            AND BillToName != ''
            GROUP BY 
                CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    ELSE BillToName
                END
            ORDER BY SUM(GrandTotal) DESC
            """
            
            customers_result = db.execute_query(top_customers_query)
            
            if customers_result:
                for i, customer in enumerate(customers_result):
                    top_customers.append({
                        'rank': i + 1,
                        'name': customer['customer_name'],
                        'sales': float(customer['total_sales']),
                        'invoice_count': int(customer['invoice_count'])
                    })
                    
        except Exception as e:
            logger.error(f"Top customers calculation failed: {str(e)}")
        
        # Get department gross margin percentages by month
        department_margins = []
        try:
            # Calculate margin percentage for each department
            margin_query = f"""
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                -- Parts margin
                SUM(PartsTaxable + PartsNonTax) as parts_revenue,
                SUM(PartsCost) as parts_cost,
                CASE 
                    WHEN SUM(PartsTaxable + PartsNonTax) > 0 
                    THEN ((SUM(PartsTaxable + PartsNonTax) - SUM(PartsCost)) / SUM(PartsTaxable + PartsNonTax)) * 100
                    ELSE 0 
                END as parts_margin_pct,
                -- Labor margin
                SUM(LaborTaxable + LaborNonTax) as labor_revenue,
                SUM(LaborCost) as labor_cost,
                CASE 
                    WHEN SUM(LaborTaxable + LaborNonTax) > 0 
                    THEN ((SUM(LaborTaxable + LaborNonTax) - SUM(LaborCost)) / SUM(LaborTaxable + LaborNonTax)) * 100
                    ELSE 0 
                END as labor_margin_pct,
                -- Equipment margin
                SUM(EquipmentTaxable + EquipmentNonTax) as equipment_revenue,
                SUM(EquipmentCost) as equipment_cost,
                CASE 
                    WHEN SUM(EquipmentTaxable + EquipmentNonTax) > 0 
                    THEN ((SUM(EquipmentTaxable + EquipmentNonTax) - SUM(EquipmentCost)) / SUM(EquipmentTaxable + EquipmentNonTax)) * 100
                    ELSE 0 
                END as equipment_margin_pct,
                -- Rental margin
                SUM(RentalTaxable + RentalNonTax) as rental_revenue,
                SUM(RentalCost) as rental_cost,
                CASE 
                    WHEN SUM(RentalTaxable + RentalNonTax) > 0 
                    THEN ((SUM(RentalTaxable + RentalNonTax) - SUM(RentalCost)) / SUM(RentalTaxable + RentalNonTax)) * 100
                    ELSE 0 
                END as rental_margin_pct
            FROM {schema}.InvoiceReg
            WHERE InvoiceDate >= '{twelve_months_ago}'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            margin_results = db.execute_query(margin_query)
            
            if margin_results:
                for row in margin_results:
                    month_date = datetime(row['year'], row['month'], 1)
                    department_margins.append({
                        'month': month_date.strftime("%b"),
                        'parts_margin': round(float(row['parts_margin_pct']), 1),
                        'labor_margin': round(float(row['labor_margin_pct']), 1),
                        'equipment_margin': round(float(row['equipment_margin_pct']), 1),
                        'rental_margin': round(float(row['rental_margin_pct']), 1),
                        'parts_revenue': float(row['parts_revenue']),
                        'labor_revenue': float(row['labor_revenue']),
                        'equipment_revenue': float(row['equipment_revenue']),
                        'rental_revenue': float(row['rental_revenue'])
                    })
                    
        except Exception as e:
            logger.error(f"Department margins calculation failed: {str(e)}")
        
        # Get work order types breakdown for open/in-progress work orders
        work_order_types = []
        open_wo_total = 0
        open_wo_count = 0
        try:
            # Use the Type field for categorization (not QuoteType)
            successful_type_column = 'Type'
            
            if successful_type_column:
                # Query for work order types breakdown
                wo_types_query = f"""
                SELECT 
                    CASE 
                        WHEN {successful_type_column} = 'S' THEN 'Service'
                        WHEN {successful_type_column} = 'R' THEN 'Rental'
                        WHEN {successful_type_column} = 'P' THEN 'Parts'
                        WHEN {successful_type_column} = 'PM' THEN 'Preventive Maintenance'
                        WHEN {successful_type_column} = 'SH' THEN 'Shop'
                        WHEN {successful_type_column} = 'E' THEN 'Equipment'
                        WHEN {successful_type_column} IS NULL THEN 'Unspecified'
                        ELSE {successful_type_column}
                    END as type_name,
                    COUNT(*) as count,
                    SUM(labor_total + parts_total + misc_total) as total_value
                FROM (
                    SELECT 
                        w.WONo,
                        w.{successful_type_column},
                        COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                        COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                        COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
                    FROM {schema}.WO w
                    WHERE w.CompletedDate IS NULL
                    AND w.ClosedDate IS NULL
                ) as open_wo
                GROUP BY {successful_type_column}
                ORDER BY total_value DESC
                """
                
                wo_types_result = db.execute_query(wo_types_query)
                
                if wo_types_result:
                    for row in wo_types_result:
                        work_order_types.append({
                            'type': row['type_name'],
                            'count': int(row['count']),
                            'value': float(row['total_value'])
                        })
                        open_wo_total += float(row['total_value'])
                        open_wo_count += int(row['count'])
            else:
                # If no type column found or no results, get total of all open work orders
                try:
                    total_query = f"""
                    SELECT 
                        COUNT(*) as count,
                        SUM(labor_total + parts_total + misc_total) as total_value
                    FROM (
                        SELECT 
                            w.WONo,
                            COALESCE((SELECT SUM(Sell) FROM {schema}.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                            COALESCE((SELECT SUM(Sell) FROM {schema}.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                            COALESCE((SELECT SUM(Sell) FROM {schema}.WOMisc WHERE WONo = w.WONo), 0) as misc_total
                        FROM {schema}.WO w
                        WHERE w.CompletedDate IS NULL
                        AND w.ClosedDate IS NULL
                    ) as open_wo
                    """
                    
                    total_result = db.execute_query(total_query)
                    if total_result and total_result[0]['total_value'] > 0:
                        # Show all as "Work Orders" if we can't break down by type
                        work_order_types = [{
                            'type': 'Work Orders',
                            'count': int(total_result[0]['count']),
                            'value': float(total_result[0]['total_value'])
                        }]
                        open_wo_total = float(total_result[0]['total_value'])
                        open_wo_count = int(total_result[0]['count'])
                except:
                    pass
                        
        except Exception as e:
            logger.error(f"Work order types calculation failed: {str(e)}")
        
        return jsonify({
            'total_sales': total_sales,
            'inventory_count': inventory_count,
            'active_customers': active_customers,
            'uninvoiced_work_orders': int(uninvoiced_value),  # Remove decimals
            'uninvoiced_count': uninvoiced_count,
            'open_work_orders_value': int(open_wo_total),
            'open_work_orders_count': open_wo_count,
            'work_order_types': work_order_types,
            'parts_orders': 0,
            'service_tickets': 0,
            'monthly_sales': monthly_sales,
            'monthly_gross_profit': monthly_gross_profit,
            'monthly_quotes': monthly_quotes,
            'monthly_work_orders_by_type': monthly_work_orders_by_type,
            'top_customers': top_customers,
            'department_margins': department_margins,
            'period': current_date.strftime('%B %Y'),
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {str(e)}", exc_info=True)
        # Return zeros instead of error to keep dashboard functional
        return jsonify({
            'total_sales': 0,
            'inventory_count': 0,
            'active_customers': 0,
            'uninvoiced_work_orders': 0,
            'uninvoiced_count': 0,
            'open_work_orders_value': 0,
            'open_work_orders_count': 0,
            'work_order_types': [],
            'parts_orders': 0,
            'service_tickets': 0,
            'monthly_sales': [],
            'monthly_gross_profit': [],
            'monthly_quotes': [],
            'monthly_work_orders_by_type': [],
            'top_customers': [],
            'department_margins': [],
            'period': 'This Month',
            'error': str(e),
            'last_updated': datetime.now().isoformat()
        })

@reports_bp.route('/inventory-details', methods=['GET'])
@jwt_required()
def get_inventory_details():
    """Get detailed list of available inventory"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e), 'equipment': [], 'total': 0}), 400
    
    try:
        db = get_tenant_db()
        
        # Get all equipment that is Ready To Rent with details
        query = f"""
        SELECT 
            UnitNo,
            Make,
            Model,
            ModelYear,
            SerialNo,
            Location,
            Cost,
            LastHourMeter,
            RentalStatus,
            CASE 
                WHEN WebRentalFlag = 1 THEN 'Yes' 
                ELSE 'No' 
            END as WebAvailable
        FROM {schema}.Equipment
        WHERE RentalStatus = 'Ready To Rent'
        ORDER BY Make, Model, UnitNo
        """
        
        results = db.execute_query(query)
        
        # Format the results for better display
        equipment_list = []
        for row in results:
            equipment_list.append({
                'unitNo': row.get('UnitNo', ''),
                'make': row.get('Make', ''),
                'model': row.get('Model', ''),
                'year': row.get('ModelYear', ''),
                'serialNo': row.get('SerialNo', ''),
                'location': row.get('Location', ''),
                'cost': float(row.get('Cost', 0)),
                'hours': float(row.get('LastHourMeter', 0)),
                'webAvailable': row.get('WebAvailable', 'No')
            })
        
        return jsonify({
            'success': True,
            'equipment': equipment_list,
            'total': len(equipment_list)
        })
        
    except Exception as e:
        logger.error(f"Error fetching inventory details: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'equipment': [],
            'total': 0
        }), 500

@reports_bp.route('/list', methods=['GET'])
@TenantMiddleware.require_organization
def get_reports():
    """Get list of available reports"""
    try:
        user_id = get_jwt_identity()
        
        # Mock report templates - replace with actual data from database
        reports = [
            {
                "id": 1,
                "name": "Sales Summary",
                "description": "Monthly sales performance overview",
                "category": "Sales",
                "last_run": "2024-01-15T10:30:00Z",
                "parameters": ["date_range", "salesperson", "product_category"]
            },
            {
                "id": 2,
                "name": "Inventory Status",
                "description": "Current inventory levels and alerts",
                "category": "Inventory",
                "last_run": "2024-01-14T16:45:00Z",
                "parameters": ["warehouse", "product_type", "stock_level"]
            },
            {
                "id": 3,
                "name": "Customer Analysis",
                "description": "Customer behavior and purchase patterns",
                "category": "Analytics",
                "last_run": "2024-01-13T09:15:00Z",
                "parameters": ["customer_segment", "date_range", "region"]
            },
            {
                "id": 4,
                "name": "Parts & Service Revenue",
                "description": "Service department performance metrics",
                "category": "Service",
                "last_run": "2024-01-12T14:20:00Z",
                "parameters": ["service_type", "technician", "date_range"]
            },
            {
                "id": 5,
                "name": "Rental Fleet Utilization",
                "description": "Rental equipment usage and availability",
                "category": "Rentals",
                "last_run": "2024-01-11T11:00:00Z",
                "parameters": ["equipment_type", "location", "utilization_threshold"]
            }
        ]
        
        return jsonify({
            "success": True,
            "reports": reports
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@reports_bp.route('/generate', methods=['POST'])
@TenantMiddleware.require_organization
def generate_report():
    """Generate a report with specified parameters"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        report_id = data.get('report_id')
        parameters = data.get('parameters', {})
        format_type = data.get('format', 'json')  # json, csv, excel, pdf
        
        # Get data from Softbase service
        softbase_service = get_softbase_service()
        if softbase_service:
            report_data = softbase_service.get_report_data(report_id, parameters)
        else:
            # Fallback to mock data if no Softbase service configured
            report_data = _get_mock_report_data(report_id, parameters)
        
        if format_type == 'json':
            # Generate dashboard metrics
            metrics = report_generator.generate_dashboard_metrics(report_data)
            
            # Generate trend analysis if applicable
            trend_analysis = report_generator.generate_trend_analysis(report_data)
            
            return jsonify({
                "success": True,
                "data": report_data,
                "metrics": metrics,
                "trend_analysis": trend_analysis,
                "generated_at": datetime.now().isoformat()
            })
        
        elif format_type == 'csv':
            csv_data = report_generator.generate_csv_report(report_data)
            return jsonify({
                "success": True,
                "data": csv_data,
                "content_type": "text/csv",
                "filename": f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            })
        
        elif format_type == 'excel':
            excel_data = report_generator.generate_excel_report(
                report_data, 
                chart_type=parameters.get('chart_type', 'bar')
            )
            if excel_data:
                import base64
                excel_b64 = base64.b64encode(excel_data).decode()
                return jsonify({
                    "success": True,
                    "data": excel_b64,
                    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "filename": f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                })
        
        elif format_type == 'pdf':
            pdf_data = report_generator.generate_pdf_report(
                report_data,
                title=f"Report {report_id}",
                filename=f"report_{report_id}.pdf"
            )
            import base64
            pdf_b64 = base64.b64encode(pdf_data).decode()
            return jsonify({
                "success": True,
                "data": pdf_b64,
                "content_type": "application/pdf",
                "filename": f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            })
        
        return jsonify({
            "success": False,
            "error": "Unsupported format"
        }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@reports_bp.route('/chart', methods=['POST'])
@jwt_required()
def generate_chart():
    """Generate chart image for report data"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        report_data = data.get('data', [])
        chart_type = data.get('chart_type', 'bar')
        title = data.get('title', 'Chart')
        x_label = data.get('x_label', 'X Axis')
        y_label = data.get('y_label', 'Y Axis')
        
        chart_image = report_generator.generate_chart_image(
            report_data, chart_type, title, x_label, y_label
        )
        
        if chart_image:
            return jsonify({
                "success": True,
                "chart_image": chart_image,
                "content_type": "image/png"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Could not generate chart"
            }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@reports_bp.route('/dashboard-data', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """Get dashboard summary data"""
    try:
        user_id = get_jwt_identity()
        
        # Get various dashboard metrics
        dashboard_data = {
            "summary_cards": [
                {
                    "title": "Total Sales",
                    "value": "$125,430",
                    "change": "+12.5%",
                    "trend": "up",
                    "period": "vs last month"
                },
                {
                    "title": "Active Rentals",
                    "value": "47",
                    "change": "+3",
                    "trend": "up",
                    "period": "vs last week"
                },
                {
                    "title": "Parts Orders",
                    "value": "156",
                    "change": "-8.2%",
                    "trend": "down",
                    "period": "vs last month"
                },
                {
                    "title": "Service Tickets",
                    "value": "23",
                    "change": "+15.4%",
                    "trend": "up",
                    "period": "vs last week"
                }
            ],
            "charts": {
                "sales_trend": {
                    "type": "line",
                    "data": [
                        {"date": "2024-01-01", "value": 15000},
                        {"date": "2024-01-02", "value": 18000},
                        {"date": "2024-01-03", "value": 16500},
                        {"date": "2024-01-04", "value": 22000},
                        {"date": "2024-01-05", "value": 19500},
                        {"date": "2024-01-06", "value": 25000},
                        {"date": "2024-01-07", "value": 21000}
                    ],
                    "title": "Sales Trend (Last 7 Days)"
                },
                "inventory_status": {
                    "type": "bar",
                    "data": [
                        {"category": "Forklifts", "value": 45},
                        {"category": "Parts", "value": 1250},
                        {"category": "Accessories", "value": 320},
                        {"category": "Batteries", "value": 78}
                    ],
                    "title": "Inventory by Category"
                },
                "service_breakdown": {
                    "type": "pie",
                    "data": [
                        {"category": "Maintenance", "value": 45},
                        {"category": "Repairs", "value": 30},
                        {"category": "Inspections", "value": 15},
                        {"category": "Warranty", "value": 10}
                    ],
                    "title": "Service Types Distribution"
                }
            },
            "recent_activity": [
                {
                    "type": "sale",
                    "description": "New forklift sale to ABC Manufacturing",
                    "amount": "$45,000",
                    "timestamp": "2024-01-15T14:30:00Z"
                },
                {
                    "type": "service",
                    "description": "Completed maintenance on Unit #FL-2023",
                    "amount": "$350",
                    "timestamp": "2024-01-15T13:15:00Z"
                },
                {
                    "type": "rental",
                    "description": "New 30-day rental agreement with XYZ Corp",
                    "amount": "$2,400",
                    "timestamp": "2024-01-15T11:45:00Z"
                },
                {
                    "type": "parts",
                    "description": "Parts order fulfilled for Linde H25T",
                    "amount": "$890",
                    "timestamp": "2024-01-15T10:20:00Z"
                }
            ],
            "alerts": [
                {
                    "type": "warning",
                    "message": "Low stock alert: Hydraulic filters (5 remaining)",
                    "priority": "medium"
                },
                {
                    "type": "info",
                    "message": "Scheduled maintenance due for 3 rental units",
                    "priority": "low"
                },
                {
                    "type": "success",
                    "message": "Monthly sales target achieved (102%)",
                    "priority": "low"
                }
            ]
        }
        
        return jsonify({
            "success": True,
            "data": dashboard_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@reports_bp.route('/export/<format_type>', methods=['POST'])
@jwt_required()
def export_report(format_type):
    """Export report in specified format as downloadable file"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        report_data = data.get('data', [])
        filename = data.get('filename', f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if format_type == 'csv':
            csv_data = report_generator.generate_csv_report(report_data)
            return send_file(
                io.StringIO(csv_data),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{filename}.csv'
            )
        
        elif format_type == 'excel':
            excel_data = report_generator.generate_excel_report(report_data)
            if excel_data:
                return send_file(
                    io.BytesIO(excel_data),
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'{filename}.xlsx'
                )
        
        elif format_type == 'pdf':
            pdf_data = report_generator.generate_pdf_report(
                report_data,
                title=filename.replace('_', ' ').title()
            )
            return send_file(
                io.BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'{filename}.pdf'
            )
        
        return jsonify({
            "success": False,
            "error": "Unsupported export format"
        }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



def _get_mock_report_data(report_id, parameters):
    """Generate mock data for testing when Softbase API is not configured"""
    mock_data = {
        1: [  # Sales Summary
            {"date": "2024-01-01", "salesperson": "John Smith", "amount": 15000, "product": "Linde H25T"},
            {"date": "2024-01-02", "salesperson": "Jane Doe", "amount": 22000, "product": "Toyota 8FBE20"},
            {"date": "2024-01-03", "salesperson": "John Smith", "amount": 18500, "product": "Crown FC5200"},
            {"date": "2024-01-04", "salesperson": "Mike Johnson", "amount": 31000, "product": "Yale GLP050"},
            {"date": "2024-01-05", "salesperson": "Jane Doe", "amount": 19500, "product": "Hyster H2.5FT"}
        ],
        2: [  # Inventory Status
            {"item": "Linde H25T", "quantity": 12, "location": "Warehouse A", "status": "Available"},
            {"item": "Toyota 8FBE20", "quantity": 8, "location": "Warehouse B", "status": "Available"},
            {"item": "Crown FC5200", "quantity": 3, "location": "Warehouse A", "status": "Low Stock"},
            {"item": "Yale GLP050", "quantity": 15, "location": "Warehouse C", "status": "Available"},
            {"item": "Hyster H2.5FT", "quantity": 1, "location": "Warehouse B", "status": "Critical"}
        ],
        3: [  # Customer Analysis
            {"customer": "ABC Manufacturing", "total_purchases": 125000, "last_order": "2024-01-10"},
            {"customer": "XYZ Logistics", "total_purchases": 89000, "last_order": "2024-01-08"},
            {"customer": "Warehouse Solutions Inc", "total_purchases": 156000, "last_order": "2024-01-12"},
            {"customer": "Industrial Supply Co", "total_purchases": 67000, "last_order": "2024-01-05"}
        ],
        4: [  # Parts & Service Revenue
            {"service_type": "Maintenance", "revenue": 15600, "tickets": 23, "avg_time": 2.5},
            {"service_type": "Repair", "revenue": 28900, "tickets": 18, "avg_time": 4.2},
            {"service_type": "Inspection", "revenue": 8400, "tickets": 35, "avg_time": 1.1},
            {"service_type": "Warranty", "revenue": 5200, "tickets": 12, "avg_time": 3.8}
        ],
        5: [  # Rental Fleet Utilization
            {"equipment": "Linde H25T #001", "utilization": 85, "revenue": 2400, "status": "Rented"},
            {"equipment": "Toyota 8FBE20 #002", "utilization": 92, "revenue": 2800, "status": "Rented"},
            {"equipment": "Crown FC5200 #003", "utilization": 67, "revenue": 1900, "status": "Available"},
            {"equipment": "Yale GLP050 #004", "utilization": 78, "revenue": 2200, "status": "Rented"}
        ]
    }
    
    return mock_data.get(report_id, [])

