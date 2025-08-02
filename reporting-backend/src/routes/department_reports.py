# Department-specific report endpoints
from flask import jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from flask import request
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
            
            # Monthly Labor Revenue - Last 12 months
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
            
            # Monthly Parts Revenue - Last 12 months
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
    
    
    @reports_bp.route('/quote-debug', methods=['GET'])
    def get_quote_debug():
        """Debug endpoint to examine WOQuote table structure"""
        try:
            db = get_db()
            
            # Get table structure
            structure_query = """
            SELECT 
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.CHARACTER_MAXIMUM_LENGTH,
                c.IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS c
            WHERE c.TABLE_SCHEMA = 'ben002' 
            AND c.TABLE_NAME = 'WOQuote'
            ORDER BY c.ORDINAL_POSITION
            """
            structure = db.execute_query(structure_query)
            
            # Get sample data
            sample_query = """
            SELECT TOP 10 *
            FROM ben002.WOQuote
            WHERE CreationTime >= '2025-01-01'
            ORDER BY CreationTime DESC
            """
            samples = db.execute_query(sample_query)
            
            # Check for duplicate quotes per customer
            duplicates_query = """
            SELECT 
                Customer,
                CAST(CreationTime AS DATE) as QuoteDate,
                COUNT(*) as QuoteCount,
                SUM(Amount) as TotalAmount
            FROM ben002.WOQuote
            WHERE CreationTime >= '2025-01-01'
            AND Amount > 0
            GROUP BY Customer, CAST(CreationTime AS DATE)
            HAVING COUNT(*) > 1
            ORDER BY QuoteDate DESC, QuoteCount DESC
            """
            duplicates = db.execute_query(duplicates_query)
            
            return jsonify({
                'table_structure': structure,
                'sample_data': samples,
                'potential_duplicates': duplicates
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500


