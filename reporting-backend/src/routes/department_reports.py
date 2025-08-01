# Department-specific report endpoints
from flask import jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from src.services.azure_sql_service import AzureSQLService

def get_db():
    """Get database connection"""
    return AzureSQLService()


def register_department_routes(reports_bp):
    """Register department report routes with the reports blueprint"""
    
    @reports_bp.route('/departments/service', methods=['GET'])
    @jwt_required()
    def get_service_department_report():
        """Get Service Department report data"""
        try:
            db = get_db()
            
            # Get current date info
            today = datetime.now()
            month_start = today.replace(day=1)
            
            # 1. Summary metrics
            summary_query = f"""
            SELECT 
                -- Open Work Orders
                (SELECT COUNT(*) FROM ben002.WO 
                 WHERE Type = 'S' AND ClosedDate IS NULL) as openWorkOrders,
                
                -- Completed Today
                (SELECT COUNT(*) FROM ben002.WO 
                 WHERE Type = 'S' AND CAST(CompletedDate as DATE) = CAST(GETDATE() as DATE)) as completedToday,
                
                -- Average Repair Time (hours)
                (SELECT AVG(DATEDIFF(hour, OpenDate, CompletedDate))
                 FROM ben002.WO 
                 WHERE Type = 'S' AND CompletedDate IS NOT NULL 
                 AND OpenDate >= DATEADD(month, -1, GETDATE())) as averageRepairTime,
                
                -- Monthly Revenue
                (SELECT SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) FROM ben002.InvoiceReg 
                 WHERE InvoiceDate >= '{month_start.strftime('%Y-%m-%d')}' 
                 AND InvoiceDate < '{today.strftime('%Y-%m-%d')}') as revenue,
                 
                -- Customers Served
                (SELECT COUNT(DISTINCT BillTo) FROM ben002.WO 
                 WHERE Type = 'S' 
                 AND OpenDate >= '{month_start.strftime('%Y-%m-%d')}'
                 AND OpenDate < '{today.strftime('%Y-%m-%d')}') as customersServed
            """
            
            summary_result = db.execute_query(summary_query)
            
            if summary_result and len(summary_result) > 0:
                row = summary_result[0]
                summary = {
                    'openWorkOrders': row.get('openWorkOrders', 0) or 0,
                    'completedToday': row.get('completedToday', 0) or 0,
                    'averageRepairTime': round(row.get('averageRepairTime', 0) or 0, 1),
                    'technicianEfficiency': 0
                    'revenue': float(row.get('revenue', 0) or 0),
                    'customersServed': row.get('customersServed', 0) or 0
                }
            else:
                summary = {
                    'openWorkOrders': 0,
                    'completedToday': 0,
                    'averageRepairTime': 0,
                    'technicianEfficiency': 87,
                    'revenue': 0,
                    'customersServed': 0
                }
            
            # 2. Work Orders by Status
            status_query = """
            SELECT 
                CASE 
                    WHEN ClosedDate IS NOT NULL THEN 'Completed'
                    WHEN CompletedDate IS NOT NULL THEN 'Completed'
                    WHEN InvoiceDate IS NOT NULL THEN 'Invoiced'
                    ELSE 'Open'
                END as status,
                COUNT(*) as count
            FROM ben002.WO
            WHERE Type = 'S'
            AND OpenDate >= DATEADD(month, -3, GETDATE())
            GROUP BY 
                CASE 
                    WHEN ClosedDate IS NOT NULL THEN 'Completed'
                    WHEN CompletedDate IS NOT NULL THEN 'Completed'
                    WHEN InvoiceDate IS NOT NULL THEN 'Invoiced'
                    ELSE 'Open'
                END
            """
            
            status_result = db.execute_query(status_query)
            
            status_colors = {
                'Open': '#f59e0b',
                'In Progress': '#3b82f6',
                'Completed': '#10b981',
                'Invoiced': '#8b5cf6'
            }
            
            workOrdersByStatus = []
            for row in status_result:
                workOrdersByStatus.append({
                    'status': row[0],
                    'count': row[1],
                    'color': status_colors.get(row[0], '#6b7280')
                })
            
            # 3. Recent Work Orders
            recent_query = """
            SELECT TOP 10
                w.WONo as id,
                w.BillTo as Customer,
                w.Equipment,
                CASE 
                    WHEN w.ClosedDate IS NOT NULL THEN 'Completed'
                    WHEN w.CompletedDate IS NOT NULL THEN 'In Progress'
                    ELSE 'Open'
                END as status,
                'Unassigned' as technician,  -- Would need technician table
                CASE 
                    WHEN w.Priority = 'H' THEN 'High'
                    WHEN w.Priority = 'M' THEN 'Medium'
                    ELSE 'Low'
                END as priority
            FROM ben002.WO w
            WHERE w.Type = 'S'
            ORDER BY w.OpenDate DESC
            """
            
            recent_result = db.execute_query(recent_query)
            
            recentWorkOrders = []
            for row in recent_result:
                recentWorkOrders.append({
                    'id': f'WO-{row[0]}',
                    'customer': row[1] or 'Unknown',
                    'equipment': row[2] or 'N/A',
                    'status': row[3],
                    'technician': row[4],
                    'priority': row[5]
                })
            
            # 4. Monthly Trend
            trend_query = """
            SELECT 
                DATENAME(month, InvoiceDate) as month,
                COUNT(DISTINCT InvoiceNo) as completed,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            GROUP BY DATENAME(month, InvoiceDate), MONTH(InvoiceDate), YEAR(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            trend_result = db.execute_query(trend_query)
            
            monthlyTrend = []
            for row in trend_result:
                monthlyTrend.append({
                    'month': row[0][:3],  # Abbreviate month name
                    'completed': row[1],
                    'revenue': float(row[2] or 0)
                })
            
            # Technician performance data not available yet
            technicianPerformance = []
            
            # 5. Monthly Labor Revenue - Last 12 months
            labor_revenue_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as labor_revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            labor_revenue_result = db.execute_query(labor_revenue_query)
            
            monthlyLaborRevenue = []
            for row in labor_revenue_result:
                month_date = datetime(row['year'], row['month'], 1)
                monthlyLaborRevenue.append({
                    'month': month_date.strftime("%b"),
                    'amount': float(row['labor_revenue'] or 0)
                })
            
            # Pad with zeros for missing months
            if len(monthlyLaborRevenue) < 12:
                all_months = []
                current_date = datetime.now()
                for i in range(11, -1, -1):
                    month_date = current_date - timedelta(days=i*30)
                    all_months.append(month_date.strftime("%b"))
                
                existing_months = [item['month'] for item in monthlyLaborRevenue]
                for month in all_months:
                    if month not in existing_months:
                        monthlyLaborRevenue.append({'month': month, 'amount': 0})
            
            return jsonify({
                'summary': summary,
                'workOrdersByStatus': workOrdersByStatus,
                'recentWorkOrders': recentWorkOrders,
                'monthlyTrend': monthlyTrend,
                'technicianPerformance': technicianPerformance,
                'monthlyLaborRevenue': monthlyLaborRevenue
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'service_report_error'
            }), 500


    @reports_bp.route('/departments/parts', methods=['GET'])
    @jwt_required()
    def get_parts_department_report():
        """Get Parts Department report data"""
        try:
            db = get_db()
            
            # 1. Summary metrics
            summary_query = """
            SELECT 
                -- Total Inventory Value
                (SELECT SUM(OnHand * Cost) FROM ben002.NationalParts WHERE OnHand > 0) as totalInventoryValue,
                
                -- Total Parts
                (SELECT COUNT(*) FROM ben002.NationalParts WHERE OnHand > 0) as totalParts,
                
                -- Low Stock Items
                (SELECT COUNT(*) FROM ben002.NationalParts 
                 WHERE OnHand > 0 AND OnHand <= MinimumStock) as lowStockItems,
                 
                -- Monthly Sales (from parts work orders)
                (SELECT SUM(i.GrandTotal) 
                 FROM ben002.InvoiceReg i
                 WHERE MONTH(i.InvoiceDate) = MONTH(GETDATE())
                 AND YEAR(i.InvoiceDate) = YEAR(GETDATE())) as monthlySales
            """
            
            summary_result = db.execute_query(summary_query)
            
            summary = {
                'totalInventoryValue': float(summary_result[0][0] or 0),
                'totalParts': summary_result[0][1] or 0,
                'lowStockItems': summary_result[0][2] or 0,
                'pendingOrders': 0
                'monthlySales': float(summary_result[0][3] or 0),
                'turnoverRate': 0
            }
            
            # 2. Inventory by Category (simplified - would need category table)
            category_query = """
            SELECT TOP 5
                CASE 
                    WHEN Description LIKE '%FILTER%' THEN 'Filters'
                    WHEN Description LIKE '%OIL%' THEN 'Oils & Fluids'
                    WHEN Description LIKE '%BELT%' THEN 'Belts'
                    WHEN Description LIKE '%BATTERY%' THEN 'Batteries'
                    ELSE 'Other'
                END as category,
                SUM(OnHand * Cost) as value,
                COUNT(*) as count
            FROM ben002.NationalParts
            WHERE OnHand > 0
            GROUP BY 
                CASE 
                    WHEN Description LIKE '%FILTER%' THEN 'Filters'
                    WHEN Description LIKE '%OIL%' THEN 'Oils & Fluids'
                    WHEN Description LIKE '%BELT%' THEN 'Belts'
                    WHEN Description LIKE '%BATTERY%' THEN 'Batteries'
                    ELSE 'Other'
                END
            ORDER BY value DESC
            """
            
            category_result = db.execute_query(category_query)
            
            inventoryByCategory = []
            for row in category_result:
                inventoryByCategory.append({
                    'category': row[0],
                    'value': float(row[1] or 0),
                    'count': row[2]
                })
            
            # 3. Top Moving Parts
            top_parts_query = """
            SELECT TOP 5
                p.PartNo,
                p.Description,
                p.OnHand as quantity,
                COUNT(wp.WONo) as monthlyUsage
            FROM ben002.NationalParts p
            LEFT JOIN ben002.WOParts wp ON p.PartNo = wp.PartNo
                AND wp.Date >= DATEADD(month, -1, GETDATE())
            WHERE p.OnHand > 0
            GROUP BY p.PartNo, p.Description, p.OnHand
            ORDER BY COUNT(wp.WONo) DESC
            """
            
            top_parts_result = db.execute_query(top_parts_query)
            
            topMovingParts = []
            for row in top_parts_result:
                topMovingParts.append({
                    'partNumber': row[0],
                    'description': row[1],
                    'quantity': row[2],
                    'monthlyUsage': row[3]
                })
            
            # 4. Low Stock Alerts
            low_stock_query = """
            SELECT TOP 5
                PartNo,
                Description,
                OnHand as currentStock,
                MinimumStock as reorderPoint,
                CASE 
                    WHEN OnHand <= MinimumStock * 0.5 THEN 'Critical'
                    ELSE 'Low'
                END as status
            FROM ben002.NationalParts
            WHERE OnHand > 0 AND OnHand <= MinimumStock
            ORDER BY (CAST(OnHand as FLOAT) / NULLIF(MinimumStock, 0)) ASC
            """
            
            low_stock_result = db.execute_query(low_stock_query)
            
            lowStockAlerts = []
            for row in low_stock_result:
                lowStockAlerts.append({
                    'partNumber': row[0],
                    'description': row[1],
                    'currentStock': row[2],
                    'reorderPoint': row[3],
                    'status': row[4]
                })
            
            # 5. Monthly Trend
            trend_query = """
            SELECT 
                DATENAME(month, InvoiceDate) as month,
                SUM(GrandTotal) as sales,
                COUNT(*) as orders
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            GROUP BY DATENAME(month, InvoiceDate), MONTH(InvoiceDate), YEAR(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            trend_result = db.execute_query(trend_query)
            
            monthlyTrend = []
            for row in trend_result:
                monthlyTrend.append({
                    'month': row[0][:3],
                    'sales': float(row[1] or 0),
                    'orders': row[2]
                })
            
            # Recent orders data not available yet
            recentOrders = []
            
            # 6. Monthly Parts Revenue - Last 12 months
            parts_revenue_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as parts_revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            parts_revenue_result = db.execute_query(parts_revenue_query)
            
            monthlyPartsRevenue = []
            for row in parts_revenue_result:
                month_date = datetime(row['year'], row['month'], 1)
                monthlyPartsRevenue.append({
                    'month': month_date.strftime("%b"),
                    'amount': float(row['parts_revenue'] or 0)
                })
            
            # Pad with zeros for missing months
            if len(monthlyPartsRevenue) < 12:
                all_months = []
                current_date = datetime.now()
                for i in range(11, -1, -1):
                    month_date = current_date - timedelta(days=i*30)
                    all_months.append(month_date.strftime("%b"))
                
                existing_months = [item['month'] for item in monthlyPartsRevenue]
                for month in all_months:
                    if month not in existing_months:
                        monthlyPartsRevenue.append({'month': month, 'amount': 0})
            
            return jsonify({
                'summary': summary,
                'inventoryByCategory': inventoryByCategory,
                'topMovingParts': topMovingParts,
                'lowStockAlerts': lowStockAlerts,
                'monthlyTrend': monthlyTrend,
                'recentOrders': recentOrders,
                'monthlyPartsRevenue': monthlyPartsRevenue
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'parts_report_error'
            }), 500


    @reports_bp.route('/departments/rental', methods=['GET'])
    @jwt_required()
    def get_rental_department_report():
        """Get Rental Department report data"""
        try:
            db = get_db()
            
            # 1. Summary metrics
            summary_query = """
            SELECT 
                -- Total Fleet Size
                (SELECT COUNT(*) FROM ben002.Equipment 
                 WHERE WebRentalFlag = 1) as totalFleetSize,
                
                -- Units on Rent
                (SELECT COUNT(*) FROM ben002.Equipment 
                 WHERE RentalStatus = 'Rented') as unitsOnRent,
                 
                -- Monthly Revenue
                (SELECT SUM(GrandTotal) 
                 FROM ben002.InvoiceReg 
                 WHERE MONTH(InvoiceDate) = MONTH(GETDATE())
                 AND YEAR(InvoiceDate) = YEAR(GETDATE())) as monthlyRevenue
            """
            
            summary_result = db.execute_query(summary_query)
            
            total_fleet = summary_result[0][0] or 1  # Avoid division by zero
            units_on_rent = summary_result[0][1] or 0
            
            summary = {
                'totalFleetSize': total_fleet,
                'unitsOnRent': units_on_rent,
                'utilizationRate': round((units_on_rent / total_fleet) * 100, 1) if total_fleet > 0 else 0,
                'monthlyRevenue': float(summary_result[0][2] or 0),
                'overdueReturns': 0,  # Would need return date tracking
                'maintenanceDue': 0   # Would need maintenance schedule
            }
            
            # 2. Fleet by Category
            fleet_query = """
            SELECT 
                CASE 
                    WHEN Model LIKE '%EXCAVATOR%' THEN 'Excavators'
                    WHEN Model LIKE '%LOADER%' THEN 'Loaders'
                    WHEN Model LIKE '%DOZER%' THEN 'Dozers'
                    WHEN Model LIKE '%COMPACTOR%' THEN 'Compactors'
                    ELSE 'Other'
                END as category,
                COUNT(*) as total,
                SUM(CASE WHEN RentalStatus = 'Rented' THEN 1 ELSE 0 END) as onRent
            FROM ben002.Equipment
            WHERE WebRentalFlag = 1
            GROUP BY 
                CASE 
                    WHEN Model LIKE '%EXCAVATOR%' THEN 'Excavators'
                    WHEN Model LIKE '%LOADER%' THEN 'Loaders'
                    WHEN Model LIKE '%DOZER%' THEN 'Dozers'
                    WHEN Model LIKE '%COMPACTOR%' THEN 'Compactors'
                    ELSE 'Other'
                END
            """
            
            fleet_result = db.execute_query(fleet_query)
            
            fleetByCategory = []
            for row in fleet_result:
                total = row[1]
                on_rent = row[2]
                fleetByCategory.append({
                    'category': row[0],
                    'total': total,
                    'onRent': on_rent,
                    'available': total - on_rent
                })
            
            # 3. Active Rentals
            rentals_query = """
            SELECT TOP 5
                w.WONo,
                w.BillTo as Customer,
                e.Make + ' ' + e.Model as equipment,
                w.OpenDate as startDate,
                NULL as endDate,  -- Would need return tracking
                0 as dailyRate,   -- Would need rate table
                'Active' as status
            FROM ben002.WO w
            JOIN ben002.Equipment e ON w.Equipment = e.StockNo
            WHERE w.Type = 'R' AND w.ClosedDate IS NULL
            ORDER BY w.OpenDate DESC
            """
            
            rentals_result = db.execute_query(rentals_query)
            
            activeRentals = []
            for row in rentals_result:
                activeRentals.append({
                    'contractNumber': f'RC-{row[0]}',
                    'customer': row[1] or 'Unknown',
                    'equipment': row[2] or 'N/A',
                    'startDate': row[3].strftime('%Y-%m-%d') if row[3] else '',
                    'endDate': row[4].strftime('%Y-%m-%d') if row[4] else '',
                    'dailyRate': row[5],
                    'status': row[6]
                })
            
            # 4. Monthly Trend
            trend_query = """
            SELECT 
                DATENAME(month, InvoiceDate) as month,
                SUM(GrandTotal) as revenue,
                COUNT(*) as rentals
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            GROUP BY DATENAME(month, InvoiceDate), MONTH(InvoiceDate), YEAR(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            trend_result = db.execute_query(trend_query)
            
            monthlyTrend = []
            for row in trend_result:
                monthlyTrend.append({
                    'month': row[0][:3],
                    'revenue': float(row[1] or 0),
                    'utilization': 0
                })
            
            # Rental duration data not available yet
            rentalsByDuration = []
            
            topCustomers = []
            
            return jsonify({
                'summary': summary,
                'fleetByCategory': fleetByCategory,
                'activeRentals': activeRentals,
                'monthlyTrend': monthlyTrend,
                'rentalsByDuration': rentalsByDuration,
                'topCustomers': topCustomers
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_report_error'
            }), 500


    @reports_bp.route('/departments/rental/sale-codes', methods=['GET'])
    @jwt_required()
    def get_sale_codes():
        """Get all unique SaleCodes to identify rental patterns"""
        try:
            db = get_db()
            
            # Get unique sale codes with counts
            codes_query = """
            SELECT 
                w.SaleCode,
                w.SaleDept,
                COUNT(*) as Count,
                MIN(c.CustomerName) as SampleCustomer
            FROM ben002.WO w
            LEFT JOIN ben002.Customer c ON w.BillTo = c.Customer
            WHERE w.Type = 'S'
            AND w.OpenDate >= DATEADD(month, -3, GETDATE())
            GROUP BY w.SaleCode, w.SaleDept
            ORDER BY Count DESC
            """
            
            codes = db.execute_query(codes_query)
            
            # Also get a sample of work orders that might be rental
            rental_sample_query = """
            SELECT TOP 10
                w.WONo,
                w.SaleCode,
                w.SaleDept,
                w.BillTo,
                c.CustomerName,
                w.Comments
            FROM ben002.WO w
            LEFT JOIN ben002.Customer c ON w.BillTo = c.Customer
            WHERE w.Type = 'S'
            AND (
                c.CustomerName LIKE '%Rental%' OR
                w.Comments LIKE '%rental%' OR
                w.Comments LIKE '%RENTAL%'
            )
            ORDER BY w.OpenDate DESC
            """
            
            rental_samples = db.execute_query(rental_sample_query)
            
            return jsonify({
                'sale_codes': codes,
                'rental_samples': rental_samples
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'sale_codes_error'
            }), 500

    @reports_bp.route('/departments/rental/wo-schema', methods=['GET'])
    @jwt_required()
    def get_wo_schema():
        """Diagnostic endpoint to understand WO table structure"""
        try:
            db = get_db()
            
            # Get column information for WO table
            schema_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'WO'
            ORDER BY ORDINAL_POSITION
            """
            
            columns = db.execute_query(schema_query)
            
            # Get a sample work order to see actual data
            sample_query = """
            SELECT TOP 1 *
            FROM ben002.WO
            WHERE Type = 'S'
            ORDER BY OpenDate DESC
            """
            
            sample = db.execute_query(sample_query)
            
            # Check for potential customer/billto fields
            customer_fields = []
            if columns:
                for col in columns:
                    col_name = col.get('COLUMN_NAME', '').lower()
                    if any(term in col_name for term in ['customer', 'cust', 'bill', 'client', 'account']):
                        customer_fields.append(col.get('COLUMN_NAME'))
            
            # Check WOLabor, WOParts, WOMisc table structures
            labor_cols_query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'WOLabor'
            ORDER BY ORDINAL_POSITION
            """
            
            parts_cols_query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'WOParts'
            ORDER BY ORDINAL_POSITION
            """
            
            labor_cols = db.execute_query(labor_cols_query)
            parts_cols = db.execute_query(parts_cols_query)
            
            return jsonify({
                'wo_columns': columns,
                'sample_work_order': sample[0] if sample else None,
                'potential_customer_fields': customer_fields,
                'labor_columns': labor_cols,
                'parts_columns': parts_cols
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'schema_error'
            }), 500


    @reports_bp.route('/departments/rental/service-report', methods=['GET'])
    @jwt_required()
    def get_rental_service_report():
        """Get Service Work Orders billed to Rental Department"""
        try:
            db = get_db()
            
            # Optimized query for rental work orders based on BillTo and Department
            optimized_query = """
            WITH RentalWOs AS (
                SELECT TOP 100
                    w.WONo,
                    w.BillTo,
                    w.BillTo as CustomerName,
                    w.ShipTo as ShipToCustomer,
                    w.UnitNo as Equipment,
                    w.SerialNo as SerialNumber,
                    w.Make,
                    w.Model,
                    w.OpenDate,
                    w.CompletedDate,
                    w.ClosedDate,
                    w.InvoiceDate,
                    CAST(NULL as varchar(50)) as InvoiceNo,
                    CASE 
                        WHEN w.ClosedDate IS NOT NULL THEN 'Closed'
                        WHEN w.InvoiceDate IS NOT NULL THEN 'Invoiced'
                        WHEN w.CompletedDate IS NOT NULL THEN 'Completed'
                        ELSE 'Open'
                    END as Status,
                    w.SaleCode,
                    w.SaleDept
                FROM ben002.WO w
                WHERE w.BillTo IN ('900006', '900066')  -- Specific BillTo customers
                AND w.SaleDept IN ('47', '45', '40')  -- PM (47), Shop Service (45), Field Service (40)
                AND (
                    -- Include Open work orders (not closed, not invoiced, not completed)
                    (w.ClosedDate IS NULL AND w.InvoiceDate IS NULL AND w.CompletedDate IS NULL)
                    OR 
                    -- Include Completed work orders (but not yet closed or invoiced)
                    (w.CompletedDate IS NOT NULL AND w.ClosedDate IS NULL AND w.InvoiceDate IS NULL)
                )
                AND w.OpenDate >= '2025-06-01'  -- Only work orders opened on or after June 1, 2025
                AND (
                    (w.WONo LIKE '140%' AND w.Type = 'S') OR  -- RENTR (Rental Repairs)
                    (w.WONo LIKE '145%' AND w.Type = 'SH') OR  -- RENTRS (Rental Shop) - Shop type
                    (w.WONo LIKE '147%' AND w.Type = 'PM')    -- RENTPM (Rental PM)
                )
                AND w.SaleCode IN ('RENTR', 'RENTRS', 'RENTPM')  -- Include all rental-related SaleCodes
                AND w.WONo NOT IN ('140001773', '140001780')  -- Exclude corrupt work orders
                ORDER BY w.OpenDate DESC
            ),
            LaborCosts AS (
                SELECT 
                    WONo,
                    SUM(Cost) as LaborCost
                FROM ben002.WOLabor
                WHERE WONo IN (SELECT WONo FROM RentalWOs)
                GROUP BY WONo
            ),
            PartsCosts AS (
                SELECT 
                    WONo,
                    SUM(Cost) as PartsCost
                FROM ben002.WOParts
                WHERE WONo IN (SELECT WONo FROM RentalWOs)
                GROUP BY WONo
            ),
            MiscCosts AS (
                SELECT 
                    WONo,
                    SUM(Cost) as MiscCost
                FROM ben002.WOMisc
                WHERE WONo IN (SELECT WONo FROM RentalWOs)
                GROUP BY WONo
            )
            SELECT 
                r.*,
                COALESCE(l.LaborCost, 0) as LaborCost,
                COALESCE(p.PartsCost, 0) as PartsCost,
                COALESCE(m.MiscCost, 0) as MiscCost,
                COALESCE(l.LaborCost, 0) + COALESCE(p.PartsCost, 0) + COALESCE(m.MiscCost, 0) as TotalCost
            FROM RentalWOs r
            LEFT JOIN LaborCosts l ON r.WONo = l.WONo
            LEFT JOIN PartsCosts p ON r.WONo = p.WONo
            LEFT JOIN MiscCosts m ON r.WONo = m.WONo
            ORDER BY TotalCost DESC, r.OpenDate DESC
            """
            
            results = db.execute_query(optimized_query)
            
            # Process the results
            work_orders = []
            total_cost = 0
            
            for wo in results:
                labor_cost = float(wo.get('LaborCost', 0) or 0)
                parts_cost = float(wo.get('PartsCost', 0) or 0)
                misc_cost = float(wo.get('MiscCost', 0) or 0)
                total_wo_cost = float(wo.get('TotalCost', 0) or 0)
                
                total_cost += total_wo_cost
                
                work_orders.append({
                    'woNumber': wo.get('WONo'),
                    'billTo': wo.get('BillTo') or '',
                    'customer': wo.get('CustomerName') or wo.get('BillTo') or 'Unknown',
                    'shipToCustomer': wo.get('ShipToCustomer') or '',
                    'serialNumber': wo.get('SerialNumber') or '',
                    'make': wo.get('Make') or '',
                    'model': wo.get('Model') or '',
                    'openDate': wo.get('OpenDate').strftime('%Y-%m-%d') if wo.get('OpenDate') else None,
                    'status': wo.get('Status'),
                    'laborCost': labor_cost,
                    'partsCost': parts_cost,
                    'miscCost': misc_cost,
                    'totalCost': total_wo_cost
                })
            
            
            # Calculate totals
            total_cost = sum(wo['totalCost'] for wo in work_orders)
            
            summary = {
                'totalWorkOrders': len(work_orders),
                'totalLaborCost': sum(wo['laborCost'] for wo in work_orders),
                'totalPartsCost': sum(wo['partsCost'] for wo in work_orders),
                'totalMiscCost': sum(wo['miscCost'] for wo in work_orders),
                'totalCost': total_cost,
                'averageCostPerWO': total_cost / len(work_orders) if work_orders else 0
            }
            
            # Monthly trend query for rental work orders
            monthly_trend_query = """
            WITH MonthlyWOs AS (
                SELECT 
                    w.WONo,
                    YEAR(w.OpenDate) as Year,
                    MONTH(w.OpenDate) as Month,
                    DATENAME(month, w.OpenDate) as MonthName
                FROM ben002.WO w
                WHERE w.BillTo IN ('900006', '900066')
                AND w.SaleDept IN ('47', '45', '40')
                AND w.ClosedDate IS NULL  -- Only open work orders
                AND w.InvoiceDate IS NULL
                AND w.CompletedDate IS NULL  -- Not completed
                AND w.OpenDate >= '2025-06-01'  -- Only work orders opened on or after June 1, 2025
                AND (
                    (w.WONo LIKE '140%' AND w.Type = 'S') OR  -- RENTR (Rental Repairs) - Service only
                    (w.WONo LIKE '145%' AND w.Type = 'S') OR  -- RENTS (Rental Shop) - Service only
                    (w.WONo LIKE '147%' AND w.Type = 'PM')    -- RENTPM (Rental PM) - PM only
                )
            )
            SELECT 
                mw.Year,
                mw.Month,
                mw.MonthName,
                COUNT(DISTINCT mw.WONo) as WorkOrderCount,
                COALESCE(SUM(l.Cost), 0) as LaborCost,
                COALESCE(SUM(p.Cost), 0) as PartsCost,
                COALESCE(SUM(m.Cost), 0) as MiscCost,
                COALESCE(SUM(l.Cost) + SUM(p.Cost) + SUM(m.Cost), 0) as TotalCost
            FROM MonthlyWOs mw
            LEFT JOIN ben002.WOLabor l ON mw.WONo = l.WONo
            LEFT JOIN ben002.WOParts p ON mw.WONo = p.WONo
            LEFT JOIN ben002.WOMisc m ON mw.WONo = m.WONo
            GROUP BY mw.Year, mw.Month, mw.MonthName
            ORDER BY mw.Year DESC, mw.Month DESC
            """
            
            try:
                monthly_trend = db.execute_query(monthly_trend_query)
                trend_data = []
                for row in monthly_trend:
                    trend_data.append({
                        'year': row.get('Year'),
                        'month': row.get('Month'),
                        'monthName': row.get('MonthName'),
                        'workOrderCount': row.get('WorkOrderCount'),
                        'laborCost': float(row.get('LaborCost', 0) or 0),
                        'partsCost': float(row.get('PartsCost', 0) or 0),
                        'miscCost': float(row.get('MiscCost', 0) or 0),
                        'totalCost': float(row.get('TotalCost', 0) or 0)
                    })
            except Exception as e:
                # Fallback to empty trend data
                print(f"Monthly trend error: {e}")
                trend_data = []
            
            return jsonify({
                'summary': summary,
                'workOrders': work_orders,
                'monthlyTrend': trend_data
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_service_report_error'
            }), 500


    @reports_bp.route('/departments/accounting-old', methods=['GET'])
    @jwt_required()
    def get_accounting_department_report_old():
        """Get Accounting Department report data"""
        try:
            db = get_db()
            
            # Get current year start
            today = datetime.now()
            year_start = datetime(today.year, 1, 1)
            month_start = today.replace(day=1)
            
            # 1. Summary metrics
            summary_query = f"""
            SELECT 
                -- Total Revenue YTD
                (SELECT SUM(GrandTotal) FROM ben002.InvoiceReg 
                 WHERE InvoiceDate >= '{year_start.strftime('%Y-%m-%d')}' 
                 AND InvoiceDate < '{today.strftime('%Y-%m-%d')}') as totalRevenue,
                 
                -- Total Expenses (expense data not available)
                0 as totalExpenses,
                
                -- Accounts Receivable
                (SELECT SUM(Balance) FROM ben002.Customer WHERE Balance > 0) as accountsReceivable,
                
                -- Overdue Invoices
                (SELECT COUNT(*) FROM ben002.InvoiceReg 
                 WHERE InvoiceStatus = 'Open' 
                 AND DATEDIFF(day, InvoiceDate, GETDATE()) > 30) as overdueInvoices,
                 
                -- Monthly Cash Flow
                (SELECT SUM(GrandTotal) FROM ben002.InvoiceReg 
                 WHERE InvoiceDate >= '{month_start.strftime('%Y-%m-%d')}'
                 AND InvoiceDate < '{today.strftime('%Y-%m-%d')}') as cashFlow
            """
            
            summary_result = db.execute_query(summary_query)
            
            total_revenue = float(summary_result[0][0] or 0)
            total_expenses = 0  # Expense data not available
            net_profit = total_revenue - total_expenses
            
            summary = {
                'totalRevenue': total_revenue,
                'totalExpenses': total_expenses,
                'netProfit': net_profit,
                'profitMargin': round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
                'accountsReceivable': float(summary_result[0][2] or 0),
                'accountsPayable': 0,  # Would need payables table
                'cashFlow': float(summary_result[0][4] or 0),
                'overdueInvoices': summary_result[0][3] or 0
            }
            
            # 2. Revenue by Department
            dept_query = f"""
            SELECT 
                Department,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{year_start.strftime('%Y-%m-%d')}'
            AND Department IS NOT NULL
            GROUP BY Department
            ORDER BY revenue DESC
            """
            
            dept_result = db.execute_query(dept_query)
            
            revenueByDepartment = []
            total_dept_revenue = sum(float(row[1] or 0) for row in dept_result)
            
            for row in dept_result:
                revenue = float(row[1] or 0)
                revenueByDepartment.append({
                    'department': row[0],
                    'revenue': revenue,
                    'percentage': round((revenue / total_dept_revenue * 100) if total_dept_revenue > 0 else 0, 1)
                })
            
            # 3. Monthly Financial Trend
            financial_trend_query = """
            SELECT 
                DATENAME(month, InvoiceDate) as month,
                SUM(GrandTotal) as revenue,
                COUNT(*) as invoiceCount
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            GROUP BY DATENAME(month, InvoiceDate), MONTH(InvoiceDate), YEAR(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            financial_trend_result = db.execute_query(financial_trend_query)
            
            monthlyFinancials = []
            for row in financial_trend_result:
                revenue = float(row[1] or 0)
                expenses = 0  # Expense data not available
                monthlyFinancials.append({
                    'month': row[0][:3],
                    'revenue': revenue,
                    'expenses': expenses,
                    'profit': revenue - expenses
                })
            
            # 4. Outstanding Invoices
            invoices_query = """
            SELECT TOP 5
                InvoiceNo,
                CustomerName,
                GrandTotal,
                DATEDIFF(day, InvoiceDate, GETDATE()) as daysOverdue,
                CASE 
                    WHEN DATEDIFF(day, InvoiceDate, GETDATE()) > 60 THEN 'Overdue'
                    WHEN DATEDIFF(day, InvoiceDate, GETDATE()) > 30 THEN 'Late'
                    ELSE 'Current'
                END as status
            FROM ben002.InvoiceReg
            WHERE InvoiceStatus = 'Open'
            ORDER BY InvoiceDate ASC
            """
            
            invoices_result = db.execute_query(invoices_query)
            
            outstandingInvoices = []
            for row in invoices_result:
                outstandingInvoices.append({
                    'invoiceNumber': f'INV-{row[0]}',
                    'customer': row[1] or 'Unknown',
                    'amount': float(row[2] or 0),
                    'daysOverdue': max(0, row[3]),
                    'status': row[4]
                })
            
            # Expense categories data not available yet
            expenseCategories = []
            
            cashFlowTrend = []
            pendingPayables = []
            
            return jsonify({
                'summary': summary,
                'revenueByDepartment': revenueByDepartment,
                'expenseCategories': expenseCategories,
                'monthlyFinancials': monthlyFinancials,
                'cashFlowTrend': cashFlowTrend,
                'outstandingInvoices': outstandingInvoices,
                'pendingPayables': pendingPayables
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'accounting_report_error'
            }), 500