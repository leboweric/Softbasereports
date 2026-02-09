from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import pandas as pd
from ..services.azure_sql_service import AzureSQLService
from ..models.user import User
import logging

logger = logging.getLogger(__name__)

softbase_reports_bp = Blueprint('softbase_reports', __name__)

def get_date_range(period='month'):
    """Get start and end dates based on period"""
    end_date = datetime.now()
    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    elif period == 'quarter':
        start_date = end_date - timedelta(days=90)
    elif period == 'year':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

@softbase_reports_bp.route('/api/reports/customer-activity', methods=['GET'])
@jwt_required()
def customer_activity_report():
    """Get customer activity report including sales, service, and equipment"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        # Get parameters
        customer_no = request.args.get('customer_no')
        period = request.args.get('period', 'month')
        start_date, end_date = get_date_range(period)
        
        db = get_tenant_db()
        
        report_data = {}
        
        # 1. Customer Information
        if customer_no:
            customer_query = f"""
            SELECT TOP 1
                ID as CustomerNo,
                Name,
                Address1 as Address,
                City,
                State,
                ZipCode as Zip,
                Phone,
                SalesmanNo,
                CreditLimit,
                Balance,
                LastSaleDate,
                LastPaymentDate,
                YTD as YTDSales,
                YTD as YTDPayments
            FROM {schema}.Customer
            WHERE ID = ?
            """
            customers = db.execute_query(customer_query, (customer_no,))
            report_data['customers'] = customers
            customer_query = None  # Clear to avoid double execution
        else:
            # Get top customers by YTD sales
            customer_query = f"""
            SELECT TOP 20
                ID as CustomerNo,
                Name,
                City,
                State,
                Balance,
                YTD as YTDSales,
                YTD as YTDPayments,
                LastSaleDate
            FROM {schema}.Customer
            WHERE YTD > 0
            ORDER BY YTD DESC
            """
            customers = db.execute_query(customer_query)
            report_data['customers'] = customers
        
        # 2. Recent Invoices
        if customer_no:
            invoice_query = f"""
            SELECT TOP 20
                InvoiceNo,
                InvoiceDate,
                Customer as CustomerNo,
                BillToName as CustomerName,
                GrandTotal as TotalAmount,
                SalesTax as TotalTax,
                InvoiceStatus as Status,
                InvoiceType,
                Department as DepartmentNo
            FROM {schema}.InvoiceReg
            WHERE Customer = ?
            AND InvoiceDate >= ?
            ORDER BY InvoiceDate DESC
            """
            invoices = db.execute_query(invoice_query, (customer_no, start_date))
            report_data['invoices'] = invoices
        
        # 3. Equipment owned by customer
        if customer_no:
            equipment_query = f"""
            SELECT 
                StockNo,
                SerialNo,
                Make,
                Model,
                ModelYear,
                RentalStatus as Status,
                AcquiredDate as PurchaseDate,
                SaleAmount as SellingPrice,
                Hours
            FROM {schema}.Equipment
            WHERE Customer = ?
            AND RentalStatus IN ('Sold', 'Rented')
            ORDER BY AcquiredDate DESC
            """
            equipment = db.execute_query(equipment_query, (customer_no,))
            report_data['equipment'] = equipment
        
        # 4. Service history
        if customer_no:
            service_query = f"""
            SELECT TOP 20
                ServiceClaimNo as ClaimNo,
                OpenDate as DateOpened,
                CloseDate as DateClosed,
                StockNo,
                SerialNo,
                TotalLabor,
                TotalParts,
                CASE WHEN CloseDate IS NULL THEN 'Open' ELSE 'Closed' END as Status
            FROM {schema}.ServiceClaim
            WHERE Customer = ?
            AND OpenDate >= ?
            ORDER BY OpenDate DESC
            """
            service = db.execute_query(service_query, (customer_no, start_date))
            report_data['service_history'] = service
        
        # 5. Summary statistics
        if customer_no:
            summary_query = f"""
            SELECT 
                COUNT(DISTINCT InvoiceNo) as total_invoices,
                SUM(GrandTotal) as total_sales,
                AVG(GrandTotal) as avg_invoice_amount,
                COUNT(DISTINCT InvoiceNo) as equipment_count
            FROM {schema}.InvoiceReg
            WHERE Customer = ?
            AND InvoiceDate >= ?
            """
            summary = db.execute_query(summary_query, (customer_no, start_date))
            report_data['summary'] = summary[0] if summary else {}
        
        return jsonify({
            'report': 'Customer Activity Report',
            'period': period,
            'date_range': {'start': start_date, 'end': end_date},
            'data': report_data,
            'generated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Customer activity report failed: {str(e)}")
        return jsonify({'error': 'Report generation failed', 'message': str(e)}), 500

@softbase_reports_bp.route('/api/reports/equipment-inventory', methods=['GET'])
@jwt_required()
def equipment_inventory_report():
    """Get equipment inventory status report"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        # Get parameters
        status = request.args.get('status', 'all')
        make = request.args.get('make')
        
        db = get_tenant_db()
        
        # Build query based on filters
        where_clauses = []
        if status != 'all':
            where_clauses.append(f"Status = '{status}'")
        if make:
            where_clauses.append(f"Make = '{make}'")
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # 1. Equipment inventory by status
        inventory_query = f"""
        SELECT 
            Status,
            COUNT(*) as Count,
            SUM(Cost) as TotalCost,
            SUM(SellingPrice) as TotalSellingPrice,
            AVG(Hours) as AvgHours
        FROM {schema}.Equipment
        {where_clause}
        GROUP BY Status
        ORDER BY Count DESC
        """
        inventory_summary = db.execute_query(inventory_query)
        
        # 2. Equipment details
        equipment_query = f"""
        SELECT TOP 100
            StockNo,
            SerialNo,
            Make,
            Model,
            ModelYear,
            Status,
            Location,
            Cost,
            SellingPrice,
            Hours,
            LastServiceDate,
            CustomerNo,
            Added
        FROM {schema}.Equipment
        {where_clause}
        ORDER BY Added DESC
        """
        equipment_list = db.execute_query(equipment_query)
        
        # 3. Equipment by make/model
        make_model_query = f"""
        SELECT 
            Make,
            Model,
            COUNT(*) as Count,
            AVG(Cost) as AvgCost,
            AVG(SellingPrice) as AvgSellingPrice
        FROM {schema}.Equipment
        {where_clause}
        GROUP BY Make, Model
        ORDER BY Count DESC
        """
        make_model_summary = db.execute_query(make_model_query)
        
        # 4. Age analysis
        age_query = f"""
        SELECT 
            ModelYear,
            COUNT(*) as Count,
            AVG(Hours) as AvgHours,
            SUM(Cost) as TotalCost
        FROM {schema}.Equipment
        WHERE ModelYear IS NOT NULL
        {' AND ' + where_clause.replace('WHERE ', '') if where_clause else ''}
        GROUP BY ModelYear
        ORDER BY ModelYear DESC
        """
        age_analysis = db.execute_query(age_query)
        
        return jsonify({
            'report': 'Equipment Inventory Report',
            'filters': {'status': status, 'make': make},
            'data': {
                'inventory_summary': inventory_summary,
                'equipment_list': equipment_list,
                'make_model_summary': make_model_summary,
                'age_analysis': age_analysis
            },
            'generated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Equipment inventory report failed: {str(e)}")
        return jsonify({'error': 'Report generation failed', 'message': str(e)}), 500

@softbase_reports_bp.route('/api/reports/sales-analysis', methods=['GET'])
@jwt_required()
def sales_analysis_report():
    """Get sales analysis report"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        period = request.args.get('period', 'month')
        department = request.args.get('department')
        salesman = request.args.get('salesman')
        
        start_date, end_date = get_date_range(period)
        
        db = get_tenant_db()
        
        # Build where clause
        where_clauses = [f"InvoiceDate BETWEEN '{start_date}' AND '{end_date}'"]
        if department:
            where_clauses.append(f"DepartmentNo = '{department}'")
        if salesman:
            where_clauses.append(f"SalesmanNo = '{salesman}'")
        
        where_clause = " AND ".join(where_clauses)
        
        # 1. Sales summary
        summary_query = f"""
        SELECT 
            COUNT(DISTINCT InvoiceNo) as TotalInvoices,
            COUNT(DISTINCT CustomerNo) as UniqueCustomers,
            SUM(TotalAmount) as TotalSales,
            SUM(TotalTax) as TotalTax,
            AVG(TotalAmount) as AvgInvoiceAmount,
            MAX(TotalAmount) as LargestInvoice
        FROM {schema}.InvoiceReg
        WHERE {where_clause}
        """
        summary = db.execute_query(summary_query)
        
        # 2. Sales by day
        daily_query = f"""
        SELECT 
            CAST(InvoiceDate as DATE) as SaleDate,
            COUNT(*) as InvoiceCount,
            SUM(TotalAmount) as DailySales
        FROM {schema}.InvoiceReg
        WHERE {where_clause}
        GROUP BY CAST(InvoiceDate as DATE)
        ORDER BY SaleDate DESC
        """
        daily_sales = db.execute_query(daily_query)
        
        # 3. Sales by department
        dept_query = f"""
        SELECT 
            DepartmentNo,
            COUNT(*) as InvoiceCount,
            SUM(TotalAmount) as TotalSales,
            AVG(TotalAmount) as AvgSale
        FROM {schema}.InvoiceReg
        WHERE {where_clause}
        GROUP BY DepartmentNo
        ORDER BY TotalSales DESC
        """
        dept_sales = db.execute_query(dept_query)
        
        # 4. Top customers
        customer_query = f"""
        SELECT TOP 20
            CustomerNo,
            CustomerName,
            COUNT(*) as InvoiceCount,
            SUM(TotalAmount) as TotalPurchases,
            AVG(TotalAmount) as AvgPurchase
        FROM {schema}.InvoiceReg
        WHERE {where_clause}
        GROUP BY CustomerNo, CustomerName
        ORDER BY TotalPurchases DESC
        """
        top_customers = db.execute_query(customer_query)
        
        # 5. Sales by type
        type_query = f"""
        SELECT 
            InvoiceType,
            COUNT(*) as Count,
            SUM(TotalAmount) as Total
        FROM {schema}.InvoiceReg
        WHERE {where_clause}
        GROUP BY InvoiceType
        ORDER BY Total DESC
        """
        sales_by_type = db.execute_query(type_query)
        
        return jsonify({
            'report': 'Sales Analysis Report',
            'period': period,
            'date_range': {'start': start_date, 'end': end_date},
            'filters': {'department': department, 'salesman': salesman},
            'data': {
                'summary': summary[0] if summary else {},
                'daily_sales': daily_sales,
                'department_sales': dept_sales,
                'top_customers': top_customers,
                'sales_by_type': sales_by_type
            },
            'generated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Sales analysis report failed: {str(e)}")
        return jsonify({'error': 'Report generation failed', 'message': str(e)}), 500

@softbase_reports_bp.route('/api/reports/service-history', methods=['GET'])
@jwt_required()
def service_history_report():
    """Get service history report"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        period = request.args.get('period', 'month')
        status = request.args.get('status', 'all')
        technician = request.args.get('technician')
        
        start_date, end_date = get_date_range(period)
        
        db = get_tenant_db()
        
        # Build where clause
        where_clauses = [f"DateOpened BETWEEN '{start_date}' AND '{end_date}'"]
        if status != 'all':
            where_clauses.append(f"Status = '{status}'")
        if technician:
            where_clauses.append(f"TechnicianNo = '{technician}'")
        
        where_clause = " AND ".join(where_clauses)
        
        # 1. Service summary
        summary_query = f"""
        SELECT 
            COUNT(*) as TotalClaims,
            SUM(TotalLabor) as TotalLaborRevenue,
            SUM(TotalParts) as TotalPartsRevenue,
            SUM(TotalLabor + TotalParts) as TotalRevenue,
            AVG(DATEDIFF(day, DateOpened, DateClosed)) as AvgDaysToClose
        FROM {schema}.ServiceClaim
        WHERE {where_clause}
        """
        summary = db.execute_query(summary_query)
        
        # 2. Service claims list
        claims_query = f"""
        SELECT TOP 100
            ClaimNo,
            DateOpened,
            DateClosed,
            CustomerNo,
            CustomerName,
            StockNo,
            SerialNo,
            Make,
            Model,
            TotalLabor,
            TotalParts,
            Status,
            TechnicianNo
        FROM {schema}.ServiceClaim
        WHERE {where_clause}
        ORDER BY DateOpened DESC
        """
        claims = db.execute_query(claims_query)
        
        # 3. Common repair codes
        repair_codes_query = f"""
        SELECT TOP 20
            rc.Code,
            rc.Description,
            COUNT(*) as Frequency,
            SUM(scr.LaborHours) as TotalHours,
            SUM(scr.LaborAmount) as TotalLabor
        FROM {schema}.ServiceClaimRepairCode scr
        JOIN {schema}.RepairCode rc ON scr.RepairCodeId = rc.Id
        JOIN {schema}.ServiceClaim sc ON scr.ServiceClaimId = sc.Id
        WHERE sc.DateOpened BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY rc.Code, rc.Description
        ORDER BY Frequency DESC
        """
        repair_codes = db.execute_query(repair_codes_query)
        
        # 4. Equipment service frequency
        equipment_query = f"""
        SELECT 
            StockNo,
            SerialNo,
            Make,
            Model,
            COUNT(*) as ServiceCount,
            SUM(TotalLabor + TotalParts) as TotalServiceCost
        FROM {schema}.ServiceClaim
        WHERE {where_clause}
        GROUP BY StockNo, SerialNo, Make, Model
        HAVING COUNT(*) > 1
        ORDER BY ServiceCount DESC
        """
        frequent_service = db.execute_query(equipment_query)
        
        return jsonify({
            'report': 'Service History Report',
            'period': period,
            'date_range': {'start': start_date, 'end': end_date},
            'filters': {'status': status, 'technician': technician},
            'data': {
                'summary': summary[0] if summary else {},
                'claims': claims,
                'common_repair_codes': repair_codes,
                'frequent_service_equipment': frequent_service
            },
            'generated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Service history report failed: {str(e)}")
        return jsonify({'error': 'Report generation failed', 'message': str(e)}), 500

@softbase_reports_bp.route('/api/reports/parts-usage', methods=['GET'])
@jwt_required()
def parts_usage_report():
    """Get parts usage and inventory report"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        period = request.args.get('period', 'month')
        part_no = request.args.get('part_no')
        
        start_date, end_date = get_date_range(period)
        
        db = get_tenant_db()
        
        # 1. Parts usage from invoices
        usage_query = f"""
        SELECT TOP 50
            PartNo,
            Description,
            COUNT(*) as TimesUsed,
            SUM(Quantity) as TotalQuantity,
            SUM(ExtendedPrice) as TotalRevenue,
            AVG(Price) as AvgPrice
        FROM {schema}.InvoicePartsDetail
        WHERE InvoiceDate BETWEEN '{start_date}' AND '{end_date}'
        {f"AND PartNo = '{part_no}'" if part_no else ''}
        GROUP BY PartNo, Description
        ORDER BY TotalRevenue DESC
        """
        parts_usage = db.execute_query(usage_query)
        
        # 2. Parts inventory levels
        inventory_query = f"""
        SELECT TOP 50
            PartNo,
            Description,
            OnHand,
            OnOrder,
            Cost,
            List,
            BinLocation
        FROM {schema}.NationalParts
        WHERE OnHand > 0
        ORDER BY (OnHand * Cost) DESC
        """
        inventory = db.execute_query(inventory_query)
        
        # 3. Low stock alert
        low_stock_query = f"""
        SELECT 
            PartNo,
            Description,
            OnHand,
            MinimumStock,
            OnOrder,
            LastSaleDate
        FROM {schema}.NationalParts
        WHERE OnHand < MinimumStock
        AND MinimumStock > 0
        ORDER BY (MinimumStock - OnHand) DESC
        """
        low_stock = db.execute_query(low_stock_query)
        
        # 4. Parts by supplier
        supplier_query = f"""
        SELECT 
            SupplierCode,
            COUNT(*) as PartCount,
            SUM(OnHand * Cost) as InventoryValue,
            AVG(List - Cost) as AvgMarkup
        FROM {schema}.NationalParts
        WHERE SupplierCode IS NOT NULL
        GROUP BY SupplierCode
        ORDER BY InventoryValue DESC
        """
        by_supplier = db.execute_query(supplier_query)
        
        return jsonify({
            'report': 'Parts Usage Report',
            'period': period,
            'date_range': {'start': start_date, 'end': end_date},
            'data': {
                'parts_usage': parts_usage,
                'current_inventory': inventory,
                'low_stock_alerts': low_stock,
                'by_supplier': by_supplier
            },
            'generated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Parts usage report failed: {str(e)}")
        return jsonify({'error': 'Report generation failed', 'message': str(e)}), 500

@softbase_reports_bp.route('/api/reports/financial-etl-now', methods=['POST'])
def run_financial_etl_now():
    """Temporary endpoint to trigger financial ETL"""
    try:
        from src.etl.etl_department_metrics import DepartmentMetricsETL
        import traceback
        
        etl = DepartmentMetricsETL()
        
        # Try just the financial extraction
        try:
            financial_data = etl._extract_financial()
            
            # Load just the financial data
            from src.services.postgres_service import PostgreSQLService
            import json
            from datetime import datetime
            
            pg = PostgreSQLService()
            snapshot_time = datetime.now()
            
            record = {
                'org_id': 4,
                'department': 'financial',
                'monthly_revenue': json.dumps(financial_data.get('monthly_revenue')) if financial_data.get('monthly_revenue') else None,
                'sub_category_1': json.dumps(financial_data.get('sub_category_1')) if financial_data.get('sub_category_1') else None,
                'sub_category_2': json.dumps(financial_data.get('sub_category_2')) if financial_data.get('sub_category_2') else None,
                'metric_1': financial_data.get('metric_1'),
                'metric_2': financial_data.get('metric_2'),
                'metric_3': financial_data.get('metric_3'),
                'count_1': financial_data.get('count_1'),
                'additional_data': json.dumps(financial_data.get('additional_data')) if financial_data.get('additional_data') else None,
                'snapshot_timestamp': snapshot_time,
                'etl_duration_seconds': 0
            }
            
            # Upsert the record
            upsert_query = """
            INSERT INTO mart_department_metrics 
            (org_id, department, monthly_revenue, sub_category_1, sub_category_2, 
             metric_1, metric_2, metric_3, count_1, additional_data, snapshot_timestamp, etl_duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (org_id, department) DO UPDATE SET
                monthly_revenue = EXCLUDED.monthly_revenue,
                sub_category_1 = EXCLUDED.sub_category_1,
                sub_category_2 = EXCLUDED.sub_category_2,
                metric_1 = EXCLUDED.metric_1,
                metric_2 = EXCLUDED.metric_2,
                metric_3 = EXCLUDED.metric_3,
                count_1 = EXCLUDED.count_1,
                additional_data = EXCLUDED.additional_data,
                snapshot_timestamp = EXCLUDED.snapshot_timestamp,
                etl_duration_seconds = EXCLUDED.etl_duration_seconds
            """
            
            pg.execute_query(upsert_query, (
                record['org_id'], record['department'], record['monthly_revenue'],
                record['sub_category_1'], record['sub_category_2'],
                record['metric_1'], record['metric_2'], record['metric_3'],
                record['count_1'], record['additional_data'],
                record['snapshot_timestamp'], record['etl_duration_seconds']
            ))
            
            return jsonify({
                'status': 'success',
                'message': 'Financial ETL completed',
                'data': financial_data
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500
            
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@softbase_reports_bp.route('/api/reports/financial-summary', methods=['GET'])
@jwt_required()
def financial_summary_report():
    """Get financial summary report"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        # Try mart table first for fast response
        if not request.args.get('refresh'):
            try:
                from src.services.postgres_service import PostgreSQLService
                import json as json_lib
                
                pg = PostgreSQLService()
                
                # Get current user's org_id for tenant isolation
                try:
                    uid = get_jwt_identity()
                    u = User.query.get(int(uid))
                    current_org_id = u.organization_id if u else 4
                except Exception:
                    current_org_id = 4
                
                query = """
                SELECT *
                FROM mart_department_metrics
                WHERE org_id = %s AND department = 'financial'
                ORDER BY snapshot_timestamp DESC
                LIMIT 1
                """
                
                result = pg.execute_query(query, (current_org_id,))
                
                if result:
                    metrics = result[0]
                    snapshot_time = metrics['snapshot_timestamp']
                    age_hours = (datetime.now() - snapshot_time).total_seconds() / 3600
                    
                    if age_hours <= 4.0:
                        logger.info(f"Using mart data for financial (age: {age_hours:.1f} hours)")
                        # JSONB columns are auto-parsed by psycopg2 RealDictCursor
                        raw = metrics['additional_data']
                        additional = json_lib.loads(raw) if isinstance(raw, str) else (raw or {})
                        raw = metrics['sub_category_1']
                        top_ar = json_lib.loads(raw) if isinstance(raw, str) else (raw or [])
                        raw = metrics['sub_category_2']
                        revenue_by_dept = json_lib.loads(raw) if isinstance(raw, str) else (raw or [])
                        
                        period = request.args.get('period', 'month')
                        start_date, end_date = get_date_range(period)
                        
                        return jsonify({
                            'report': 'Financial Summary Report',
                            'period': period,
                            'date_range': {'start': start_date, 'end': end_date},
                            'data': {
                                'ar_summary': additional.get('ar_summary', {}),
                                'ar_detail': top_ar,
                                'revenue_by_department': revenue_by_dept,
                                'daily_collections': [],
                                'inventory_value': []
                            },
                            'generated_at': snapshot_time.isoformat(),
                            '_source': 'mart',
                            '_snapshot_time': snapshot_time.isoformat()
                        }), 200
            except Exception as e:
                logger.warning(f"Failed to get mart data for financial: {e}")
        
        # Fall back to live queries
        period = request.args.get('period', 'month')
        start_date, end_date = get_date_range(period)
        
        db = get_tenant_db()
        
        # 1. Accounts Receivable summary
        ar_summary_query = f"""
        SELECT 
            COUNT(DISTINCT CustomerNo) as CustomersWithBalance,
            SUM(Balance) as TotalAR,
            SUM(CASE WHEN DaysPastDue > 0 THEN Balance ELSE 0 END) as PastDueAmount,
            SUM(CASE WHEN DaysPastDue > 30 THEN Balance ELSE 0 END) as Over30Days,
            SUM(CASE WHEN DaysPastDue > 60 THEN Balance ELSE 0 END) as Over60Days,
            SUM(CASE WHEN DaysPastDue > 90 THEN Balance ELSE 0 END) as Over90Days
        FROM {schema}.Customer
        WHERE Balance > 0
        """
        ar_summary = db.execute_query(ar_summary_query)
        
        # 2. Top AR balances
        ar_detail_query = f"""
        SELECT TOP 20
            CustomerNo,
            Name,
            Balance,
            CreditLimit,
            DaysPastDue,
            LastPaymentDate,
            LastPaymentAmount
        FROM {schema}.Customer
        WHERE Balance > 0
        ORDER BY Balance DESC
        """
        ar_detail = db.execute_query(ar_detail_query)
        
        # 3. Revenue by department
        revenue_query = f"""
        SELECT 
            DepartmentNo,
            COUNT(*) as TransactionCount,
            SUM(TotalAmount) as Revenue,
            SUM(TotalTax) as TaxCollected
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY DepartmentNo
        ORDER BY Revenue DESC
        """
        revenue_by_dept = db.execute_query(revenue_query)
        
        # 4. Cash flow
        cashflow_query = f"""
        SELECT 
            CAST(PaymentDate as DATE) as Date,
            SUM(PaymentAmount) as DailyCollections,
            COUNT(*) as PaymentCount
        FROM {schema}.ARDetail
        WHERE PaymentDate BETWEEN '{start_date}' AND '{end_date}'
        AND TransactionType = 'Payment'
        GROUP BY CAST(PaymentDate as DATE)
        ORDER BY Date DESC
        """
        cashflow = db.execute_query(cashflow_query)
        
        # 5. Inventory value
        inventory_value_query = f"""
        SELECT 
            Status,
            COUNT(*) as Count,
            SUM(Cost) as TotalCost,
            SUM(SellingPrice) as TotalRetailValue
        FROM {schema}.Equipment
        WHERE Status IN ('In Stock', 'On Order')
        GROUP BY Status
        """
        inventory_value = db.execute_query(inventory_value_query)
        
        return jsonify({
            'report': 'Financial Summary Report',
            'period': period,
            'date_range': {'start': start_date, 'end': end_date},
            'data': {
                'ar_summary': ar_summary[0] if ar_summary else {},
                'ar_detail': ar_detail,
                'revenue_by_department': revenue_by_dept,
                'daily_collections': cashflow,
                'inventory_value': inventory_value
            },
            'generated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Financial summary report failed: {str(e)}")
        return jsonify({'error': 'Report generation failed', 'message': str(e)}), 500

@softbase_reports_bp.route('/api/reports/available', methods=['GET'])
@jwt_required()
def available_reports():
    """Get list of available reports"""
    reports = [
        {
            'id': 'customer-activity',
            'name': 'Customer Activity Report',
            'description': 'Customer sales, service, and equipment history',
            'parameters': ['customer_no', 'period']
        },
        {
            'id': 'equipment-inventory',
            'name': 'Equipment Inventory Report',
            'description': 'Current inventory status and analysis',
            'parameters': ['status', 'make']
        },
        {
            'id': 'sales-analysis',
            'name': 'Sales Analysis Report',
            'description': 'Sales trends and performance metrics',
            'parameters': ['period', 'department', 'salesman']
        },
        {
            'id': 'service-history',
            'name': 'Service History Report',
            'description': 'Service claims and repair analysis',
            'parameters': ['period', 'status', 'technician']
        },
        {
            'id': 'parts-usage',
            'name': 'Parts Usage Report',
            'description': 'Parts inventory and usage analysis',
            'parameters': ['period', 'part_no']
        },
        {
            'id': 'financial-summary',
            'name': 'Financial Summary Report',
            'description': 'AR balances, revenue, and cash flow',
            'parameters': ['period']
        }
    ]
    
    return jsonify({'reports': reports}), 200