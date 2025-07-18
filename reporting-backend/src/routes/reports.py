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

def get_softbase_service():
    """Get Softbase service instance for current organization"""
    if hasattr(g, 'current_organization'):
        return SoftbaseService(g.current_organization)
    return None

@reports_bp.route('/debug-dashboard', methods=['GET'])
def debug_dashboard():
    """Debug dashboard queries - NO AUTH REQUIRED for testing"""
    try:
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
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
        FROM ben002.InvoiceReg
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
        inventory_query = """
        SELECT COUNT(*) as inventory_count
        FROM ben002.Equipment
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
        customers_query = """
        SELECT COUNT(DISTINCT ID) as active_customers
        FROM ben002.Customer
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
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        # Get ServiceClaim columns
        columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'ServiceClaim' 
        AND TABLE_SCHEMA = 'ben002'
        ORDER BY ORDINAL_POSITION
        """
        
        columns = db.execute_query(columns_query)
        
        # Get sample completed but not invoiced claims
        sample_query = """
        SELECT TOP 10 *
        FROM ben002.ServiceClaim
        WHERE CloseDate IS NOT NULL
        ORDER BY CloseDate DESC
        """
        
        samples = db.execute_query(sample_query)
        
        # Check for invoice-related columns
        invoice_columns = [col for col in columns if 'invoice' in col['COLUMN_NAME'].lower() or 'bill' in col['COLUMN_NAME'].lower()]
        
        return jsonify({
            'success': True,
            'columns': columns,
            'invoice_related_columns': invoice_columns,
            'sample_closed_claims': samples
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
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        results = {}
        
        # Check Equipment table columns
        equipment_columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Equipment' 
        AND TABLE_SCHEMA = 'ben002'
        ORDER BY ORDINAL_POSITION
        """
        
        results['equipment_columns'] = db.execute_query(equipment_columns_query)
        
        # Check Customer table columns
        customer_columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Customer' 
        AND TABLE_SCHEMA = 'ben002'
        ORDER BY ORDINAL_POSITION
        """
        
        results['customer_columns'] = db.execute_query(customer_columns_query)
        
        # Get sample Equipment record to see actual data
        try:
            equipment_sample = """
            SELECT TOP 1 *
            FROM ben002.Equipment
            """
            results['equipment_sample'] = db.execute_query(equipment_sample)
        except Exception as e:
            results['equipment_sample_error'] = str(e)
        
        # Get sample Customer record to see actual data
        try:
            customer_sample = """
            SELECT TOP 1 *
            FROM ben002.Customer
            """
            results['customer_sample'] = db.execute_query(customer_sample)
        except Exception as e:
            results['customer_sample_error'] = str(e)
        
        # Try to count equipment with different status columns
        try:
            # Try Status column
            status_count = """
            SELECT Status, COUNT(*) as count
            FROM ben002.Equipment
            GROUP BY Status
            """
            results['equipment_status_values'] = db.execute_query(status_count)
        except:
            try:
                # Try RentalStatus column
                rental_status_count = """
                SELECT RentalStatus, COUNT(*) as count
                FROM ben002.Equipment
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
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        # Test multiple date ranges to find the $11,998,467.41
        results = {}
        
        # Test 1: Nov 1, 2024 forward (current query)
        query1 = """
        SELECT 
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales,
            MIN(InvoiceDate) as first_invoice,
            MAX(InvoiceDate) as last_invoice
        FROM ben002.InvoiceReg
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
        FROM ben002.InvoiceReg
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
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '2024-11-01' AND InvoiceDate <= '2025-10-31'
        """
        result4 = db.execute_query(query4)
        results['full_fiscal_2025'] = {
            'total': float(result4[0]['total_sales']) if result4[0]['total_sales'] else 0,
            'count': result4[0]['invoice_count']
        }
        
        # Get monthly breakdown for better understanding
        monthly_query = """
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as monthly_total
        FROM ben002.InvoiceReg
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
    try:
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        # Get current month's sales
        current_date = datetime.now()
        month_start = current_date.replace(day=1).strftime('%Y-%m-%d')
        
        query = f"""
        SELECT COALESCE(SUM(GrandTotal), 0) as month_sales
        FROM ben002.InvoiceReg
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
    try:
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        # Get current month's sales
        current_date = datetime.now()
        month_start = current_date.replace(day=1).strftime('%Y-%m-%d')
        
        sales_query = f"""
        SELECT COALESCE(SUM(GrandTotal), 0) as total_sales
        FROM ben002.InvoiceReg
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
        inventory_query = """
        SELECT COUNT(*) as inventory_count
        FROM ben002.Equipment
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
        FROM ben002.InvoiceReg
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
            FROM ben002.InvoiceReg
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
        
        # Get uninvoiced work orders value
        uninvoiced_value = 0
        try:
            # Query for completed service claims that haven't been invoiced
            # Assuming InvoiceNo or similar field indicates if it's been invoiced
            uninvoiced_query = """
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(TotalLabor + TotalParts), 0) as total_value
            FROM ben002.ServiceClaim
            WHERE CloseDate IS NOT NULL
            AND (InvoiceNo IS NULL OR InvoiceNo = 0 OR InvoiceNo = '')
            """
            
            uninvoiced_result = db.execute_query(uninvoiced_query)
            if uninvoiced_result:
                uninvoiced_value = float(uninvoiced_result[0]['total_value'])
                uninvoiced_count = int(uninvoiced_result[0]['count'])
            else:
                uninvoiced_count = 0
        except Exception as e:
            logger.error(f"Uninvoiced work orders query failed: {str(e)}")
            uninvoiced_count = 0
        
        return jsonify({
            'total_sales': total_sales,
            'inventory_count': inventory_count,
            'active_customers': active_customers,
            'uninvoiced_work_orders': int(uninvoiced_value),  # Remove decimals
            'uninvoiced_count': uninvoiced_count,
            'parts_orders': 0,
            'service_tickets': 0,
            'monthly_sales': monthly_sales,
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
            'parts_orders': 0,
            'service_tickets': 0,
            'monthly_sales': [],
            'period': 'This Month',
            'error': str(e),
            'last_updated': datetime.now().isoformat()
        })

@reports_bp.route('/inventory-details', methods=['GET'])
@jwt_required()
def get_inventory_details():
    """Get detailed list of available inventory"""
    try:
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        # Get all equipment that is Ready To Rent with details
        query = """
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
        FROM ben002.Equipment
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

