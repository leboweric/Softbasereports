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
        logger.info("Starting inventory turns calculation")
        
        # Get query parameters with validation
        try:
            months = int(request.args.get('months', 12))
            lead_time_days = int(request.args.get('lead_time_days', 14))
            service_level = float(request.args.get('service_level', 0.95))
            target_turns = float(request.args.get('target_turns', 5.0))
            min_usage_threshold = int(request.args.get('min_usage', 5))
            logger.info(f"Parameters: months={months}, lead_time_days={lead_time_days}, service_level={service_level}, target_turns={target_turns}, min_usage={min_usage_threshold}")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameters: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Invalid parameters: {str(e)}'
            }), 400
        
        # Initialize database connection
        try:
            db = AzureSQLService()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Database connection failed: {str(e)}'
            }), 500
        
        # Calculate date range for analysis
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            logger.info(f"Analyzing parts usage from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        except Exception as e:
            logger.error(f"Date calculation error: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Date calculation error: {str(e)}'
            }), 500
        
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
        
        # Execute the query with detailed error handling
        try:
            logger.info("Executing parts usage query...")
            logger.debug(f"Query: {usage_query[:500]}...")  # Log first 500 chars of query
            usage_results = db.execute_query(usage_query)
            logger.info(f"Query executed successfully, returned {len(usage_results) if usage_results else 0} rows")
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            logger.error(f"Query that failed: {usage_query}")
            return jsonify({
                'success': False,
                'error': f'Database query failed: {str(e)}',
                'query_error': True
            }), 500
        
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
        try:
            df = pd.DataFrame(usage_results)
            logger.info(f"Created DataFrame with {len(df)} rows and columns: {list(df.columns)}")
        except Exception as e:
            logger.error(f"Failed to create DataFrame: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to process data: {str(e)}',
                'data_processing_error': True
            }), 500
        
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
        # Extract data with error handling
        try:
            part_no = row['PartNo']
            description = row['Description'] or ''
            total_usage = float(row['TotalUsage'] or 0)
            current_stock = float(row['CurrentStock'] or 0)
            cost = float(row['Cost'] or 0)
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error extracting data for part: {str(e)}, row data: {dict(row)}")
            return None
        
        if total_usage <= 0:
            logger.debug(f"Skipping part {part_no} - no usage data")
            return None
        
        # Calculate time-based metrics with error checking
        try:
            analysis_days = months * 30
            avg_daily_usage = total_usage / analysis_days if analysis_days > 0 else 0
            avg_monthly_usage = total_usage / months if months > 0 else 0
        except (ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating time metrics for part {part_no}: {str(e)}")
            return None
        
        # Calculate usage variability from monthly data
        try:
            usage_std_dev = calculate_usage_variability(row.get('MonthlyUsageData', ''), months)
        except Exception as e:
            logger.error(f"Error calculating usage variability for part {part_no}: {str(e)}")
            usage_std_dev = 0
        
        # Calculate optimal order quantity for target turns
        try:
            target_days_supply = 365 / target_turns if target_turns > 0 else 365
            optimal_order_qty = max(1, round(avg_daily_usage * target_days_supply))
        except (ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating optimal order quantity for part {part_no}: {str(e)}")
            optimal_order_qty = 1
        
        # Calculate safety stock using standard formula
        try:
            if usage_std_dev > 0:
                safety_stock = max(0, round(z_score * usage_std_dev * np.sqrt(lead_time_days / 30)))
            else:
                safety_stock = round(avg_daily_usage * lead_time_days * 0.5)  # 50% buffer if no variability
        except Exception as e:
            logger.error(f"Error calculating safety stock for part {part_no}: {str(e)}")
            safety_stock = round(avg_daily_usage * 7)  # Default to 7 days buffer
        
        # Calculate reorder point (min level)
        try:
            reorder_point = max(1, round((avg_daily_usage * lead_time_days) + safety_stock))
        except Exception as e:
            logger.error(f"Error calculating reorder point for part {part_no}: {str(e)}")
            reorder_point = 1
        
        # Calculate max level
        try:
            max_level = reorder_point + optimal_order_qty
        except Exception as e:
            logger.error(f"Error calculating max level for part {part_no}: {str(e)}")
            max_level = reorder_point + 1
        
        # Calculate current turns
        try:
            if current_stock > 0 and cost > 0:
                current_turns = (total_usage * cost) / (current_stock * cost) * (12 / months)
            else:
                current_turns = 0
        except (ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating current turns for part {part_no}: {str(e)}")
            current_turns = 0
        
        # Determine recommended action
        try:
            recommended_action = get_recommended_action(current_turns, target_turns, current_stock, reorder_point, max_level)
        except Exception as e:
            logger.error(f"Error determining recommended action for part {part_no}: {str(e)}")
            recommended_action = "Review usage pattern"
        
        # Calculate annual value
        try:
            annual_usage = total_usage * (12 / months) if months > 0 else total_usage
            annual_value = annual_usage * cost
        except Exception as e:
            logger.error(f"Error calculating annual value for part {part_no}: {str(e)}")
            annual_usage = total_usage
            annual_value = 0
        
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

@parts_inventory_bp.route('/api/parts/test-tables', methods=['GET'])
@jwt_required()
def test_tables():
    """
    Test endpoint to verify table and column names exist
    """
    try:
        db = AzureSQLService()
        logger.info("Testing database table and column access...")
        
        results = {}
        
        # Test 1: Check if Parts table exists and get column names
        try:
            parts_schema_query = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'Parts'
            ORDER BY ORDINAL_POSITION
            """
            parts_columns = db.execute_query(parts_schema_query)
            results['parts_table'] = {
                'exists': len(parts_columns) > 0,
                'columns': parts_columns,
                'column_count': len(parts_columns)
            }
            logger.info(f"Parts table has {len(parts_columns)} columns")
        except Exception as e:
            logger.error(f"Error checking Parts table: {str(e)}")
            results['parts_table'] = {'error': str(e)}
        
        # Test 2: Sample Parts data
        try:
            parts_sample_query = """
            SELECT TOP 3 PartNo, Description, Cost, List, OnHand
            FROM ben002.Parts 
            WHERE PartNo IS NOT NULL AND PartNo != ''
            """
            parts_sample = db.execute_query(parts_sample_query)
            results['parts_sample'] = {
                'success': True,
                'sample_data': parts_sample,
                'row_count': len(parts_sample)
            }
            logger.info(f"Parts table sample query returned {len(parts_sample)} rows")
        except Exception as e:
            logger.error(f"Error sampling Parts table: {str(e)}")
            results['parts_sample'] = {'error': str(e)}
        
        # Test 3: Check if InvoiceDetail table exists
        try:
            invoice_detail_query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'InvoiceDetail'
            ORDER BY ORDINAL_POSITION
            """
            invoice_columns = db.execute_query(invoice_detail_query)
            results['invoice_detail_table'] = {
                'exists': len(invoice_columns) > 0,
                'columns': invoice_columns,
                'column_count': len(invoice_columns)
            }
            logger.info(f"InvoiceDetail table has {len(invoice_columns)} columns")
        except Exception as e:
            logger.error(f"Error checking InvoiceDetail table: {str(e)}")
            results['invoice_detail_table'] = {'error': str(e)}
        
        # Test 4: Check if WOParts table exists
        try:
            woparts_query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'WOParts'
            ORDER BY ORDINAL_POSITION
            """
            woparts_columns = db.execute_query(woparts_query)
            results['woparts_table'] = {
                'exists': len(woparts_columns) > 0,
                'columns': woparts_columns,
                'column_count': len(woparts_columns)
            }
            logger.info(f"WOParts table has {len(woparts_columns)} columns")
        except Exception as e:
            logger.error(f"Error checking WOParts table: {str(e)}")
            results['woparts_table'] = {'error': str(e)}
        
        # Test 5: Test join between Parts and InvoiceDetail
        try:
            join_test_query = """
            SELECT TOP 3 
                p.PartNo, 
                p.Description,
                id.Quantity,
                ir.InvoiceDate
            FROM ben002.Parts p
            LEFT JOIN ben002.InvoiceDetail id ON p.PartNo = id.PartNo
            LEFT JOIN ben002.InvoiceReg ir ON id.InvoiceNo = ir.InvoiceNo
            WHERE p.PartNo IS NOT NULL 
            AND ir.InvoiceDate >= DATEADD(MONTH, -1, GETDATE())
            """
            join_test = db.execute_query(join_test_query)
            results['join_test'] = {
                'success': True,
                'sample_joins': join_test,
                'row_count': len(join_test)
            }
            logger.info(f"Join test returned {len(join_test)} rows")
        except Exception as e:
            logger.error(f"Error testing joins: {str(e)}")
            results['join_test'] = {'error': str(e)}
        
        # Test 6: Check for required imports
        import_status = {
            'pandas': 'pd' in globals(),
            'numpy': 'np' in globals(),
            'scipy': HAS_SCIPY,
            'datetime': 'datetime' in globals(),
            'logging': 'logging' in globals()
        }
        results['imports'] = import_status
        
        return jsonify({
            'success': True,
            'test_results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@parts_inventory_bp.route('/api/parts/schema-tables', methods=['GET'])
@jwt_required()
def get_schema_tables():
    """
    Discover all tables in ben002 schema to find correct table names
    """
    try:
        db = AzureSQLService()
        logger.info("Discovering tables in ben002 schema...")
        
        # Get all tables in ben002 schema
        tables_query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002'
        ORDER BY TABLE_NAME
        """
        
        all_tables = db.execute_query(tables_query)
        
        # Filter for relevant tables (Invoice, Parts, WO related)
        relevant_tables = []
        for table in all_tables:
            table_name = table['TABLE_NAME'].lower()
            if any(keyword in table_name for keyword in ['invoice', 'part', 'wo', 'work']):
                relevant_tables.append(table)
        
        # Get column info for relevant tables
        table_details = {}
        for table in relevant_tables[:10]:  # Limit to first 10 to avoid timeout
            table_name = table['TABLE_NAME']
            try:
                columns_query = f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = db.execute_query(columns_query)
                
                # Get sample data
                sample_query = f"""
                SELECT TOP 3 *
                FROM ben002.{table_name}
                """
                try:
                    sample_data = db.execute_query(sample_query)
                except:
                    sample_data = []
                
                table_details[table_name] = {
                    'schema_info': table,
                    'columns': columns,
                    'sample_data': sample_data,
                    'column_count': len(columns),
                    'sample_row_count': len(sample_data)
                }
                
            except Exception as e:
                logger.error(f"Error getting details for table {table_name}: {str(e)}")
                table_details[table_name] = {
                    'schema_info': table,
                    'error': str(e)
                }
        
        # Specifically look for common variations
        specific_checks = {
            'invoice_tables': [],
            'parts_tables': [],
            'wo_tables': []
        }
        
        for table in all_tables:
            table_name = table['TABLE_NAME'].lower()
            if 'invoice' in table_name:
                specific_checks['invoice_tables'].append(table['TABLE_NAME'])
            elif 'part' in table_name:
                specific_checks['parts_tables'].append(table['TABLE_NAME'])
            elif 'wo' in table_name or 'work' in table_name:
                specific_checks['wo_tables'].append(table['TABLE_NAME'])
        
        return jsonify({
            'success': True,
            'all_tables_count': len(all_tables),
            'relevant_tables': relevant_tables,
            'table_details': table_details,
            'categorized_tables': specific_checks,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error discovering schema tables: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@parts_inventory_bp.route('/api/parts/table-sample/<table_name>', methods=['GET'])
@jwt_required()
def get_table_sample(table_name):
    """
    Get detailed sample data from a specific table
    """
    try:
        db = AzureSQLService()
        logger.info(f"Getting sample data from table: {table_name}")
        
        # Validate table name exists
        check_query = f"""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = '{table_name}'
        """
        
        table_exists = db.execute_query(check_query)
        if not table_exists:
            return jsonify({
                'success': False,
                'error': f'Table ben002.{table_name} does not exist'
            }), 404
        
        # Get columns
        columns_query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        
        columns = db.execute_query(columns_query)
        
        # Get sample data
        sample_query = f"""
        SELECT TOP 10 *
        FROM ben002.{table_name}
        """
        
        sample_data = db.execute_query(sample_query)
        
        # Get row count
        count_query = f"""
        SELECT COUNT(*) as row_count
        FROM ben002.{table_name}
        """
        
        count_result = db.execute_query(count_query)
        total_rows = count_result[0]['row_count'] if count_result else 0
        
        return jsonify({
            'success': True,
            'table_name': table_name,
            'columns': columns,
            'sample_data': sample_data,
            'total_rows': total_rows,
            'sample_row_count': len(sample_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting table sample for {table_name}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'table_name': table_name,
            'timestamp': datetime.now().isoformat()
        }), 500

@parts_inventory_bp.route('/api/parts/simple-test', methods=['GET'])
@jwt_required()
def simple_test():
    """
    Simple test to verify basic table access and identify the exact error
    """
    try:
        db = AzureSQLService()
        logger.info("Starting simple test...")
        
        # Test 1: Simple Parts table query
        try:
            parts_query = "SELECT TOP 5 PartNo, Description, Cost, OnHand FROM ben002.Parts WHERE PartNo IS NOT NULL"
            logger.info(f"Testing Parts query: {parts_query}")
            parts_result = db.execute_query(parts_query)
            logger.info(f"Parts query succeeded, got {len(parts_result)} rows")
        except Exception as e:
            logger.error(f"Parts query failed: {str(e)}")
            return jsonify({
                'success': False,
                'test': 'parts_table',
                'error': str(e),
                'step': 1
            }), 500
        
        # Test 2: Simple InvoiceDetail query
        try:
            invoice_query = "SELECT TOP 5 PartNo, Quantity FROM ben002.InvoiceDetail WHERE PartNo IS NOT NULL"
            logger.info(f"Testing InvoiceDetail query: {invoice_query}")
            invoice_result = db.execute_query(invoice_query)
            logger.info(f"InvoiceDetail query succeeded, got {len(invoice_result)} rows")
        except Exception as e:
            logger.error(f"InvoiceDetail query failed: {str(e)}")
            return jsonify({
                'success': False,
                'test': 'invoice_detail_table',
                'error': str(e),
                'step': 2
            }), 500
        
        # Test 3: Simple WOParts query
        try:
            woparts_query = "SELECT TOP 5 PartNo, Qty FROM ben002.WOParts WHERE PartNo IS NOT NULL"
            logger.info(f"Testing WOParts query: {woparts_query}")
            woparts_result = db.execute_query(woparts_query)
            logger.info(f"WOParts query succeeded, got {len(woparts_result)} rows")
        except Exception as e:
            logger.error(f"WOParts query failed: {str(e)}")
            return jsonify({
                'success': False,
                'test': 'woparts_table',
                'error': str(e),
                'step': 3
            }), 500
        
        # Test 4: Simple join between Parts and InvoiceDetail
        try:
            join_query = """
            SELECT TOP 5 p.PartNo, p.Description, id.Quantity
            FROM ben002.Parts p
            LEFT JOIN ben002.InvoiceDetail id ON p.PartNo = id.PartNo
            WHERE p.PartNo IS NOT NULL
            """
            logger.info(f"Testing simple join: {join_query}")
            join_result = db.execute_query(join_query)
            logger.info(f"Simple join succeeded, got {len(join_result)} rows")
        except Exception as e:
            logger.error(f"Simple join failed: {str(e)}")
            return jsonify({
                'success': False,
                'test': 'simple_join',
                'error': str(e),
                'step': 4
            }), 500
        
        # Test 5: Date filtering (this might be the issue)
        try:
            date_query = """
            SELECT TOP 5 p.PartNo, ir.InvoiceDate
            FROM ben002.Parts p
            LEFT JOIN ben002.InvoiceDetail id ON p.PartNo = id.PartNo
            LEFT JOIN ben002.InvoiceReg ir ON id.InvoiceNo = ir.InvoiceNo
            WHERE ir.InvoiceDate >= '2024-01-01'
            """
            logger.info(f"Testing date filtering: {date_query}")
            date_result = db.execute_query(date_query)
            logger.info(f"Date filtering succeeded, got {len(date_result)} rows")
        except Exception as e:
            logger.error(f"Date filtering failed: {str(e)}")
            return jsonify({
                'success': False,
                'test': 'date_filtering',
                'error': str(e),
                'step': 5
            }), 500
        
        return jsonify({
            'success': True,
            'tests_passed': 5,
            'results': {
                'parts_count': len(parts_result),
                'invoice_detail_count': len(invoice_result),
                'woparts_count': len(woparts_result),
                'join_count': len(join_result),
                'date_filter_count': len(date_result)
            },
            'sample_data': {
                'parts': parts_result[:2],
                'invoice_detail': invoice_result[:2],
                'woparts': woparts_result[:2]
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in simple test: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'test': 'general_error',
            'timestamp': datetime.now().isoformat()
        }), 500