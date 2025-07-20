# Simplified department report endpoints for testing
from flask import jsonify
from flask_jwt_extended import jwt_required
import datetime
from src.services.azure_sql_service import AzureSQLService


def get_db():
    """Get database connection"""
    return AzureSQLService()


def register_department_routes(reports_bp):
    """Register department report routes with the reports blueprint"""
    
    @reports_bp.route('/departments/invoice-columns', methods=['GET'])
    @jwt_required()
    def get_invoice_columns():
        """Get InvoiceReg table columns to find the right linkage"""
        try:
            db = get_db()
            
            # Get all columns from InvoiceReg
            query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'InvoiceReg'
            ORDER BY ORDINAL_POSITION
            """
            
            result = db.execute_query(query)
            
            # Also get a sample row to see actual data
            sample_query = """
            SELECT TOP 1 * FROM ben002.InvoiceReg
            """
            
            sample_result = db.execute_query(sample_query)
            
            return jsonify({
                'columns': result,
                'sample': sample_result[0] if sample_result else {},
                'column_names': [col['COLUMN_NAME'] for col in result] if result else []
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/test-invoice-link', methods=['GET'])
    @jwt_required()
    def test_invoice_link():
        """Test linking InvoiceReg to WO table via ControlNo"""
        try:
            db = get_db()
            
            # First, get column names from WO table
            wo_columns_query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'WO'
            AND COLUMN_NAME LIKE '%WO%' OR COLUMN_NAME LIKE '%Number%' OR COLUMN_NAME = 'Id'
            ORDER BY ORDINAL_POSITION
            """
            
            wo_columns = db.execute_query(wo_columns_query)
            
            # Get sample from WO table to see structure
            wo_sample_query = """
            SELECT TOP 1 * FROM ben002.WO WHERE Type = 'S'
            """
            
            wo_sample = db.execute_query(wo_sample_query)
            
            # Try to identify the primary key column
            # Let's check if there's a ControlNo in WO table that matches
            test_query = """
            SELECT TOP 10
                i.InvoiceNo,
                i.ControlNo,
                i.InvoiceDate,
                i.GrandTotal
            FROM ben002.InvoiceReg i
            WHERE i.ControlNo IS NOT NULL
            ORDER BY i.InvoiceDate DESC
            """
            
            result = db.execute_query(test_query)
            
            return jsonify({
                'wo_columns': wo_columns,
                'wo_sample': wo_sample[0] if wo_sample else {},
                'invoice_samples': result,
                'error': 'Need to identify correct WO table primary key column'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/service', methods=['GET'])
    @jwt_required()
    def get_service_department_report():
        """Get Service Department report data"""
        try:
            db = get_db()
            
            # Get current date info for month calculations
            today = datetime.datetime.now()
            current_month_start = today.replace(day=1)
            last_month_end = current_month_start - datetime.timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            
            # Count open and recently closed work orders
            test_query = f"""
            SELECT 
                COUNT(*) as total_service,
                SUM(CASE WHEN ClosedDate IS NULL THEN 1 ELSE 0 END) as open_service,
                SUM(CASE 
                    WHEN ClosedDate >= '{current_month_start.strftime('%Y-%m-%d')}' 
                    THEN 1 ELSE 0 
                END) as closed_this_month,
                SUM(CASE 
                    WHEN ClosedDate >= '{last_month_start.strftime('%Y-%m-%d')}' 
                    AND ClosedDate < '{current_month_start.strftime('%Y-%m-%d')}'
                    THEN 1 ELSE 0 
                END) as closed_last_month
            FROM ben002.WO 
            WHERE Type = 'S'
            """
            
            test_result = db.execute_query(test_query)
            
            # Query for monthly trend - completed work orders and revenue
            trend_query = """
            SELECT 
                YEAR(ClosedDate) as year,
                MONTH(ClosedDate) as month,
                DATENAME(month, ClosedDate) as month_name,
                COUNT(*) as completed
            FROM ben002.WO
            WHERE Type = 'S' 
            AND ClosedDate IS NOT NULL
            AND ClosedDate >= DATEADD(month, -6, GETDATE())
            GROUP BY YEAR(ClosedDate), MONTH(ClosedDate), DATENAME(month, ClosedDate)
            ORDER BY YEAR(ClosedDate), MONTH(ClosedDate)
            """
            
            trend_result = db.execute_query(trend_query)
            
            # Query for monthly revenue from invoices
            # TODO: Need to find correct column to link InvoiceReg to WO table
            # For now showing all invoices - check /api/reports/departments/invoice-columns
            revenue_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            revenue_result = db.execute_query(revenue_query)
            
            # Create a revenue lookup dictionary
            revenue_by_month = {}
            if revenue_result:
                for row in revenue_result:
                    key = f"{row.get('year', '')}-{row.get('month', '')}"
                    revenue_by_month[key] = float(row.get('revenue', 0) or 0)
            
            # Return minimal data structure for testing
            if test_result and len(test_result) > 0:
                row = test_result[0]
                open_count = row.get('open_service', 0) or 0
                total_count = row.get('total_service', 0) or 0
                closed_this_month = row.get('closed_this_month', 0) or 0
                closed_last_month = row.get('closed_last_month', 0) or 0
            else:
                open_count = 0
                total_count = 0
                closed_this_month = 0
                closed_last_month = 0
                
            # Get month names for labels
            current_month_name = today.strftime('%B')  # e.g., "July"
            last_month_name = last_month_end.strftime('%B')  # e.g., "June"
                
            return jsonify({
                'summary': {
                    'openWorkOrders': open_count,
                    'completedToday': 0,
                    'averageRepairTime': 0,
                    'technicianEfficiency': 87,
                    'revenue': 0,
                    'customersServed': 0
                },
                'workOrdersByStatus': [
                    {'name': 'Open', 'status': 'Open', 'count': open_count, 'color': '#f59e0b'},
                    {'name': f'Closed {current_month_name}', 'status': 'Closed This Month', 'count': closed_this_month, 'color': '#10b981'},
                    {'name': f'Closed {last_month_name}', 'status': 'Closed Last Month', 'count': closed_last_month, 'color': '#3b82f6'}
                ],
                'recentWorkOrders': [],
                'monthlyTrend': [
                    {
                        'month': row.get('month_name', '')[:3],  # Abbreviate month name
                        'completed': row.get('completed', 0),
                        'revenue': revenue_by_month.get(
                            f"{row.get('year', '')}-{row.get('month', '')}", 
                            0
                        )
                    }
                    for row in trend_result
                ] if trend_result else [],
                'technicianPerformance': [],
                'debug': {
                    'total_service_orders': total_count,
                    'open_service_orders': open_count,
                    'closed_this_month': closed_this_month,
                    'closed_last_month': closed_last_month,
                    'current_month': current_month_name,
                    'last_month': last_month_name
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'service_report_error',
                'details': f"Query failed: {str(e)}"
            }), 500