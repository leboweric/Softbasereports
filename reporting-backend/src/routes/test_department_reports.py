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
    
    @reports_bp.route('/departments/verify-service-revenue', methods=['GET'])
    @jwt_required()
    def verify_service_revenue():
        """Verify Service revenue calculations against known values"""
        try:
            db = get_db()
            
            results = {}
            
            # Test 1: Get July Service revenue using the join
            july_join_query = """
            SELECT 
                COUNT(DISTINCT i.InvoiceNo) as invoice_count,
                COUNT(*) as row_count,
                SUM(i.GrandTotal) as total_revenue
            FROM ben002.InvoiceReg i
            INNER JOIN ben002.WO w ON i.ControlNo = w.UnitNo
            WHERE w.Type = 'S'
            AND MONTH(i.InvoiceDate) = 7
            AND YEAR(i.InvoiceDate) = 2025
            """
            
            results['july_with_join'] = db.execute_query(july_join_query)[0]
            
            # Test 2: Check for duplicates - why are we getting more rows?
            duplicate_check = """
            SELECT TOP 10
                i.InvoiceNo,
                i.ControlNo,
                i.GrandTotal,
                COUNT(*) as match_count
            FROM ben002.InvoiceReg i
            INNER JOIN ben002.WO w ON i.ControlNo = w.UnitNo
            WHERE w.Type = 'S'
            AND MONTH(i.InvoiceDate) = 7
            AND YEAR(i.InvoiceDate) = 2025
            GROUP BY i.InvoiceNo, i.ControlNo, i.GrandTotal
            HAVING COUNT(*) > 1
            """
            
            results['duplicates'] = db.execute_query(duplicate_check)
            
            # Test 3: Try using SaleDept instead - check if certain depts are Service
            dept_breakdown = """
            SELECT 
                SaleDept,
                SaleCode,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = 7
            AND YEAR(InvoiceDate) = 2025
            GROUP BY SaleDept, SaleCode
            ORDER BY revenue DESC
            """
            
            results['july_by_dept'] = db.execute_query(dept_breakdown)
            
            # Test 4: Look for SaleCode patterns that might indicate Service
            service_codes = """
            SELECT DISTINCT TOP 20
                SaleCode,
                COUNT(*) as count,
                SUM(LaborCost + LaborTaxable + LaborNonTax) as labor_revenue,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = 7
            AND YEAR(InvoiceDate) = 2025
            AND (LaborCost > 0 OR LaborTaxable > 0 OR LaborNonTax > 0)
            GROUP BY SaleCode
            ORDER BY labor_revenue DESC
            """
            
            results['service_likely_codes'] = db.execute_query(service_codes)
            
            # Test 5: Verify our Service filter gives correct July total
            service_total_query = """
            SELECT 
                SUM(CASE WHEN SaleCode = 'RDCST' THEN GrandTotal ELSE 0 END) as field_service,
                SUM(CASE WHEN SaleCode = 'SHPCST' THEN GrandTotal ELSE 0 END) as shop_service,
                SUM(CASE WHEN SaleCode = 'FMROAD' THEN GrandTotal ELSE 0 END) as fm_road,
                SUM(CASE WHEN SaleCode IN ('RDCST', 'SHPCST', 'FMROAD') THEN GrandTotal ELSE 0 END) as total_service
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = 7
            AND YEAR(InvoiceDate) = 2025
            """
            
            results['service_breakdown'] = db.execute_query(service_total_query)[0]
            
            # Test 6: Try Department approach (40=Field, 45=Shop)
            try:
                dept_total_query = """
                SELECT 
                    SUM(CASE WHEN Dept = 40 THEN GrandTotal ELSE 0 END) as field_service_dept,
                    SUM(CASE WHEN Dept = 45 THEN GrandTotal ELSE 0 END) as shop_service_dept,
                    SUM(CASE WHEN Dept IN (40, 45) THEN GrandTotal ELSE 0 END) as total_service_dept
                FROM ben002.InvoiceReg
                WHERE MONTH(InvoiceDate) = 7
                AND YEAR(InvoiceDate) = 2025
                """
                results['service_dept_breakdown'] = db.execute_query(dept_total_query)[0]
            except Exception as e:
                results['service_dept_breakdown'] = {'error': str(e)}
            
            return jsonify(results)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/test-saledept', methods=['GET'])
    @jwt_required()
    def test_saledept():
        """Test SaleDept values in InvoiceReg to find Service department code"""
        try:
            db = get_db()
            
            # Get distribution of SaleDept values
            dept_query = """
            SELECT 
                SaleDept,
                SaleCode,
                COUNT(*) as count,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -1, GETDATE())
            GROUP BY SaleDept, SaleCode
            ORDER BY COUNT(*) DESC
            """
            
            dept_result = db.execute_query(dept_query)
            
            # Get sample invoices for each SaleDept
            samples = {}
            if dept_result:
                for dept in dept_result[:5]:  # Top 5 departments
                    sample_query = f"""
                    SELECT TOP 3 
                        InvoiceNo,
                        SaleDept,
                        SaleCode,
                        SerialNo,
                        GrandTotal,
                        LaborCost,
                        PartsCost
                    FROM ben002.InvoiceReg
                    WHERE SaleDept = {dept['SaleDept']}
                    ORDER BY InvoiceDate DESC
                    """
                    samples[f"dept_{dept['SaleDept']}"] = db.execute_query(sample_query)
            
            return jsonify({
                'department_distribution': dept_result,
                'samples': samples
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/test-service-revenue', methods=['GET'])
    @jwt_required()
    def test_service_revenue():
        """Test the actual revenue query to see why it's returning 0"""
        try:
            db = get_db()
            
            # Test 1: Count total invoices in last 6 months
            total_invoices_query = """
            SELECT COUNT(*) as total, SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            """
            total_result = db.execute_query(total_invoices_query)
            
            # Test 2: Count invoices that have ControlNo
            with_control_query = """
            SELECT COUNT(*) as count, SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            AND ControlNo IS NOT NULL
            """
            control_result = db.execute_query(with_control_query)
            
            # Test 3: Try the join to see how many match
            join_test_query = """
            SELECT COUNT(*) as matches, SUM(i.GrandTotal) as matched_revenue
            FROM ben002.InvoiceReg i
            INNER JOIN ben002.WO w ON i.ControlNo = w.UnitNo
            WHERE i.InvoiceDate >= DATEADD(month, -6, GETDATE())
            """
            join_result = db.execute_query(join_test_query)
            
            # Test 4: Try the full service filter
            service_test_query = """
            SELECT COUNT(*) as service_matches, SUM(i.GrandTotal) as service_revenue
            FROM ben002.InvoiceReg i
            INNER JOIN ben002.WO w ON i.ControlNo = w.UnitNo
            WHERE w.Type = 'S'
            AND i.InvoiceDate >= DATEADD(month, -6, GETDATE())
            """
            service_result = db.execute_query(service_test_query)
            
            # Test 5: Sample of unmatched ControlNo values
            unmatched_query = """
            SELECT TOP 10 i.ControlNo, i.InvoiceNo, i.GrandTotal
            FROM ben002.InvoiceReg i
            WHERE i.InvoiceDate >= DATEADD(month, -6, GETDATE())
            AND i.ControlNo IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM ben002.WO w WHERE w.UnitNo = i.ControlNo
            )
            """
            unmatched_result = db.execute_query(unmatched_query)
            
            return jsonify({
                'total_invoices': total_result[0] if total_result else {},
                'with_controlno': control_result[0] if control_result else {},
                'join_matches': join_result[0] if join_result else {},
                'service_matches': service_result[0] if service_result else {},
                'unmatched_samples': unmatched_result
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/test-invoice-link-v2', methods=['GET'])
    @jwt_required()
    def test_invoice_link_v2():
        """Test linking InvoiceReg to WO table - try different approaches"""
        try:
            db = get_db()
            
            # Try to find which column in WO table matches ControlNo format
            # First, let's see what ControlNo values look like
            control_sample_query = """
            SELECT DISTINCT TOP 5 ControlNo
            FROM ben002.InvoiceReg
            WHERE ControlNo IS NOT NULL 
            AND ControlNo != ''
            """
            
            control_samples = db.execute_query(control_sample_query)
            
            # Now try different potential join columns
            results = {}
            
            # Test 1: Try ControlNo = ControlNo
            try:
                test1 = """
                SELECT COUNT(*) as matches
                FROM ben002.InvoiceReg i
                INNER JOIN ben002.WO w ON i.ControlNo = w.ControlNo
                WHERE i.ControlNo IS NOT NULL
                """
                result1 = db.execute_query(test1)
                results['ControlNo_to_ControlNo'] = result1[0]['matches'] if result1 else 0
            except:
                results['ControlNo_to_ControlNo'] = 'Column not found'
            
            # Test 2: Try ControlNo = Id (as string)
            try:
                test2 = """
                SELECT COUNT(*) as matches
                FROM ben002.InvoiceReg i
                INNER JOIN ben002.WO w ON i.ControlNo = CAST(w.Id AS NVARCHAR)
                WHERE i.ControlNo IS NOT NULL
                """
                result2 = db.execute_query(test2)
                results['ControlNo_to_Id'] = result2[0]['matches'] if result2 else 0
            except:
                results['ControlNo_to_Id'] = 'Failed'
            
            # Test 3: List all string columns from WO that might contain work order numbers
            string_columns_query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'WO'
            AND DATA_TYPE IN ('nvarchar', 'varchar', 'char')
            """
            
            string_columns = db.execute_query(string_columns_query)
            
            return jsonify({
                'control_samples': control_samples,
                'test_results': results,
                'wo_string_columns': string_columns
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/test-invoice-link', methods=['GET'])
    @jwt_required()
    def test_invoice_link():
        """Test linking InvoiceReg to WO table via ControlNo"""
        try:
            db = get_db()
            
            # First, get ALL column names from WO table
            wo_columns_query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'WO'
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
            
            # Query for monthly revenue from Service invoices
            # Option 1: If Dept column exists, use Department codes (40=Field, 45=Shop)
            # Option 2: Otherwise fall back to SaleCode filter
            # First, try with Department codes
            revenue_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE Dept IN (40, 45)
            AND InvoiceDate >= DATEADD(month, -6, GETDATE())
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            # Try Department approach first
            try:
                revenue_result = db.execute_query(revenue_query)
            except Exception as e:
                # If Dept column doesn't exist, fall back to SaleCode
                if "Invalid column name 'Dept'" in str(e):
                    revenue_query = """
                    SELECT 
                        YEAR(InvoiceDate) as year,
                        MONTH(InvoiceDate) as month,
                        SUM(GrandTotal) as revenue
                    FROM ben002.InvoiceReg
                    WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD')
                    AND InvoiceDate >= DATEADD(month, -6, GETDATE())
                    GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
                    ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
                    """
                    revenue_result = db.execute_query(revenue_query)
                else:
                    raise e
            
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
                
            # Calculate current month's Service revenue
            # Try Department approach first, fall back to SaleCode if needed
            current_month_revenue_query = f"""
            SELECT COALESCE(SUM(GrandTotal), 0) as revenue
            FROM ben002.InvoiceReg
            WHERE Dept IN (40, 45)
            AND MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            """
            
            try:
                revenue_result = db.execute_query(current_month_revenue_query)
                current_month_revenue = float(revenue_result[0]['revenue']) if revenue_result else 0
            except Exception as e:
                if "Invalid column name 'Dept'" in str(e):
                    # Fall back to SaleCode approach
                    current_month_revenue_query = f"""
                    SELECT COALESCE(SUM(GrandTotal), 0) as revenue
                    FROM ben002.InvoiceReg
                    WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD')
                    AND MONTH(InvoiceDate) = {today.month}
                    AND YEAR(InvoiceDate) = {today.year}
                    """
                    revenue_result = db.execute_query(current_month_revenue_query)
                    current_month_revenue = float(revenue_result[0]['revenue']) if revenue_result else 0
                else:
                    current_month_revenue = 0
            
            # Get month names for labels
            current_month_name = today.strftime('%B')  # e.g., "July"
            last_month_name = last_month_end.strftime('%B')  # e.g., "June"
                
            return jsonify({
                'summary': {
                    'openWorkOrders': open_count,
                    'completedToday': 0,
                    'averageRepairTime': 0,
                    'technicianEfficiency': 87,
                    'revenue': current_month_revenue,
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