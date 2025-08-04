# Department-specific report endpoints
from flask import jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from flask import request
from src.services.azure_sql_service import AzureSQLService
import json
import logging

logger = logging.getLogger(__name__)

def get_db():
    """Get database connection"""
    return AzureSQLService()


def register_department_routes(reports_bp):
    """Register department report routes with the reports blueprint"""
    
    @reports_bp.route('/departments/service/pace', methods=['GET'])
    @jwt_required()
    def get_service_pace():
        """Get service department revenue pace comparing current month to previous month"""
        try:
            db = get_db()
            
            # Get current date info
            now = datetime.now()
            current_year = now.year
            current_month = now.month
            current_day = now.day
            
            # Calculate previous month
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year
            
            # Get service revenue through same day for current and previous month
            current_query = f"""
            SELECT SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {current_year}
                AND MONTH(InvoiceDate) = {current_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND SaleCode IN ('SVE', 'SVP', 'SVM', 'SVR', 'SVW')
            """
            
            prev_query = f"""
            SELECT SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {prev_year}
                AND MONTH(InvoiceDate) = {prev_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND SaleCode IN ('SVE', 'SVP', 'SVM', 'SVR', 'SVW')
            """
            
            current_result = db.execute_query(current_query)
            prev_result = db.execute_query(prev_query)
            
            current_revenue = float(current_result[0]['total_revenue'] or 0) if current_result else 0
            previous_revenue = float(prev_result[0]['total_revenue'] or 0) if prev_result else 0
            
            # Calculate pace percentage
            pace_percentage = round(((current_revenue / previous_revenue) - 1) * 100, 1) if previous_revenue > 0 else 0
            
            return jsonify({
                'pace_percentage': pace_percentage,
                'current_revenue': current_revenue,
                'previous_revenue': previous_revenue,
                'current_month': current_month,
                'current_day': current_day
            })
            
        except Exception as e:
            logger.error(f"Error fetching service pace: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/service', methods=['GET'])
    @jwt_required()
    def get_service_department_report():
        """Get Service Department report data"""
        try:
            db = get_db()
            
            # Monthly Labor Revenue and Margins - Last 12 months
            labor_revenue_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as labor_revenue,
                SUM(COALESCE(LaborCost, 0)) as labor_cost
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            labor_revenue_result = db.execute_query(labor_revenue_query)
            
            monthlyLaborRevenue = []
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month
            
            for row in labor_revenue_result:
                month_date = datetime(row['year'], row['month'], 1)
                labor_revenue = float(row['labor_revenue'] or 0)
                labor_cost = float(row['labor_cost'] or 0)
                
                # Check if this is current month or future
                is_current_or_future = (row['year'] > current_year) or (row['year'] == current_year and row['month'] >= current_month)
                
                # Calculate gross margin percentage only for historical months
                margin_percentage = None
                if not is_current_or_future and labor_revenue > 0:
                    margin_percentage = round(((labor_revenue - labor_cost) / labor_revenue) * 100, 1)
                
                monthlyLaborRevenue.append({
                    'month': month_date.strftime("%b"),
                    'amount': labor_revenue,
                    'margin': margin_percentage
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
                        monthlyLaborRevenue.append({
                            'month': month, 
                            'amount': 0,
                            'margin': None  # Use None/null for no data instead of 0
                        })
            
            return jsonify({
                'monthlyLaborRevenue': monthlyLaborRevenue
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'service_report_error'
            }), 500


    @reports_bp.route('/departments/parts/pace', methods=['GET'])
    @jwt_required()
    def get_parts_pace():
        """Get parts department sales pace comparing current month to previous month"""
        try:
            db = get_db()
            
            # Get current date info
            now = datetime.now()
            current_year = now.year
            current_month = now.month
            current_day = now.day
            
            # Calculate previous month
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year
            
            # Get parts sales through same day for current and previous month
            current_query = f"""
            SELECT SUM(GrandTotal) as total_sales
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {current_year}
                AND MONTH(InvoiceDate) = {current_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND SaleCode IN ('PRT', 'PCR', 'PAG', 'PIN', 'PRB')
            """
            
            prev_query = f"""
            SELECT SUM(GrandTotal) as total_sales
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {prev_year}
                AND MONTH(InvoiceDate) = {prev_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND SaleCode IN ('PRT', 'PCR', 'PAG', 'PIN', 'PRB')
            """
            
            current_result = db.execute_query(current_query)
            prev_result = db.execute_query(prev_query)
            
            current_sales = float(current_result[0]['total_sales'] or 0) if current_result else 0
            previous_sales = float(prev_result[0]['total_sales'] or 0) if prev_result else 0
            
            # Calculate pace percentage
            pace_percentage = round(((current_sales / previous_sales) - 1) * 100, 1) if previous_sales > 0 else 0
            
            return jsonify({
                'pace_percentage': pace_percentage,
                'current_sales': current_sales,
                'previous_sales': previous_sales,
                'current_month': current_month,
                'current_day': current_day
            })
            
        except Exception as e:
            logger.error(f"Error fetching parts pace: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/parts', methods=['GET'])
    @jwt_required()
    def get_parts_department_report():
        """Get Parts Department report data"""
        try:
            db = get_db()
            
            # Monthly Parts Revenue and Margins - Last 12 months
            parts_revenue_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as parts_revenue,
                SUM(COALESCE(PartsCost, 0)) as parts_cost
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            parts_revenue_result = db.execute_query(parts_revenue_query)
            
            monthlyPartsRevenue = []
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month
            
            for row in parts_revenue_result:
                month_date = datetime(row['year'], row['month'], 1)
                parts_revenue = float(row['parts_revenue'] or 0)
                parts_cost = float(row['parts_cost'] or 0)
                
                # Check if this is current month or future
                is_current_or_future = (row['year'] > current_year) or (row['year'] == current_year and row['month'] >= current_month)
                
                # Calculate gross margin percentage only for historical months
                margin_percentage = None
                if not is_current_or_future and parts_revenue > 0:
                    margin_percentage = round(((parts_revenue - parts_cost) / parts_revenue) * 100, 1)
                
                monthlyPartsRevenue.append({
                    'month': month_date.strftime("%b"),
                    'amount': parts_revenue,
                    'margin': margin_percentage
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
                        monthlyPartsRevenue.append({
                            'month': month, 
                            'amount': 0,
                            'margin': None  # Use None/null for no data instead of 0
                        })
            
            return jsonify({
                'monthlyPartsRevenue': monthlyPartsRevenue
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'parts_report_error'
            }), 500


    @reports_bp.route('/departments/parts/top10', methods=['GET'])
    @jwt_required()
    def get_parts_top10():
        """Get top 10 parts by quantity sold in last 30 days"""
        try:
            db = get_db()
            
            top_parts_query = """
            SELECT TOP 10
                wp.PartNo,
                MAX(wp.Description) as Description,
                COUNT(DISTINCT wp.WONo) as OrderCount,
                SUM(wp.Qty) as TotalQuantity,
                SUM(wp.Sell) as TotalRevenue,
                AVG(wp.Sell / NULLIF(wp.Qty, 0)) as AvgUnitPrice,
                MAX(p.OnHand) as CurrentStock,
                MAX(p.Cost) as UnitCost,
                CASE 
                    WHEN MAX(p.OnHand) = 0 THEN 'Out of Stock'
                    WHEN MAX(p.OnHand) < 10 THEN 'Low Stock'
                    ELSE 'In Stock'
                END as StockStatus
            FROM ben002.WOParts wp
            LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
            INNER JOIN ben002.WO w ON wp.WONo = w.WONo
            WHERE w.OpenDate >= DATEADD(day, -30, GETDATE())
            AND wp.Qty > 0
            AND wp.Description NOT LIKE '%OIL%'
            AND wp.Description NOT LIKE '%GREASE%'
            AND wp.Description NOT LIKE '%ANTI-FREEZE%'
            AND wp.Description NOT LIKE '%ANTIFREEZE%'
            AND wp.Description NOT LIKE '%COOLANT%'
            GROUP BY wp.PartNo
            ORDER BY SUM(wp.Qty) DESC
            """
            
            results = db.execute_query(top_parts_query)
            
            top_parts = []
            for part in results:
                top_parts.append({
                    'partNo': part.get('PartNo', ''),
                    'description': part.get('Description', ''),
                    'orderCount': part.get('OrderCount', 0),
                    'totalQuantity': part.get('TotalQuantity', 0),
                    'totalRevenue': float(part.get('TotalRevenue', 0)),
                    'avgUnitPrice': float(part.get('AvgUnitPrice', 0)),
                    'currentStock': part.get('CurrentStock', 0),
                    'unitCost': float(part.get('UnitCost', 0)),
                    'stockStatus': part.get('StockStatus', '')
                })
            
            return jsonify({
                'topParts': top_parts,
                'period': 'Last 30 days'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'top_parts_error'
            }), 500


    @reports_bp.route('/departments/parts/reorder-alert', methods=['GET'])
    @jwt_required()
    def get_parts_reorder_alert():
        """Get parts reorder point alerts - identifies parts needing reorder"""
        try:
            db = get_db()
            
            # Calculate average daily usage and current stock levels
            reorder_alert_query = """
            WITH PartUsage AS (
                -- Calculate average daily usage over last 90 days
                SELECT 
                    wp.PartNo,
                    MAX(wp.Description) as Description,
                    COUNT(DISTINCT wp.WONo) as OrderCount,
                    SUM(wp.Qty) as TotalQtyUsed,
                    DATEDIFF(day, MIN(w.OpenDate), MAX(w.OpenDate)) + 1 as DaysInPeriod,
                    CAST(SUM(wp.Qty) AS FLOAT) / NULLIF(DATEDIFF(day, MIN(w.OpenDate), MAX(w.OpenDate)) + 1, 0) as AvgDailyUsage
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                WHERE w.OpenDate >= DATEADD(day, -90, GETDATE())
                    AND wp.Qty > 0
                GROUP BY wp.PartNo
                HAVING COUNT(DISTINCT wp.WONo) >= 3  -- At least 3 orders in period
            ),
            CurrentStock AS (
                -- Get current stock levels and costs
                SELECT 
                    PartNo,
                    MAX(OnHand) as OnHand,
                    MAX(OnOrder) as OnOrder,
                    MAX(Cost) as Cost,
                    MAX(List) as List,
                    -- Estimate reorder point as 14 days of average usage (2 week lead time)
                    -- This should be replaced with actual reorder point field if available
                    0 as ReorderPoint,
                    0 as MinStock
                FROM ben002.Parts
                WHERE OnHand IS NOT NULL
                GROUP BY PartNo
            )
            SELECT 
                cs.PartNo,
                pu.Description,
                cs.OnHand as CurrentStock,
                cs.OnOrder as OnOrder,
                CAST(pu.AvgDailyUsage AS DECIMAL(10,2)) as AvgDailyUsage,
                -- Calculate days of stock remaining
                CASE 
                    WHEN pu.AvgDailyUsage > 0 
                    THEN CAST(cs.OnHand / pu.AvgDailyUsage AS INT)
                    ELSE 999
                END as DaysOfStock,
                -- Estimate reorder point (14 days lead time + 7 days safety stock)
                CAST(CEILING(pu.AvgDailyUsage * 21) AS INT) as SuggestedReorderPoint,
                -- Reorder quantity (30 days worth)
                CAST(CEILING(pu.AvgDailyUsage * 30) AS INT) as SuggestedOrderQty,
                cs.Cost,
                cs.List,
                pu.OrderCount as OrdersLast90Days,
                -- Alert level
                CASE 
                    WHEN cs.OnHand <= 0 THEN 'Out of Stock'
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 7) THEN 'Critical'
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 14) THEN 'Low'
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 21) THEN 'Reorder'
                    ELSE 'OK'
                END as AlertLevel
            FROM CurrentStock cs
            INNER JOIN PartUsage pu ON cs.PartNo = pu.PartNo
            WHERE cs.OnHand < (pu.AvgDailyUsage * 21)  -- Below suggested reorder point
                OR cs.OnHand <= 0  -- Or completely out
            ORDER BY 
                CASE 
                    WHEN cs.OnHand <= 0 THEN 1
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 7) THEN 2
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 14) THEN 3
                    ELSE 4
                END,
                pu.AvgDailyUsage DESC
            """
            
            reorder_alerts = db.execute_query(reorder_alert_query)
            
            # Get summary statistics
            summary_query = """
            WITH PartUsage AS (
                SELECT 
                    wp.PartNo,
                    CAST(SUM(wp.Qty) AS FLOAT) / NULLIF(DATEDIFF(day, MIN(w.OpenDate), MAX(w.OpenDate)) + 1, 0) as AvgDailyUsage
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                WHERE w.OpenDate >= DATEADD(day, -90, GETDATE())
                    AND wp.Qty > 0
                GROUP BY wp.PartNo
                HAVING COUNT(DISTINCT wp.WONo) >= 3
            ),
            PartsAggregated AS (
                SELECT 
                    PartNo,
                    MAX(OnHand) as OnHand
                FROM ben002.Parts
                GROUP BY PartNo
            )
            SELECT 
                COUNT(CASE WHEN pa.OnHand <= 0 THEN 1 END) as OutOfStock,
                COUNT(CASE WHEN pa.OnHand > 0 AND pa.OnHand < (pu.AvgDailyUsage * 7) THEN 1 END) as Critical,
                COUNT(CASE WHEN pa.OnHand >= (pu.AvgDailyUsage * 7) AND pa.OnHand < (pu.AvgDailyUsage * 14) THEN 1 END) as Low,
                COUNT(CASE WHEN pa.OnHand >= (pu.AvgDailyUsage * 14) AND pa.OnHand < (pu.AvgDailyUsage * 21) THEN 1 END) as NeedsReorder,
                COUNT(*) as TotalTrackedParts
            FROM PartsAggregated pa
            INNER JOIN PartUsage pu ON pa.PartNo = pu.PartNo
            """
            
            summary_result = db.execute_query(summary_query)
            
            summary = {
                'outOfStock': 0,
                'critical': 0,
                'low': 0,
                'needsReorder': 0,
                'totalTracked': 0
            }
            
            if summary_result and len(summary_result) > 0:
                row = summary_result[0]
                summary = {
                    'outOfStock': row.get('OutOfStock', 0),
                    'critical': row.get('Critical', 0),
                    'low': row.get('Low', 0),
                    'needsReorder': row.get('NeedsReorder', 0),
                    'totalTracked': row.get('TotalTrackedParts', 0)
                }
            
            # Format the alerts
            formatted_alerts = []
            for alert in reorder_alerts:
                formatted_alerts.append({
                    'partNo': alert.get('PartNo', ''),
                    'description': alert.get('Description', ''),
                    'currentStock': alert.get('CurrentStock', 0),
                    'onOrder': alert.get('OnOrder', 0),
                    'avgDailyUsage': float(alert.get('AvgDailyUsage', 0)),
                    'daysOfStock': alert.get('DaysOfStock', 0),
                    'suggestedReorderPoint': alert.get('SuggestedReorderPoint', 0),
                    'suggestedOrderQty': alert.get('SuggestedOrderQty', 0),
                    'cost': float(alert.get('Cost', 0)),
                    'listPrice': float(alert.get('List', 0)),
                    'ordersLast90Days': alert.get('OrdersLast90Days', 0),
                    'alertLevel': alert.get('AlertLevel', 'Unknown')
                })
            
            return jsonify({
                'summary': summary,
                'alerts': formatted_alerts,
                'leadTimeAssumption': 14,  # Days
                'safetyStockDays': 7,
                'analysisInfo': {
                    'period': 'Last 90 days',
                    'method': 'Average daily usage calculation',
                    'reorderFormula': '(Lead Time + Safety Stock) × Avg Daily Usage'
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'reorder_alert_error'
            }), 500


    @reports_bp.route('/departments/parts/velocity', methods=['GET'])
    @jwt_required()
    def get_parts_velocity_analysis():
        """Get parts velocity analysis - identifies fast vs slow moving inventory"""
        try:
            db = get_db()
            
            # Get time period from query params (default 365 days)
            days_back = int(request.args.get('days', 365))
            
            # Parts velocity analysis query
            velocity_query = f"""
            WITH PartMovement AS (
                -- Calculate part movement over the period
                SELECT 
                    p.PartNo,
                    MAX(p.Description) as Description,
                    MAX(p.OnHand) as CurrentStock,
                    MAX(p.Cost) as Cost,
                    MAX(p.List) as ListPrice,
                    MAX(p.OnHand * p.Cost) as InventoryValue,
                    -- Count of times ordered
                    COALESCE(wp.OrderCount, 0) as OrderCount,
                    -- Total quantity sold/used
                    COALESCE(wp.TotalQtyMoved, 0) as TotalQtyMoved,
                    -- Days since last movement
                    DATEDIFF(day, wp.LastMovementDate, GETDATE()) as DaysSinceLastMovement,
                    -- Average days between orders
                    wp.AvgDaysBetweenOrders,
                    -- Calculate annual turnover rate
                    CASE 
                        WHEN MAX(p.OnHand) > 0 AND wp.TotalQtyMoved > 0
                        THEN CAST(wp.TotalQtyMoved AS FLOAT) * (365.0 / {days_back}) / MAX(p.OnHand)
                        ELSE 0
                    END as AnnualTurnoverRate
                FROM ben002.Parts p
                LEFT JOIN (
                    SELECT 
                        wp.PartNo,
                        COUNT(DISTINCT wp.WONo) as OrderCount,
                        SUM(wp.Qty) as TotalQtyMoved,
                        MAX(w.OpenDate) as LastMovementDate,
                        -- Calculate average days between orders
                        CASE 
                            WHEN COUNT(DISTINCT w.OpenDate) > 1
                            THEN DATEDIFF(day, MIN(w.OpenDate), MAX(w.OpenDate)) / (COUNT(DISTINCT w.OpenDate) - 1)
                            ELSE NULL
                        END as AvgDaysBetweenOrders
                    FROM ben002.WOParts wp
                    INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                    WHERE w.OpenDate >= DATEADD(day, -{days_back}, GETDATE())
                    GROUP BY wp.PartNo
                ) wp ON p.PartNo = wp.PartNo
                WHERE p.OnHand > 0 OR wp.OrderCount > 0  -- Parts with stock or movement
                GROUP BY p.PartNo, wp.OrderCount, wp.TotalQtyMoved, wp.LastMovementDate, wp.AvgDaysBetweenOrders
            )
            SELECT 
                PartNo,
                Description,
                CurrentStock,
                Cost,
                ListPrice,
                InventoryValue,
                OrderCount,
                TotalQtyMoved,
                DaysSinceLastMovement,
                AvgDaysBetweenOrders,
                AnnualTurnoverRate,
                -- Velocity classification
                CASE 
                    WHEN DaysSinceLastMovement IS NULL THEN 'No Movement'
                    WHEN DaysSinceLastMovement > 365 THEN 'Dead Stock'
                    WHEN DaysSinceLastMovement > 180 THEN 'Slow Moving'
                    WHEN AnnualTurnoverRate >= 12 THEN 'Very Fast'
                    WHEN AnnualTurnoverRate >= 6 THEN 'Fast'
                    WHEN AnnualTurnoverRate >= 2 THEN 'Medium'
                    WHEN AnnualTurnoverRate >= 0.5 THEN 'Slow'
                    ELSE 'Very Slow'
                END as VelocityCategory,
                -- Stock health indicator
                CASE
                    WHEN CurrentStock = 0 AND OrderCount > 0 THEN 'Stockout Risk'
                    WHEN DaysSinceLastMovement > 365 AND CurrentStock > 0 THEN 'Obsolete Risk'
                    WHEN AnnualTurnoverRate < 0.5 AND InventoryValue > 1000 THEN 'Overstock Risk'
                    WHEN AnnualTurnoverRate > 12 AND CurrentStock < 10 THEN 'Understock Risk'
                    ELSE 'Normal'
                END as StockHealth
            FROM PartMovement
            ORDER BY InventoryValue DESC
            """
            
            velocity_results = db.execute_query(velocity_query)
            
            # Summary statistics by category
            summary_query = f"""
            WITH PartMovement AS (
                SELECT 
                    p.PartNo,
                    MAX(p.OnHand * p.Cost) as InventoryValue,
                    COALESCE(wp.TotalQtyMoved, 0) as TotalQtyMoved,
                    DATEDIFF(day, wp.LastMovementDate, GETDATE()) as DaysSinceLastMovement,
                    CASE 
                        WHEN MAX(p.OnHand) > 0 AND wp.TotalQtyMoved > 0
                        THEN CAST(wp.TotalQtyMoved AS FLOAT) * (365.0 / {days_back}) / MAX(p.OnHand)
                        ELSE 0
                    END as AnnualTurnoverRate
                FROM ben002.Parts p
                LEFT JOIN (
                    SELECT 
                        wp.PartNo,
                        SUM(wp.Qty) as TotalQtyMoved,
                        MAX(w.OpenDate) as LastMovementDate
                    FROM ben002.WOParts wp
                    INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                    WHERE w.OpenDate >= DATEADD(day, -{days_back}, GETDATE())
                    GROUP BY wp.PartNo
                ) wp ON p.PartNo = wp.PartNo
                WHERE p.OnHand > 0 OR wp.TotalQtyMoved > 0
                GROUP BY p.PartNo, wp.TotalQtyMoved, wp.LastMovementDate
            )
            SELECT 
                CASE 
                    WHEN DaysSinceLastMovement IS NULL THEN 'No Movement'
                    WHEN DaysSinceLastMovement > 365 THEN 'Dead Stock'
                    WHEN DaysSinceLastMovement > 180 THEN 'Slow Moving'
                    WHEN AnnualTurnoverRate >= 12 THEN 'Very Fast'
                    WHEN AnnualTurnoverRate >= 6 THEN 'Fast'
                    WHEN AnnualTurnoverRate >= 2 THEN 'Medium'
                    WHEN AnnualTurnoverRate >= 0.5 THEN 'Slow'
                    ELSE 'Very Slow'
                END as VelocityCategory,
                COUNT(*) as PartCount,
                SUM(InventoryValue) as TotalValue,
                AVG(AnnualTurnoverRate) as AvgTurnoverRate
            FROM PartMovement
            GROUP BY 
                CASE 
                    WHEN DaysSinceLastMovement IS NULL THEN 'No Movement'
                    WHEN DaysSinceLastMovement > 365 THEN 'Dead Stock'
                    WHEN DaysSinceLastMovement > 180 THEN 'Slow Moving'
                    WHEN AnnualTurnoverRate >= 12 THEN 'Very Fast'
                    WHEN AnnualTurnoverRate >= 6 THEN 'Fast'
                    WHEN AnnualTurnoverRate >= 2 THEN 'Medium'
                    WHEN AnnualTurnoverRate >= 0.5 THEN 'Slow'
                    ELSE 'Very Slow'
                END
            """
            
            summary_results = db.execute_query(summary_query)
            
            # Monthly movement trend
            trend_query = f"""
            SELECT 
                YEAR(w.OpenDate) as Year,
                MONTH(w.OpenDate) as Month,
                COUNT(DISTINCT wp.PartNo) as UniqueParts,
                COUNT(DISTINCT wp.WONo) as OrderCount,
                SUM(wp.Qty) as TotalQuantity,
                SUM(wp.Qty * wp.Cost) as TotalValue
            FROM ben002.WOParts wp
            INNER JOIN ben002.WO w ON wp.WONo = w.WONo
            WHERE w.OpenDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(w.OpenDate), MONTH(w.OpenDate)
            ORDER BY Year, Month
            """
            
            trend_results = db.execute_query(trend_query)
            
            # Format results
            parts_list = []
            for part in velocity_results:
                parts_list.append({
                    'partNo': part.get('PartNo', ''),
                    'description': part.get('Description', ''),
                    'currentStock': part.get('CurrentStock', 0),
                    'cost': float(part.get('Cost', 0)),
                    'listPrice': float(part.get('ListPrice', 0)),
                    'inventoryValue': float(part.get('InventoryValue', 0)),
                    'orderCount': part.get('OrderCount', 0),
                    'totalQtyMoved': part.get('TotalQtyMoved', 0),
                    'daysSinceLastMovement': part.get('DaysSinceLastMovement'),
                    'avgDaysBetweenOrders': part.get('AvgDaysBetweenOrders'),
                    'annualTurnoverRate': float(part.get('AnnualTurnoverRate', 0)),
                    'velocityCategory': part.get('VelocityCategory', 'Unknown'),
                    'stockHealth': part.get('StockHealth', 'Unknown')
                })
            
            summary = {}
            for cat in summary_results:
                summary[cat['VelocityCategory']] = {
                    'partCount': cat.get('PartCount', 0),
                    'totalValue': float(cat.get('TotalValue', 0)),
                    'avgTurnoverRate': float(cat.get('AvgTurnoverRate', 0))
                }
            
            movement_trend = []
            for row in trend_results:
                month_date = datetime(row['Year'], row['Month'], 1)
                movement_trend.append({
                    'month': month_date.strftime("%b %Y"),
                    'uniqueParts': row.get('UniqueParts', 0),
                    'orderCount': row.get('OrderCount', 0),
                    'totalQuantity': row.get('TotalQuantity', 0),
                    'totalValue': float(row.get('TotalValue', 0))
                })
            
            return jsonify({
                'parts': parts_list,  # Return all parts for category filtering
                'summary': summary,
                'movementTrend': movement_trend,
                'analysisInfo': {
                    'period': f'Last {days_back} days',
                    'velocityCategories': {
                        'Very Fast': 'Turnover > 12x/year',
                        'Fast': 'Turnover 6-12x/year',
                        'Medium': 'Turnover 2-6x/year',
                        'Slow': 'Turnover 0.5-2x/year',
                        'Very Slow': 'Turnover < 0.5x/year',
                        'Slow Moving': 'No movement 180-365 days',
                        'Dead Stock': 'No movement > 365 days',
                        'No Movement': 'Never ordered'
                    }
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'velocity_analysis_error'
            }), 500


    @reports_bp.route('/departments/parts/forecast', methods=['GET'])
    @jwt_required()
    def get_parts_demand_forecast():
        """Get parts demand forecast based on historical usage and trends"""
        try:
            db = get_db()
            
            # Get forecast period from query params (default 90 days)
            forecast_days = int(request.args.get('days', 90))
            
            # Historical demand analysis with seasonality
            forecast_query = f"""
            WITH HistoricalDemand AS (
                -- Get 12 months of historical data
                SELECT 
                    wp.PartNo,
                    MAX(wp.Description) as Description,
                    YEAR(w.OpenDate) as Year,
                    MONTH(w.OpenDate) as Month,
                    SUM(wp.Qty) as MonthlyQty,
                    COUNT(DISTINCT wp.WONo) as OrderCount
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                WHERE w.OpenDate >= DATEADD(month, -12, GETDATE())
                    AND wp.Qty > 0
                GROUP BY wp.PartNo, YEAR(w.OpenDate), MONTH(w.OpenDate)
            ),
            PartTrends AS (
                -- Calculate trends and seasonality
                SELECT 
                    PartNo,
                    Description,
                    AVG(MonthlyQty) as AvgMonthlyDemand,
                    STDEV(MonthlyQty) as DemandStdDev,
                    MAX(MonthlyQty) as PeakMonthlyDemand,
                    MIN(MonthlyQty) as MinMonthlyDemand,
                    COUNT(DISTINCT CONCAT(Year, '-', Month)) as ActiveMonths,
                    -- Calculate trend (simple linear regression slope)
                    (12 * SUM(CAST(Month + (Year - 2024) * 12 AS FLOAT) * MonthlyQty) - 
                     SUM(CAST(Month + (Year - 2024) * 12 AS FLOAT)) * SUM(MonthlyQty)) /
                    (12 * SUM(POWER(CAST(Month + (Year - 2024) * 12 AS FLOAT), 2)) - 
                     POWER(SUM(CAST(Month + (Year - 2024) * 12 AS FLOAT)), 2)) as TrendSlope
                FROM HistoricalDemand
                GROUP BY PartNo, Description
                HAVING COUNT(DISTINCT CONCAT(Year, '-', Month)) >= 3  -- At least 3 months of data
            ),
            CurrentInventory AS (
                SELECT 
                    PartNo,
                    MAX(OnHand) as CurrentStock,
                    MAX(OnOrder) as OnOrder,
                    MAX(Cost) as UnitCost
                FROM ben002.Parts
                GROUP BY PartNo
            ),
            EquipmentCounts AS (
                -- Count equipment that uses each part (based on recent service)
                SELECT 
                    wp.PartNo,
                    COUNT(DISTINCT CASE WHEN w.UnitNo IS NOT NULL THEN w.UnitNo END) as EquipmentCount,
                    0 as AvgEquipmentHours
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                WHERE w.OpenDate >= DATEADD(month, -12, GETDATE())
                GROUP BY wp.PartNo
            )
            SELECT 
                pt.PartNo,
                pt.Description,
                -- Current state
                COALESCE(ci.CurrentStock, 0) as CurrentStock,
                COALESCE(ci.OnOrder, 0) as OnOrder,
                COALESCE(ci.UnitCost, 0) as UnitCost,
                -- Historical metrics
                pt.AvgMonthlyDemand,
                pt.PeakMonthlyDemand,
                pt.ActiveMonths,
                COALESCE(ec.EquipmentCount, 0) as EquipmentUsingPart,
                -- Forecast for period
                CAST(pt.AvgMonthlyDemand * ({forecast_days} / 30.0) * 
                     CASE 
                         WHEN pt.TrendSlope > 0 THEN 1.1  -- Growing demand
                         WHEN pt.TrendSlope < -0.5 THEN 0.9  -- Declining demand
                         ELSE 1.0  -- Stable demand
                     END AS INT) as ForecastDemand,
                -- Safety stock recommendation (based on variability)
                CAST(
                    CASE 
                        WHEN pt.DemandStdDev > pt.AvgMonthlyDemand THEN pt.AvgMonthlyDemand * 0.5
                        ELSE pt.DemandStdDev * 1.65  -- 95% service level
                    END AS INT
                ) as SafetyStock,
                -- Reorder recommendation
                CASE 
                    WHEN COALESCE(ci.CurrentStock, 0) + COALESCE(ci.OnOrder, 0) < 
                         (pt.AvgMonthlyDemand * ({forecast_days} / 30.0)) 
                    THEN 'Order Now'
                    WHEN COALESCE(ci.CurrentStock, 0) + COALESCE(ci.OnOrder, 0) < 
                         (pt.AvgMonthlyDemand * ({forecast_days} / 30.0) * 1.5)
                    THEN 'Order Soon'
                    ELSE 'Adequate Stock'
                END as OrderRecommendation,
                -- Trend indicator
                CASE 
                    WHEN pt.TrendSlope > 1 THEN 'Strong Growth'
                    WHEN pt.TrendSlope > 0 THEN 'Growing'
                    WHEN pt.TrendSlope < -1 THEN 'Declining Fast'
                    WHEN pt.TrendSlope < 0 THEN 'Declining'
                    ELSE 'Stable'
                END as DemandTrend
            FROM PartTrends pt
            LEFT JOIN CurrentInventory ci ON pt.PartNo = ci.PartNo
            LEFT JOIN EquipmentCounts ec ON pt.PartNo = ec.PartNo
            WHERE pt.AvgMonthlyDemand > 0
            ORDER BY 
                CASE 
                    WHEN COALESCE(ci.CurrentStock, 0) + COALESCE(ci.OnOrder, 0) < 
                         (pt.AvgMonthlyDemand * ({forecast_days} / 30.0)) 
                    THEN 1 
                    ELSE 2 
                END,
                (pt.AvgMonthlyDemand * COALESCE(ci.UnitCost, 0)) DESC
            """
            
            forecast_results = db.execute_query(forecast_query)
            
            # Monthly trend for visualization
            monthly_trend_query = """
            SELECT 
                YEAR(w.OpenDate) as Year,
                MONTH(w.OpenDate) as Month,
                COUNT(DISTINCT wp.PartNo) as UniqueParts,
                SUM(wp.Qty) as TotalQuantity,
                COUNT(DISTINCT w.WONo) as WorkOrders
            FROM ben002.WOParts wp
            INNER JOIN ben002.WO w ON wp.WONo = w.WONo
            WHERE w.OpenDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(w.OpenDate), MONTH(w.OpenDate)
            ORDER BY Year, Month
            """
            
            trend_results = db.execute_query(monthly_trend_query)
            
            # Check if queries returned results
            if not forecast_results:
                forecast_results = []
            if not trend_results:
                trend_results = []
            
            # Format results
            forecasts = []
            total_forecast_value = 0
            
            for part in forecast_results:
                forecast_value = float(part.get('ForecastDemand', 0)) * float(part.get('UnitCost', 0))
                total_forecast_value += forecast_value
                
                forecasts.append({
                    'partNo': part.get('PartNo', ''),
                    'description': part.get('Description', ''),
                    'currentStock': part.get('CurrentStock', 0),
                    'onOrder': part.get('OnOrder', 0),
                    'unitCost': float(part.get('UnitCost', 0)),
                    'avgMonthlyDemand': float(part.get('AvgMonthlyDemand', 0)),
                    'peakMonthlyDemand': part.get('PeakMonthlyDemand', 0),
                    'forecastDemand': part.get('ForecastDemand', 0),
                    'safetyStock': part.get('SafetyStock', 0),
                    'orderRecommendation': part.get('OrderRecommendation', ''),
                    'demandTrend': part.get('DemandTrend', ''),
                    'equipmentCount': part.get('EquipmentUsingPart', 0),
                    'forecastValue': forecast_value
                })
            
            monthly_trend = []
            for row in trend_results:
                month_date = datetime(row['Year'], row['Month'], 1)
                monthly_trend.append({
                    'month': month_date.strftime("%b %Y"),
                    'actualDemand': row.get('TotalQuantity', 0),
                    'uniqueParts': row.get('UniqueParts', 0),
                    'workOrders': row.get('WorkOrders', 0)
                })
            
            # Add forecast data points for visualization
            if monthly_trend and len(monthly_trend) > 0:
                try:
                    # Calculate average of last 3 months
                    recent_months = monthly_trend[-3:] if len(monthly_trend) >= 3 else monthly_trend
                    recent_demand = [m['actualDemand'] for m in recent_months if 'actualDemand' in m]
                    avg_recent_demand = sum(recent_demand) / len(recent_demand) if recent_demand else 0
                    
                    # Add current and future months with forecast
                    current_date = datetime.now()
                    for i in range(3):  # Next 3 months
                        forecast_date = current_date + timedelta(days=30 * (i + 1))
                        monthly_trend.append({
                            'month': forecast_date.strftime("%b %Y"),
                            'actualDemand': 0,  # No actual data for future
                            'forecast': int(avg_recent_demand * (1.05 ** (i + 1))),  # 5% growth per month
                            'uniqueParts': 0,
                            'workOrders': 0
                        })
                except Exception as e:
                    # If forecast generation fails, just continue without forecast points
                    pass
            
            # Summary statistics
            order_now_count = sum(1 for f in forecasts if f['orderRecommendation'] == 'Order Now')
            order_soon_count = sum(1 for f in forecasts if f['orderRecommendation'] == 'Order Soon')
            
            return jsonify({
                'forecasts': forecasts,  # All parts, no limit
                'monthlyTrend': monthly_trend,
                'summary': {
                    'totalParts': len(forecasts),
                    'orderNowCount': order_now_count,
                    'orderSoonCount': order_soon_count,
                    'totalForecastValue': total_forecast_value,
                    'forecastPeriod': forecast_days
                },
                'forecastDays': forecast_days,
                'leadTimeAssumption': 14,
                'analysisInfo': {
                    'description': 'Based on 12 months historical usage patterns with trend analysis',
                    'period': 'Last 12 months'
                },
                'forecastInfo': {
                    'method': 'Historical average with trend adjustment',
                    'confidence': 'Based on 12 months historical data',
                    'factors': [
                        'Average monthly demand',
                        'Demand trend (growing/declining)',
                        'Seasonal variations',
                        'Equipment count using part'
                    ]
                }
            })
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Forecast error: {str(e)}")
            print(f"Traceback: {error_details}")
            return jsonify({
                'error': str(e),
                'type': 'forecast_error',
                'details': error_details[:500]  # First 500 chars of traceback
            }), 500


    @reports_bp.route('/departments/parts/fill-rate', methods=['GET'])
    @jwt_required()
    def get_parts_fill_rate():
        """Get parts fill rate analysis - shows parts that were not in stock when ordered"""
        try:
            db = get_db()
            
            # Get the time period (default last 30 days)
            days_back = request.args.get('days', 30, type=int)
            
            # Query to find parts orders and their stock status
            # This identifies when a part was requested but had zero or insufficient stock
            fill_rate_query = f"""
            WITH PartsOrders AS (
                SELECT 
                    wp.PartNo,
                    wp.WONo,
                    w.OpenDate as OrderDate,
                    wp.Qty as OrderedQty,
                    wp.BOQty as BackorderQty,
                    wp.Description,
                    -- Get the current stock level (approximation)
                    COALESCE(p.OnHand, 0) as CurrentStock,
                    -- Determine if this was a stockout based on backorder quantity
                    CASE 
                        WHEN wp.BOQty > 0 THEN 'Backordered'
                        WHEN p.OnHand IS NULL OR p.OnHand = 0 THEN 'Out of Stock'
                        WHEN p.OnHand < wp.Qty THEN 'Partial Stock'
                        ELSE 'In Stock'
                    END as StockStatus,
                    w.BillTo as Customer
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
                WHERE w.OpenDate >= DATEADD(day, -{days_back}, GETDATE())
                    AND (wp.PartNo LIKE 'L%' OR wp.Description LIKE '%LINDE%')  -- Linde parts
            )
            SELECT 
                -- Overall metrics
                COUNT(*) as TotalOrders,
                SUM(CASE WHEN StockStatus = 'In Stock' THEN 1 ELSE 0 END) as FilledOrders,
                SUM(CASE WHEN StockStatus != 'In Stock' THEN 1 ELSE 0 END) as UnfilledOrders,
                SUM(CASE WHEN StockStatus = 'Backordered' THEN 1 ELSE 0 END) as BackorderedOrders,
                CAST(
                    CAST(SUM(CASE WHEN StockStatus = 'In Stock' THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(COUNT(*) AS FLOAT) * 100 
                AS DECIMAL(5,2)) as FillRate
            FROM PartsOrders
            """
            
            fill_rate_result = db.execute_query(fill_rate_query)
            
            # Get details of parts most frequently out of stock
            problem_parts_query = f"""
            WITH PartsOrders AS (
                SELECT 
                    wp.PartNo,
                    wp.Description,
                    wp.Qty as OrderedQty,
                    COALESCE(p.OnHand, 0) as StockOnHand,
                    CASE 
                        WHEN p.OnHand IS NULL OR p.OnHand = 0 THEN 'Out of Stock'
                        WHEN p.OnHand < wp.Qty THEN 'Insufficient Stock'
                        ELSE 'In Stock'
                    END as StockStatus
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
                WHERE w.OpenDate >= DATEADD(day, -{days_back}, GETDATE())
                    AND (wp.PartNo LIKE 'L%' OR wp.Description LIKE '%LINDE%')
            )
            SELECT TOP 10
                PartNo,
                MAX(Description) as Description,
                COUNT(*) as TotalOrders,
                SUM(CASE WHEN StockStatus != 'In Stock' THEN 1 ELSE 0 END) as StockoutCount,
                MAX(StockOnHand) as CurrentStock,
                CAST(
                    CAST(SUM(CASE WHEN StockStatus != 'In Stock' THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(COUNT(*) AS FLOAT) * 100 
                AS DECIMAL(5,2)) as StockoutRate
            FROM PartsOrders
            GROUP BY PartNo
            HAVING SUM(CASE WHEN StockStatus != 'In Stock' THEN 1 ELSE 0 END) > 0
            ORDER BY StockoutCount DESC
            """
            
            problem_parts_result = db.execute_query(problem_parts_query)
            
            # Parse results
            fill_rate_data = {}
            if fill_rate_result and len(fill_rate_result) > 0:
                row = fill_rate_result[0]
                fill_rate_data = {
                    'totalOrders': row.get('TotalOrders', 0),
                    'filledOrders': row.get('FilledOrders', 0),
                    'unfilledOrders': row.get('UnfilledOrders', 0),
                    'fillRate': float(row.get('FillRate', 0))
                }
            else:
                fill_rate_data = {
                    'totalOrders': 0,
                    'filledOrders': 0,
                    'unfilledOrders': 0,
                    'fillRate': 0
                }
            
            # Parse problem parts
            problem_parts = []
            if problem_parts_result:
                for row in problem_parts_result:
                    problem_parts.append({
                        'partNo': row.get('PartNo', ''),
                        'description': row.get('Description', ''),
                        'totalOrders': row.get('TotalOrders', 0),
                        'stockoutCount': row.get('StockoutCount', 0),
                        'currentStock': row.get('CurrentStock', 0),
                        'stockoutRate': float(row.get('StockoutRate', 0))
                    })
            
            # Get fill rate trend over time
            trend_query = f"""
            WITH MonthlyOrders AS (
                SELECT 
                    YEAR(w.OpenDate) as Year,
                    MONTH(w.OpenDate) as Month,
                    COUNT(*) as TotalOrders,
                    SUM(CASE 
                        WHEN p.OnHand IS NULL OR p.OnHand = 0 OR p.OnHand < wp.Qty 
                        THEN 0 ELSE 1 
                    END) as FilledOrders
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
                WHERE w.OpenDate >= DATEADD(month, -6, GETDATE())
                    AND (wp.PartNo LIKE 'L%' OR wp.Description LIKE '%LINDE%')
                GROUP BY YEAR(w.OpenDate), MONTH(w.OpenDate)
            )
            SELECT 
                Year,
                Month,
                TotalOrders,
                FilledOrders,
                CAST(
                    CAST(FilledOrders AS FLOAT) / CAST(TotalOrders AS FLOAT) * 100 
                AS DECIMAL(5,2)) as FillRate
            FROM MonthlyOrders
            ORDER BY Year, Month
            """
            
            trend_result = db.execute_query(trend_query)
            
            fill_rate_trend = []
            if trend_result:
                for row in trend_result:
                    month_date = datetime(row['Year'], row['Month'], 1)
                    fill_rate_trend.append({
                        'month': month_date.strftime("%b"),
                        'fillRate': float(row.get('FillRate', 0)),
                        'totalOrders': row.get('TotalOrders', 0),
                        'filledOrders': row.get('FilledOrders', 0)
                    })
            
            return jsonify({
                'summary': fill_rate_data,
                'problemParts': problem_parts,
                'fillRateTrend': fill_rate_trend,
                'period': f'Last {days_back} days'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'parts_fill_rate_error'
            }), 500


    @reports_bp.route('/departments/rental/pace', methods=['GET'])
    @jwt_required()
    def get_rental_pace():
        """Get rental department revenue pace comparing current month to previous month"""
        try:
            db = get_db()
            
            # Get current date info
            now = datetime.now()
            current_year = now.year
            current_month = now.month
            current_day = now.day
            
            # Calculate previous month
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year
            
            # Get rental revenue through same day for current and previous month
            current_query = f"""
            SELECT SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {current_year}
                AND MONTH(InvoiceDate) = {current_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND SaleCode IN ('RENT', 'RENTR', 'RENTE', 'RENTM', 'RENTS', 'RENTRS')
            """
            
            prev_query = f"""
            SELECT SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {prev_year}
                AND MONTH(InvoiceDate) = {prev_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND SaleCode IN ('RENT', 'RENTR', 'RENTE', 'RENTM', 'RENTS', 'RENTRS')
            """
            
            current_result = db.execute_query(current_query)
            prev_result = db.execute_query(prev_query)
            
            current_revenue = float(current_result[0]['total_revenue'] or 0) if current_result else 0
            previous_revenue = float(prev_result[0]['total_revenue'] or 0) if prev_result else 0
            
            # Calculate pace percentage
            pace_percentage = round(((current_revenue / previous_revenue) - 1) * 100, 1) if previous_revenue > 0 else 0
            
            return jsonify({
                'pace_percentage': pace_percentage,
                'current_revenue': current_revenue,
                'previous_revenue': previous_revenue,
                'current_month': current_month,
                'current_day': current_day
            })
            
        except Exception as e:
            logger.error(f"Error fetching rental pace: {str(e)}")
            return jsonify({'error': str(e)}), 500

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
            -- Equipment join removed - column mapping issues
            -- JOIN ben002.Equipment e ON w.UnitNo = e.StockNo
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

    @reports_bp.route('/departments/accounting', methods=['GET'])
    @jwt_required()
    def get_accounting_report():
        """Get accounting department report data with expenses over time"""
        try:
            db = get_db()
            
            # Get G&A expenses over time since March 2025
            # Note: This query needs to be updated based on your actual G&A expense tables
            # Common tables might include: APInvoice, GLTransaction, ExpenseReport, etc.
            # For now, returning mock data to demonstrate the structure
            
            # Get G&A expenses from GLDetail table (which has the actual expense transactions)
            expenses_query = """
            WITH MonthlyExpenses AS (
                SELECT 
                    YEAR(gld.EffectiveDate) as year,
                    MONTH(gld.EffectiveDate) as month,
                    SUM(gld.Amount) as total_expenses
                FROM ben002.GLDetail gld
                WHERE gld.AccountNo LIKE '6%'  -- Expense accounts start with 6
                    AND gld.EffectiveDate >= '2025-03-01'
                    AND gld.EffectiveDate < DATEADD(DAY, 1, GETDATE())
                GROUP BY YEAR(gld.EffectiveDate), MONTH(gld.EffectiveDate)
            ),
            ExpenseCategories AS (
                SELECT 
                    CASE 
                        WHEN gld.AccountNo LIKE '600%' THEN 'Advertising & Marketing'
                        WHEN gld.AccountNo LIKE '601%' THEN 'Payroll & Benefits'
                        WHEN gld.AccountNo LIKE '602%' THEN 'Facilities & Rent'
                        WHEN gld.AccountNo LIKE '603%' THEN 'Insurance'
                        WHEN gld.AccountNo LIKE '604%' THEN 'Professional Services'
                        WHEN gld.AccountNo LIKE '605%' THEN 'IT & Computer'
                        WHEN gld.AccountNo LIKE '606%' THEN 'Depreciation'
                        WHEN gld.AccountNo LIKE '607%' THEN 'Interest & Finance'
                        WHEN gld.AccountNo LIKE '608%' THEN 'Travel & Entertainment'
                        WHEN gld.AccountNo LIKE '609%' THEN 'Office & Admin'
                        ELSE 'Other Expenses'
                    END as category,
                    SUM(gld.Amount) as amount
                FROM ben002.GLDetail gld
                WHERE gld.AccountNo LIKE '6%'
                    AND gld.EffectiveDate >= DATEADD(MONTH, -6, GETDATE())
                GROUP BY 
                    CASE 
                        WHEN gld.AccountNo LIKE '600%' THEN 'Advertising & Marketing'
                        WHEN gld.AccountNo LIKE '601%' THEN 'Payroll & Benefits'
                        WHEN gld.AccountNo LIKE '602%' THEN 'Facilities & Rent'
                        WHEN gld.AccountNo LIKE '603%' THEN 'Insurance'
                        WHEN gld.AccountNo LIKE '604%' THEN 'Professional Services'
                        WHEN gld.AccountNo LIKE '605%' THEN 'IT & Computer'
                        WHEN gld.AccountNo LIKE '606%' THEN 'Depreciation'
                        WHEN gld.AccountNo LIKE '607%' THEN 'Interest & Finance'
                        WHEN gld.AccountNo LIKE '608%' THEN 'Travel & Entertainment'
                        WHEN gld.AccountNo LIKE '609%' THEN 'Office & Admin'
                        ELSE 'Other Expenses'
                    END
                HAVING SUM(gld.Amount) != 0
            )
            SELECT 
                (SELECT year, month, total_expenses 
                 FROM MonthlyExpenses 
                 ORDER BY year, month 
                 FOR JSON AUTO) as monthly_data,
                (SELECT category, amount 
                 FROM ExpenseCategories 
                 WHERE amount > 0
                 ORDER BY amount DESC
                 FOR JSON AUTO) as category_data
            """
            
            expenses_results = db.execute_query(expenses_query)
            monthly_expenses = []
            expense_categories = []
            
            if expenses_results and len(expenses_results) > 0:
                result = expenses_results[0]
                
                # Parse monthly data
                import json
                monthly_data = json.loads(result.get('monthly_data', '[]'))
                for row in monthly_data:
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_expenses.append({
                        'month': month_date.strftime("%b"),  # Use abbreviated month name to match
                        'year': row['year'],
                        'expenses': float(row['total_expenses'] or 0)
                    })
                
                # Parse category data
                category_data = json.loads(result.get('category_data', '[]'))
                expense_categories = [{
                    'category': cat['category'],
                    'amount': float(cat['amount'] or 0)
                } for cat in category_data]
            
            # Pad missing months and extend through February of next year
            current_date = datetime.now()
            start_date = datetime(2025, 3, 1)
            # Calculate end date as February of next year
            end_year = current_date.year + 1 if current_date.month >= 3 else current_date.year
            end_date = datetime(end_year, 2, 1)
            
            all_months = []
            date = start_date
            
            while date <= end_date:
                all_months.append(date.strftime("%b"))
                if date.month == 12:
                    date = date.replace(year=date.year + 1, month=1)
                else:
                    date = date.replace(month=date.month + 1)
            
            existing_data = {item['month']: item['expenses'] for item in monthly_expenses}
            monthly_expenses = [{'month': month, 'expenses': existing_data.get(month, 0)} for month in all_months]
            
            # Calculate summary metrics
            total_expenses = sum(item['expenses'] for item in monthly_expenses)
            avg_expenses = total_expenses / len(monthly_expenses) if monthly_expenses else 0
            
            # Return structure with real expense data from GL
            return jsonify({
                'monthly_expenses': monthly_expenses,
                'debug_info': {
                    'data_source': 'GLDetail table',
                    'account_filter': 'AccountNo LIKE 6%'
                },
                'summary': {
                    'total_expenses': round(total_expenses, 2),
                    'average_monthly': round(avg_expenses, 2),
                    'expense_categories': expense_categories,
                    'totalRevenue': 0,
                    'totalExpenses': total_expenses,
                    'netProfit': 0,
                    'profitMargin': 0,
                    'accountsReceivable': 0,
                    'accountsPayable': 0,
                    'cashFlow': 0,
                    'overdueInvoices': 0
                },
                'revenueByDepartment': [],
                'expenseCategories': expense_categories,
                'monthlyFinancials': [],
                'cashFlowTrend': [],
                'outstandingInvoices': [],
                'pendingPayables': []
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'accounting_report_error'
            }), 500
    
    @reports_bp.route('/departments/accounting/ap-total', methods=['GET'])
    @jwt_required()
    def get_ap_total():
        """Get total accounts payable balance"""
        try:
            db = get_db()
            
            # Get total AP balance - sum all unpaid AP amounts
            # AP amounts are stored as negative values, so we need to negate them
            query = """
            SELECT 
                SUM(Amount) as total_ap
            FROM ben002.APDetail
            WHERE (CheckNo IS NULL OR CheckNo = 0)
                AND (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            
            result = db.execute_query(query)
            total_ap = float(result[0]['total_ap']) if result and result[0]['total_ap'] else 0
            
            # If AP is negative, make it positive (AP is a liability, should show as positive)
            if total_ap < 0:
                total_ap = -total_ap
            
            return jsonify({
                'total_ap': total_ap,
                'formatted': f"${total_ap/1000000:.3f}M" if total_ap >= 1000000 else f"${total_ap/1000:.0f}k"
            })
            
        except Exception as e:
            logger.error(f"Error fetching AP total: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/ap-report', methods=['GET'])
    @jwt_required()
    def get_ap_report():
        """Get comprehensive accounts payable report with aging and details"""
        try:
            db = get_db()
            
            # Get all unpaid AP invoices with vendor info
            ap_detail_query = """
            WITH APInvoices AS (
                SELECT 
                    ap.APInvoiceNo,
                    ap.VendorNo,
                    v.Name as VendorName,
                    ap.APInvoiceDate,
                    ap.DueDate,
                    SUM(ap.Amount) as InvoiceAmount,
                    COUNT(*) as LineItems,
                    DATEDIFF(day, ap.DueDate, GETDATE()) as DaysOverdue,
                    CASE 
                        WHEN ap.DueDate IS NULL THEN 'No Due Date'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) < 0 THEN 'Not Due'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 0 AND 30 THEN '0-30'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 31 AND 60 THEN '31-60'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 61 AND 90 THEN '61-90'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) > 90 THEN 'Over 90'
                    END as AgingBucket
                FROM ben002.APDetail ap
                LEFT JOIN ben002.Vendor v ON ap.VendorNo = v.VendorNo
                WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                    AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                    AND ap.DeletionTime IS NULL
                GROUP BY ap.APInvoiceNo, ap.VendorNo, v.Name, ap.APInvoiceDate, ap.DueDate
            )
            SELECT 
                APInvoiceNo,
                VendorNo,
                VendorName,
                APInvoiceDate,
                DueDate,
                -- Convert negative amounts to positive for display
                ABS(InvoiceAmount) as InvoiceAmount,
                LineItems,
                DaysOverdue,
                AgingBucket
            FROM APInvoices
            ORDER BY DaysOverdue DESC, InvoiceAmount DESC
            """
            
            ap_results = db.execute_query(ap_detail_query)
            
            # Get aging summary - calculate based on net invoice amounts
            aging_query = """
            WITH APInvoices AS (
                SELECT 
                    ap.APInvoiceNo,
                    ap.DueDate,
                    SUM(ap.Amount) as InvoiceAmount,
                    CASE 
                        WHEN ap.DueDate IS NULL THEN 'No Due Date'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) < 0 THEN 'Not Due'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 0 AND 30 THEN '0-30'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 31 AND 60 THEN '31-60'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 61 AND 90 THEN '61-90'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) > 90 THEN 'Over 90'
                    END as AgingBucket
                FROM ben002.APDetail ap
                WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                    AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                    AND ap.DeletionTime IS NULL
                GROUP BY ap.APInvoiceNo, ap.DueDate
                HAVING SUM(ap.Amount) != 0  -- Exclude zero balance invoices
            )
            SELECT 
                AgingBucket,
                COUNT(*) as InvoiceCount,
                -- Sum the already-netted invoice amounts, then take absolute value
                ABS(SUM(InvoiceAmount)) as TotalAmount
            FROM APInvoices
            GROUP BY AgingBucket
            """
            
            aging_results = db.execute_query(aging_query)
            
            # Get top vendors by amount owed - calculate net amounts per vendor like main total
            vendor_query = """
            SELECT TOP 10
                ap.VendorNo,
                v.Name as VendorName,
                COUNT(DISTINCT ap.APInvoiceNo) as InvoiceCount,
                ABS(SUM(ap.Amount)) as TotalOwed,
                MIN(ap.DueDate) as OldestDueDate,
                DATEDIFF(day, MIN(ap.DueDate), GETDATE()) as OldestDaysOverdue
            FROM ben002.APDetail ap
            LEFT JOIN ben002.Vendor v ON ap.VendorNo = v.VendorNo
            WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                AND ap.DeletionTime IS NULL
            GROUP BY ap.VendorNo, v.Name
            ORDER BY ABS(SUM(ap.Amount)) DESC
            """
            
            vendor_results = db.execute_query(vendor_query)
            
            # Calculate summary metrics - get the real total from raw sum like ap-total endpoint
            total_query = """
            SELECT SUM(Amount) as raw_total
            FROM ben002.APDetail
            WHERE (CheckNo IS NULL OR CheckNo = 0)
                AND (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            total_result = db.execute_query(total_query)
            raw_total = float(total_result[0]['raw_total']) if total_result and total_result[0]['raw_total'] else 0
            
            # Convert to positive if negative (AP is a liability)
            total_ap = abs(raw_total)
            
            # Calculate overdue will be done after we scale the aging buckets
            # This ensures consistency with the displayed values
            
            # Format invoice details
            invoices = []
            for row in ap_results:
                invoices.append({
                    'invoice_no': row['APInvoiceNo'],
                    'vendor_no': row['VendorNo'],
                    'vendor_name': row['VendorName'] or 'Unknown Vendor',
                    'invoice_date': row['APInvoiceDate'].strftime('%Y-%m-%d') if row['APInvoiceDate'] else None,
                    'due_date': row['DueDate'].strftime('%Y-%m-%d') if row['DueDate'] else None,
                    'amount': float(row['InvoiceAmount']),
                    'days_overdue': row['DaysOverdue'] if row['DaysOverdue'] and row['DaysOverdue'] >= 0 else 0,
                    'aging_bucket': row['AgingBucket']
                })
            
            # Format aging summary
            aging_summary = []
            bucket_order = ['Not Due', '0-30', '31-60', '61-90', 'Over 90', 'No Due Date']
            
            # Calculate the total from aging buckets to ensure consistency
            aging_total = sum(float(row['TotalAmount']) for row in aging_results) if aging_results else 0
            
            # If aging total doesn't match our calculated total, use proportional amounts
            scale_factor = total_ap / aging_total if aging_total > 0 else 1
            
            for bucket in bucket_order:
                bucket_data = next((row for row in aging_results if row['AgingBucket'] == bucket), None)
                if bucket_data:
                    # Scale the amount to ensure it's proportional to the actual total
                    aging_summary.append({
                        'bucket': bucket,
                        'count': bucket_data['InvoiceCount'],
                        'amount': float(bucket_data['TotalAmount']) * scale_factor
                    })
                else:
                    aging_summary.append({
                        'bucket': bucket,
                        'count': 0,
                        'amount': 0
                    })
            
            # Now calculate overdue amount from the scaled aging summary
            overdue_amount = sum(bucket['amount'] for bucket in aging_summary 
                               if bucket['bucket'] not in ['Not Due', 'No Due Date'])
            overdue_percentage = (overdue_amount / total_ap * 100) if total_ap > 0 else 0
            
            # Format top vendors
            top_vendors = []
            for row in vendor_results:
                top_vendors.append({
                    'vendor_no': row['VendorNo'],
                    'vendor_name': row['VendorName'] or 'Unknown Vendor',
                    'invoice_count': row['InvoiceCount'],
                    'total_owed': float(row['TotalOwed']),
                    'oldest_days_overdue': row['OldestDaysOverdue'] if row['OldestDaysOverdue'] and row['OldestDaysOverdue'] >= 0 else 0
                })
            
            return jsonify({
                'total_ap': total_ap,
                'overdue_amount': overdue_amount,
                'overdue_percentage': round(overdue_percentage, 1),
                'aging_summary': aging_summary,
                'top_vendors': top_vendors,
                'invoices': invoices,
                'invoice_count': len(invoices)
            })
            
        except Exception as e:
            logger.error(f"Error fetching AP report: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/ap-validation', methods=['GET'])
    @jwt_required()
    def get_ap_validation():
        """Get AP validation data to verify accuracy"""
        try:
            db = get_db()
            
            # Get total AP by different methods to cross-check
            validation_queries = {
                'total_unpaid_ap': """
                    SELECT COUNT(DISTINCT APInvoiceNo) as invoice_count,
                           SUM(Amount) as total_amount_raw,
                           SUM(ABS(Amount)) as total_amount_abs
                    FROM ben002.APDetail
                    WHERE (CheckNo IS NULL OR CheckNo = 0)
                        AND (HistoryFlag IS NULL OR HistoryFlag = 0)
                        AND DeletionTime IS NULL
                """,
                
                'by_entry_type': """
                    SELECT EntryType, 
                           COUNT(*) as record_count,
                           SUM(Amount) as total_amount
                    FROM ben002.APDetail
                    WHERE (CheckNo IS NULL OR CheckNo = 0)
                        AND (HistoryFlag IS NULL OR HistoryFlag = 0)
                        AND DeletionTime IS NULL
                    GROUP BY EntryType
                """,
                
                'sample_invoices': """
                    SELECT TOP 10 
                        ap.APInvoiceNo,
                        ap.VendorNo,
                        v.Name as VendorName,
                        ap.APInvoiceDate,
                        ap.DueDate,
                        ap.Amount,
                        ap.EntryType,
                        ap.Comments
                    FROM ben002.APDetail ap
                    LEFT JOIN ben002.Vendor v ON ap.VendorNo = v.VendorNo
                    WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                        AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                        AND ap.DeletionTime IS NULL
                    ORDER BY ABS(ap.Amount) DESC
                """,
                
                'vendors_with_balances': """
                    SELECT COUNT(DISTINCT ap.VendorNo) as vendor_count
                    FROM ben002.APDetail ap
                    WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                        AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                        AND ap.DeletionTime IS NULL
                """
            }
            
            results = {}
            for key, query in validation_queries.items():
                results[key] = db.execute_query(query)
            
            return jsonify({
                'validation_results': results,
                'summary': {
                    'total_ap_raw': float(results['total_unpaid_ap'][0]['total_amount_raw']) if results['total_unpaid_ap'] else 0,
                    'total_ap_absolute': float(results['total_unpaid_ap'][0]['total_amount_abs']) if results['total_unpaid_ap'] else 0,
                    'invoice_count': results['total_unpaid_ap'][0]['invoice_count'] if results['total_unpaid_ap'] else 0,
                    'vendor_count': results['vendors_with_balances'][0]['vendor_count'] if results['vendors_with_balances'] else 0
                }
            })
            
        except Exception as e:
            logger.error(f"Error in AP validation: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/ar-report', methods=['GET'])
    @jwt_required()
    def get_ar_report():
        """Get accounts receivable aging report"""
        try:
            db = get_db()
            
            # First get the total AR amount
            total_ar_query = """
            SELECT SUM(Amount) as total_ar
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            
            total_ar_result = db.execute_query(total_ar_query)
            total_ar = float(total_ar_result[0]['total_ar']) if total_ar_result and total_ar_result[0]['total_ar'] else 0
            
            # Get AR aging buckets by invoice balance (not individual records)
            # Using source system bucket structure: Current (0-29), 30-60, 60-90, 90-120, 120+
            ar_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    ar.CustomerNo,
                    MIN(ar.Due) as Due,  -- Use earliest due date for the invoice
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL  -- Exclude non-invoice transactions
                GROUP BY ar.InvoiceNo, ar.CustomerNo
                HAVING SUM(ar.Amount) > 0.01  -- Only invoices with outstanding balance
            )
            SELECT 
                CASE 
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) < 30 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 30 AND 59 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 60 AND 89 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 90 AND 120 THEN '90-120'
                    WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
                END as AgingBucket,
                COUNT(*) as RecordCount,
                SUM(NetBalance) as TotalAmount
            FROM InvoiceBalances
            GROUP BY 
                CASE 
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) < 30 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 30 AND 59 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 60 AND 89 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 90 AND 120 THEN '90-120'
                    WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
                END
            """
            
            ar_results = db.execute_query(ar_query)
            
            # Calculate over 90 days directly from the data
            # Get a direct calculation of invoices over 90 days
            over_90_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL
                GROUP BY ar.InvoiceNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT SUM(NetBalance) as total_over_90
            FROM InvoiceBalances
            WHERE DATEDIFF(day, Due, GETDATE()) >= 90
            """
            
            over_90_result = db.execute_query(over_90_query)
            over_90_amount = float(over_90_result[0]['total_over_90']) if over_90_result and over_90_result[0]['total_over_90'] else 0
            over_90_percentage = (over_90_amount / total_ar * 100) if total_ar > 0 else 0
            
            # Get specific customer AR over 90 days
            customer_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance  -- Amounts already have correct signs
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                CASE 
                    WHEN c.Name = 'POLARIS INDUSTRIES' OR c.Name = 'POLARIS' OR c.Name = 'POLARIS INJECT MOLDING'
                    THEN 'POLARIS INDUSTRIES'
                    ELSE c.Name
                END as CustomerName,
                COUNT(ib.InvoiceNo) as InvoiceCount,
                SUM(ib.NetBalance) as TotalAmount,
                MIN(ib.Due) as OldestDueDate,
                MAX(DATEDIFF(day, ib.Due, GETDATE())) as MaxDaysOverdue
            FROM InvoiceBalances ib
            INNER JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE DATEDIFF(day, ib.Due, GETDATE()) >= 90  -- 90 days and over
                AND (
                    UPPER(c.Name) LIKE '%POLARIS%' OR
                    UPPER(c.Name) LIKE '%GREDE%' OR
                    UPPER(c.Name) LIKE '%OWENS%'
                )
            GROUP BY CASE 
                WHEN c.Name = 'POLARIS INDUSTRIES' OR c.Name = 'POLARIS' OR c.Name = 'POLARIS INJECT MOLDING'
                THEN 'POLARIS INDUSTRIES'
                ELSE c.Name
            END
            ORDER BY SUM(ib.NetBalance) DESC
            """
            
            customer_results = db.execute_query(customer_query)
            
            # Get aging breakdown for visualization - matching our actual buckets
            aging_summary = []
            for bucket in ['Current', '30-60', '60-90', '90-120', '120+']:
                row = next((r for r in ar_results if r['AgingBucket'] == bucket), None)
                aging_summary.append({
                    'bucket': bucket,
                    'amount': float(row['TotalAmount']) if row else 0,
                    'count': row['RecordCount'] if row else 0
                })
            
            # Add debug info to see what's in ar_results
            debug_buckets = {}
            for row in ar_results:
                debug_buckets[row['AgingBucket']] = float(row['TotalAmount'])
            
            return jsonify({
                'total_ar': float(total_ar),
                'over_90_amount': float(over_90_amount),
                'over_90_percentage': round(over_90_percentage, 1),
                'aging_summary': aging_summary,
                'debug_buckets': debug_buckets,  # Temporary debug info
                'specific_customers': [
                    {
                        'name': row['CustomerName'],
                        'amount': float(row['TotalAmount']),
                        'invoice_count': row['InvoiceCount'],
                        'oldest_due_date': row['OldestDueDate'].isoformat() if row['OldestDueDate'] else None,
                        'max_days_overdue': row['MaxDaysOverdue']
                    }
                    for row in customer_results
                ]
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'ar_report_error'
            }), 500

    @reports_bp.route('/departments/accounting/version', methods=['GET'])
    @jwt_required()
    def get_version():
        """Get version info to verify deployment"""
        return jsonify({
            'version': '2024-12-04-fix-ar-calculations',
            'ar_calculation': 'using SUM(Amount) directly',
            'polaris_merge': 'enabled',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @reports_bp.route('/departments/accounting/ar-debug', methods=['GET'])
    @jwt_required()
    def get_ar_debug():
        """Debug endpoint to analyze AR calculations"""
        try:
            db = get_db()
            
            # Get raw AR totals and check EntryType values
            raw_query = """
            SELECT 
                COUNT(*) as total_records,
                SUM(Amount) as raw_total,
                SUM(CASE WHEN EntryType = 'Invoice' THEN Amount ELSE 0 END) as invoice_total,
                SUM(CASE WHEN EntryType = 'Payment' THEN Amount ELSE 0 END) as payment_total,
                SUM(CASE WHEN EntryType = 'Voucher' THEN Amount ELSE 0 END) as voucher_total,
                SUM(CASE WHEN EntryType = 'Journal' THEN Amount ELSE 0 END) as journal_total,
                SUM(CASE WHEN EntryType = 'AR Journal' THEN Amount ELSE 0 END) as ar_journal_total,
                COUNT(DISTINCT InvoiceNo) as unique_invoices
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            
            # Get EntryType distribution
            entry_type_query = """
            SELECT 
                EntryType,
                COUNT(*) as count,
                SUM(Amount) as total_amount
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            GROUP BY EntryType
            ORDER BY COUNT(*) DESC
            """
            
            raw_results = db.execute_query(raw_query)
            raw_data = dict(raw_results[0]) if raw_results else {}
            
            entry_type_results = db.execute_query(entry_type_query)
            entry_types = [dict(row) for row in entry_type_results]
            
            # Get net AR using the same logic as the main query
            net_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    ar.Due,
                    SUM(ar.Amount) as NetBalance  -- Amounts already have correct signs
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo, ar.Due
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                COUNT(*) as open_invoices,
                SUM(NetBalance) as total_ar
            FROM InvoiceBalances
            """
            
            net_results = db.execute_query(net_query)
            net_data = dict(net_results[0]) if net_results else {}
            
            # Get sample of largest open balances
            sample_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    ar.Due,
                    SUM(ar.Amount) as NetBalance  -- Amounts already have correct signs
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo, ar.Due
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT TOP 10
                ib.CustomerNo,
                c.Name as CustomerName,
                ib.InvoiceNo,
                ib.NetBalance,
                ib.Due
            FROM InvoiceBalances ib
            LEFT JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            ORDER BY ib.NetBalance DESC
            """
            
            sample_results = db.execute_query(sample_query)
            
            return jsonify({
                'raw_totals': raw_data,
                'entry_types': entry_types,
                'net_ar': net_data,
                'calculated_net': float(raw_data.get('raw_total', 0)),  # Just use the raw total since amounts have correct signs
                'largest_open_balances': [dict(row) for row in sample_results],
                'message': 'AR Debug Information'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'ar_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/customer-ar-debug', methods=['GET'])
    @jwt_required()
    def get_customer_ar_debug():
        """Debug specific customer AR over 90 days"""
        try:
            db = get_db()
            
            # Get all customers matching our criteria
            customer_list_query = """
            SELECT DISTINCT c.Number, c.Name
            FROM ben002.Customer c
            WHERE UPPER(c.Name) LIKE '%POLARIS%' 
               OR UPPER(c.Name) LIKE '%GREDE%' 
               OR UPPER(c.Name) LIKE '%OWENS%'
            ORDER BY c.Name
            """
            
            customers = db.execute_query(customer_list_query)
            
            # Get AR balances for these customers
            balance_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                c.Name as CustomerName,
                COUNT(CASE WHEN DATEDIFF(day, ib.Due, GETDATE()) >= 90 THEN 1 END) as InvoicesOver90,
                SUM(CASE WHEN DATEDIFF(day, ib.Due, GETDATE()) >= 90 THEN ib.NetBalance ELSE 0 END) as AmountOver90,
                COUNT(*) as TotalOpenInvoices,
                SUM(ib.NetBalance) as TotalARBalance
            FROM InvoiceBalances ib
            INNER JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE UPPER(c.Name) LIKE '%POLARIS%' 
               OR UPPER(c.Name) LIKE '%GREDE%' 
               OR UPPER(c.Name) LIKE '%OWENS%'
            GROUP BY c.Name
            ORDER BY SUM(CASE WHEN DATEDIFF(day, ib.Due, GETDATE()) > 90 THEN ib.NetBalance ELSE 0 END) DESC
            """
            
            balances = db.execute_query(balance_query)
            
            # Get specific invoices over 90 days
            detail_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT TOP 30
                c.Name as CustomerName,
                ib.InvoiceNo,
                ib.Due,
                DATEDIFF(day, ib.Due, GETDATE()) as DaysOverdue,
                ib.NetBalance
            FROM InvoiceBalances ib
            INNER JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE DATEDIFF(day, ib.Due, GETDATE()) >= 90
                AND (UPPER(c.Name) LIKE '%POLARIS%' 
                     OR UPPER(c.Name) LIKE '%GREDE%' 
                     OR UPPER(c.Name) LIKE '%OWENS%')
            ORDER BY ib.NetBalance DESC
            """
            
            details = db.execute_query(detail_query)
            
            return jsonify({
                'customer_list': [dict(row) for row in customers],
                'customer_balances': [dict(row) for row in balances],
                'invoice_details': [dict(row) for row in details]
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'customer_ar_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/ar-over90-full', methods=['GET'])
    @jwt_required()
    def get_ar_over90_full():
        """Get ALL invoices over 90 days for detailed analysis"""
        try:
            db = get_db()
            
            # Get all invoices over 90 days with details
            query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    ar.CustomerNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL
                GROUP BY ar.InvoiceNo, ar.CustomerNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                ib.InvoiceNo,
                ib.CustomerNo,
                c.Name as CustomerName,
                ib.Due,
                DATEDIFF(day, ib.Due, GETDATE()) as DaysOld,
                ib.NetBalance
            FROM InvoiceBalances ib
            LEFT JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE DATEDIFF(day, ib.Due, GETDATE()) >= 90
            ORDER BY DATEDIFF(day, ib.Due, GETDATE()) DESC, ib.NetBalance DESC
            """
            
            results = db.execute_query(query)
            
            # Calculate totals by days old ranges
            totals = {
                '90-120': 0,
                '120+': 0,
                'total': 0
            }
            
            invoices = []
            for row in results:
                invoice = dict(row)
                amount = float(invoice.get('NetBalance', 0))
                days = int(invoice.get('DaysOld', 0))
                
                if 90 <= days <= 120:
                    totals['90-120'] += amount
                elif days > 120:
                    totals['120+'] += amount
                totals['total'] += amount
                
                invoices.append(invoice)
            
            return jsonify({
                'invoices': invoices,  # Return ALL invoices
                'totals': totals,
                'total_count': len(results)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'ar_over90_full_error'
            }), 500

    @reports_bp.route('/departments/accounting/over90-debug', methods=['GET'])
    @jwt_required()
    def get_over90_debug():
        """Debug over 90 days AR calculation"""
        try:
            db = get_db()
            
            # Get all invoices over 90 days with details
            query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    ar.CustomerNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL
                GROUP BY ar.InvoiceNo, ar.CustomerNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                ib.InvoiceNo,
                ib.CustomerNo,
                c.Name as CustomerName,
                ib.Due,
                DATEDIFF(day, ib.Due, GETDATE()) as DaysOld,
                ib.NetBalance
            FROM InvoiceBalances ib
            LEFT JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE DATEDIFF(day, ib.Due, GETDATE()) >= 90
            ORDER BY ib.NetBalance DESC
            """
            
            results = db.execute_query(query)
            
            # Calculate totals by days old ranges
            totals = {
                '90-120': 0,
                '120+': 0,
                'total': 0
            }
            
            invoices = []
            for row in results:
                invoice = dict(row)
                amount = float(invoice.get('NetBalance', 0))
                days = int(invoice.get('DaysOld', 0))
                
                if 90 <= days <= 120:
                    totals['90-120'] += amount
                elif days > 120:
                    totals['120+'] += amount
                totals['total'] += amount
                
                invoices.append(invoice)
            
            return jsonify({
                'invoices': invoices[:100],  # Return top 100
                'totals': totals,
                'total_count': len(results)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'over90_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/ar-aging-debug', methods=['GET'])
    @jwt_required()
    def get_ar_aging_debug():
        """Comprehensive AR aging debug endpoint"""
        try:
            db = get_db()
            
            # 1. Get total AR same way as main report
            total_query = """
            SELECT SUM(Amount) as total_ar
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            total_result = db.execute_query(total_query)
            total_ar = float(total_result[0]['total_ar']) if total_result and total_result[0]['total_ar'] else 0
            
            # 2. Get aging buckets by invoice balance (matching main report)
            buckets_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    ar.CustomerNo,
                    MIN(ar.Due) as Due,  -- Use earliest due date for the invoice
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL  -- Exclude non-invoice transactions
                GROUP BY ar.InvoiceNo, ar.CustomerNo
                HAVING SUM(ar.Amount) > 0.01  -- Only invoices with outstanding balance
            )
            SELECT 
                CASE 
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30 THEN '1-30'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 31 AND 60 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 91 AND 120 THEN '90-120'
                    WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
                END as AgingBucket,
                COUNT(*) as RecordCount,
                SUM(NetBalance) as TotalAmount
            FROM InvoiceBalances
            GROUP BY 
                CASE 
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30 THEN '1-30'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 31 AND 60 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 91 AND 120 THEN '90-120'
                    WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
                END
            """
            bucket_results = db.execute_query(buckets_query)
            
            # Calculate bucket totals
            buckets = {}
            bucket_sum = 0
            for row in bucket_results:
                buckets[row['AgingBucket']] = {
                    'amount': float(row['TotalAmount']),
                    'count': row['RecordCount']
                }
                bucket_sum += float(row['TotalAmount'])
            
            # Calculate over 90 days
            over_90 = sum(buckets.get(b, {}).get('amount', 0) for b in ['90-120', '120+'])
            
            # 3. Check for NULL due dates
            null_due_query = """
            SELECT COUNT(*) as count, SUM(Amount) as amount
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
                AND Due IS NULL
            """
            null_due_result = db.execute_query(null_due_query)
            null_due_data = dict(null_due_result[0]) if null_due_result else {}
            
            # 4. Get EntryType breakdown
            entry_type_query = """
            SELECT EntryType, COUNT(*) as count, SUM(Amount) as amount
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            GROUP BY EntryType
            ORDER BY ABS(SUM(Amount)) DESC
            """
            entry_type_results = db.execute_query(entry_type_query)
            entry_types = [dict(row) for row in entry_type_results]
            
            # 5. Sample records around 90 days
            sample_90_query = """
            SELECT TOP 20
                InvoiceNo,
                CustomerNo,
                EntryType,
                Amount,
                Due,
                DATEDIFF(day, Due, GETDATE()) as DaysOld
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
                AND DATEDIFF(day, Due, GETDATE()) BETWEEN 85 AND 95
            ORDER BY Amount DESC
            """
            sample_90_results = db.execute_query(sample_90_query)
            
            # 6. Your expected values from database pull
            expected_total = 1697050.59
            expected_current = 389448.08
            expected_1_30 = 312764.25
            expected_31_60 = 173548.60
            expected_61_90 = 27931.75
            expected_over_90 = 201479.00  # Your actual database pull value
            
            return jsonify({
                'calculated': {
                    'total_ar': total_ar,
                    'bucket_sum': bucket_sum,
                    'difference': total_ar - bucket_sum,
                    'over_90_amount': over_90,
                    'over_90_percentage': round((over_90 / total_ar * 100), 1) if total_ar > 0 else 0
                },
                'buckets': buckets,
                'null_due_dates': null_due_data,
                'entry_types': entry_types,
                'sample_90_days': [dict(row) for row in sample_90_results],
                'expected': {
                    'total_ar': expected_total,
                    'current': expected_current,
                    '1-30': expected_1_30,
                    '31-60': expected_31_60,
                    '61-90': expected_61_90,
                    'over_90': expected_over_90,
                    'over_90_percentage': round((expected_over_90 / expected_total * 100), 1)
                },
                'differences': {
                    'total_ar_diff': total_ar - expected_total,
                    'current_diff': buckets.get('Current', {}).get('amount', 0) - expected_current,
                    '1-30_diff': buckets.get('1-30', {}).get('amount', 0) - expected_1_30,
                    '30-60_diff': buckets.get('30-60', {}).get('amount', 0) - expected_31_60,
                    '60-90_diff': buckets.get('60-90', {}).get('amount', 0) - expected_61_90,
                    'over_90_diff': over_90 - expected_over_90
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'ar_aging_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/expense-debug', methods=['GET'])
    @jwt_required()
    def get_expense_debug():
        """Debug endpoint to analyze expense calculations"""
        try:
            db = get_db()
            
            # Get detailed breakdown for a specific month
            month = request.args.get('month', '2025-07')  # Default to July 2025
            
            # Get expense breakdown by category
            breakdown_query = f"""
            SELECT 
                COUNT(*) as invoice_count,
                SUM(COALESCE(PartsCost, 0)) as parts_cost,
                SUM(COALESCE(LaborCost, 0)) as labor_cost,
                SUM(COALESCE(EquipmentCost, 0)) as equipment_cost,
                SUM(COALESCE(RentalCost, 0)) as rental_cost,
                SUM(COALESCE(MiscCost, 0)) as misc_cost,
                SUM(COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + 
                    COALESCE(EquipmentCost, 0) + COALESCE(RentalCost, 0) + 
                    COALESCE(MiscCost, 0)) as total_cost,
                -- Also check revenue fields for comparison
                SUM(GrandTotal) as total_revenue,
                SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as parts_revenue,
                SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as labor_revenue
            FROM ben002.InvoiceReg
            WHERE FORMAT(InvoiceDate, 'yyyy-MM') = '{month}'
            """
            
            result = db.execute_query(breakdown_query)
            
            if result:
                breakdown = result[0]
                
                # Get sample invoices with high costs
                sample_query = f"""
                SELECT TOP 10
                    InvoiceNo,
                    InvoiceDate,
                    BillToName,
                    SaleDept,
                    SaleCode,
                    PartsCost,
                    LaborCost,
                    EquipmentCost,
                    RentalCost,
                    MiscCost,
                    (COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + 
                     COALESCE(EquipmentCost, 0) + COALESCE(RentalCost, 0) + 
                     COALESCE(MiscCost, 0)) as total_cost,
                    GrandTotal as revenue
                FROM ben002.InvoiceReg
                WHERE FORMAT(InvoiceDate, 'yyyy-MM') = '{month}'
                ORDER BY (COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + 
                         COALESCE(EquipmentCost, 0) + COALESCE(RentalCost, 0) + 
                         COALESCE(MiscCost, 0)) DESC
                """
                
                samples = db.execute_query(sample_query)
                
                # Get monthly trend with breakdown
                trend_query = """
                SELECT 
                    FORMAT(InvoiceDate, 'yyyy-MM') as month,
                    COUNT(*) as invoices,
                    SUM(COALESCE(PartsCost, 0)) as parts,
                    SUM(COALESCE(LaborCost, 0)) as labor,
                    SUM(COALESCE(EquipmentCost, 0)) as equipment,
                    SUM(COALESCE(RentalCost, 0)) as rental,
                    SUM(COALESCE(MiscCost, 0)) as misc,
                    SUM(COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + 
                        COALESCE(EquipmentCost, 0) + COALESCE(RentalCost, 0) + 
                        COALESCE(MiscCost, 0)) as total
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= '2025-03-01'
                GROUP BY FORMAT(InvoiceDate, 'yyyy-MM')
                ORDER BY FORMAT(InvoiceDate, 'yyyy-MM')
                """
                
                trend = db.execute_query(trend_query)
                
                return jsonify({
                    'month': month,
                    'summary': {
                        'invoice_count': int(breakdown['invoice_count']),
                        'parts_cost': float(breakdown['parts_cost'] or 0),
                        'labor_cost': float(breakdown['labor_cost'] or 0),
                        'equipment_cost': float(breakdown['equipment_cost'] or 0),
                        'rental_cost': float(breakdown['rental_cost'] or 0),
                        'misc_cost': float(breakdown['misc_cost'] or 0),
                        'total_cost': float(breakdown['total_cost'] or 0),
                        'total_revenue': float(breakdown['total_revenue'] or 0),
                        'parts_revenue': float(breakdown['parts_revenue'] or 0),
                        'labor_revenue': float(breakdown['labor_revenue'] or 0)
                    },
                    'sample_invoices': [{
                        'invoice_no': row['InvoiceNo'],
                        'date': row['InvoiceDate'].strftime('%Y-%m-%d') if row['InvoiceDate'] else None,
                        'customer': row['BillToName'],
                        'department': row['SaleDept'],
                        'sale_code': row['SaleCode'],
                        'parts_cost': float(row['PartsCost'] or 0),
                        'labor_cost': float(row['LaborCost'] or 0),
                        'equipment_cost': float(row['EquipmentCost'] or 0),
                        'rental_cost': float(row['RentalCost'] or 0),
                        'misc_cost': float(row['MiscCost'] or 0),
                        'total_cost': float(row['total_cost'] or 0),
                        'revenue': float(row['revenue'] or 0)
                    } for row in samples],
                    'monthly_trend': [{
                        'month': row['month'],
                        'invoices': int(row['invoices']),
                        'parts': float(row['parts'] or 0),
                        'labor': float(row['labor'] or 0),
                        'equipment': float(row['equipment'] or 0),
                        'rental': float(row['rental'] or 0),
                        'misc': float(row['misc'] or 0),
                        'total': float(row['total'] or 0)
                    } for row in trend]
                })
            
            return jsonify({
                'error': 'No data found for the specified month'
            }), 404
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'expense_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/find-expense-tables', methods=['GET'])
    @jwt_required()
    def find_expense_tables():
        """Help identify G&A expense tables in the database"""
        try:
            db = get_db()
            
            # Query to find potential expense-related tables
            table_query = """
            SELECT 
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ben002'
            AND (
                TABLE_NAME LIKE '%expense%'
                OR TABLE_NAME LIKE '%payable%'
                OR TABLE_NAME LIKE '%AP%'
                OR TABLE_NAME LIKE '%GL%'
                OR TABLE_NAME LIKE '%ledger%'
                OR TABLE_NAME LIKE '%vendor%'
                OR TABLE_NAME LIKE '%payroll%'
                OR TABLE_NAME LIKE '%salary%'
                OR TABLE_NAME LIKE '%wage%'
                OR TABLE_NAME LIKE '%payment%'
                OR TABLE_NAME LIKE '%disbursement%'
                OR TABLE_NAME LIKE '%purchase%'
                OR TABLE_NAME LIKE '%journal%'
                OR TABLE_NAME LIKE '%transaction%'
            )
            ORDER BY TABLE_NAME
            """
            
            tables = db.execute_query(table_query)
            
            # For each table, get column information
            table_details = []
            for table in tables[:20]:  # Limit to first 20 tables
                table_name = table['TABLE_NAME']
                
                column_query = f"""
                SELECT TOP 10
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = db.execute_query(column_query)
                
                # Try to get row count
                try:
                    count_query = f"SELECT COUNT(*) as row_count FROM ben002.{table_name}"
                    count_result = db.execute_query(count_query)
                    row_count = count_result[0]['row_count'] if count_result else 0
                except:
                    row_count = -1
                
                table_details.append({
                    'table_name': table_name,
                    'row_count': row_count,
                    'columns': [{
                        'name': col['COLUMN_NAME'],
                        'type': col['DATA_TYPE'],
                        'nullable': col['IS_NULLABLE'] == 'YES'
                    } for col in columns]
                })
            
            return jsonify({
                'potential_tables': table_details,
                'message': 'Found potential G&A expense tables'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'table_discovery_error'
            }), 500

    @reports_bp.route('/departments/rental/monthly-revenue', methods=['GET'])
    @jwt_required()
    def get_rental_monthly_revenue():
        """Get monthly rental revenue with gross margin"""
        try:
            db = get_db()
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            # Get monthly rental revenue and cost data
            query = """
            WITH MonthlyData AS (
                SELECT 
                    YEAR(InvoiceDate) as year,
                    MONTH(InvoiceDate) as month,
                    SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as rental_revenue,
                    SUM(COALESCE(RentalCost, 0)) as rental_cost
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
                    AND (SaleCode LIKE 'RENT%' OR (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0)
                GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            )
            SELECT 
                year,
                month,
                rental_revenue,
                rental_cost
            FROM MonthlyData
            ORDER BY year, month
            """
            
            results = db.execute_query(query)
            
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            # Convert results to dictionary for easy lookup
            data_by_month = {}
            for row in results:
                year = row['year']
                month = row['month']
                rental_revenue = float(row['rental_revenue'] or 0)
                rental_cost = float(row['rental_cost'] or 0)
                
                # Check if this is current month or future
                is_current_or_future = (year > current_year) or (year == current_year and month >= current_month)
                
                # Calculate gross margin percentage only for historical months
                margin_percentage = None
                if not is_current_or_future and rental_revenue > 0:
                    margin_percentage = round(((rental_revenue - rental_cost) / rental_revenue) * 100, 1)
                
                month_key = f"{year}-{month}"
                data_by_month[month_key] = {
                    'month': month_names[month - 1],
                    'amount': rental_revenue,
                    'cost': rental_cost,
                    'margin': margin_percentage
                }
            
            # Generate full 12-month range (6 months back, current month, 5 months forward)
            monthly_data = []
            current_date = datetime.now()
            
            for i in range(-6, 6):  # -6 to +5 gives us 12 months total
                # Calculate the target date
                target_date = current_date + timedelta(days=i * 30.5)  # Approximate month offset
                target_month = (current_date.month + i - 1) % 12 + 1
                target_year = current_date.year + (current_date.month + i - 1) // 12
                
                month_key = f"{target_year}-{target_month}"
                
                if month_key in data_by_month:
                    monthly_data.append(data_by_month[month_key])
                else:
                    # Add empty data for missing months (including future)
                    monthly_data.append({
                        'month': month_names[target_month - 1],
                        'amount': 0,
                        'cost': 0,
                        'margin': None
                    })
            
            return jsonify({
                'monthlyRentalRevenue': monthly_data
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_monthly_revenue_error'
            }), 500

    @reports_bp.route('/departments/rental/debug-revenue', methods=['GET'])
    @jwt_required()
    def debug_rental_revenue():
        """Debug endpoint to check rental revenue data"""
        try:
            db = get_db()
            
            # First check what columns exist in InvoiceReg
            columns_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'InvoiceReg' 
            AND TABLE_SCHEMA = 'ben002'
            AND (COLUMN_NAME LIKE '%dept%' OR COLUMN_NAME LIKE '%Dept%' OR COLUMN_NAME = 'SaleCode')
            ORDER BY COLUMN_NAME
            """
            
            columns_result = db.execute_query(columns_query)
            column_names = [row['COLUMN_NAME'] for row in columns_result]
            
            # Check SaleCodes
            dept_query = """
            SELECT DISTINCT SaleCode, COUNT(*) as count
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
            GROUP BY SaleCode
            ORDER BY SaleCode
            """
            
            dept_results = db.execute_query(dept_query)
            departments = [{'salecode': row['SaleCode'], 'count': row['count']} for row in dept_results]
            
            # Check rental data with different approaches
            rental_queries = {
                
                'by_salecode': """
                SELECT 
                    YEAR(InvoiceDate) as year,
                    MONTH(InvoiceDate) as month,
                    SaleCode,
                    COUNT(*) as invoice_count,
                    SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as rental_revenue
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
                    AND SaleCode IN ('RENTR', 'RENTRS', 'RENTPM')
                GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate), SaleCode
                ORDER BY year, month, SaleCode
                """,
                
                'any_rental_revenue': """
                SELECT TOP 10
                    InvoiceDate,
                    Department,
                    SaleCode,
                    RentalTaxable,
                    RentalNonTax,
                    RentalCost,
                    GrandTotal
                FROM ben002.InvoiceReg
                WHERE (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
                ORDER BY InvoiceDate DESC
                """,
                
                'sample_invoices': """
                SELECT TOP 10
                    InvoiceDate,
                    Department,
                    SaleCode,
                    LaborTaxable,
                    LaborNonTax,
                    PartsTaxable,
                    PartsNonTax,
                    RentalTaxable,
                    RentalNonTax,
                    EquipmentTaxable,
                    EquipmentNonTax,
                    GrandTotal
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= DATEADD(month, -1, GETDATE())
                ORDER BY InvoiceDate DESC
                """
            }
            
            results = {}
            for key, query in rental_queries.items():
                try:
                    result = db.execute_query(query)
                    if key in ['by_department', 'by_salecode']:
                        results[key] = [dict(row) for row in result]
                    else:
                        results[key] = [dict(row) for row in result]
                except Exception as e:
                    results[key] = f"Error: {str(e)}"
            
            return jsonify({
                'columns': column_names,
                'salecodes': departments,
                'rental_data': results,
                'message': 'Debug data for rental revenue troubleshooting'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'debug_error'
            }), 500

    @reports_bp.route('/departments/rental/top-customers', methods=['GET'])
    @jwt_required()
    def get_rental_top_customers():
        """Get top 10 rental customers by revenue"""
        try:
            db = get_db()
            
            # Get top 10 rental customers by total revenue with current rental count
            # Combine POLARIS INDUSTRIES and POLARIS as one customer
            query = """
            WITH RentalRevenue AS (
                SELECT 
                    CASE 
                        WHEN BillToName = 'POLARIS INDUSTRIES' OR BillToName = 'POLARIS' 
                        THEN 'POLARIS INDUSTRIES'
                        ELSE BillToName
                    END as customer_name,
                    COUNT(DISTINCT InvoiceNo) as invoice_count,
                    SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as total_revenue,
                    MAX(InvoiceDate) as last_invoice_date
                FROM ben002.InvoiceReg
                WHERE (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
                    AND BillToName IS NOT NULL
                    AND BillToName != ''
                    AND BillToName NOT LIKE '%RENTAL FLEET%'
                    AND BillToName NOT LIKE '%EXPENSE%'
                    AND BillToName NOT LIKE '%INTERNAL%'
                    AND YEAR(InvoiceDate) = YEAR(GETDATE())  -- YTD filter
                GROUP BY CASE 
                    WHEN BillToName = 'POLARIS INDUSTRIES' OR BillToName = 'POLARIS' 
                    THEN 'POLARIS INDUSTRIES'
                    ELSE BillToName
                END
            ),
            RankedCustomers AS (
                SELECT 
                    customer_name,
                    invoice_count,
                    total_revenue,
                    last_invoice_date,
                    ROW_NUMBER() OVER (ORDER BY total_revenue DESC) as rank
                FROM RentalRevenue
                WHERE total_revenue > 0
            ),
            -- Get current rental counts from RentalHistory for current month
            CurrentRentals AS (
                SELECT 
                    CASE 
                        WHEN c.Name = 'POLARIS INDUSTRIES' OR c.Name = 'POLARIS' 
                        THEN 'POLARIS INDUSTRIES'
                        ELSE c.Name
                    END as customer_name,
                    COUNT(DISTINCT rh.SerialNo) as units_on_rent
                FROM ben002.RentalHistory rh
                INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
                INNER JOIN ben002.Customer c ON e.CustomerNo = c.Number
                WHERE rh.Year = YEAR(GETDATE()) 
                    AND rh.Month = MONTH(GETDATE())
                    AND rh.DaysRented > 0
                    AND e.CustomerNo IS NOT NULL
                    AND e.CustomerNo != ''
                GROUP BY CASE 
                    WHEN c.Name = 'POLARIS INDUSTRIES' OR c.Name = 'POLARIS' 
                    THEN 'POLARIS INDUSTRIES'
                    ELSE c.Name
                END
            )
            SELECT TOP 10
                rc.rank,
                rc.customer_name,
                rc.invoice_count,
                rc.total_revenue,
                rc.last_invoice_date,
                DATEDIFF(day, rc.last_invoice_date, GETDATE()) as days_since_last_invoice,
                COALESCE(cr.units_on_rent, 0) as units_on_rent
            FROM RankedCustomers rc
            LEFT JOIN CurrentRentals cr ON rc.customer_name = cr.customer_name
            ORDER BY rc.rank
            """
            
            results = db.execute_query(query)
            
            # Calculate total YTD revenue for percentage calculation
            total_query = """
            SELECT SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as total
            FROM ben002.InvoiceReg
            WHERE (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
                AND BillToName NOT LIKE '%RENTAL FLEET%'
                AND BillToName NOT LIKE '%EXPENSE%'
                AND BillToName NOT LIKE '%INTERNAL%'
                AND YEAR(InvoiceDate) = YEAR(GETDATE())  -- YTD filter
            """
            
            total_result = db.execute_query(total_query)
            total_revenue = float(total_result[0]['total'] or 0)
            
            top_customers = []
            for row in results:
                revenue = float(row['total_revenue'] or 0)
                percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
                
                top_customers.append({
                    'rank': row['rank'],
                    'name': row['customer_name'],
                    'invoice_count': row['invoice_count'],
                    'revenue': revenue,
                    'percentage': round(percentage, 1),
                    'last_invoice_date': row['last_invoice_date'].strftime('%Y-%m-%d') if row['last_invoice_date'] else None,
                    'days_since_last': row['days_since_last_invoice'],
                    'units_on_rent': row['units_on_rent']
                })
            
            return jsonify({
                'top_customers': top_customers,
                'total_revenue': total_revenue
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_top_customers_error'
            }), 500

    @reports_bp.route('/departments/rental/units-on-rent', methods=['GET'])
    @jwt_required()
    def get_units_on_rent():
        """Get count of units currently on rent based on RentalHistory"""
        try:
            db = get_db()
            
            # Count distinct units with rental activity in current month
            # This directly shows what's on rent regardless of ownership
            query = """
            SELECT COUNT(DISTINCT SerialNo) as units_on_rent
            FROM ben002.RentalHistory
            WHERE Year = YEAR(GETDATE()) 
                AND Month = MONTH(GETDATE())
                AND DaysRented > 0
                AND RentAmount > 0
                AND DeletionTime IS NULL
            """
            
            result = db.execute_query(query)
            units_on_rent = result[0]['units_on_rent'] if result else 0
            
            return jsonify({
                'units_on_rent': units_on_rent
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_on_rent_error'
            }), 500
    
    @reports_bp.route('/departments/rental/units-on-rent-detail', methods=['GET'])
    @jwt_required()
    def get_units_on_rent_detail():
        """Get detailed list of units currently on rent with customer information"""
        try:
            db = get_db()
            
            # Get units on rent from RentalHistory with equipment details
            query = """
            SELECT 
                rh.SerialNo,
                rh.DaysRented,
                rh.RentAmount,
                e.UnitNo,
                e.Make,
                e.Model,
                e.ModelYear,
                e.Location,
                e.DayRent,
                e.WeekRent,
                e.MonthRent,
                e.CustomerNo,
                c.Name as CustomerName
            FROM ben002.RentalHistory rh
            INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
                AND rh.RentAmount > 0
                AND rh.DeletionTime IS NULL
            ORDER BY c.Name, e.Make, e.Model, e.UnitNo
            """
            
            results = db.execute_query(query)
            
            units_detail = []
            for row in results:
                # Handle customer info - could be from Equipment owner or from rental activity
                customer_name = row['CustomerName']
                if not customer_name or customer_name == 'RENTAL FLEET - EXPENSE':
                    customer_name = 'Rental Customer'
                    
                units_detail.append({
                    'customer_name': customer_name,
                    'customer_no': row['CustomerNo'] or '',
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'make': row['Make'],
                    'model': row['Model'],
                    'model_year': row['ModelYear'],
                    'location': row['Location'],
                    'days_rented': row['DaysRented'],
                    'rent_amount': float(row['RentAmount'] or 0),
                    'day_rent': float(row['DayRent'] or 0),
                    'week_rent': float(row['WeekRent'] or 0),
                    'month_rent': float(row['MonthRent'] or 0)
                })
            
            return jsonify({
                'units': units_detail,
                'count': len(units_detail)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_on_rent_detail_error'
            }), 500

    @reports_bp.route('/departments/rental/units-on-hold', methods=['GET'])
    @jwt_required()
    def get_units_on_hold():
        """Get count of units currently on hold"""
        try:
            db = get_db()
            
            # Count units with RentalStatus = 'Hold'
            query = """
            SELECT COUNT(*) as units_on_hold
            FROM ben002.Equipment
            WHERE RentalStatus = 'Hold'
            """
            
            result = db.execute_query(query)
            units_on_hold = result[0]['units_on_hold'] if result else 0
            
            return jsonify({
                'units_on_hold': units_on_hold
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_on_hold_error'
            }), 500

    @reports_bp.route('/departments/rental/units-on-hold-detail', methods=['GET'])
    @jwt_required()
    def get_units_on_hold_detail():
        """Get detailed list of units currently on hold"""
        try:
            db = get_db()
            
            # Get detailed information for units on hold
            query = """
            SELECT 
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                e.ModelYear,
                e.Location,
                e.Cost,
                e.Sell as ListPrice,
                e.DayRent,
                e.WeekRent,
                e.MonthRent,
                e.RentalStatus,
                -- Get customer info if assigned
                e.CustomerNo,
                c.Name as CustomerName
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE e.RentalStatus = 'Hold'
            ORDER BY e.Make, e.Model, e.UnitNo
            """
            
            results = db.execute_query(query)
            
            units_detail = []
            for row in results:
                units_detail.append({
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'make': row['Make'],
                    'model': row['Model'],
                    'model_year': row['ModelYear'],
                    'location': row['Location'],
                    'cost': float(row['Cost'] or 0),
                    'list_price': float(row['ListPrice'] or 0),
                    'day_rent': float(row['DayRent'] or 0),
                    'week_rent': float(row['WeekRent'] or 0),
                    'month_rent': float(row['MonthRent'] or 0),
                    'rental_status': row['RentalStatus'],
                    'customer_no': row['CustomerNo'] or '',
                    'customer_name': row['CustomerName'] or 'No Customer Assigned'
                })
            
            return jsonify({
                'units': units_detail,
                'count': len(units_detail)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_on_hold_detail_error'
            }), 500
    
    @reports_bp.route('/departments/rental/equipment-report', methods=['GET'])
    @jwt_required()
    def get_rental_equipment_report():
        """Get all equipment associated with the rental department"""
        try:
            db = get_db()
            
            # Get equipment owned by rental department (900006)
            query = """
            WITH RentalEquipment AS (
                SELECT 
                    e.UnitNo,
                    e.SerialNo,
                    e.Make,
                    e.Model,
                    e.ModelYear,
                    e.RentalStatus,
                    e.Location,
                    e.Cost,
                    e.Retail as ListPrice,
                    e.DayRent,
                    e.WeekRent,
                    e.MonthRent,
                    e.CustomerNo,
                    e.Customer as CustomerFlag,
                    e.LastHourMeter,
                    e.LastHourMeterDate,
                    e.RentalYTD,
                    e.RentalITD,
                    c.Name as CurrentCustomer,
                    -- Check if currently on rent
                    CASE 
                        WHEN rh.SerialNo IS NOT NULL THEN 'On Rent'
                        WHEN e.RentalStatus = 'On Hold' THEN 'On Hold'
                        WHEN e.RentalStatus = 'Ready To Rent' THEN 'Available'
                        ELSE COALESCE(e.RentalStatus, 'Unknown')
                    END as CurrentStatus,
                    rh.DaysRented as CurrentMonthDays,
                    rh.RentAmount as CurrentMonthRevenue
                FROM ben002.Equipment e
                LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
                LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
                    AND rh.Year = YEAR(GETDATE()) 
                    AND rh.Month = MONTH(GETDATE())
                    AND rh.DaysRented > 0
                    AND rh.DeletionTime IS NULL
                WHERE (e.CustomerNo = '900006'  -- RENTAL FLEET - EXPENSE
                    OR e.InventoryDept = 40  -- Rental department
                    OR e.RentalStatus IS NOT NULL)
                    AND UPPER(e.Make) IN ('LINDE', 'KOMATSU', 'BENDI', 'CLARK', 'CROWN', 'UNICARRIERS')
            )
            SELECT 
                UnitNo,
                SerialNo,
                Make,
                Model,
                ModelYear,
                CurrentStatus,
                RentalStatus,
                Location,
                Cost,
                ListPrice,
                DayRent,
                WeekRent,
                MonthRent,
                CustomerNo,
                CurrentCustomer,
                LastHourMeter,
                LastHourMeterDate,
                RentalYTD,
                RentalITD,
                CurrentMonthDays,
                CurrentMonthRevenue,
                -- Calculate utilization
                CASE 
                    WHEN CurrentStatus = 'On Rent' THEN 100
                    WHEN CurrentStatus = 'Available' THEN 0
                    ELSE NULL
                END as UtilizationPercent
            FROM RentalEquipment
            ORDER BY CurrentStatus DESC, UnitNo
            """
            
            results = db.execute_query(query)
            
            # Get summary statistics
            summary_query = """
            SELECT 
                COUNT(*) as total_units,
                COUNT(CASE WHEN e.CustomerNo = '900006' THEN 1 END) as fleet_owned_units,
                COUNT(CASE WHEN rh.SerialNo IS NOT NULL THEN 1 END) as units_on_rent,
                COUNT(CASE WHEN e.RentalStatus = 'Ready To Rent' THEN 1 END) as available_units,
                COUNT(CASE WHEN e.RentalStatus = 'On Hold' THEN 1 END) as on_hold_units,
                SUM(e.Cost) as total_fleet_value,
                SUM(e.RentalYTD) as total_ytd_revenue,
                SUM(rh.RentAmount) as current_month_revenue
            FROM ben002.Equipment e
            LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
                AND rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
                AND rh.DeletionTime IS NULL
            WHERE (e.CustomerNo = '900006'
                OR e.InventoryDept = 40
                OR e.RentalStatus IS NOT NULL)
                AND UPPER(e.Make) IN ('LINDE', 'KOMATSU', 'BENDI', 'CLARK', 'CROWN', 'UNICARRIERS')
            """
            
            summary_result = db.execute_query(summary_query)
            summary = summary_result[0] if summary_result else {}
            
            # Get breakdown by make
            make_breakdown_query = """
            SELECT 
                e.Make,
                COUNT(*) as unit_count,
                COUNT(CASE WHEN rh.SerialNo IS NOT NULL THEN 1 END) as on_rent_count,
                SUM(e.Cost) as total_value,
                SUM(e.RentalYTD) as ytd_revenue
            FROM ben002.Equipment e
            LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
                AND rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
                AND rh.DeletionTime IS NULL
            WHERE (e.CustomerNo = '900006' OR e.InventoryDept = 40 OR e.RentalStatus IS NOT NULL)
                AND UPPER(e.Make) IN ('LINDE', 'KOMATSU', 'BENDI', 'CLARK', 'CROWN', 'UNICARRIERS')
            GROUP BY e.Make
            ORDER BY unit_count DESC
            """
            
            make_breakdown = db.execute_query(make_breakdown_query)
            
            return jsonify({
                'equipment': results,
                'summary': summary,
                'make_breakdown': make_breakdown
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_equipment_report_error'
            }), 500

    @reports_bp.route('/departments/rental/rental-fleet-diagnostic', methods=['GET'])
    @jwt_required()
    def get_rental_fleet_diagnostic():
        """Diagnostic to understand the rental fleet ownership"""
        try:
            db = get_db()
            
            diagnostics = {}
            
            # 1. Count total equipment owned by RENTAL FLEET (900006)
            query1 = """
            SELECT 
                COUNT(*) as total_fleet_units,
                COUNT(CASE WHEN RentalStatus = 'Ready To Rent' THEN 1 END) as ready_to_rent,
                COUNT(CASE WHEN RentalStatus = 'Hold' THEN 1 END) as on_hold,
                COUNT(CASE WHEN RentalStatus IS NULL THEN 1 END) as null_status
            FROM ben002.Equipment
            WHERE CustomerNo = '900006'
            """
            diagnostics['rental_fleet_owned'] = db.execute_query(query1)
            
            # 2. Get rental activity for fleet equipment
            query2 = """
            SELECT 
                COUNT(DISTINCT e.SerialNo) as units_with_activity,
                COUNT(DISTINCT CASE WHEN rh.SerialNo IS NOT NULL THEN e.SerialNo END) as units_in_rental_history
            FROM ben002.Equipment e
            LEFT JOIN (
                SELECT DISTINCT SerialNo 
                FROM ben002.RentalHistory 
                WHERE Year = YEAR(GETDATE()) 
                AND Month = MONTH(GETDATE())
                AND DaysRented > 0
            ) rh ON e.SerialNo = rh.SerialNo
            WHERE e.CustomerNo = '900006'
            """
            diagnostics['fleet_rental_activity'] = db.execute_query(query2)
            
            # 3. Sample of rental fleet equipment
            query3 = """
            SELECT TOP 10
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                e.RentalStatus,
                e.DayRent,
                e.WeekRent,
                e.MonthRent
            FROM ben002.Equipment e
            WHERE e.CustomerNo = '900006'
            ORDER BY e.UnitNo
            """
            diagnostics['fleet_sample'] = db.execute_query(query3)
            
            # 4. Check RentalContract structure
            query4 = """
            SELECT 
                COUNT(*) as total_contracts
            FROM ben002.RentalContract
            WHERE DeletionTime IS NULL
            """
            diagnostics['rental_contract_summary'] = db.execute_query(query4)
            
            # 5. Get count of all equipment by CustomerNo to see the big picture
            query5 = """
            SELECT 
                CustomerNo,
                c.Name as CustomerName,
                COUNT(*) as equipment_count
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE CustomerNo IN ('900006', '900007', '900008', '900009')
            GROUP BY CustomerNo, c.Name
            ORDER BY equipment_count DESC
            """
            diagnostics['internal_customer_equipment'] = db.execute_query(query5)
            
            return jsonify(diagnostics)
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_fleet_diagnostic_error'
            }), 500

    @reports_bp.route('/departments/rental/rental-vs-sales-diagnostic', methods=['GET'])
    @jwt_required()
    def get_rental_vs_sales_diagnostic():
        """Diagnostic to determine if CustomerNo means rental or sale"""
        try:
            db = get_db()
            
            diagnostics = {}
            
            # 1. Check Equipment with CustomerNo and their Customer flag
            query1 = """
            SELECT 
                CASE 
                    WHEN Customer = 1 THEN 'Customer Flag = 1'
                    WHEN Customer = 0 THEN 'Customer Flag = 0'
                    ELSE 'Customer Flag NULL'
                END as customer_flag_status,
                COUNT(*) as count,
                COUNT(CASE WHEN CustomerNo IS NOT NULL AND CustomerNo != '' THEN 1 END) as has_customer_no
            FROM ben002.Equipment
            GROUP BY Customer
            """
            diagnostics['customer_flag_analysis'] = db.execute_query(query1)
            
            # 2. Sample equipment with CustomerNo to see patterns
            query2 = """
            SELECT TOP 20
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                e.Customer as CustomerFlag,
                e.CustomerNo,
                c.Name as CustomerName,
                e.RentalStatus,
                e.DayRent,
                e.WeekRent,
                e.MonthRent,
                -- Check if this equipment has rental history
                CASE WHEN rh.SerialNo IS NOT NULL THEN 'Has Rental History' ELSE 'No Rental History' END as rental_history_status,
                -- Check if sold through invoice
                CASE WHEN inv.SerialNo IS NOT NULL THEN 'Found in Invoice' ELSE 'Not in Invoice' END as invoice_status
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            LEFT JOIN (
                SELECT DISTINCT SerialNo 
                FROM ben002.RentalHistory 
                WHERE Year >= 2024
            ) rh ON e.SerialNo = rh.SerialNo
            LEFT JOIN (
                SELECT DISTINCT SerialNo 
                FROM ben002.InvoiceReg 
                WHERE SerialNo IS NOT NULL
            ) inv ON e.SerialNo = inv.SerialNo
            WHERE e.CustomerNo IS NOT NULL 
                AND e.CustomerNo != ''
                AND e.CustomerNo != '0'
            ORDER BY e.UnitNo
            """
            diagnostics['sample_equipment_with_customer'] = db.execute_query(query2)
            
            # 3. Check RentalContract to see if it links to Equipment
            query3 = """
            SELECT TOP 10
                rc.RentalContractNo,
                rc.CustomerNo,
                c.Name as CustomerName,
                rc.StartDate,
                rc.EndDate,
                rc.DeliveryCharge,
                rc.PickupCharge
            FROM ben002.RentalContract rc
            LEFT JOIN ben002.Customer c ON rc.CustomerNo = c.Number
            WHERE rc.DeletionTime IS NULL
            ORDER BY rc.RentalContractNo DESC
            """
            diagnostics['rental_contracts_sample'] = db.execute_query(query3)
            
            # 4. Check if there's a RentalContractEquipment table
            query4 = """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ben002'
            AND TABLE_NAME LIKE '%Rental%Equipment%'
            """
            diagnostics['rental_equipment_tables'] = db.execute_query(query4)
            
            return jsonify(diagnostics)
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_vs_sales_diagnostic_error'
            }), 500

    @reports_bp.route('/departments/rental/units-diagnostic', methods=['GET'])
    @jwt_required()
    def get_units_diagnostic():
        """Diagnostic to find where the 400 units on rent are tracked"""
        try:
            db = get_db()
            
            diagnostics = {}
            
            # 1. Check Equipment table RentalStatus values
            status_query = """
            SELECT RentalStatus, COUNT(*) as count
            FROM ben002.Equipment
            GROUP BY RentalStatus
            ORDER BY count DESC
            """
            diagnostics['equipment_rental_status'] = db.execute_query(status_query)
            
            # 2. Check Equipment table for units with CustomerNo
            customer_query = """
            SELECT 
                CASE 
                    WHEN CustomerNo IS NULL OR CustomerNo = '' THEN 'No Customer'
                    WHEN Customer = 1 THEN 'Has Customer Flag'
                    ELSE 'Has CustomerNo Only'
                END as status,
                COUNT(*) as count
            FROM ben002.Equipment
            GROUP BY 
                CASE 
                    WHEN CustomerNo IS NULL OR CustomerNo = '' THEN 'No Customer'
                    WHEN Customer = 1 THEN 'Has Customer Flag'
                    ELSE 'Has CustomerNo Only'
                END
            """
            diagnostics['equipment_customer_status'] = db.execute_query(customer_query)
            
            # 3. Count Equipment with CustomerNo that are likely on rent
            on_rent_query = """
            SELECT COUNT(*) as count
            FROM ben002.Equipment
            WHERE CustomerNo IS NOT NULL 
                AND CustomerNo != ''
                AND CustomerNo != '0'
            """
            diagnostics['equipment_with_customer'] = db.execute_query(on_rent_query)
            
            # 4. Sample of equipment with customers
            sample_query = """
            SELECT TOP 10
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                e.RentalStatus,
                e.CustomerNo,
                e.Customer as CustomerFlag,
                c.Name as CustomerName
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE e.CustomerNo IS NOT NULL 
                AND e.CustomerNo != ''
                AND e.CustomerNo != '0'
            ORDER BY e.UnitNo
            """
            diagnostics['sample_equipment_with_customer'] = db.execute_query(sample_query)
            
            # 5. Check RentalContract table
            contract_query = """
            SELECT COUNT(*) as active_contracts
            FROM ben002.RentalContract
            WHERE DeletionTime IS NULL
            """
            diagnostics['rental_contracts'] = db.execute_query(contract_query)
            
            # 6. Check RentalHistory current month total
            history_query = """
            SELECT 
                COUNT(DISTINCT SerialNo) as unique_units,
                COUNT(*) as total_records
            FROM ben002.RentalHistory
            WHERE Year = YEAR(GETDATE()) AND Month = MONTH(GETDATE())
            """
            diagnostics['rental_history_current_month'] = db.execute_query(history_query)
            
            return jsonify(diagnostics)
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_diagnostic_error'
            }), 500

    @reports_bp.route('/departments/rental/available-forklifts', methods=['GET'])
    @jwt_required()
    def get_available_forklifts():
        """Get list of all available rental equipment (Ready To Rent status)"""
        try:
            db = get_db()
            
            # Get ALL equipment that is Ready To Rent (matches the inventory count logic)
            query = """
            SELECT 
                UnitNo,
                SerialNo,
                Make,
                Model,
                ModelYear,
                Cost,
                Sell as ListPrice,
                RentalStatus,
                Location,
                DayRent,
                WeekRent,
                MonthRent
            FROM ben002.Equipment
            WHERE RentalStatus = 'Ready To Rent'
            ORDER BY Make, Model, UnitNo
            """
            
            results = db.execute_query(query)
            
            forklifts = []
            for row in results:
                forklifts.append({
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'make': row['Make'],
                    'model': row['Model'],
                    'model_year': row['ModelYear'],
                    'cost': float(row['Cost'] or 0),
                    'list_price': float(row['ListPrice'] or 0),
                    'rental_status': row['RentalStatus'],
                    'location': row['Location'],
                    'day_rent': float(row['DayRent'] or 0),
                    'week_rent': float(row['WeekRent'] or 0),
                    'month_rent': float(row['MonthRent'] or 0)
                })
            
            return jsonify({
                'forklifts': forklifts,
                'count': len(forklifts)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'available_forklifts_error'
            }), 500

    @reports_bp.route('/departments/rental/forklift-query-diagnostic', methods=['GET'])
    @jwt_required()
    def get_forklift_query_diagnostic():
        """Diagnostic to understand what the forklift query actually returns"""
        try:
            db = get_db()
            
            # Test the exact query from available-forklifts endpoint
            query = """
            SELECT 
                UnitNo,
                SerialNo,
                Make,
                Model,
                ModelYear,
                Cost,
                Sell as ListPrice,
                COALESCE(RentalStatus, 'On Rent') as RentalStatus,
                -- Additional debug fields
                UPPER(Make) as UpperMake,
                UPPER(Model) as UpperModel,
                CASE 
                    WHEN UPPER(Model) LIKE '%FORK%' THEN 'Model contains FORK'
                    WHEN UPPER(Make) LIKE '%FORK%' THEN 'Make contains FORK'
                    ELSE 'No match'
                END as MatchReason
            FROM ben002.Equipment
            WHERE UPPER(Model) LIKE '%FORK%' OR UPPER(Make) LIKE '%FORK%'
            ORDER BY Make, Model, UnitNo
            """
            
            results = db.execute_query(query)
            
            # Count total equipment
            count_query = "SELECT COUNT(*) as total_equipment FROM ben002.Equipment"
            count_result = db.execute_query(count_query)
            total_equipment = count_result[0]['total_equipment'] if count_result else 0
            
            # Get some sample equipment records to understand the data better
            sample_query = """
            SELECT TOP 10
                UnitNo,
                SerialNo,
                Make,
                Model,
                UPPER(Make) as UpperMake,
                UPPER(Model) as UpperModel
            FROM ben002.Equipment
            WHERE Make IS NOT NULL AND Model IS NOT NULL
            ORDER BY UnitNo
            """
            
            sample_results = db.execute_query(sample_query)
            
            # Test alternative forklift queries
            alt_queries = {}
            
            # Query 1: More specific forklift matching
            alt1_query = """
            SELECT COUNT(*) as count FROM ben002.Equipment
            WHERE (UPPER(Model) LIKE '%FORKLIFT%' 
                   OR UPPER(Model) LIKE 'FORK%'
                   OR UPPER(Make) IN ('YALE', 'HYSTER', 'TOYOTA', 'CROWN', 'CLARK', 'LINDE')
                   OR UPPER(Model) LIKE '%LIFT TRUCK%')
            """
            alt1_result = db.execute_query(alt1_query)
            alt_queries['specific_forklift_terms'] = alt1_result[0]['count'] if alt1_result else 0
            
            # Query 2: Just looking for FORKLIFT in model
            alt2_query = """
            SELECT COUNT(*) as count FROM ben002.Equipment
            WHERE UPPER(Model) LIKE '%FORKLIFT%'
            """
            alt2_result = db.execute_query(alt2_query)
            alt_queries['model_contains_forklift'] = alt2_result[0]['count'] if alt2_result else 0
            
            # Query 3: Common forklift manufacturers
            alt3_query = """
            SELECT COUNT(*) as count FROM ben002.Equipment
            WHERE UPPER(Make) IN ('YALE', 'HYSTER', 'TOYOTA', 'CROWN', 'CLARK', 'LINDE', 'CATERPILLAR', 'KOMATSU')
            """
            alt3_result = db.execute_query(alt3_query)
            alt_queries['known_forklift_makes'] = alt3_result[0]['count'] if alt3_result else 0
            
            return jsonify({
                'forklift_results': results,
                'forklift_count': len(results),
                'total_equipment_count': total_equipment,
                'sample_equipment': sample_results,
                'alternative_queries': alt_queries,
                'query_used': query
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'forklift_diagnostic_error'
            }), 500
    
    @reports_bp.route('/departments/rental/customer-units-diagnostic', methods=['GET'])
    @jwt_required()
    def get_customer_units_diagnostic():
        """Diagnostic to understand customer rental units"""
        try:
            db = get_db()
            
            # Check RentalHistory for current month
            query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT SerialNo) as unique_units,
                MIN(Year) as min_year,
                MAX(Year) as max_year,
                MIN(Month) as min_month,
                MAX(Month) as max_month
            FROM ben002.RentalHistory
            WHERE Year = YEAR(GETDATE()) AND Month = MONTH(GETDATE())
            """
            
            results = db.execute_query(query)
            
            # Get sample rental history with customer info
            sample_query = """
            SELECT TOP 10
                rh.SerialNo,
                rh.Year,
                rh.Month,
                rh.DaysRented,
                rh.RentAmount,
                e.UnitNo,
                e.CustomerNo,
                c.Name as CustomerName
            FROM ben002.RentalHistory rh
            LEFT JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
            ORDER BY rh.RentAmount DESC
            """
            
            sample_results = db.execute_query(sample_query)
            
            # Count by customer
            customer_query = """
            SELECT 
                COALESCE(c.Name, 'No Customer') as customer_name,
                COUNT(DISTINCT rh.SerialNo) as units_on_rent,
                SUM(rh.RentAmount) as total_rent
            FROM ben002.RentalHistory rh
            LEFT JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
            GROUP BY c.Name
            ORDER BY COUNT(DISTINCT rh.SerialNo) DESC
            """
            
            customer_results = db.execute_query(customer_query)
            
            return jsonify({
                'current_month_summary': results[0] if results else {},
                'sample_rentals': [dict(row) for row in sample_results] if sample_results else [],
                'customers_with_units': [dict(row) for row in customer_results] if customer_results else []
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'customer_units_diagnostic_error'
            }), 500
    
    @reports_bp.route('/departments/rental/rental-status-diagnostic', methods=['GET'])
    @jwt_required()
    def get_rental_status_diagnostic():
        """Diagnostic endpoint to check rental indicators"""
        try:
            db = get_db()
            
            # Check rental contracts - this is the real answer!
            rental_contract_query = """
            SELECT 
                COUNT(DISTINCT rc.RentalContractNo) as active_contracts,
                COUNT(DISTINCT re.SerialNo) as units_on_contract
            FROM ben002.RentalContract rc
            LEFT JOIN ben002.RentalContractEquipment re ON rc.RentalContractNo = re.RentalContractNo
            WHERE rc.DeletionTime IS NULL
                AND (rc.EndDate IS NULL OR rc.EndDate >= GETDATE() OR rc.OpenEndedContract = 1)
            """
            
            # If RentalContractEquipment doesn't exist, try simpler query
            try:
                contract_results = db.execute_query(rental_contract_query)
            except:
                # Fallback if join table doesn't exist
                rental_contract_query = """
                SELECT COUNT(*) as active_contracts
                FROM ben002.RentalContract
                WHERE DeletionTime IS NULL
                    AND (EndDate IS NULL OR EndDate >= GETDATE() OR OpenEndedContract = 1)
                """
                contract_results = db.execute_query(rental_contract_query)
            
            # Check various rental indicators in Equipment table
            query = """
            SELECT 
                -- Unit types
                COUNT(*) as total_equipment,
                COUNT(CASE WHEN UnitType = 'Rental' OR UnitType LIKE '%Rent%' THEN 1 END) as rental_unit_type,
                COUNT(CASE WHEN WebRentalFlag = 1 THEN 1 END) as web_rental_flag,
                COUNT(CASE WHEN RentalRateCode IS NOT NULL AND RentalRateCode != '' THEN 1 END) as has_rental_rate,
                
                -- Current rental status
                COUNT(CASE WHEN CustomerNo IS NOT NULL AND CustomerNo != '' THEN 1 END) as has_customer,
                COUNT(CASE WHEN RentalStatus = 'Ready To Rent' THEN 1 END) as ready_to_rent,
                COUNT(CASE WHEN RentalStatus IS NULL OR RentalStatus = '' THEN 1 END) as null_status,
                
                -- Combinations
                COUNT(CASE WHEN (UnitType = 'Rental' OR WebRentalFlag = 1) AND CustomerNo IS NOT NULL AND CustomerNo != '' THEN 1 END) as rental_units_with_customer,
                COUNT(CASE WHEN (UnitType = 'Rental' OR WebRentalFlag = 1) AND (RentalStatus = 'Ready To Rent' OR RentalStatus = 'Hold') THEN 1 END) as rental_units_available
            FROM ben002.Equipment
            """
            
            results = db.execute_query(query)
            
            # Check UnitType values
            unit_type_query = """
            SELECT DISTINCT UnitType, COUNT(*) as count
            FROM ben002.Equipment
            WHERE UnitType IS NOT NULL
            GROUP BY UnitType
            ORDER BY count DESC
            """
            
            unit_type_results = db.execute_query(unit_type_query)
            
            # Sample rental units with customer info
            sample_query = """
            SELECT TOP 10
                e.UnitNo, e.Make, e.Model, e.UnitType, e.WebRentalFlag, e.RentalStatus, 
                e.CustomerNo, c.Name as CustomerName,
                e.RentalRateCode, e.DayRent, e.WeekRent, e.MonthRent
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE (e.UnitType = 'Rental' OR e.WebRentalFlag = 1 OR e.RentalRateCode IS NOT NULL)
                AND e.CustomerNo IS NOT NULL AND e.CustomerNo != ''
            """
            
            sample_results = db.execute_query(sample_query)
            
            # Check if RentalContractEquipment or similar table exists to link contracts to equipment/customers
            contract_link_query = """
            SELECT TOP 5 
                rc.RentalContractNo,
                rc.StartDate,
                rc.EndDate,
                e.SerialNo,
                e.UnitNo,
                e.CustomerNo,
                c.Name as CustomerName
            FROM ben002.RentalContract rc
            INNER JOIN ben002.Equipment e ON e.CustomerNo IS NOT NULL
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE rc.DeletionTime IS NULL
                AND (rc.EndDate IS NULL OR rc.EndDate >= GETDATE() OR rc.OpenEndedContract = 1)
                AND EXISTS (
                    SELECT 1 FROM ben002.RentalHistory rh 
                    WHERE rh.SerialNo = e.SerialNo 
                    AND rh.Year = YEAR(GETDATE()) 
                    AND rh.Month = MONTH(GETDATE())
                )
            """
            
            try:
                contract_link_results = db.execute_query(contract_link_query)
            except:
                contract_link_results = []
            
            return jsonify({
                'rental_contracts': contract_results[0] if contract_results else {},
                'rental_indicators': results[0] if results else {},
                'unit_types': [{'type': row['UnitType'], 'count': row['count']} for row in unit_type_results] if unit_type_results else [],
                'sample_rental_units': [dict(row) for row in sample_results] if sample_results else [],
                'contract_equipment_links': [dict(row) for row in contract_link_results] if contract_link_results else []
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_status_diagnostic_error'
            }), 500

    @reports_bp.route('/departments/accounting/sales-commissions', methods=['GET'])
    @jwt_required()
    def get_sales_commissions():
        """Get sales commission report for a specific month"""
        try:
            db = get_db()
            
            # Get month parameter (format: YYYY-MM)
            month_param = request.args.get('month')
            if not month_param:
                # Default to previous month
                today = datetime.today()
                prev_month = today.replace(day=1) - timedelta(days=1)
                month_param = prev_month.strftime('%Y-%m')
            
            # Parse month parameter
            year, month = map(int, month_param.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Query to get sales by salesman and category
            # Note: We need to identify which invoices are for Rental, Used, Allied, and New Equipment
            # This will depend on how these are categorized in the database
            sales_query = """
            SELECT 
                COALESCE(c.Salesman1, 'Unassigned') as SalesRep,
                SUM(CASE 
                    WHEN ir.SaleCode = 'RENTAL'
                    THEN COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)
                    ELSE 0 
                END) as RentalSales,
                SUM(CASE 
                    -- USEDEQ/USEDEQP are used equipment, RNTSALE is selling used rental units
                    WHEN ir.SaleCode IN ('USEDEQ', 'USEDEQP', 'RNTSALE')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as UsedEquipmentSales,
                SUM(CASE 
                    -- Allied equipment - placeholder for now, no specific codes identified yet
                    WHEN 1=0  -- No codes currently mapped to Allied
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as AlliedEquipmentSales,
                SUM(CASE 
                    -- LINDEN is new Linde equipment, NEWEQ/NEWEQP-R are other new equipment
                    WHEN ir.SaleCode IN ('LINDEN', 'NEWEQ', 'NEWEQP-R')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as NewEquipmentSales
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceDate >= %s
                AND ir.InvoiceDate <= %s
                AND c.Salesman1 IS NOT NULL
                AND c.Salesman1 != ''
            GROUP BY c.Salesman1
            ORDER BY SUM(
                COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0) +
                COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
            ) DESC
            """
            
            results = db.execute_query(sales_query, [start_date, end_date])
            
            # Get commission rates (this would normally come from a commission table)
            # For now, using a default rate - this should be customizable per sales rep
            default_commission_rate = 0.02  # 2% default
            
            salespeople = []
            totals = {
                'rental': 0,
                'used_equipment': 0,
                'allied_equipment': 0,
                'new_equipment': 0,
                'total_sales': 0,
                'total_commissions': 0
            }
            
            for row in results:
                rental = float(row['RentalSales'] or 0)
                used = float(row['UsedEquipmentSales'] or 0)
                allied = float(row['AlliedEquipmentSales'] or 0)
                new = float(row['NewEquipmentSales'] or 0)
                total_sales = rental + used + allied + new
                
                # Calculate commission (in real implementation, rates would vary by rep and category)
                commission_rate = default_commission_rate
                commission_amount = total_sales * commission_rate
                
                salespeople.append({
                    'name': row['SalesRep'],
                    'rental': rental,
                    'used_equipment': used,
                    'allied_equipment': allied,
                    'new_equipment': new,
                    'total_sales': total_sales,
                    'commission_rate': commission_rate,
                    'commission_amount': commission_amount
                })
                
                # Update totals
                totals['rental'] += rental
                totals['used_equipment'] += used
                totals['allied_equipment'] += allied
                totals['new_equipment'] += new
                totals['total_sales'] += total_sales
                totals['total_commissions'] += commission_amount
            
            return jsonify({
                'month': month_param,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'salespeople': salespeople,
                'totals': totals
            })
            
        except Exception as e:
            logger.error(f"Error fetching sales commissions: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/sales-commission-diagnostic', methods=['GET'])
    @jwt_required()
    def get_sales_commission_diagnostic():
        """Diagnostic endpoint to understand sales data structure"""
        try:
            db = get_db()
            
            # Get month parameter
            month_param = request.args.get('month')
            if not month_param:
                today = datetime.today()
                prev_month = today.replace(day=1) - timedelta(days=1)
                month_param = prev_month.strftime('%Y-%m')
            
            year, month = map(int, month_param.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # 1. Check what SaleCodes exist
            sale_codes_query = """
            SELECT 
                ir.SaleCode,
                COUNT(*) as InvoiceCount,
                SUM(COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)) as RentalRevenue,
                SUM(COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) as EquipmentRevenue,
                SUM(ir.GrandTotal) as TotalRevenue
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
            GROUP BY ir.SaleCode
            ORDER BY COUNT(*) DESC
            """
            
            sale_codes = db.execute_query(sale_codes_query, [start_date, end_date])
            
            # 2. Check sample invoices with equipment sales
            equipment_sample_query = """
            SELECT TOP 20
                ir.InvoiceNo,
                ir.SaleCode,
                ir.BillToName,
                c.Salesman1,
                ir.Comments,
                ir.EquipmentTaxable,
                ir.EquipmentNonTax,
                ir.RentalTaxable,
                ir.RentalNonTax
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
                AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)
            ORDER BY ir.InvoiceDate DESC
            """
            
            equipment_samples = db.execute_query(equipment_sample_query, [start_date, end_date])
            
            # 3. Check salesmen distribution
            salesmen_query = """
            SELECT 
                c.Salesman1,
                COUNT(DISTINCT ir.InvoiceNo) as InvoiceCount,
                SUM(ir.GrandTotal) as TotalSales
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
                AND c.Salesman1 IS NOT NULL
            GROUP BY c.Salesman1
            ORDER BY SUM(ir.GrandTotal) DESC
            """
            
            salesmen = db.execute_query(salesmen_query, [start_date, end_date])
            
            # 4. Check rental invoices
            rental_check_query = """
            SELECT 
                COUNT(*) as RentalInvoiceCount,
                SUM(ir.RentalTaxable + ir.RentalNonTax) as TotalRentalRevenue
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
                AND (ir.RentalTaxable > 0 OR ir.RentalNonTax > 0)
            """
            
            rental_check = db.execute_query(rental_check_query, [start_date, end_date])
            
            return jsonify({
                'month': month_param,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'sale_codes': [dict(row) for row in sale_codes],
                'equipment_samples': [dict(row) for row in equipment_samples],
                'salesmen_summary': [dict(row) for row in salesmen],
                'rental_summary': dict(rental_check[0]) if rental_check else {},
                'diagnostic_info': {
                    'total_sale_codes': len(sale_codes),
                    'total_salesmen': len(salesmen),
                    'has_equipment_sales': any(row['EquipmentRevenue'] > 0 for row in sale_codes) if sale_codes else False,
                    'has_rental_sales': rental_check[0]['TotalRentalRevenue'] > 0 if rental_check and rental_check[0]['TotalRentalRevenue'] else False
                }
            })
            
        except Exception as e:
            logger.error(f"Error in sales commission diagnostic: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/sales-commission-buckets', methods=['GET'])
    @jwt_required()
    def get_sales_commission_buckets():
        """Get detailed bucket diagnostics with sample invoices for each category"""
        try:
            db = get_db()
            
            # Get month parameter
            month_param = request.args.get('month')
            if not month_param:
                today = datetime.today()
                prev_month = today.replace(day=1) - timedelta(days=1)
                month_param = prev_month.strftime('%Y-%m')
            
            year, month = map(int, month_param.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            buckets = {
                'rental': {
                    'name': 'Rental',
                    'sale_codes': ['RENTAL'],
                    'field': 'Rental',
                    'sample_invoices': []
                },
                'used_equipment': {
                    'name': 'Used Equipment', 
                    'sale_codes': ['USEDEQ', 'USEDEQP', 'RNTSALE'],
                    'field': 'Equipment',
                    'sample_invoices': []
                },
                'allied_equipment': {
                    'name': 'Allied Equipment',
                    'sale_codes': [],  # No codes currently mapped
                    'field': 'Equipment',
                    'sample_invoices': []
                },
                'new_equipment': {
                    'name': 'New Equipment',
                    'sale_codes': ['LINDEN', 'NEWEQ', 'NEWEQP-R'],
                    'field': 'Equipment',
                    'sample_invoices': []
                }
            }
            
            # Get sample invoices for each bucket
            for bucket_key, bucket_info in buckets.items():
                # Skip buckets with no sale codes
                if not bucket_info['sale_codes']:
                    bucket_info['sample_invoices'] = []
                    continue
                    
                sale_codes_str = "','".join(bucket_info['sale_codes'])
                
                if bucket_info['field'] == 'Rental':
                    amount_condition = "(ir.RentalTaxable > 0 OR ir.RentalNonTax > 0)"
                else:  # Equipment
                    amount_condition = "(ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)"
                
                sample_query = f"""
                SELECT TOP 5
                    ir.InvoiceNo,
                    ir.InvoiceDate,
                    ir.SaleCode,
                    ir.BillToName,
                    c.Salesman1,
                    ir.Comments,
                    ir.RentalTaxable,
                    ir.RentalNonTax,
                    ir.EquipmentTaxable,
                    ir.EquipmentNonTax,
                    ir.GrandTotal,
                    CASE 
                        WHEN '{bucket_info['field']}' = 'Rental'
                        THEN COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)
                        ELSE COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    END as CategoryAmount
                FROM ben002.InvoiceReg ir
                LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
                WHERE ir.InvoiceDate >= %s 
                    AND ir.InvoiceDate <= %s
                    AND ir.SaleCode IN ('{sale_codes_str}')
                    AND {amount_condition}
                ORDER BY ir.InvoiceDate DESC
                """
                
                samples = db.execute_query(sample_query, [start_date, end_date])
                bucket_info['sample_invoices'] = [dict(row) for row in samples]
            
            # Get summary statistics for each bucket
            summary_query = """
            SELECT 
                SUM(CASE 
                    WHEN ir.SaleCode = 'RENTAL'
                    THEN COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)
                    ELSE 0 
                END) as RentalTotal,
                COUNT(CASE WHEN ir.SaleCode = 'RENTAL' THEN 1 ELSE NULL END) as RentalCount,
                
                SUM(CASE 
                    WHEN ir.SaleCode IN ('USEDEQ', 'USEDEQP', 'RNTSALE')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as UsedTotal,
                COUNT(CASE WHEN ir.SaleCode IN ('USEDEQ', 'USEDEQP', 'RNTSALE') THEN 1 ELSE NULL END) as UsedCount,
                
                SUM(CASE 
                    WHEN 1=0  -- No codes currently mapped to Allied
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as AlliedTotal,
                COUNT(CASE WHEN 1=0 THEN 1 ELSE NULL END) as AlliedCount,
                
                SUM(CASE 
                    WHEN ir.SaleCode IN ('LINDEN', 'NEWEQ', 'NEWEQP-R')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as NewTotal,
                COUNT(CASE WHEN ir.SaleCode IN ('LINDEN', 'NEWEQ', 'NEWEQP-R') THEN 1 ELSE NULL END) as NewCount
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
            """
            
            summary = db.execute_query(summary_query, [start_date, end_date])
            summary_data = dict(summary[0]) if summary else {}
            
            # Check all SaleCodes that have equipment revenue but aren't mapped
            unmapped_query = """
            SELECT 
                ir.SaleCode,
                COUNT(*) as InvoiceCount,
                SUM(COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) as EquipmentRevenue
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s 
                AND ir.InvoiceDate <= %s
                AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)
                AND ir.SaleCode NOT IN ('USEDEQ', 'USEDEQP', 'RNTSALE', 'LINDEN', 'NEWEQ', 'NEWEQP-R')
            GROUP BY ir.SaleCode
            ORDER BY SUM(COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) DESC
            """
            
            unmapped = db.execute_query(unmapped_query, [start_date, end_date])
            
            return jsonify({
                'month': month_param,
                'buckets': buckets,
                'summary': {
                    'rental': {
                        'total': float(summary_data.get('RentalTotal', 0)),
                        'count': int(summary_data.get('RentalCount', 0))
                    },
                    'used_equipment': {
                        'total': float(summary_data.get('UsedTotal', 0)),
                        'count': int(summary_data.get('UsedCount', 0))
                    },
                    'allied_equipment': {
                        'total': float(summary_data.get('AlliedTotal', 0)),
                        'count': int(summary_data.get('AlliedCount', 0))
                    },
                    'new_equipment': {
                        'total': float(summary_data.get('NewTotal', 0)),
                        'count': int(summary_data.get('NewCount', 0))
                    }
                },
                'unmapped_equipment_codes': [dict(row) for row in unmapped] if unmapped else []
            })
            
        except Exception as e:
            logger.error(f"Error in sales commission buckets: {str(e)}")
            return jsonify({'error': str(e)}), 500


