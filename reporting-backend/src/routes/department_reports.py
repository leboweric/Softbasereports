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


    @reports_bp.route('/departments/rental/service-report', methods=['GET'])
    @jwt_required()
    def get_rental_service_report():
        """Get Service Work Orders billed to Rental Department"""
        try:
            db = get_db()
            
            # Get service work orders - minimal query
            service_wo_query = """
            SELECT TOP 50
                w.WONo,
                w.OpenDate,
                w.CompletedDate,
                w.ClosedDate
            FROM ben002.WO w
            WHERE w.Type = 'S'
            ORDER BY w.OpenDate DESC
            """
            
            service_wos = db.execute_query(service_wo_query)
            
            # Process the results with separate queries for costs
            work_orders = []
            total_cost = 0
            total_revenue = 0
            
            for wo in service_wos:
                wo_no = wo.get('WONo')
                
                # Get costs with separate queries
                labor_cost_query = f"SELECT COALESCE(SUM(Cost), 0) as cost FROM ben002.WOLabor WHERE WONo = '{wo_no}'"
                parts_cost_query = f"SELECT COALESCE(SUM(Cost), 0) as cost FROM ben002.WOParts WHERE WONo = '{wo_no}'"
                misc_cost_query = f"SELECT COALESCE(SUM(Cost), 0) as cost FROM ben002.WOMisc WHERE WONo = '{wo_no}'"
                
                labor_sell_query = f"SELECT COALESCE(SUM(Sell), 0) as sell FROM ben002.WOLabor WHERE WONo = '{wo_no}'"
                parts_sell_query = f"SELECT COALESCE(SUM(Sell), 0) as sell FROM ben002.WOParts WHERE WONo = '{wo_no}'"
                misc_sell_query = f"SELECT COALESCE(SUM(Sell), 0) as sell FROM ben002.WOMisc WHERE WONo = '{wo_no}'"
                
                try:
                    labor_cost_result = db.execute_query(labor_cost_query)
                    labor_cost = float(labor_cost_result[0]['cost'] if labor_cost_result else 0)
                except:
                    labor_cost = 0
                    
                try:
                    parts_cost_result = db.execute_query(parts_cost_query)
                    parts_cost = float(parts_cost_result[0]['cost'] if parts_cost_result else 0)
                except:
                    parts_cost = 0
                    
                try:
                    misc_cost_result = db.execute_query(misc_cost_query)
                    misc_cost = float(misc_cost_result[0]['cost'] if misc_cost_result else 0)
                except:
                    misc_cost = 0
                    
                try:
                    labor_sell_result = db.execute_query(labor_sell_query)
                    labor_sell = float(labor_sell_result[0]['sell'] if labor_sell_result else 0)
                except:
                    labor_sell = 0
                    
                try:
                    parts_sell_result = db.execute_query(parts_sell_query)
                    parts_sell = float(parts_sell_result[0]['sell'] if parts_sell_result else 0)
                except:
                    parts_sell = 0
                    
                try:
                    misc_sell_result = db.execute_query(misc_sell_query)
                    misc_sell = float(misc_sell_result[0]['sell'] if misc_sell_result else 0)
                except:
                    misc_sell = 0
                
                total_wo_cost = labor_cost + parts_cost + misc_cost
                total_wo_revenue = labor_sell + parts_sell + misc_sell
                
                total_cost += total_wo_cost
                total_revenue += total_wo_revenue
                
                status = 'Open'
                if wo.get('ClosedDate'):
                    status = 'Closed'
                elif wo.get('CompletedDate'):
                    status = 'Completed'
                
                work_orders.append({
                    'woNumber': wo_no,
                    'customer': 'Rental Department',
                    'equipment': '',
                    'make': '',
                    'model': '',
                    'openDate': wo.get('OpenDate').strftime('%Y-%m-%d') if wo.get('OpenDate') else None,
                    'completedDate': wo.get('CompletedDate').strftime('%Y-%m-%d') if wo.get('CompletedDate') else None,
                    'closedDate': wo.get('ClosedDate').strftime('%Y-%m-%d') if wo.get('ClosedDate') else None,
                    'invoiceDate': None,
                    'invoiceNo': None,
                    'status': status,
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
            
            # Get summary statistics
            summary = {
                'totalWorkOrders': len(work_orders),
                'openWorkOrders': len([wo for wo in work_orders if wo['status'] == 'Open']),
                'completedWorkOrders': len([wo for wo in work_orders if wo['status'] in ['Completed', 'Closed', 'Invoiced']]),
                'totalCost': total_cost,
                'totalRevenue': total_revenue,
                'totalProfit': total_revenue - total_cost,
                'averageCostPerWO': total_cost / len(work_orders) if work_orders else 0,
                'averageRevenuePerWO': total_revenue / len(work_orders) if work_orders else 0
            }
            
            # Get monthly trend - simplified
            monthly_trend_query = """
            SELECT 
                YEAR(w.OpenDate) as Year,
                MONTH(w.OpenDate) as Month,
                DATENAME(month, w.OpenDate) as MonthName,
                COUNT(*) as WorkOrderCount
            FROM ben002.WO w
            WHERE w.Type = 'S'
            AND w.OpenDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(w.OpenDate), MONTH(w.OpenDate), DATENAME(month, w.OpenDate)
            ORDER BY Year DESC, Month DESC
            """
            
            monthly_trend = db.execute_query(monthly_trend_query)
            
            trend_data = []
            for row in monthly_trend:
                # For now, just show work order counts
                trend_data.append({
                    'year': row.get('Year'),
                    'month': row.get('Month'),
                    'monthName': row.get('MonthName'),
                    'workOrderCount': row.get('WorkOrderCount'),
                    'totalCost': 0,  # Placeholder
                    'totalRevenue': 0,  # Placeholder
                    'profit': 0  # Placeholder
                })
            
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