"""
Parts Inventory Min/Max with 5-Turn Matrix
Calculates optimal inventory levels to achieve target inventory turns
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
# Try to import scipy, fall back to manual calculation if not available
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
import logging
from src.services.azure_sql_service import AzureSQLService

logger = logging.getLogger(__name__)
parts_inventory_bp = Blueprint('parts_inventory', __name__)

@parts_inventory_bp.route('/api/parts/inventory-turns', methods=['GET'])
@jwt_required()
def calculate_inventory_turns():
    """
    Calculate min/max inventory levels for parts to achieve target turns
    """
    try:
        # Get query parameters
        months = int(request.args.get('months', 12))
        lead_time_days = int(request.args.get('lead_time_days', 14))
        service_level = float(request.args.get('service_level', 0.95))
        target_turns = float(request.args.get('target_turns', 5.0))
        min_usage_threshold = int(request.args.get('min_usage', 5))  # Minimum usage to include
        
        db = AzureSQLService()
        
        # Calculate date range for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        logger.info(f"Analyzing parts usage from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get parts usage data from multiple sources
        usage_query = f"""
        WITH PartsUsage AS (
            -- Parts sold to customers (InvoiceDetail)
            SELECT 
                p.PartNo,
                p.Description,
                p.Cost,
                p.List as ListPrice,
                p.OnHand as CurrentStock,
                COALESCE(SUM(
                    CASE WHEN ir.InvoiceDate >= '{start_date.strftime('%Y-%m-%d')}'
                         AND ir.InvoiceDate <= '{end_date.strftime('%Y-%m-%d')}'
                    THEN COALESCE(id.Quantity, 0) 
                    ELSE 0 END
                ), 0) as SoldQuantity,
                
                -- Parts used in work orders (WOParts)
                COALESCE(SUM(
                    CASE WHEN wo.OpenDate >= '{start_date.strftime('%Y-%m-%d')}'
                         AND wo.OpenDate <= '{end_date.strftime('%Y-%m-%d')}'
                    THEN COALESCE(wop.Qty, 0)
                    ELSE 0 END
                ), 0) as WorkOrderQuantity,
                
                -- Get monthly usage for variability calculation
                STRING_AGG(
                    CASE WHEN ir.InvoiceDate >= '{start_date.strftime('%Y-%m-%d')}'
                         AND ir.InvoiceDate <= '{end_date.strftime('%Y-%m-%d')}'
                    THEN CONCAT(
                        YEAR(ir.InvoiceDate), '-', 
                        FORMAT(MONTH(ir.InvoiceDate), '00'), ':', 
                        COALESCE(id.Quantity, 0)
                    )
                    ELSE NULL END, '|'
                ) as MonthlyUsageData
                
            FROM ben002.Parts p
            LEFT JOIN ben002.InvoiceDetail id ON p.PartNo = id.PartNo
            LEFT JOIN ben002.InvoiceReg ir ON id.InvoiceNo = ir.InvoiceNo
            LEFT JOIN ben002.WOParts wop ON p.PartNo = wop.PartNo
            LEFT JOIN ben002.WO wo ON wop.WONo = wo.WONo
            
            WHERE p.PartNo IS NOT NULL 
            AND p.PartNo != ''
            AND (p.Cost > 0 OR p.List > 0)  -- Only include parts with costs
            
            GROUP BY p.PartNo, p.Description, p.Cost, p.List, p.OnHand
            
            HAVING (
                COALESCE(SUM(
                    CASE WHEN ir.InvoiceDate >= '{start_date.strftime('%Y-%m-%d')}'
                         AND ir.InvoiceDate <= '{end_date.strftime('%Y-%m-%d')}'
                    THEN COALESCE(id.Quantity, 0) 
                    ELSE 0 END
                ), 0) +
                COALESCE(SUM(
                    CASE WHEN wo.OpenDate >= '{start_date.strftime('%Y-%m-%d')}'
                         AND wo.OpenDate <= '{end_date.strftime('%Y-%m-%d')}'
                    THEN COALESCE(wop.Qty, 0)
                    ELSE 0 END
                ), 0)
            ) >= {min_usage_threshold}
        )
        SELECT 
            PartNo,
            Description,
            COALESCE(Cost, 0) as Cost,
            COALESCE(ListPrice, 0) as ListPrice,
            COALESCE(CurrentStock, 0) as CurrentStock,
            (SoldQuantity + WorkOrderQuantity) as TotalUsage,
            SoldQuantity,
            WorkOrderQuantity,
            MonthlyUsageData
        FROM PartsUsage
        ORDER BY (SoldQuantity + WorkOrderQuantity) DESC
        """
        
        logger.info("Executing parts usage query...")
        usage_results = db.execute_query(usage_query)
        
        if not usage_results:
            return jsonify({
                'success': True,
                'parts': [],
                'summary': {
                    'total_parts_analyzed': 0,
                    'avg_turns_current': 0,
                    'target_turns': target_turns,
                    'potential_savings': 0
                }
            })
        
        # Convert to DataFrame for calculations
        df = pd.DataFrame(usage_results)
        
        # Calculate inventory turn metrics for each part
        parts_data = []
        total_potential_savings = 0
        
        # Z-score for service level (95% = 1.645, 99% = 2.326)
        if HAS_SCIPY:
            z_score = stats.norm.ppf(service_level)
        else:
            # Manual approximation for common service levels
            z_score_map = {
                0.90: 1.282,
                0.95: 1.645,
                0.99: 2.326
            }
            z_score = z_score_map.get(service_level, 1.645)  # Default to 95%
        
        for _, row in df.iterrows():
            part_data = calculate_part_metrics(
                row, months, lead_time_days, target_turns, z_score
            )
            
            if part_data:
                parts_data.append(part_data)
                # Calculate potential savings
                if part_data['recommended_action'] == 'Reduce stock':
                    potential_reduction = max(0, part_data['current_stock'] - part_data['max_level'])
                    total_potential_savings += potential_reduction * part_data['cost_per_unit']
        
        # Calculate summary statistics
        current_turns = [p['current_turns'] for p in parts_data if p['current_turns'] > 0]
        avg_current_turns = np.mean(current_turns) if current_turns else 0
        
        summary = {
            'total_parts_analyzed': len(parts_data),
            'avg_turns_current': round(avg_current_turns, 2),
            'target_turns': target_turns,
            'potential_savings': round(total_potential_savings, 2),
            'analysis_period_months': months,
            'lead_time_days': lead_time_days,
            'service_level': service_level,
            'min_usage_threshold': min_usage_threshold
        }
        
        return jsonify({
            'success': True,
            'parts': parts_data[:500],  # Limit to first 500 parts
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error calculating inventory turns: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_part_metrics(row, months, lead_time_days, target_turns, z_score):
    """
    Calculate inventory metrics for a single part
    """
    try:
        part_no = row['PartNo']
        description = row['Description'] or ''
        total_usage = float(row['TotalUsage'] or 0)
        current_stock = float(row['CurrentStock'] or 0)
        cost = float(row['Cost'] or 0)
        
        if total_usage <= 0:
            return None
        
        # Calculate time-based metrics
        analysis_days = months * 30
        avg_daily_usage = total_usage / analysis_days
        avg_monthly_usage = total_usage / months
        
        # Calculate usage variability from monthly data
        usage_std_dev = calculate_usage_variability(row.get('MonthlyUsageData', ''), months)
        
        # Calculate optimal order quantity for target turns
        # Target Days of Supply = 365 / target_turns
        target_days_supply = 365 / target_turns
        optimal_order_qty = max(1, round(avg_daily_usage * target_days_supply))
        
        # Calculate safety stock using standard formula
        # Safety Stock = Z-score × σ × √Lead Time
        if usage_std_dev > 0:
            safety_stock = max(0, round(z_score * usage_std_dev * np.sqrt(lead_time_days / 30)))
        else:
            safety_stock = round(avg_daily_usage * lead_time_days * 0.5)  # 50% buffer if no variability
        
        # Calculate reorder point (min level)
        reorder_point = max(1, round((avg_daily_usage * lead_time_days) + safety_stock))
        
        # Calculate max level
        max_level = reorder_point + optimal_order_qty
        
        # Calculate current turns
        if current_stock > 0 and cost > 0:
            current_turns = (total_usage * cost) / (current_stock * cost) * (12 / months)
        else:
            current_turns = 0
        
        # Determine recommended action
        recommended_action = get_recommended_action(current_turns, target_turns, current_stock, reorder_point, max_level)
        
        # Calculate annual value
        annual_usage = total_usage * (12 / months)
        annual_value = annual_usage * cost
        
        return {
            'part_number': part_no,
            'description': description[:100],  # Truncate long descriptions
            'last_12mo_usage': int(total_usage * (12 / months)),  # Annualized
            'avg_monthly_usage': round(avg_monthly_usage, 1),
            'avg_daily_usage': round(avg_daily_usage, 2),
            'usage_std_dev': round(usage_std_dev, 2),
            'optimal_order_qty': optimal_order_qty,
            'reorder_point_min': reorder_point,
            'max_level': max_level,
            'current_stock': int(current_stock),
            'current_turns': round(current_turns, 1),
            'target_turns': target_turns,
            'recommended_action': recommended_action,
            'cost_per_unit': round(cost, 2),
            'annual_value': round(annual_value, 2),
            'safety_stock': safety_stock
        }
        
    except Exception as e:
        logger.error(f"Error calculating metrics for part {row.get('PartNo', 'unknown')}: {str(e)}")
        return None

def calculate_usage_variability(monthly_data_str, months):
    """
    Calculate standard deviation of monthly usage
    """
    try:
        if not monthly_data_str or monthly_data_str == 'None':
            return 0
        
        # Parse the monthly usage data
        # Format: "2024-01:5|2024-02:3|2024-03:8"
        monthly_usage = {}
        
        if '|' in monthly_data_str:
            for entry in monthly_data_str.split('|'):
                if ':' in entry and entry.strip():
                    try:
                        month, qty = entry.split(':')
                        monthly_usage[month] = float(qty)
                    except:
                        continue
        
        if len(monthly_usage) < 2:
            return 0
        
        # Fill in missing months with 0
        usage_values = list(monthly_usage.values())
        
        # Calculate standard deviation
        if len(usage_values) > 1:
            return np.std(usage_values, ddof=1)
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Error calculating usage variability: {str(e)}")
        return 0

def get_recommended_action(current_turns, target_turns, current_stock, reorder_point, max_level):
    """
    Determine recommended action based on current vs target performance
    """
    if current_stock <= reorder_point:
        return "Order now"
    elif current_stock > max_level:
        return "Reduce stock"
    elif current_turns > target_turns * 1.2:
        return "Consider increasing stock"
    elif current_turns < target_turns * 0.8:
        return "Reduce stock"
    elif abs(current_turns - target_turns) > target_turns * 0.3:
        return "Review usage pattern"
    else:
        return "Optimal"

@parts_inventory_bp.route('/api/parts/inventory-summary', methods=['GET'])
@jwt_required()
def get_inventory_summary():
    """
    Get high-level inventory summary statistics
    """
    try:
        db = AzureSQLService()
        
        summary_query = """
        SELECT 
            COUNT(*) as total_parts,
            SUM(CASE WHEN OnHand > 0 THEN 1 ELSE 0 END) as parts_in_stock,
            SUM(OnHand * Cost) as total_inventory_value,
            AVG(Cost) as avg_part_cost,
            COUNT(CASE WHEN OnHand = 0 THEN 1 END) as zero_stock_parts,
            COUNT(CASE WHEN OnHand < MinStock THEN 1 END) as below_min_parts
        FROM ben002.Parts
        WHERE Cost > 0
        """
        
        result = db.execute_query(summary_query)
        
        if result:
            summary = result[0]
            return jsonify({
                'success': True,
                'summary': {
                    'total_parts': summary['total_parts'],
                    'parts_in_stock': summary['parts_in_stock'],
                    'total_inventory_value': round(float(summary['total_inventory_value'] or 0), 2),
                    'avg_part_cost': round(float(summary['avg_part_cost'] or 0), 2),
                    'zero_stock_parts': summary['zero_stock_parts'],
                    'below_min_parts': summary['below_min_parts']
                }
            })
        else:
            return jsonify({
                'success': True,
                'summary': {
                    'total_parts': 0,
                    'parts_in_stock': 0,
                    'total_inventory_value': 0,
                    'avg_part_cost': 0,
                    'zero_stock_parts': 0,
                    'below_min_parts': 0
                }
            })
        
    except Exception as e:
        logger.error(f"Error getting inventory summary: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parts_inventory_bp.route('/api/parts/part-detail', methods=['GET'])
@jwt_required()
def get_part_detail():
    """
    Get detailed information for a specific part including usage history
    """
    try:
        part_no = request.args.get('part_no')
        if not part_no:
            return jsonify({
                'success': False,
                'error': 'Part number is required'
            }), 400
        
        db = AzureSQLService()
        
        # Get part master data
        part_query = f"""
        SELECT 
            PartNo,
            Description,
            Cost,
            List,
            OnHand,
            Allocated,
            OnOrder,
            BackOrder,
            MinStock,
            MaxStock,
            Bin
        FROM ben002.Parts
        WHERE PartNo = '{part_no}'
        """
        
        part_result = db.execute_query(part_query)
        if not part_result:
            return jsonify({
                'success': False,
                'error': 'Part not found'
            }), 404
        
        # Get usage history by month for last 12 months
        usage_query = f"""
        WITH MonthlyUsage AS (
            SELECT 
                YEAR(ir.InvoiceDate) as Year,
                MONTH(ir.InvoiceDate) as Month,
                SUM(COALESCE(id.Quantity, 0)) as SoldQty,
                SUM(COALESCE(id.Quantity * id.Price, 0)) as SoldValue
            FROM ben002.InvoiceDetail id
            JOIN ben002.InvoiceReg ir ON id.InvoiceNo = ir.InvoiceNo
            WHERE id.PartNo = '{part_no}'
            AND ir.InvoiceDate >= DATEADD(MONTH, -12, GETDATE())
            GROUP BY YEAR(ir.InvoiceDate), MONTH(ir.InvoiceDate)
            
            UNION ALL
            
            SELECT 
                YEAR(wo.OpenDate) as Year,
                MONTH(wo.OpenDate) as Month,
                SUM(COALESCE(wop.Qty, 0)) as UsedQty,
                SUM(COALESCE(wop.Qty * wop.Cost, 0)) as UsedValue
            FROM ben002.WOParts wop
            JOIN ben002.WO wo ON wop.WONo = wo.WONo
            WHERE wop.PartNo = '{part_no}'
            AND wo.OpenDate >= DATEADD(MONTH, -12, GETDATE())
            GROUP BY YEAR(wo.OpenDate), MONTH(wo.OpenDate)
        )
        SELECT 
            Year,
            Month,
            SUM(SoldQty) as TotalQuantity,
            SUM(SoldValue) as TotalValue
        FROM MonthlyUsage
        GROUP BY Year, Month
        ORDER BY Year, Month
        """
        
        usage_history = db.execute_query(usage_query)
        
        return jsonify({
            'success': True,
            'part': part_result[0],
            'usage_history': usage_history
        })
        
    except Exception as e:
        logger.error(f"Error getting part detail: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500