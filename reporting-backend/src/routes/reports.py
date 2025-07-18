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

@reports_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """Get real dashboard summary data from Softbase database"""
    try:
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        # Get current month date range
        today = datetime.now()
        first_day_of_month = today.replace(day=1)
        thirty_days_ago = today - timedelta(days=30)
        
        # Get total sales for current month
        sales_query = f"""
        SELECT 
            COALESCE(SUM(GrandTotal), 0) as total_sales,
            COUNT(DISTINCT InvoiceNo) as invoice_count
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '{first_day_of_month.strftime('%Y-%m-%d')}'
        """
        
        sales_result = db.execute_query(sales_query)
        total_sales = float(sales_result[0]['total_sales']) if sales_result else 0.0
        
        # Get inventory count (in stock equipment)
        inventory_query = """
        SELECT COUNT(*) as inventory_count
        FROM ben002.Equipment
        WHERE RentalStatus = 'In Stock'
        """
        
        inventory_result = db.execute_query(inventory_query)
        inventory_count = inventory_result[0]['inventory_count'] if inventory_result else 0
        
        # Get active customers (customers with recent activity)
        customers_query = f"""
        SELECT COUNT(DISTINCT Customer) as active_customers
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '{thirty_days_ago.strftime('%Y-%m-%d')}'
        """
        
        customers_result = db.execute_query(customers_query)
        active_customers = customers_result[0]['active_customers'] if customers_result else 0
        
        # Get open service tickets
        service_query = """
        SELECT COUNT(*) as open_tickets
        FROM ben002.ServiceClaim
        WHERE Status = 'Open'
        """
        
        service_result = db.execute_query(service_query)
        service_tickets = service_result[0]['open_tickets'] if service_result else 0
        
        # Get parts on order (low stock)
        parts_query = """
        SELECT COUNT(*) as low_stock_parts
        FROM ben002.NationalParts
        WHERE QtyOnHand < 10 AND QtyOnHand >= 0
        """
        
        parts_result = db.execute_query(parts_query)
        parts_orders = parts_result[0]['low_stock_parts'] if parts_result else 0
        
        return jsonify({
            'total_sales': total_sales,
            'inventory_count': inventory_count,
            'active_customers': active_customers,
            'parts_orders': parts_orders,
            'service_tickets': service_tickets,
            'monthly_sales': [],  # TODO: Implement monthly sales data
            'period': 'This Month',
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

