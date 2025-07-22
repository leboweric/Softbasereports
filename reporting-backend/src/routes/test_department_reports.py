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
    
    @reports_bp.route('/departments/list-salecodes', methods=['GET'])
    @jwt_required()
    def list_salecodes():
        """Just list all SaleCodes and their July totals"""
        try:
            db = get_db()
            
            query = """
            SELECT 
                SaleCode,
                COUNT(*) as count,
                SUM(GrandTotal) as total
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = 7
            AND YEAR(InvoiceDate) = 2025
            GROUP BY SaleCode
            ORDER BY total DESC
            """
            
            results = db.execute_query(query)
            
            # Find which ones might be Service
            service_keywords = ['SERVICE', 'SVC', 'REPAIR', 'MAINT', 'LABOR', 'FIELD', 'SHOP', 'ROAD', 'FM']
            potential_service = []
            
            for row in results:
                code = row.get('SaleCode', '').upper()
                if any(keyword in code for keyword in service_keywords):
                    potential_service.append(row)
            
            return jsonify({
                'all_codes': results,
                'potential_service': potential_service,
                'total_count': len(results)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/simple-service-test', methods=['GET'])
    @jwt_required()
    def simple_service_test():
        """Simple test to find Service revenue"""
        try:
            db = get_db()
            
            # First, let's just get July 2025 totals by SaleCode
            query = """
            SELECT 
                SaleCode,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = 7
            AND YEAR(InvoiceDate) = 2025
            GROUP BY SaleCode
            HAVING SUM(GrandTotal) > 1000
            ORDER BY total_revenue DESC
            """
            
            results = db.execute_query(query)
            
            # Also try with RecvAccount if it exists
            recv_results = []
            try:
                recv_query = """
                SELECT 
                    RecvAccount,
                    COUNT(*) as invoice_count,
                    SUM(GrandTotal) as total_revenue
                FROM ben002.InvoiceReg
                WHERE MONTH(InvoiceDate) = 7
                AND YEAR(InvoiceDate) = 2025
                AND RecvAccount IS NOT NULL
                GROUP BY RecvAccount
                HAVING SUM(GrandTotal) > 1000
                ORDER BY total_revenue DESC
                """
                recv_results = db.execute_query(recv_query)
            except:
                pass
            
            # Calculate specific totals
            summaries = {
                'salecode_fm': sum(r['total_revenue'] for r in results if r.get('SaleCode') in ['FMROAD', 'FMSHOP']),
                'recv_410004_410005': sum(r['total_revenue'] for r in recv_results if r.get('RecvAccount') in ['410004', '410005']),
                'total_july': sum(r['total_revenue'] for r in results),
                'field_only': next((r['total_revenue'] for r in results if r.get('SaleCode') == 'FMROAD'), 0),
                'shop_only': next((r['total_revenue'] for r in results if r.get('SaleCode') == 'FMSHOP'), 0)
            }
            
            return jsonify({
                'details': results[:50],  # Top 50 combinations
                'summaries': summaries,
                'target': 72891  # Your July target
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/get-all-columns', methods=['GET'])
    @jwt_required()
    def get_all_columns():
        """Get ALL column names from InvoiceReg and WO tables"""
        try:
            db = get_db()
            
            # Get InvoiceReg columns
            invoice_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'InvoiceReg'
            ORDER BY ORDINAL_POSITION
            """
            
            invoice_columns = db.execute_query(invoice_query)
            
            # Get WO table columns
            wo_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'WO'
            ORDER BY ORDINAL_POSITION
            """
            
            wo_columns = db.execute_query(wo_query)
            
            # Get sample data
            invoice_sample = db.execute_query("SELECT TOP 1 * FROM ben002.InvoiceReg WHERE MONTH(InvoiceDate) = 7 AND YEAR(InvoiceDate) = 2025")
            wo_sample = db.execute_query("SELECT TOP 1 * FROM ben002.WO WHERE Type = 'S'")
            
            return jsonify({
                'invoice_columns': invoice_columns,
                'wo_columns': wo_columns,
                'invoice_sample': invoice_sample[0] if invoice_sample else {},
                'wo_sample': wo_sample[0] if wo_sample else {},
                'invoice_column_names': [col['COLUMN_NAME'] for col in invoice_columns] if invoice_columns else [],
                'wo_column_names': [col['COLUMN_NAME'] for col in wo_columns] if wo_columns else []
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
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
    
    @reports_bp.route('/departments/debug-revenue-number', methods=['GET'])
    @jwt_required()
    def debug_revenue_number():
        """Debug where $23,511.68 is coming from"""
        try:
            db = get_db()
            today = datetime.datetime.now()
            
            results = {
                'target_amount': 23511.68,
                'current_date': {
                    'month': today.month,
                    'year': today.year,
                    'month_name': today.strftime('%B')
                }
            }
            
            # Test 1: Check what the Service endpoint is actually querying
            # RecvAccount approach
            recv_account_query = f"""
            SELECT 
                'RecvAccount' as method,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue,
                MIN(InvoiceDate) as min_date,
                MAX(InvoiceDate) as max_date
            FROM ben002.InvoiceReg
            WHERE RecvAccount IN ('410004', '410005')
            AND MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            """
            
            try:
                results['recv_account_test'] = db.execute_query(recv_account_query)[0]
            except Exception as e:
                results['recv_account_test'] = {'error': str(e)}
            
            # Test 2: Department approach
            dept_query = f"""
            SELECT 
                'Department' as method,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue,
                MIN(InvoiceDate) as min_date,
                MAX(InvoiceDate) as max_date
            FROM ben002.InvoiceReg
            WHERE Dept IN (40, 45)
            AND MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            """
            
            try:
                results['dept_test'] = db.execute_query(dept_query)[0]
            except Exception as e:
                results['dept_test'] = {'error': str(e)}
            
            # Test 3: SaleCode approach (FMROAD, FMSHOP)
            salecode_query = f"""
            SELECT 
                'SaleCode' as method,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue,
                MIN(InvoiceDate) as min_date,
                MAX(InvoiceDate) as max_date
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('FMROAD', 'FMSHOP')
            AND MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            """
            
            results['salecode_test'] = db.execute_query(salecode_query)[0]
            
            # Test 4: Find ANY combination that equals $23,511.68
            find_exact_query = f"""
            SELECT TOP 10
                SaleCode,
                Dept,
                RecvAccount,
                COUNT(*) as count,
                SUM(GrandTotal) as total
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            GROUP BY SaleCode, Dept, RecvAccount
            HAVING SUM(GrandTotal) BETWEEN 23500 AND 23520
            ORDER BY ABS(SUM(GrandTotal) - 23511.68)
            """
            
            results['exact_match_search'] = db.execute_query(find_exact_query)
            
            # Test 5: Check if it's a single SaleCode
            single_salecode_query = f"""
            SELECT 
                SaleCode,
                COUNT(*) as count,
                SUM(GrandTotal) as total
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            GROUP BY SaleCode
            HAVING SUM(GrandTotal) BETWEEN 23000 AND 24000
            ORDER BY ABS(SUM(GrandTotal) - 23511.68)
            """
            
            results['single_salecode_matches'] = db.execute_query(single_salecode_query)
            
            # Test 6: Check July data specifically (in case date is wrong)
            july_test_query = """
            SELECT 
                'July RecvAccount' as method,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE RecvAccount IN ('410004', '410005')
            AND MONTH(InvoiceDate) = 7
            AND YEAR(InvoiceDate) = 2025
            """
            
            try:
                results['july_recv_account'] = db.execute_query(july_test_query)[0]
            except:
                results['july_recv_account'] = {'error': 'Failed'}
            
            # Test 7: Show what RecvAccount values exist for current month
            recv_values_query = f"""
            SELECT TOP 20
                RecvAccount,
                COUNT(*) as count,
                SUM(GrandTotal) as total
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            AND RecvAccount IS NOT NULL
            GROUP BY RecvAccount
            ORDER BY SUM(GrandTotal) DESC
            """
            
            try:
                results['recv_account_values'] = db.execute_query(recv_values_query)
            except:
                results['recv_account_values'] = []
            
            return jsonify(results)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/test-current-month', methods=['GET'])
    @jwt_required()
    def test_current_month():
        """Test current month Service revenue calculation"""
        try:
            db = get_db()
            today = datetime.datetime.now()
            
            results = {}
            
            # Test 1: Total invoices this month (no filter)
            total_query = f"""
            SELECT 
                COUNT(*) as count,
                SUM(GrandTotal) as total
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            """
            results['total_current_month'] = db.execute_query(total_query)[0]
            
            # Test 2: Department approach
            dept_query = f"""
            SELECT 
                Dept,
                COUNT(*) as count,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            AND Dept IN (40, 45)
            GROUP BY Dept
            """
            try:
                results['by_department'] = db.execute_query(dept_query)
            except Exception as e:
                results['by_department'] = {'error': str(e)}
            
            # Test 3: SaleCode approach (correct revenue codes)
            salecode_query = f"""
            SELECT 
                SaleCode,
                COUNT(*) as count,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            AND SaleCode IN ('FMROAD', 'FMSHOP')
            GROUP BY SaleCode
            """
            results['by_salecode'] = db.execute_query(salecode_query)
            
            # Test 4: All departments this month to see distribution
            all_dept_query = f"""
            SELECT TOP 10
                Dept,
                COUNT(*) as count,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            GROUP BY Dept
            ORDER BY revenue DESC
            """
            try:
                results['all_departments'] = db.execute_query(all_dept_query)
            except:
                results['all_departments'] = []
            
            # Test 5: Check if we're in November or July
            results['current_month'] = {
                'month': today.month,
                'year': today.year,
                'month_name': today.strftime('%B')
            }
            
            return jsonify(results)
            
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
            
            # Test 5: Verify Service revenue with correct SaleCodes
            service_total_query = """
            SELECT 
                SUM(CASE WHEN SaleCode = 'FMROAD' THEN GrandTotal ELSE 0 END) as field_service_revenue,
                SUM(CASE WHEN SaleCode = 'FMSHOP' THEN GrandTotal ELSE 0 END) as shop_service_revenue,
                SUM(CASE WHEN SaleCode IN ('FMROAD', 'FMSHOP') THEN GrandTotal ELSE 0 END) as total_service_revenue,
                SUM(CASE WHEN SaleCode = 'RDCST' THEN GrandTotal ELSE 0 END) as field_cost,
                SUM(CASE WHEN SaleCode = 'SHPCST' THEN GrandTotal ELSE 0 END) as shop_cost
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
    
    @reports_bp.route('/departments/test-account-numbers', methods=['GET'])
    @jwt_required()
    def test_account_numbers():
        """Test using Account numbers for Service revenue"""
        try:
            db = get_db()
            
            results = {}
            
            # First, check if there's an Account column in InvoiceReg
            column_check = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'InvoiceReg'
            AND COLUMN_NAME LIKE '%Account%'
            ORDER BY COLUMN_NAME
            """
            
            results['account_columns'] = db.execute_query(column_check)
            
            # Try different account column names
            # RecvAccount is confirmed to exist
            for col_name in ['RecvAccount', 'Account', 'AccountNo', 'AccountNumber', 'AcctNo', 'GLAccount']:
                try:
                    test_query = f"""
                    SELECT TOP 5
                        {col_name} as account,
                        COUNT(*) as count,
                        SUM(GrandTotal) as revenue
                    FROM ben002.InvoiceReg
                    WHERE {col_name} IN ('410004', '410005')
                    AND MONTH(InvoiceDate) = 7
                    AND YEAR(InvoiceDate) = 2025
                    GROUP BY {col_name}
                    """
                    result = db.execute_query(test_query)
                    if result:
                        results[f'found_in_{col_name}'] = result
                        
                        # Get monthly breakdown
                        monthly_query = f"""
                        SELECT 
                            CONCAT(YEAR(InvoiceDate), '-', RIGHT('0' + CAST(MONTH(InvoiceDate) AS VARCHAR), 2)) as month,
                            SUM(CASE WHEN {col_name} = '410004' THEN GrandTotal ELSE 0 END) as field_revenue,
                            SUM(CASE WHEN {col_name} = '410005' THEN GrandTotal ELSE 0 END) as shop_revenue,
                            SUM(GrandTotal) as total_revenue
                        FROM ben002.InvoiceReg
                        WHERE {col_name} IN ('410004', '410005')
                        AND InvoiceDate >= '2025-03-01'
                        AND InvoiceDate < '2025-08-01'
                        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
                        ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
                        """
                        results[f'monthly_by_{col_name}'] = db.execute_query(monthly_query)
                        break
                except:
                    continue
            
            # Also check for any account fields with 4100 prefix
            account_search = """
            SELECT DISTINCT TOP 20
                SaleAcct,
                COUNT(*) as count,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE SaleAcct LIKE '4100%'
            AND MONTH(InvoiceDate) = 7
            AND YEAR(InvoiceDate) = 2025
            GROUP BY SaleAcct
            ORDER BY revenue DESC
            """
            
            try:
                results['sale_acct_search'] = db.execute_query(account_search)
            except:
                # Try other potential column names
                for col in ['GLAcct', 'GLAccount', 'SalesAcct']:
                    try:
                        search_query = f"""
                        SELECT DISTINCT TOP 20
                            {col} as account,
                            COUNT(*) as count,
                            SUM(GrandTotal) as revenue
                        FROM ben002.InvoiceReg
                        WHERE {col} LIKE '4100%'
                        AND MONTH(InvoiceDate) = 7
                        AND YEAR(InvoiceDate) = 2025
                        GROUP BY {col}
                        ORDER BY revenue DESC
                        """
                        results[f'{col}_search'] = db.execute_query(search_query)
                        break
                    except:
                        continue
            
            return jsonify(results)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/match-historical-revenue', methods=['GET'])
    @jwt_required()
    def match_historical_revenue():
        """Try to match historical Service revenue numbers"""
        try:
            db = get_db()
            
            # Target values to match (from user's historical data)
            targets = {
                '2025-03': 102148,  # March
                '2025-04': 128987,  # April 
                '2025-05': 95081,   # May
                '2025-06': 106463,  # June
                '2025-07': 72891    # July (Field: 54191 + Shop: ~18700)
            }
            
            results = {'targets': targets}
            
            # Test 1: Department 40 only (Field Service)
            dept40_query = """
            SELECT 
                CONCAT(YEAR(InvoiceDate), '-', RIGHT('0' + CAST(MONTH(InvoiceDate) AS VARCHAR), 2)) as month,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE Dept = 40
            AND InvoiceDate >= '2025-03-01'
            AND InvoiceDate < '2025-08-01'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            try:
                results['dept_40_only'] = db.execute_query(dept40_query)
            except:
                results['dept_40_only'] = []
            
            # Test 2: FMROAD only
            fmroad_query = """
            SELECT 
                CONCAT(YEAR(InvoiceDate), '-', RIGHT('0' + CAST(MONTH(InvoiceDate) AS VARCHAR), 2)) as month,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode = 'FMROAD'
            AND InvoiceDate >= '2025-03-01'
            AND InvoiceDate < '2025-08-01'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            results['fmroad_only'] = db.execute_query(fmroad_query)
            
            # Test 3: Department 40 + 45
            both_dept_query = """
            SELECT 
                CONCAT(YEAR(InvoiceDate), '-', RIGHT('0' + CAST(MONTH(InvoiceDate) AS VARCHAR), 2)) as month,
                SUM(CASE WHEN Dept = 40 THEN GrandTotal ELSE 0 END) as field_revenue,
                SUM(CASE WHEN Dept = 45 THEN GrandTotal ELSE 0 END) as shop_revenue,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE Dept IN (40, 45)
            AND InvoiceDate >= '2025-03-01'
            AND InvoiceDate < '2025-08-01'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            try:
                results['both_departments'] = db.execute_query(both_dept_query)
            except:
                results['both_departments'] = []
            
            # Test 4: FMROAD + FMSHOP
            both_salecode_query = """
            SELECT 
                CONCAT(YEAR(InvoiceDate), '-', RIGHT('0' + CAST(MONTH(InvoiceDate) AS VARCHAR), 2)) as month,
                SUM(CASE WHEN SaleCode = 'FMROAD' THEN GrandTotal ELSE 0 END) as field_revenue,
                SUM(CASE WHEN SaleCode = 'FMSHOP' THEN GrandTotal ELSE 0 END) as shop_revenue,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('FMROAD', 'FMSHOP')
            AND InvoiceDate >= '2025-03-01'
            AND InvoiceDate < '2025-08-01'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            results['both_salecodes'] = db.execute_query(both_salecode_query)
            
            # Test 5: Check all SaleCodes with significant revenue
            all_codes_query = """
            SELECT 
                SaleCode,
                SUM(CASE WHEN MONTH(InvoiceDate) = 7 THEN GrandTotal ELSE 0 END) as july_revenue,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '2025-03-01'
            AND InvoiceDate < '2025-08-01'
            GROUP BY SaleCode
            HAVING SUM(CASE WHEN MONTH(InvoiceDate) = 7 THEN GrandTotal ELSE 0 END) > 5000
            ORDER BY july_revenue DESC
            """
            
            results['significant_codes'] = db.execute_query(all_codes_query)
            
            return jsonify(results)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/validate-march-revenue', methods=['GET'])
    @jwt_required()
    def validate_march_revenue():
        """Validate March 2025 revenue breakdown by SaleCode"""
        try:
            db = get_db()
            
            # Get March revenue broken down by each SaleCode
            revenue_breakdown_query = """
            SELECT 
                SaleCode,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                             'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                             'RENTR', 'RENT-DEL', 'MO-RENT')
            AND YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 3
            GROUP BY SaleCode
            ORDER BY revenue DESC
            """
            
            revenue_breakdown = db.execute_query(revenue_breakdown_query)
            
            # Get total for March with our current filter
            total_query = """
            SELECT SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                             'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                             'RENTR', 'RENT-DEL', 'MO-RENT')
            AND YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 3
            """
            
            total_result = db.execute_query(total_query)
            
            # Get service-only codes (excluding rental/equipment)
            service_only_query = """
            SELECT SUM(GrandTotal) as service_revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'PM', 'PM-FM', 'EDCO', 'SERVP-A')
            AND YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 3
            """
            
            service_only = db.execute_query(service_only_query)
            
            # Get rental codes separately
            rental_query = """
            SELECT SUM(GrandTotal) as rental_revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('RENTR', 'RENTPM', 'NEWEQP-R')
            AND YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 3
            """
            
            rental_result = db.execute_query(rental_query)
            
            # Calculate the difference
            total_rev = total_result[0]['total_revenue'] if total_result else 0
            service_rev = service_only[0]['service_revenue'] if service_only else 0
            rental_rev = rental_result[0]['rental_revenue'] if rental_result else 0
            
            return jsonify({
                'march_total_with_all_codes': total_rev,
                'march_service_only': service_rev,
                'march_rental_only': rental_rev,
                'odata_reported': 253672,
                'difference': total_rev - 253672,
                'revenue_by_salecode': revenue_breakdown,
                'salecodes_included': ['RDCST', 'SHPCST', 'FMROAD', 'PM', 'PM-FM', 'EDCO', 
                                     'RENTR', 'RENTPM', 'NEWEQP-R', 'SERVP-A']
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/validate-march-workorders', methods=['GET'])
    @jwt_required()
    def validate_march_workorders():
        """Validate March 2025 completed work orders by SaleCode"""
        try:
            db = get_db()
            
            # Get March completed WOs broken down by SaleCode
            breakdown_query = """
            SELECT 
                SaleCode,
                COUNT(*) as count
            FROM ben002.WO
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                             'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                             'RENTR', 'RENT-DEL', 'MO-RENT')
            AND ClosedDate IS NOT NULL
            AND YEAR(ClosedDate) = 2025
            AND MONTH(ClosedDate) = 3
            GROUP BY SaleCode
            ORDER BY count DESC
            """
            
            salecode_breakdown = db.execute_query(breakdown_query)
            
            # Get total for March
            total_query = """
            SELECT COUNT(*) as total_count
            FROM ben002.WO
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                             'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                             'RENTR', 'RENT-DEL', 'MO-RENT')
            AND ClosedDate IS NOT NULL
            AND YEAR(ClosedDate) = 2025
            AND MONTH(ClosedDate) = 3
            """
            
            total_result = db.execute_query(total_query)
            
            # Get sample of March WOs to verify they're service-related
            sample_query = """
            SELECT TOP 20
                WONo,
                SaleCode,
                Type,
                CustomerSale,
                Make,
                Model,
                ClosedDate,
                Technician
            FROM ben002.WO
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                             'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                             'RENTR', 'RENT-DEL', 'MO-RENT')
            AND ClosedDate IS NOT NULL
            AND YEAR(ClosedDate) = 2025
            AND MONTH(ClosedDate) = 3
            ORDER BY ClosedDate DESC
            """
            
            sample_wos = db.execute_query(sample_query)
            
            # Also check WOs by Type for comparison
            type_breakdown = """
            SELECT 
                Type,
                COUNT(*) as count
            FROM ben002.WO
            WHERE ClosedDate IS NOT NULL
            AND YEAR(ClosedDate) = 2025
            AND MONTH(ClosedDate) = 3
            GROUP BY Type
            ORDER BY count DESC
            """
            
            type_results = db.execute_query(type_breakdown)
            
            return jsonify({
                'march_total': total_result[0]['total_count'] if total_result else 0,
                'by_salecode': salecode_breakdown,
                'sample_workorders': sample_wos,
                'all_types_comparison': type_results,
                'labor_salecodes_used': ['RDCST', 'SHPCST', 'FMROAD', 'PM', 'PM-FM', 'EDCO', 
                                        'RENTR', 'RENTPM', 'NEWEQP-R', 'SERVP-A']
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/open-work-orders-detail', methods=['GET'])
    @jwt_required()
    def get_open_work_orders_detail():
        """Get detailed list of open work orders for RDCST and SHPCST only"""
        try:
            db = get_db()
            
            # Get all open work orders for RDCST and SHPCST only
            detail_query = """
            SELECT 
                WONo,
                SaleCode,
                CustomerSale,
                SerialNo,
                Make,
                Model,
                UnitNo,
                Type,
                Technician,
                Writer,
                OpenDate,
                SaleDept,
                SaleBranch,
                PONo,
                Comments
            FROM ben002.WO
            WHERE ClosedDate IS NULL
            AND SaleCode IN ('RDCST', 'SHPCST')
            ORDER BY OpenDate DESC
            """
            
            results = db.execute_query(detail_query)
            
            # Get summary by SaleCode
            summary_query = """
            SELECT 
                SaleCode,
                COUNT(*) as count
            FROM ben002.WO
            WHERE ClosedDate IS NULL
            AND SaleCode IN ('RDCST', 'SHPCST')
            GROUP BY SaleCode
            ORDER BY count DESC
            """
            
            summary = db.execute_query(summary_query)
            
            return jsonify({
                'work_orders': results,
                'total_count': len(results),
                'summary_by_salecode': summary
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/explore-wo-salecodes', methods=['GET'])
    @jwt_required()
    def explore_wo_salecodes():
        """Explore Work Order table to find SaleCode field"""
        try:
            db = get_db()
            
            # 1. Check if WO table has SaleCode or similar columns
            column_query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'WO'
            AND (COLUMN_NAME LIKE '%Sale%' OR COLUMN_NAME LIKE '%Code%' 
                 OR COLUMN_NAME LIKE '%Type%' OR COLUMN_NAME LIKE '%Category%')
            ORDER BY COLUMN_NAME
            """
            
            sale_columns = db.execute_query(column_query)
            
            # 2. Get sample of open work orders
            sample_query = """
            SELECT TOP 10 *
            FROM ben002.WO
            WHERE ClosedDate IS NULL
            ORDER BY DateOpened DESC
            """
            
            open_samples = db.execute_query(sample_query)
            
            # 3. Count open work orders by Type
            type_counts = """
            SELECT 
                Type,
                COUNT(*) as count
            FROM ben002.WO
            WHERE ClosedDate IS NULL
            GROUP BY Type
            ORDER BY count DESC
            """
            
            type_results = db.execute_query(type_counts)
            
            # 4. Try to find SaleCode in WO
            try:
                salecode_test = """
                SELECT 
                    SaleCode,
                    COUNT(*) as count
                FROM ben002.WO
                WHERE ClosedDate IS NULL
                AND SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                               'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                               'RENTR', 'RENT-DEL', 'MO-RENT')
                GROUP BY SaleCode
                """
                salecode_counts = db.execute_query(salecode_test)
            except:
                salecode_counts = {'error': 'SaleCode column not found in WO table'}
            
            return jsonify({
                'sale_related_columns': sale_columns,
                'open_wo_samples': open_samples[:3] if open_samples else [],
                'open_by_type': type_results,
                'open_by_salecode': salecode_counts,
                'total_open': sum(t.get('count', 0) for t in type_results) if type_results else 0
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/verify-service-salecodes', methods=['GET'])
    @jwt_required()
    def verify_service_salecodes():
        """Verify all labor-related Service SaleCodes"""
        try:
            db = get_db()
            
            # Define all labor-related SaleCodes
            labor_salecodes = ['RDCST', 'SHPCST', 'FMROAD', 'PM', 'PM-FM', 'EDCO', 
                              'RENTR', 'RENTPM', 'NEWEQP-R', 'SERVP-A']
            
            # Monthly breakdown using all labor SaleCodes
            monthly_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(CASE WHEN SaleCode IN ('RDCST', 'FMROAD') THEN GrandTotal ELSE 0 END) as field_revenue,
                SUM(CASE WHEN SaleCode = 'SHPCST' THEN GrandTotal ELSE 0 END) as shop_revenue,
                SUM(CASE WHEN SaleCode IN ('PM', 'PM-FM', 'RENTPM') THEN GrandTotal ELSE 0 END) as pm_revenue,
                SUM(CASE WHEN SaleCode IN ('RENTR', 'NEWEQP-R') THEN GrandTotal ELSE 0 END) as rental_revenue,
                SUM(CASE WHEN SaleCode IN ('EDCO', 'SERVP-A') THEN GrandTotal ELSE 0 END) as other_revenue,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                             'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                             'RENTR', 'RENT-DEL', 'MO-RENT')
            AND InvoiceDate >= '2025-03-01'
            AND InvoiceDate < '2025-12-01'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY year, month
            """
            
            monthly_results = db.execute_query(monthly_query)
            
            # Compare with historical targets
            targets = {
                '2025-03': 102148,
                '2025-04': 128987,
                '2025-05': 95081,
                '2025-06': 106463,
                '2025-07': 72891
            }
            
            # Add comparison to results
            for row in monthly_results:
                month_key = f"{row['year']}-{str(row['month']).zfill(2)}"
                if month_key in targets:
                    row['target'] = targets[month_key]
                    row['difference'] = row['total_revenue'] - targets[month_key]
                    row['match_percent'] = round((row['total_revenue'] / targets[month_key]) * 100, 1)
            
            # Get current month total with breakdown
            current_query = """
            SELECT 
                SUM(CASE WHEN SaleCode IN ('RDCST', 'FMROAD') THEN GrandTotal ELSE 0 END) as field_revenue,
                SUM(CASE WHEN SaleCode = 'SHPCST' THEN GrandTotal ELSE 0 END) as shop_revenue,
                SUM(CASE WHEN SaleCode IN ('PM', 'PM-FM', 'RENTPM') THEN GrandTotal ELSE 0 END) as pm_revenue,
                SUM(CASE WHEN SaleCode IN ('RENTR', 'NEWEQP-R') THEN GrandTotal ELSE 0 END) as rental_revenue,
                SUM(CASE WHEN SaleCode IN ('EDCO', 'SERVP-A') THEN GrandTotal ELSE 0 END) as other_revenue,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                             'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                             'RENTR', 'RENT-DEL', 'MO-RENT')
            AND MONTH(InvoiceDate) = MONTH(GETDATE())
            AND YEAR(InvoiceDate) = YEAR(GETDATE())
            """
            
            current_month = db.execute_query(current_query)
            
            return jsonify({
                'monthly_breakdown': monthly_results,
                'current_month': current_month[0] if current_month else {},
                'targets': targets,
                'salecodes_used': labor_salecodes
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/analyze-labor-sales', methods=['GET'])
    @jwt_required()
    def analyze_labor_sales():
        """Analyze Labor Sales data to match OData wolabor endpoint"""
        try:
            db = get_db()
            
            # 1. First, let's find labor-related columns in InvoiceReg
            labor_columns_query = """
            SELECT 
                SUM(LaborCost) as total_labor_cost,
                SUM(LaborTaxable) as total_labor_taxable,
                SUM(LaborNonTax) as total_labor_nontax,
                SUM(LaborCost + LaborTaxable + LaborNonTax) as total_labor_revenue,
                COUNT(*) as invoice_count
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = 2025 
            AND MONTH(InvoiceDate) = 7
            AND (LaborCost > 0 OR LaborTaxable > 0 OR LaborNonTax > 0)
            """
            
            labor_totals = db.execute_query(labor_columns_query)
            
            # 2. Break down by SaleCode to see which codes have labor
            labor_by_salecode = """
            SELECT 
                SaleCode,
                COUNT(*) as invoice_count,
                SUM(LaborCost) as labor_cost,
                SUM(LaborTaxable) as labor_taxable,
                SUM(LaborNonTax) as labor_nontax,
                SUM(LaborCost + LaborTaxable + LaborNonTax) as total_labor,
                SUM(GrandTotal) as grand_total
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = 2025 
            AND MONTH(InvoiceDate) = 7
            AND (LaborCost > 0 OR LaborTaxable > 0 OR LaborNonTax > 0)
            GROUP BY SaleCode
            ORDER BY total_labor DESC
            """
            
            labor_salecodes = db.execute_query(labor_by_salecode)
            
            # 3. Check if there's a WOLabor or similar table
            tables_query = """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ben002'
            AND (TABLE_NAME LIKE '%labor%' OR TABLE_NAME LIKE '%Labor%' OR TABLE_NAME = 'WOLabor')
            ORDER BY TABLE_NAME
            """
            
            labor_tables = db.execute_query(tables_query)
            
            # 4. Monthly trend of labor sales
            monthly_labor = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(LaborCost + LaborTaxable + LaborNonTax) as labor_revenue,
                COUNT(*) as invoice_count
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '2025-03-01'
            AND InvoiceDate < '2025-08-01'
            AND (LaborCost > 0 OR LaborTaxable > 0 OR LaborNonTax > 0)
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY year, month
            """
            
            monthly_trend = db.execute_query(monthly_labor)
            
            # 5. Check Work Order table for labor information
            wo_labor_query = """
            SELECT TOP 10
                Type,
                LaborType,
                LaborCost,
                LaborPrice,
                Hours
            FROM ben002.WO
            WHERE Type = 'S'
            AND (LaborCost > 0 OR LaborPrice > 0)
            ORDER BY DateOpened DESC
            """
            
            try:
                wo_labor_sample = db.execute_query(wo_labor_query)
            except:
                # Try different column names
                wo_labor_query_alt = """
                SELECT TOP 5 * 
                FROM ben002.WO
                WHERE Type = 'S'
                """
                try:
                    wo_labor_sample = db.execute_query(wo_labor_query_alt)
                except:
                    wo_labor_sample = []
            
            return jsonify({
                'labor_totals': labor_totals[0] if labor_totals else {},
                'labor_by_salecode': labor_salecodes,
                'labor_tables_found': labor_tables,
                'monthly_labor_trend': monthly_trend,
                'wo_labor_sample': wo_labor_sample,
                'target_july': 72891
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/analyze-service-revenue', methods=['GET'])
    @jwt_required()
    def analyze_service_revenue():
        """Comprehensive Service revenue analysis"""
        try:
            db = get_db()
            
            # 1. Get all July invoices grouped by SaleCode with RecvAccount
            salecode_query = """
            SELECT 
                SaleCode,
                RecvAccount,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = 2025 
            AND MONTH(InvoiceDate) = 7
            GROUP BY SaleCode, RecvAccount
            ORDER BY total_revenue DESC
            """
            
            salecode_results = db.execute_query(salecode_query)
            
            # 2. Find all invoices with FMROAD or FMSHOP
            service_codes_query = """
            SELECT 
                SaleCode,
                RecvAccount,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = 2025 
            AND MONTH(InvoiceDate) = 7
            AND SaleCode IN ('FMROAD', 'FMSHOP')
            GROUP BY SaleCode, RecvAccount
            """
            
            service_codes_results = db.execute_query(service_codes_query)
            
            # 3. Check for account 410004 and 410005
            account_query = """
            SELECT 
                RecvAccount,
                SaleCode,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = 2025 
            AND MONTH(InvoiceDate) = 7
            AND RecvAccount IN ('410004', '410005')
            GROUP BY RecvAccount, SaleCode
            ORDER BY RecvAccount, total_revenue DESC
            """
            
            account_results = db.execute_query(account_query)
            
            # 4. Find all SaleCodes that start with FM (service-related)
            fm_query = """
            SELECT 
                SaleCode,
                RecvAccount,
                COUNT(*) as invoice_count,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = 2025 
            AND MONTH(InvoiceDate) = 7
            AND SaleCode LIKE 'FM%'
            GROUP BY SaleCode, RecvAccount
            ORDER BY total_revenue DESC
            """
            
            fm_results = db.execute_query(fm_query)
            
            # 5. Get grand total for July
            total_query = """
            SELECT 
                SUM(GrandTotal) as total_july_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = 2025 
            AND MONTH(InvoiceDate) = 7
            """
            
            total_results = db.execute_query(total_query)
            
            # 6. Sample invoices for FMROAD and FMSHOP
            sample_query = """
            SELECT TOP 10
                InvoiceNo,
                CustomerName,
                SaleCode,
                RecvAccount,
                GrandTotal,
                InvoiceDate
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = 2025 
            AND MONTH(InvoiceDate) = 7
            AND SaleCode IN ('FMROAD', 'FMSHOP')
            ORDER BY GrandTotal DESC
            """
            
            sample_results = db.execute_query(sample_query)
            
            return jsonify({
                'salecode_breakdown': salecode_results,
                'service_codes': service_codes_results,
                'account_breakdown': account_results,
                'fm_salecodes': fm_results,
                'total_july': total_results[0] if total_results else {},
                'sample_invoices': sample_results
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/find-service-salecodes', methods=['GET'])
    @jwt_required()
    def find_service_salecodes():
        """Find the correct SaleCode values for Service revenue"""
        try:
            db = get_db()
            
            results = {}
            
            # Look for all SaleCodes and their patterns
            salecode_analysis = """
            SELECT 
                SaleCode,
                SaleDept,
                COUNT(*) as count,
                SUM(GrandTotal) as total_revenue,
                AVG(LaborCost + LaborTaxable + LaborNonTax) as avg_labor,
                AVG(PartsCost + PartsTaxable + PartsNonTax) as avg_parts
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = 7 
            AND YEAR(InvoiceDate) = 2025
            GROUP BY SaleCode, SaleDept
            HAVING SUM(GrandTotal) > 1000
            ORDER BY SUM(GrandTotal) DESC
            """
            
            results['salecode_analysis'] = db.execute_query(salecode_analysis)
            
            # Look specifically at departments 40 and 45
            dept_salecodes = """
            SELECT DISTINCT
                Dept,
                SaleCode,
                COUNT(*) as count,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = 7 
            AND YEAR(InvoiceDate) = 2025
            AND Dept IN (40, 45)
            GROUP BY Dept, SaleCode
            ORDER BY Dept, revenue DESC
            """
            
            try:
                results['dept_salecodes'] = db.execute_query(dept_salecodes)
            except:
                results['dept_salecodes'] = []
            
            # Look for SaleCodes that might be Service (not containing 'CST')
            non_cost_codes = """
            SELECT 
                SaleCode,
                COUNT(*) as count,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE MONTH(InvoiceDate) = 7 
            AND YEAR(InvoiceDate) = 2025
            AND SaleCode NOT LIKE '%CST%'
            AND (LaborCost > 0 OR LaborTaxable > 0 OR LaborNonTax > 0)
            GROUP BY SaleCode
            ORDER BY revenue DESC
            """
            
            results['non_cost_codes'] = db.execute_query(non_cost_codes)
            
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
            
            # Count open and recently closed work orders for SHPCST and RDCST separately
            test_query = f"""
            SELECT 
                SaleCode,
                COUNT(*) as total,
                SUM(CASE WHEN ClosedDate IS NULL THEN 1 ELSE 0 END) as open_count,
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
            WHERE SaleCode IN ('SHPCST', 'RDCST')
            GROUP BY SaleCode
            """
            
            test_result = db.execute_query(test_query)
            
            # Calculate average repair time for SHPCST and RDCST in days
            avg_repair_query = f"""
            SELECT 
                SaleCode,
                AVG(CAST(DATEDIFF(day, OpenDate, ClosedDate) AS FLOAT)) as avg_days
            FROM ben002.WO
            WHERE SaleCode IN ('SHPCST', 'RDCST')
            AND ClosedDate IS NOT NULL
            AND OpenDate IS NOT NULL
            AND ClosedDate >= '{current_month_start.strftime('%Y-%m-%d')}'
            GROUP BY SaleCode
            """
            
            avg_repair_result = db.execute_query(avg_repair_query)
            
            # Calculate technician efficiency based on completed work orders
            # Efficiency = (Completed WOs this month / (Completed this month + Currently Open)) * 100
            efficiency_query = f"""
            SELECT 
                CAST(COUNT(CASE WHEN ClosedDate IS NOT NULL 
                      AND ClosedDate >= '{current_month_start.strftime('%Y-%m-%d')}' 
                      AND ClosedDate < DATEADD(month, 1, '{current_month_start.strftime('%Y-%m-%d')}')
                      THEN 1 END) AS FLOAT) * 100.0 / 
                NULLIF(COUNT(CASE WHEN 
                    (ClosedDate IS NOT NULL AND ClosedDate >= '{current_month_start.strftime('%Y-%m-%d')}')
                    OR ClosedDate IS NULL 
                    THEN 1 END), 0) as efficiency_percent
            FROM ben002.WO
            WHERE SaleCode IN ('SHPCST', 'RDCST')
            AND Technician IS NOT NULL
            AND Technician != ''
            """
            
            efficiency_result = db.execute_query(efficiency_query)
            
            # Debug query to see the actual counts
            debug_efficiency_query = f"""
            SELECT 
                COUNT(CASE WHEN ClosedDate IS NOT NULL 
                      AND ClosedDate >= '{current_month_start.strftime('%Y-%m-%d')}' 
                      THEN 1 END) as completed_this_month,
                COUNT(CASE WHEN ClosedDate IS NULL THEN 1 END) as currently_open,
                COUNT(*) as total_with_technician
            FROM ben002.WO
            WHERE SaleCode IN ('SHPCST', 'RDCST')
            AND Technician IS NOT NULL
            AND Technician != ''
            """
            
            debug_result = db.execute_query(debug_efficiency_query)
            
            # Query for monthly trend - completed work orders by SHPCST and RDCST with avg close time
            # Starting from March 2025
            trend_query = """
            SELECT 
                YEAR(ClosedDate) as year,
                MONTH(ClosedDate) as month,
                DATENAME(month, ClosedDate) as month_name,
                SUM(CASE WHEN SaleCode = 'SHPCST' THEN 1 ELSE 0 END) as shop_completed,
                SUM(CASE WHEN SaleCode = 'RDCST' THEN 1 ELSE 0 END) as road_completed,
                AVG(CASE WHEN SaleCode = 'SHPCST' AND OpenDate IS NOT NULL 
                    THEN DATEDIFF(day, OpenDate, ClosedDate) ELSE NULL END) as shop_avg_days,
                AVG(CASE WHEN SaleCode = 'RDCST' AND OpenDate IS NOT NULL 
                    THEN DATEDIFF(day, OpenDate, ClosedDate) ELSE NULL END) as road_avg_days
            FROM ben002.WO
            WHERE SaleCode IN ('SHPCST', 'RDCST')
            AND ClosedDate IS NOT NULL
            AND ClosedDate >= '2025-03-01'
            AND ClosedDate < DATEADD(month, 1, GETDATE())
            GROUP BY YEAR(ClosedDate), MONTH(ClosedDate), DATENAME(month, ClosedDate)
            ORDER BY YEAR(ClosedDate), MONTH(ClosedDate)
            """
            
            trend_result = db.execute_query(trend_query)
            
            # Query for monthly sales trend for RDCST and SHPCST combined
            # Starting from March 2025
            sales_trend_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                DATENAME(month, InvoiceDate) as month_name,
                SUM(CASE WHEN SaleCode = 'SHPCST' THEN GrandTotal ELSE 0 END) as shop_sales,
                SUM(CASE WHEN SaleCode = 'RDCST' THEN GrandTotal ELSE 0 END) as road_sales,
                SUM(GrandTotal) as total_sales
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('SHPCST', 'RDCST')
            AND InvoiceDate >= '2025-03-01'
            AND InvoiceDate < DATEADD(month, 1, GETDATE())
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate), DATENAME(month, InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            sales_trend_result = db.execute_query(sales_trend_query)
            
            # Query for technician performance - show last 30 days of activity
            technician_performance_query = f"""
            SELECT TOP 10
                Technician,
                COUNT(CASE WHEN ClosedDate IS NOT NULL 
                      AND ClosedDate >= DATEADD(day, -30, GETDATE())
                      THEN 1 END) as completed_this_month,
                CAST(COUNT(CASE WHEN ClosedDate IS NOT NULL 
                      AND ClosedDate >= DATEADD(day, -30, GETDATE())
                      THEN 1 END) AS FLOAT) * 100.0 / 
                NULLIF(COUNT(CASE WHEN 
                    (ClosedDate >= DATEADD(day, -30, GETDATE())) OR 
                    (ClosedDate IS NULL) 
                    THEN 1 END), 0) as efficiency
            FROM ben002.WO
            WHERE SaleCode IN ('SHPCST', 'RDCST')
            AND Technician IS NOT NULL
            AND Technician != ''
            GROUP BY Technician
            HAVING COUNT(CASE WHEN ClosedDate IS NOT NULL 
                      AND ClosedDate >= DATEADD(day, -30, GETDATE())
                      THEN 1 END) > 0
            ORDER BY completed_this_month DESC
            """
            
            technician_result = db.execute_query(technician_performance_query)
            
            # Debug: Check if we have any technicians at all
            debug_tech_query = """
            SELECT TOP 20
                Technician,
                COUNT(*) as total_count,
                COUNT(CASE WHEN ClosedDate IS NOT NULL THEN 1 END) as closed_count,
                COUNT(CASE WHEN ClosedDate IS NULL THEN 1 END) as open_count
            FROM ben002.WO
            WHERE SaleCode IN ('SHPCST', 'RDCST')
            GROUP BY Technician
            ORDER BY total_count DESC
            """
            
            debug_tech_result = db.execute_query(debug_tech_query)
            
            # Query for monthly revenue from Service/Labor invoices
            # Updated to match OData exactly - excluding pure rental codes
            # Starting from March 2025
            revenue_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                             'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                             'RENTR', 'RENT-DEL', 'MO-RENT')
            AND InvoiceDate >= '2025-03-01'
            AND InvoiceDate < DATEADD(month, 1, GETDATE())
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
            
            # Process results by SaleCode
            shop_data = {'open': 0, 'closed_this_month': 0, 'closed_last_month': 0, 'avg_repair_days': 0}
            road_data = {'open': 0, 'closed_this_month': 0, 'closed_last_month': 0, 'avg_repair_days': 0}
            total_open = 0
            
            if test_result:
                for row in test_result:
                    if row.get('SaleCode') == 'SHPCST':
                        shop_data['open'] = row.get('open_count', 0) or 0
                        shop_data['closed_this_month'] = row.get('closed_this_month', 0) or 0
                        shop_data['closed_last_month'] = row.get('closed_last_month', 0) or 0
                    elif row.get('SaleCode') == 'RDCST':
                        road_data['open'] = row.get('open_count', 0) or 0
                        road_data['closed_this_month'] = row.get('closed_this_month', 0) or 0
                        road_data['closed_last_month'] = row.get('closed_last_month', 0) or 0
                
                total_open = shop_data['open'] + road_data['open']
            
            # Process average repair times
            if avg_repair_result:
                for row in avg_repair_result:
                    avg_days = round(row.get('avg_days', 0) or 0, 1)
                    if row.get('SaleCode') == 'SHPCST':
                        shop_data['avg_repair_days'] = avg_days
                    elif row.get('SaleCode') == 'RDCST':
                        road_data['avg_repair_days'] = avg_days
            
            # Process efficiency result
            technician_efficiency = 0
            if efficiency_result and len(efficiency_result) > 0:
                efficiency_percent = efficiency_result[0].get('efficiency_percent', 0)
                technician_efficiency = round(efficiency_percent or 0, 0)
                
            # Calculate current month's Service/Labor revenue
            # Updated to match OData exactly - excluding pure rental codes
            current_month_revenue_query = f"""
            SELECT COALESCE(SUM(GrandTotal), 0) as revenue
            FROM ben002.InvoiceReg
            WHERE SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                             'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                             'RENTR', 'RENT-DEL', 'MO-RENT')
            AND MONTH(InvoiceDate) = {today.month}
            AND YEAR(InvoiceDate) = {today.year}
            """
            
            try:
                result = db.execute_query(current_month_revenue_query)
                current_month_revenue = float(result[0]['revenue']) if result else 0
            except:
                current_month_revenue = 0
            
            # Get month names for labels
            current_month_name = today.strftime('%B')  # e.g., "July"
            last_month_name = last_month_end.strftime('%B')  # e.g., "June"
                
            return jsonify({
                'summary': {
                    'openWorkOrders': total_open,
                    'completedToday': 0,
                    'shopAvgRepairTime': shop_data['avg_repair_days'],
                    'roadAvgRepairTime': road_data['avg_repair_days'],
                    'technicianEfficiency': int(technician_efficiency),
                    'revenue': current_month_revenue,
                    'customersServed': 0
                },
                'shopWorkOrdersByStatus': [
                    {'name': 'Open', 'status': 'Open', 'count': shop_data['open'], 'color': '#f59e0b'},
                    {'name': f'Closed {current_month_name}', 'status': 'Closed This Month', 'count': shop_data['closed_this_month'], 'color': '#10b981'},
                    {'name': f'Closed {last_month_name}', 'status': 'Closed Last Month', 'count': shop_data['closed_last_month'], 'color': '#3b82f6'}
                ],
                'roadWorkOrdersByStatus': [
                    {'name': 'Open', 'status': 'Open', 'count': road_data['open'], 'color': '#f59e0b'},
                    {'name': f'Closed {current_month_name}', 'status': 'Closed This Month', 'count': road_data['closed_this_month'], 'color': '#10b981'},
                    {'name': f'Closed {last_month_name}', 'status': 'Closed Last Month', 'count': road_data['closed_last_month'], 'color': '#3b82f6'}
                ],
                'recentWorkOrders': [],
                'monthlyTrend': [
                    {
                        'month': row.get('month_name', '')[:3],  # Abbreviate month name
                        'shop_completed': row.get('shop_completed', 0),
                        'road_completed': row.get('road_completed', 0),
                        'shop_avg_days': round(row.get('shop_avg_days', 0) or 0, 1),
                        'road_avg_days': round(row.get('road_avg_days', 0) or 0, 1)
                    }
                    for row in trend_result
                ] if trend_result else [],
                'salesTrend': [
                    {
                        'month': row.get('month_name', '')[:3],  # Abbreviate month name
                        'shop_sales': float(row.get('shop_sales', 0) or 0),
                        'road_sales': float(row.get('road_sales', 0) or 0),
                        'total_sales': float(row.get('total_sales', 0) or 0)
                    }
                    for row in sales_trend_result
                ] if sales_trend_result else [],
                'technicianPerformance': [
                    {
                        'name': row.get('Technician', ''),
                        'completed': row.get('completed_this_month', 0),
                        'efficiency': round(row.get('efficiency', 0) or 0, 0)
                    }
                    for row in (technician_result or [])
                ],
                'debug': {
                    'total_open': total_open,
                    'shop_data': shop_data,
                    'road_data': road_data,
                    'current_month': current_month_name,
                    'last_month': last_month_name,
                    'efficiency_debug': debug_result[0] if debug_result else None,
                    'efficiency_raw': efficiency_result[0] if efficiency_result else None,
                    'technician_data': technician_result,
                    'technician_debug': debug_tech_result
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'service_report_error',
                'details': f"Query failed: {str(e)}"
            }), 500
    
    @reports_bp.route('/departments/accounting', methods=['GET'])
    @jwt_required()
    def get_accounting_department_report():
        """Get Accounting Department report with real financial data"""
        logger.info("Accounting endpoint called from test_department_reports.py")
        try:
            db = get_db()
            
            # Get current date info
            today = datetime.datetime.now()
            year_start = datetime.datetime(today.year, 1, 1)
            month_start = today.replace(day=1)
            
            # Get monthly financial data for the last 12 months
            monthly_financial_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                DATENAME(month, InvoiceDate) as month_name,
                -- Revenue
                SUM(GrandTotal) as revenue,
                -- Cost breakdown
                SUM(ISNULL(LaborCost, 0)) as labor_cost,
                SUM(ISNULL(PartsCost, 0)) as parts_cost,
                SUM(ISNULL(MiscCost, 0)) as misc_cost,
                SUM(ISNULL(EquipmentCost, 0)) as equipment_cost,
                SUM(ISNULL(RentalCost, 0)) as rental_cost,
                -- Total costs
                SUM(ISNULL(LaborCost, 0) + ISNULL(PartsCost, 0) + ISNULL(MiscCost, 0) + 
                    ISNULL(EquipmentCost, 0) + ISNULL(RentalCost, 0)) as total_cost,
                -- Invoice count
                COUNT(DISTINCT InvoiceNo) as invoice_count
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
            AND InvoiceDate < DATEADD(month, 1, GETDATE())
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate), DATENAME(month, InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            monthly_result = db.execute_query(monthly_financial_query)
            
            monthlyFinancials = []
            logger.info(f"Monthly financial data rows: {len(monthly_result) if monthly_result else 0}")
            for row in monthly_result:
                revenue = float(row.get('revenue', 0) or 0)
                total_cost = float(row.get('total_cost', 0) or 0)
                
                # Calculate gross profit
                gross_profit = revenue - total_cost
                
                # Estimate overhead/operating expenses (15% of revenue as placeholder)
                overhead = revenue * 0.15
                
                # Total expenses = COGS + overhead
                total_expenses = total_cost + overhead
                
                # Net profit
                net_profit = revenue - total_expenses
                
                monthlyFinancials.append({
                    'month': row.get('month_name', '')[:3],  # Abbreviate month
                    'revenue': round(revenue, 2),
                    'expenses': round(total_expenses, 2),
                    'profit': round(net_profit, 2),
                    'cogs': round(total_cost, 2),  # Cost of Goods Sold
                    'overhead': round(overhead, 2),
                    'margin': round((gross_profit / revenue * 100) if revenue > 0 else 0, 1)
                })
            
            # Get YTD summary
            ytd_summary_query = f"""
            SELECT 
                -- Total Revenue YTD
                SUM(GrandTotal) as total_revenue,
                -- Total Costs YTD
                SUM(ISNULL(LaborCost, 0) + ISNULL(PartsCost, 0) + ISNULL(MiscCost, 0) + 
                    ISNULL(EquipmentCost, 0) + ISNULL(RentalCost, 0)) as total_cogs,
                -- Accounts Receivable (from Customer table)
                (SELECT SUM(Balance) FROM ben002.Customer WHERE Balance > 0) as accounts_receivable,
                -- Overdue Invoices
                (SELECT COUNT(*) FROM ben002.InvoiceReg 
                 WHERE InvoiceStatus = 'Open' 
                 AND DATEDIFF(day, InvoiceDate, GETDATE()) > 30) as overdue_invoices,
                -- Current Month Cash Flow
                (SELECT SUM(GrandTotal) FROM ben002.InvoiceReg 
                 WHERE MONTH(InvoiceDate) = {today.month}
                 AND YEAR(InvoiceDate) = {today.year}) as monthly_cash_flow
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{year_start.strftime('%Y-%m-%d')}'
            AND InvoiceDate < '{today.strftime('%Y-%m-%d')}'
            """
            
            summary_result = db.execute_query(ytd_summary_query)
            
            if summary_result:
                total_revenue = float(summary_result[0].get('total_revenue', 0) or 0)
                total_cogs = float(summary_result[0].get('total_cogs', 0) or 0)
                overhead_ytd = total_revenue * 0.15  # Estimate
                total_expenses = total_cogs + overhead_ytd
                net_profit = total_revenue - total_expenses
                
                summary = {
                    'totalRevenue': round(total_revenue, 2),
                    'totalExpenses': round(total_expenses, 2),
                    'netProfit': round(net_profit, 2),
                    'profitMargin': round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
                    'accountsReceivable': round(float(summary_result[0].get('accounts_receivable', 0) or 0), 2),
                    'accountsPayable': 0,  # Would need vendor/payables table
                    'cashFlow': round(float(summary_result[0].get('monthly_cash_flow', 0) or 0), 2),
                    'overdueInvoices': summary_result[0].get('overdue_invoices', 0) or 0
                }
            else:
                summary = {
                    'totalRevenue': 0,
                    'totalExpenses': 0,
                    'netProfit': 0,
                    'profitMargin': 0,
                    'accountsReceivable': 0,
                    'accountsPayable': 0,
                    'cashFlow': 0,
                    'overdueInvoices': 0
                }
            
            # Revenue by Department
            dept_revenue_query = f"""
            SELECT 
                CASE 
                    WHEN SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                        'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                        'RENTR', 'RENT-DEL', 'MO-RENT') THEN 'Service'
                    WHEN SaleCode IN ('PARTS', 'PARTSNT', 'FREIGHT', 'SHOPSP') THEN 'Parts'
                    WHEN SaleCode IN ('RENT', 'DLVPKUP', 'DAMAGE', 'DAMAGE-', 'STRENT', 
                        'HRENT', 'LIFTTRK', 'STRENT+') THEN 'Rental'
                    WHEN SaleCode IN ('USEDEQ', 'RTLEQP', 'ALLIEDE', 'NEWEQP') THEN 'Equipment'
                    ELSE 'Other'
                END as department,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{year_start.strftime('%Y-%m-%d')}'
            GROUP BY 
                CASE 
                    WHEN SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                        'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                        'RENTR', 'RENT-DEL', 'MO-RENT') THEN 'Service'
                    WHEN SaleCode IN ('PARTS', 'PARTSNT', 'FREIGHT', 'SHOPSP') THEN 'Parts'
                    WHEN SaleCode IN ('RENT', 'DLVPKUP', 'DAMAGE', 'DAMAGE-', 'STRENT', 
                        'HRENT', 'LIFTTRK', 'STRENT+') THEN 'Rental'
                    WHEN SaleCode IN ('USEDEQ', 'RTLEQP', 'ALLIEDE', 'NEWEQP') THEN 'Equipment'
                    ELSE 'Other'
                END
            ORDER BY revenue DESC
            """
            
            dept_result = db.execute_query(dept_revenue_query)
            
            revenueByDepartment = []
            total_dept_revenue = sum(float(row.get('revenue', 0) or 0) for row in dept_result) if dept_result else 0
            
            if dept_result:
                for row in dept_result:
                    revenue = float(row.get('revenue', 0) or 0)
                    revenueByDepartment.append({
                        'department': row.get('department', 'Unknown'),
                        'revenue': round(revenue, 2),
                        'percentage': round((revenue / total_dept_revenue * 100) if total_dept_revenue > 0 else 0, 1)
                    })
            
            # Expense categories based on actual costs
            expense_breakdown_query = f"""
            SELECT 
                SUM(ISNULL(LaborCost, 0)) as labor_cost,
                SUM(ISNULL(PartsCost, 0)) as parts_cost,
                SUM(ISNULL(MiscCost, 0)) as misc_cost,
                SUM(ISNULL(EquipmentCost, 0)) as equipment_cost,
                SUM(ISNULL(RentalCost, 0)) as rental_cost,
                SUM(ISNULL(LaborCost, 0) + ISNULL(PartsCost, 0) + ISNULL(MiscCost, 0) + 
                    ISNULL(EquipmentCost, 0) + ISNULL(RentalCost, 0)) as total_cost
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{year_start.strftime('%Y-%m-%d')}'
            """
            
            expense_result = db.execute_query(expense_breakdown_query)
            
            expenseCategories = []
            if expense_result:
                labor = float(expense_result[0].get('labor_cost', 0) or 0)
                parts = float(expense_result[0].get('parts_cost', 0) or 0)
                misc = float(expense_result[0].get('misc_cost', 0) or 0)
                equipment = float(expense_result[0].get('equipment_cost', 0) or 0)
                rental = float(expense_result[0].get('rental_cost', 0) or 0)
                total = float(expense_result[0].get('total_cost', 0) or 0)
                overhead = total_revenue * 0.15  # Estimate overhead
                
                total_with_overhead = total + overhead
                
                expenseCategories = [
                    {'category': 'Labor', 'amount': round(labor, 2), 
                     'percentage': round((labor / total_with_overhead * 100) if total_with_overhead > 0 else 0, 1)},
                    {'category': 'Parts & Materials', 'amount': round(parts, 2), 
                     'percentage': round((parts / total_with_overhead * 100) if total_with_overhead > 0 else 0, 1)},
                    {'category': 'Equipment', 'amount': round(equipment, 2), 
                     'percentage': round((equipment / total_with_overhead * 100) if total_with_overhead > 0 else 0, 1)},
                    {'category': 'Overhead', 'amount': round(overhead, 2), 
                     'percentage': round((overhead / total_with_overhead * 100) if total_with_overhead > 0 else 0, 1)},
                    {'category': 'Other', 'amount': round(misc + rental, 2), 
                     'percentage': round(((misc + rental) / total_with_overhead * 100) if total_with_overhead > 0 else 0, 1)}
                ]
            
            logger.info(f"Returning {len(monthlyFinancials)} months of financial data")
            if monthlyFinancials:
                logger.info(f"Sample month data: {monthlyFinancials[0]}")
            
            return jsonify({
                'summary': summary,
                'revenueByDepartment': revenueByDepartment,
                'expenseCategories': expenseCategories,
                'monthlyFinancials': monthlyFinancials,
                'cashFlowTrend': [],  # Would need payment data
                'outstandingInvoices': [],  # Could add if needed
                'pendingPayables': []  # Would need vendor data
            })
            
        except Exception as e:
            logger.error(f"Error in accounting report: {str(e)}")
            return jsonify({
                'error': str(e),
                'type': 'accounting_report_error'
            }), 500
    
    @reports_bp.route('/departments/database-explorer', methods=['GET'])
    @jwt_required()
    def database_explorer():
        """Explore database schema and data"""
        try:
            db = get_db()
            table_name = request.args.get('table')
            
            if not table_name:
                # Return list of all tables
                tables_query = """
                SELECT 
                    t.TABLE_NAME,
                    t.TABLE_TYPE,
                    p.rows AS row_count
                FROM INFORMATION_SCHEMA.TABLES t
                LEFT JOIN sys.partitions p ON p.object_id = OBJECT_ID('ben002.' + t.TABLE_NAME)
                WHERE t.TABLE_SCHEMA = 'ben002'
                AND p.index_id IN (0,1)
                ORDER BY p.rows DESC
                """
                
                tables = db.execute_query(tables_query)
                return jsonify({
                    'tables': tables,
                    'total_tables': len(tables)
                })
            
            else:
                # Return info about specific table
                # Get columns
                columns_query = f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = db.execute_query(columns_query)
                
                # Get sample data
                limit = request.args.get('limit', 10)
                sample_query = f"SELECT TOP {limit} * FROM ben002.{table_name}"
                
                try:
                    sample_data = db.execute_query(sample_query)
                except Exception as e:
                    sample_data = []
                    logger.error(f"Error getting sample data: {str(e)}")
                
                # Get row count
                count_query = f"SELECT COUNT(*) as total_rows FROM ben002.{table_name}"
                count_result = db.execute_query(count_query)
                
                return jsonify({
                    'table_name': table_name,
                    'columns': columns,
                    'total_rows': count_result[0]['total_rows'] if count_result else 0,
                    'sample_data': sample_data
                })
                
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'database_explorer_error'
            }), 500
    
    @reports_bp.route('/database-explorer', methods=['GET'])
    @jwt_required()
    def comprehensive_database_explorer():
        """Comprehensive database explorer with all tables info"""
        try:
            db = get_db()
            
            # Check if this is a full export request
            full_export = request.args.get('full_export', 'false').lower() == 'true'
            
            # Get all tables with details
            tables_query = """
            SELECT 
                t.TABLE_NAME as table_name,
                p.rows as row_count
            FROM INFORMATION_SCHEMA.TABLES t
            LEFT JOIN sys.partitions p ON p.object_id = OBJECT_ID('ben002.' + t.TABLE_NAME)
            WHERE t.TABLE_SCHEMA = 'ben002'
            AND t.TABLE_TYPE = 'BASE TABLE'
            AND p.index_id IN (0,1)
            ORDER BY t.TABLE_NAME
            """
            
            tables = db.execute_query(tables_query)
            
            # Determine how many tables to process
            tables_to_process = tables if full_export else tables[:20]
            
            # Get tables with full info
            tables_with_details = []
            for table in tables_to_process:
                table_name = table['table_name']
                
                # Get columns
                columns_query = f"""
                SELECT 
                    COLUMN_NAME as column_name,
                    DATA_TYPE as data_type,
                    CHARACTER_MAXIMUM_LENGTH as character_maximum_length,
                    IS_NULLABLE as is_nullable,
                    COLUMN_DEFAULT as column_default
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = db.execute_query(columns_query)
                
                # Get primary keys
                pk_query = f"""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
                AND TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME = '{table_name}'
                """
                
                primary_keys = db.execute_query(pk_query)
                pk_list = [pk['COLUMN_NAME'] for pk in primary_keys]
                
                # Get sample data
                try:
                    sample_query = f"SELECT TOP 5 * FROM ben002.{table_name}"
                    sample_data = db.execute_query(sample_query)
                except:
                    sample_data = []
                
                # Get relationships (foreign keys)
                fk_query = f"""
                SELECT 
                    fkc.COLUMN_NAME as column,
                    pk.TABLE_NAME as referenced_table,
                    pkc.COLUMN_NAME as referenced_column
                FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fkc
                    ON rc.CONSTRAINT_NAME = fkc.CONSTRAINT_NAME
                    AND rc.CONSTRAINT_SCHEMA = fkc.CONSTRAINT_SCHEMA
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pkc
                    ON rc.UNIQUE_CONSTRAINT_NAME = pkc.CONSTRAINT_NAME
                    AND rc.UNIQUE_CONSTRAINT_SCHEMA = pkc.CONSTRAINT_SCHEMA
                JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS pk
                    ON pkc.CONSTRAINT_NAME = pk.CONSTRAINT_NAME
                    AND pkc.CONSTRAINT_SCHEMA = pk.CONSTRAINT_SCHEMA
                WHERE fkc.TABLE_SCHEMA = 'ben002'
                AND fkc.TABLE_NAME = '{table_name}'
                """
                
                relationships = []
                try:
                    fk_results = db.execute_query(fk_query)
                    for fk in fk_results:
                        relationships.append({
                            'type': 'foreign_key',
                            'column': fk['column'],
                            'referenced_table': fk['referenced_table'],
                            'referenced_column': fk['referenced_column']
                        })
                except:
                    pass
                
                tables_with_details.append({
                    'table_name': table_name,
                    'row_count': table['row_count'] or 0,
                    'columns': columns,
                    'primary_keys': pk_list,
                    'sample_data': sample_data,
                    'relationships': relationships
                })
            
            # Calculate summary stats
            total_rows = sum(t['row_count'] or 0 for t in tables)
            
            # Get total relationships count
            relationships_query = """
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS
            WHERE CONSTRAINT_SCHEMA = 'ben002'
            """
            rel_result = db.execute_query(relationships_query)
            total_relationships = rel_result[0]['count'] if rel_result else 0
            
            return jsonify({
                'export_date': datetime.now().isoformat(),
                'tables': tables_with_details,
                'summary': {
                    'total_tables': len(tables),
                    'total_rows': total_rows,
                    'total_relationships': total_relationships
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'database_explorer_error'
            }), 500