# Department-specific report endpoints
from flask import jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
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
                (SELECT SUM(GrandTotal) FROM ben002.InvoiceReg 
                 WHERE Department = 'Service' 
                 AND InvoiceDate >= '{month_start.strftime('%Y-%m-%d')}' 
                 AND InvoiceDate < '{today.strftime('%Y-%m-%d')}') as revenue,
                 
                -- Customers Served
                (SELECT COUNT(DISTINCT Customer) FROM ben002.WO 
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
                    'technicianEfficiency': 87,  # Placeholder - would need technician table
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
                w.Customer,
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
            WHERE Department = 'Service'
            AND InvoiceDate >= DATEADD(month, -6, GETDATE())
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
            
            # Placeholder for technician performance (would need technician data)
            technicianPerformance = [
                {'name': 'Technician 1', 'completed': 45, 'efficiency': 92},
                {'name': 'Technician 2', 'completed': 38, 'efficiency': 88},
                {'name': 'Technician 3', 'completed': 41, 'efficiency': 90}
            ]
            
            return jsonify({
                'summary': summary,
                'workOrdersByStatus': workOrdersByStatus,
                'recentWorkOrders': recentWorkOrders,
                'monthlyTrend': monthlyTrend,
                'technicianPerformance': technicianPerformance
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
                 WHERE i.Department = 'Parts'
                 AND MONTH(i.InvoiceDate) = MONTH(GETDATE())
                 AND YEAR(i.InvoiceDate) = YEAR(GETDATE())) as monthlySales
            """
            
            summary_result = db.execute_query(summary_query)
            
            summary = {
                'totalInventoryValue': float(summary_result[0][0] or 0),
                'totalParts': summary_result[0][1] or 0,
                'lowStockItems': summary_result[0][2] or 0,
                'pendingOrders': 0,  # Would need purchase order table
                'monthlySales': float(summary_result[0][3] or 0),
                'turnoverRate': 4.2  # Placeholder
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
            WHERE Department = 'Parts'
            AND InvoiceDate >= DATEADD(month, -6, GETDATE())
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
            
            # Placeholder for recent orders
            recentOrders = []
            
            return jsonify({
                'summary': summary,
                'inventoryByCategory': inventoryByCategory,
                'topMovingParts': topMovingParts,
                'lowStockAlerts': lowStockAlerts,
                'monthlyTrend': monthlyTrend,
                'recentOrders': recentOrders
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
                 WHERE Department = 'Rental'
                 AND MONTH(InvoiceDate) = MONTH(GETDATE())
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
                w.Customer,
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
            WHERE Department = 'Rental'
            AND InvoiceDate >= DATEADD(month, -6, GETDATE())
            GROUP BY DATENAME(month, InvoiceDate), MONTH(InvoiceDate), YEAR(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            trend_result = db.execute_query(trend_query)
            
            monthlyTrend = []
            for row in trend_result:
                monthlyTrend.append({
                    'month': row[0][:3],
                    'revenue': float(row[1] or 0),
                    'utilization': 65 + (row[2] % 10)  # Placeholder calculation
                })
            
            # Placeholder data
            rentalsByDuration = [
                {'duration': 'Daily', 'count': 15, 'revenue': 45000},
                {'duration': 'Weekly', 'count': 35, 'revenue': 125000},
                {'duration': 'Monthly', 'count': 38, 'revenue': 215750}
            ]
            
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
            LEFT JOIN ben002.Customer c ON w.BillTo = c.CustomerNo
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
            LEFT JOIN ben002.Customer c ON w.BillTo = c.CustomerNo
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
            
            # Get service work orders - now we know the correct columns
            service_wo_query = """
            SELECT TOP 100
                w.WONo,
                w.BillTo,
                c.CustomerName,
                w.UnitNo as Equipment,
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
            LEFT JOIN ben002.Customer c ON w.BillTo = c.CustomerNo
            WHERE w.Type = 'S'  -- Service work orders
            AND (
                -- Rental department service codes
                w.SaleCode = 'RENTR' OR     -- Rental Repairs (SaleDept 40)
                w.SaleCode = 'RENTRS'       -- Rental Repairs - Shop (SaleDept 45)
            )
            ORDER BY w.OpenDate DESC
            """
            
            service_wos = db.execute_query(service_wo_query)
            
            # Process the results
            work_orders = []
            total_cost = 0
            total_revenue = 0
            
            for wo in service_wos:
                wo_no = wo.get('WONo')
                
                # Get costs in a single query for efficiency
                cost_query = f"""
                SELECT 
                    COALESCE(SUM(l.Cost), 0) as LaborCost,
                    COALESCE(SUM(l.Sell), 0) as LaborSell,
                    COALESCE((SELECT SUM(Cost * Quantity) FROM ben002.WOParts WHERE WONo = {wo_no}), 0) as PartsCost,
                    COALESCE((SELECT SUM(Sell * Quantity) FROM ben002.WOParts WHERE WONo = {wo_no}), 0) as PartsSell,
                    COALESCE((SELECT SUM(Cost) FROM ben002.WOMisc WHERE WONo = {wo_no}), 0) as MiscCost,
                    COALESCE((SELECT SUM(Sell) FROM ben002.WOMisc WHERE WONo = {wo_no}), 0) as MiscSell
                FROM ben002.WOLabor l
                WHERE l.WONo = {wo_no}
                """
                
                try:
                    cost_result = db.execute_query(cost_query)
                    if cost_result and len(cost_result) > 0:
                        costs = cost_result[0]
                        labor_cost = float(costs.get('LaborCost', 0) or 0)
                        labor_sell = float(costs.get('LaborSell', 0) or 0)
                        parts_cost = float(costs.get('PartsCost', 0) or 0)
                        parts_sell = float(costs.get('PartsSell', 0) or 0)
                        misc_cost = float(costs.get('MiscCost', 0) or 0)
                        misc_sell = float(costs.get('MiscSell', 0) or 0)
                    else:
                        labor_cost = labor_sell = parts_cost = parts_sell = misc_cost = misc_sell = 0
                except:
                    labor_cost = labor_sell = parts_cost = parts_sell = misc_cost = misc_sell = 0
                
                total_wo_cost = labor_cost + parts_cost + misc_cost
                total_wo_revenue = labor_sell + parts_sell + misc_sell
                
                total_cost += total_wo_cost
                total_revenue += total_wo_revenue
                
                work_orders.append({
                    'woNumber': wo_no,
                    'customer': wo.get('CustomerName') or wo.get('BillTo') or 'Unknown',
                    'equipment': wo.get('Equipment') or '',
                    'make': wo.get('Make') or '',
                    'model': wo.get('Model') or '',
                    'openDate': wo.get('OpenDate').strftime('%Y-%m-%d') if wo.get('OpenDate') else None,
                    'completedDate': wo.get('CompletedDate').strftime('%Y-%m-%d') if wo.get('CompletedDate') else None,
                    'closedDate': wo.get('ClosedDate').strftime('%Y-%m-%d') if wo.get('ClosedDate') else None,
                    'invoiceDate': wo.get('InvoiceDate').strftime('%Y-%m-%d') if wo.get('InvoiceDate') else None,
                    'invoiceNo': wo.get('InvoiceNo'),
                    'status': wo.get('Status'),
                    'laborCost': labor_cost,
                    'partsCost': parts_cost,
                    'miscCost': misc_cost,
                    'totalCost': total_wo_cost,
                    'laborRevenue': labor_sell,
                    'partsRevenue': parts_sell,
                    'miscRevenue': misc_sell,
                    'totalRevenue': total_wo_revenue,
                    'profit': total_wo_revenue - total_wo_cost
                })
            
            # If no data found, return mock data to show the format
            if not work_orders:
                work_orders = [
                {
                    'woNumber': 'WO-2024-001',
                    'customer': 'Rental Department',
                    'equipment': 'CAT 320D',
                    'make': 'Caterpillar',
                    'model': '320D',
                    'openDate': '2024-06-01',
                    'completedDate': '2024-06-05',
                    'closedDate': '2024-06-05',
                    'invoiceDate': '2024-06-06',
                    'invoiceNo': 'INV-2024-001',
                    'status': 'Closed',
                    'laborCost': 1200.00,
                    'partsCost': 800.00,
                    'miscCost': 150.00,
                    'totalCost': 2150.00,
                    'laborRevenue': 1500.00,
                    'partsRevenue': 1000.00,
                    'miscRevenue': 200.00,
                    'totalRevenue': 2700.00,
                    'profit': 550.00
                },
                {
                    'woNumber': 'WO-2024-002',
                    'customer': 'Rental Department',
                    'equipment': 'Komatsu PC200',
                    'make': 'Komatsu',
                    'model': 'PC200',
                    'openDate': '2024-06-10',
                    'completedDate': '2024-06-12',
                    'closedDate': None,
                    'invoiceDate': None,
                    'invoiceNo': None,
                    'status': 'Completed',
                    'laborCost': 800.00,
                    'partsCost': 1200.00,
                    'miscCost': 100.00,
                    'totalCost': 2100.00,
                    'laborRevenue': 1000.00,
                    'partsRevenue': 1500.00,
                    'miscRevenue': 125.00,
                    'totalRevenue': 2625.00,
                    'profit': 525.00
                },
                {
                    'woNumber': 'WO-2024-003',
                    'customer': 'Rental Department',
                    'equipment': 'John Deere 544K',
                    'make': 'John Deere',
                    'model': '544K',
                    'openDate': '2024-06-15',
                    'completedDate': None,
                    'closedDate': None,
                    'invoiceDate': None,
                    'invoiceNo': None,
                    'status': 'Open',
                    'laborCost': 500.00,
                    'partsCost': 300.00,
                    'miscCost': 50.00,
                    'totalCost': 850.00,
                    'laborRevenue': 625.00,
                    'partsRevenue': 375.00,
                    'miscRevenue': 65.00,
                    'totalRevenue': 1065.00,
                    'profit': 215.00
                }
            ]
            
            # Calculate totals
            total_cost = sum(wo['totalCost'] for wo in work_orders)
            total_revenue = sum(wo['totalRevenue'] for wo in work_orders)
            
            summary = {
                'totalWorkOrders': len(work_orders),
                'openWorkOrders': len([wo for wo in work_orders if wo['status'] == 'Open']),
                'completedWorkOrders': len([wo for wo in work_orders if wo['status'] in ['Completed', 'Closed']]),
                'totalCost': total_cost,
                'totalRevenue': total_revenue,
                'totalProfit': total_revenue - total_cost,
                'averageCostPerWO': total_cost / len(work_orders) if work_orders else 0,
                'averageRevenuePerWO': total_revenue / len(work_orders) if work_orders else 0
            }
            
            # Get monthly trend for rental service work orders
            monthly_trend_query = """
            SELECT 
                YEAR(w.OpenDate) as Year,
                MONTH(w.OpenDate) as Month,
                DATENAME(month, w.OpenDate) as MonthName,
                COUNT(*) as WorkOrderCount
            FROM ben002.WO w
            LEFT JOIN ben002.Customer c ON w.BillTo = c.CustomerNo
            WHERE w.Type = 'S'
            AND (
                w.SaleCode = 'RENTR' OR     -- Rental Repairs
                w.SaleCode = 'RENTRS'       -- Rental Repairs - Shop
            )
            AND w.OpenDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(w.OpenDate), MONTH(w.OpenDate), DATENAME(month, w.OpenDate)
            ORDER BY Year DESC, Month DESC
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
                        'totalCost': 0,  # Would need to calculate separately
                        'totalRevenue': 0,  # Would need to calculate separately
                        'profit': 0  # Would need to calculate separately
                    })
            except:
                # Fallback to empty trend data
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
                 
                -- Total Expenses (placeholder - would need expense table)
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
            total_expenses = total_revenue * 0.75  # Placeholder calculation
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
                expenses = revenue * 0.75  # Placeholder
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
            
            # Placeholder data
            expenseCategories = [
                {'category': 'Labor', 'amount': total_expenses * 0.35, 'percentage': 35},
                {'category': 'Parts & Materials', 'amount': total_expenses * 0.25, 'percentage': 25},
                {'category': 'Equipment', 'amount': total_expenses * 0.20, 'percentage': 20},
                {'category': 'Overhead', 'amount': total_expenses * 0.15, 'percentage': 15},
                {'category': 'Other', 'amount': total_expenses * 0.05, 'percentage': 5}
            ]
            
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