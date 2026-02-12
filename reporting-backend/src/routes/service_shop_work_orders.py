from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
import logging

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

logger = logging.getLogger(__name__)

service_shop_bp = Blueprint('service_shop', __name__)

@service_shop_bp.route('/api/reports/departments/service/shop-work-orders', methods=['GET'])
@jwt_required()
def get_shop_work_orders():
    """
    Get open shop work orders with cost overrun alerts.
    Compares actual labor hours vs quoted hours to prevent budget overruns.
    """
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        
        # DEBUG QUERY 1: Investigate work order types
        debug_type_query = f"""
        SELECT DISTINCT 
            Type,
            COUNT(*) as Count
        FROM [{schema}].WO
        WHERE ClosedDate IS NULL
        GROUP BY Type
        ORDER BY COUNT(*) DESC
        """
        
        debug_results = db.execute_query(debug_type_query)
        logger.info("=== DEBUG: Work Order Types ===")
        for row in debug_results:
            logger.info(f"Type: {row['Type']}, Count: {row['Count']}")
        
        # DEBUG QUERY 2: Investigate WOMisc descriptions for labor
        debug_misc_query = f"""
        SELECT DISTINCT TOP 30 Description 
        FROM [{schema}].WOMisc 
        WHERE Description LIKE '%LABOR%'
           OR Description LIKE '%SHOP%'
           OR Description LIKE '%REPAIR%'
        ORDER BY Description
        """
        
        misc_results = db.execute_query(debug_misc_query)
        logger.info("=== DEBUG: WOMisc Labor Descriptions ===")
        for row in misc_results:
            logger.info(f"Description: '{row['Description']}'")
        
        # DEBUG QUERY 3: Check specific work orders with quotes
        debug_quotes_query = f"""
        SELECT TOP 20
            wm.WONo,
            wm.Description,
            wm.Sell,
            w.Type
        FROM [{schema}].WOMisc wm
        INNER JOIN [{schema}].WO w ON wm.WONo = w.WONo
        LEFT JOIN [{schema}].Customer c ON w.BillTo = c.Number
        WHERE w.Type = 'SH'  -- Shop work orders only
          AND w.ClosedDate IS NULL
          AND w.WONo NOT LIKE '9%'  -- CRITICAL: Exclude quotes!
          AND c.Name NOT IN (
            'NEW EQUIP PREP - EXPENSE',
            'RENTAL FLEET - EXPENSE', 
            'USED EQUIP. PREP-EXPENSE',
            'SVC REWORK/SVC WARRANTY',
            'NEW EQ. INTNL RNTL/DEMO'
          )  -- Exclude internal expense accounts
          AND wm.Sell > 0
        ORDER BY wm.Sell DESC
        """
        
        quotes_results = db.execute_query(debug_quotes_query)
        logger.info("=== DEBUG: Sample WOMisc Records with Quotes ===")
        for row in quotes_results:
            logger.info(f"WO: {row['WONo']}, Type: {row['Type']}, Description: '{row['Description']}', Sell: {row['Sell']}")
        
        # Per Softbase support: Use LaborRate view joined via WO.LaborRate = LR.Code
        # to get the actual labor rate for each work order.
        # QuotedHours = QuotedAmount / (LaborRate * (1 - Discount/100))
        # Rounded to whole number since quotes are always in whole hours
        # Using NULLIF to prevent divide-by-zero errors
        # schema already defined at the start of the function

        query = f"""
        SELECT
            w.WONo,
            w.BillTo as CustomerNo,
            c.Name as CustomerName,
            w.UnitNo,
            w.SerialNo,
            w.OpenDate,

            -- Labor rate info (for debugging/transparency)
            lr.Rate as LaborRate,
            w.LaborDiscount,

            -- Quoted labor amount from WOQuote
            COALESCE(quoted.QuotedAmount, 0) as QuotedAmount,

            -- Calculate quoted hours using actual labor rate from LaborRate view
            -- Formula: QuotedAmount / (Rate * (1 - Discount/100))
            -- Round to whole number since quotes are always in whole hours
            -- Use NULLIF to handle divide-by-zero safely
            CASE
                WHEN quoted.QuotedAmount IS NULL OR quoted.QuotedAmount = 0 THEN 0
                WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                ELSE ROUND(quoted.QuotedAmount / 189.0, 0)  -- Fallback to $189 if no rate
            END as QuotedHours,

            -- Actual labor hours from WOLabor
            COALESCE(SUM(l.Hours), 0) as ActualHours,

            -- Percentage used: ActualHours / QuotedHours * 100
            -- Calculate QuotedHours first, then divide (using NULLIF to avoid divide-by-zero)
            COALESCE(
                COALESCE(SUM(l.Hours), 0) * 100.0 /
                NULLIF(
                    CASE
                        WHEN quoted.QuotedAmount IS NULL OR quoted.QuotedAmount = 0 THEN NULL
                        WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                        THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                        ELSE ROUND(quoted.QuotedAmount / 189.0, 0)
                    END,
                0),
            0) as PercentUsed,

            -- Alert level based on percentage used
            CASE
                WHEN quoted.QuotedAmount IS NULL OR quoted.QuotedAmount = 0 THEN 'NO_QUOTE'
                WHEN CASE
                        WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                        THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                        ELSE ROUND(quoted.QuotedAmount / 189.0, 0)
                     END IS NULL OR
                     CASE
                        WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                        THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                        ELSE ROUND(quoted.QuotedAmount / 189.0, 0)
                     END = 0 THEN 'NO_QUOTE'
                WHEN COALESCE(SUM(l.Hours), 0) * 100.0 /
                     NULLIF(CASE
                        WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                        THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                        ELSE ROUND(quoted.QuotedAmount / 189.0, 0)
                     END, 0) >= 100 THEN 'CRITICAL'
                WHEN COALESCE(SUM(l.Hours), 0) * 100.0 /
                     NULLIF(CASE
                        WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                        THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                        ELSE ROUND(quoted.QuotedAmount / 189.0, 0)
                     END, 0) >= 90 THEN 'RED'
                WHEN COALESCE(SUM(l.Hours), 0) * 100.0 /
                     NULLIF(CASE
                        WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                        THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                        ELSE ROUND(quoted.QuotedAmount / 189.0, 0)
                     END, 0) >= 80 THEN 'YELLOW'
                ELSE 'GREEN'
            END as AlertLevel

        FROM [{schema}].WO w

        LEFT JOIN [{schema}].Customer c ON w.BillTo = c.Number

        -- Join LaborRate view to get actual hourly rate for this work order
        LEFT JOIN [{schema}].LaborRate lr ON lr.Code = w.LaborRate

        -- Get quoted labor amount from WOQuote table
        LEFT JOIN (
            SELECT
                WONo,
                SUM(Amount) as QuotedAmount
            FROM [{schema}].WOQuote
            WHERE Type = 'L'  -- L = Labor quotes
            GROUP BY WONo
        ) quoted ON w.WONo = quoted.WONo

        LEFT JOIN [{schema}].WOLabor l ON w.WONo = l.WONo

        WHERE w.Type = 'SH'  -- Shop work orders only
          AND w.ClosedDate IS NULL
          AND w.DeleterUserId IS NULL  -- Exclude deleted work orders
          AND w.WONo NOT LIKE '9%'  -- CRITICAL: Exclude quotes!
          AND c.Name NOT IN (
            'NEW EQUIP PREP - EXPENSE',
            'RENTAL FLEET - EXPENSE',
            'USED EQUIP. PREP-EXPENSE',
            'SVC REWORK/SVC WARRANTY',
            'NEW EQ. INTNL RNTL/DEMO'
          )  -- Exclude internal expense accounts

        GROUP BY
            w.WONo, w.BillTo, c.Name, w.UnitNo, w.SerialNo,
            w.OpenDate, quoted.QuotedAmount, lr.Rate, w.LaborDiscount

        ORDER BY
            CASE
                WHEN quoted.QuotedAmount IS NULL OR quoted.QuotedAmount = 0 THEN 4
                ELSE
                    CASE
                        WHEN COALESCE(
                             COALESCE(SUM(l.Hours), 0) * 100.0 /
                             NULLIF(CASE
                                WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                                THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                                ELSE ROUND(quoted.QuotedAmount / 189.0, 0)
                             END, 0), 0) >= 100 THEN 1
                        WHEN COALESCE(
                             COALESCE(SUM(l.Hours), 0) * 100.0 /
                             NULLIF(CASE
                                WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                                THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                                ELSE ROUND(quoted.QuotedAmount / 189.0, 0)
                             END, 0), 0) >= 90 THEN 2
                        WHEN COALESCE(
                             COALESCE(SUM(l.Hours), 0) * 100.0 /
                             NULLIF(CASE
                                WHEN lr.Rate IS NOT NULL AND lr.Rate > 0 AND (1 - COALESCE(w.LaborDiscount, 0) / 100.0) > 0
                                THEN ROUND(quoted.QuotedAmount / NULLIF(lr.Rate * (1 - COALESCE(w.LaborDiscount, 0) / 100.0), 0), 0)
                                ELSE ROUND(quoted.QuotedAmount / 189.0, 0)
                             END, 0), 0) >= 80 THEN 3
                        ELSE 5
                    END
            END,
            w.OpenDate
        """
        
        results = db.execute_query(query)

        work_orders = []
        if results:
            for row in results:
                work_orders.append({
                    'wo_number': row['WONo'],
                    'customer_no': row['CustomerNo'],
                    'customer_name': row['CustomerName'] or 'Unknown',
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'open_date': row['OpenDate'].isoformat() if row['OpenDate'] else None,
                    'labor_rate': float(row['LaborRate']) if row['LaborRate'] else 189.0,
                    'labor_discount': float(row['LaborDiscount']) if row['LaborDiscount'] else 0,
                    'quoted_amount': float(row['QuotedAmount']) if row['QuotedAmount'] else 0,
                    'quoted_hours': int(row['QuotedHours']) if row['QuotedHours'] else 0,  # Now whole numbers
                    'actual_hours': float(row['ActualHours']) if row['ActualHours'] else 0,
                    'percent_used': float(row['PercentUsed']) if row['PercentUsed'] else 0,
                    'alert_level': row['AlertLevel']
                })
        
        # Calculate summary stats
        total_work_orders = len(work_orders)
        critical_count = len([wo for wo in work_orders if wo['alert_level'] == 'CRITICAL'])
        red_count = len([wo for wo in work_orders if wo['alert_level'] == 'RED'])
        yellow_count = len([wo for wo in work_orders if wo['alert_level'] == 'YELLOW'])
        no_quote_count = len([wo for wo in work_orders if wo['alert_level'] == 'NO_QUOTE'])
        warning_count = red_count + yellow_count
        
        # Calculate hours at risk and unbillable labor value
        critical_and_red = [wo for wo in work_orders if wo['alert_level'] in ['CRITICAL', 'RED']]
        
        hours_at_risk = 0
        for wo in critical_and_red:
            if wo['quoted_hours'] > 0:
                hours_over = wo['actual_hours'] - wo['quoted_hours']
                if hours_over > 0:
                    hours_at_risk += hours_over
        
        LABOR_RATE = 189
        unbillable_labor_value = hours_at_risk * LABOR_RATE
        
        # DEBUG: Log final results summary
        logger.info(f"=== DEBUG: Final Results Summary ===")
        logger.info(f"Total work orders found: {total_work_orders}")
        logger.info(f"Critical alerts: {critical_count}")
        logger.info(f"Red alerts: {red_count}")
        logger.info(f"Yellow alerts: {yellow_count}")
        logger.info(f"Work orders with quotes: {len([wo for wo in work_orders if wo['quoted_amount'] > 0])}")
        logger.info(f"Work orders with NO_QUOTE: {len([wo for wo in work_orders if wo['alert_level'] == 'NO_QUOTE'])}")
        
        return jsonify({
            'work_orders': work_orders,
            'summary': {
                'total_work_orders': total_work_orders,
                'critical_count': critical_count,
                'red_count': red_count,
                'yellow_count': yellow_count,
                'no_quote_count': no_quote_count,
                'warning_count': warning_count,
                'hours_at_risk': round(hours_at_risk, 1),
                'unbillable_labor_value': round(unbillable_labor_value, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching shop work orders: {str(e)}")
        return jsonify({'error': str(e)}), 500


@service_shop_bp.route('/api/reports/departments/service/shop-work-orders/debug-misc', methods=['GET'])
@jwt_required()
def debug_womisc_descriptions():
    """
    Debug endpoint: See actual WOMisc descriptions for open shop work orders
    """
    try:
        db = get_tenant_db()
        
        # Get actual WOMisc records for open shop WOs
        schema = get_tenant_schema()

        query = f"""
        SELECT DISTINCT TOP 50
            wm.WONo,
            wm.Description,
            wm.Sell,
            w.Type
        FROM [{schema}].WOMisc wm
        INNER JOIN [{schema}].WO w ON wm.WONo = w.WONo
        LEFT JOIN [{schema}].Customer c ON w.BillTo = c.Number
        WHERE w.Type = 'SH'
          AND w.ClosedDate IS NULL
          AND w.WONo NOT LIKE '9%'
          AND c.Name NOT IN (
            'NEW EQUIP PREP - EXPENSE',
            'RENTAL FLEET - EXPENSE', 
            'USED EQUIP. PREP-EXPENSE',
            'SVC REWORK/SVC WARRANTY',
            'NEW EQ. INTNL RNTL/DEMO'
          )
        ORDER BY wm.WONo DESC
        """
        
        results = db.execute_query(query)
        
        misc_items = []
        if results:
            for row in results:
                misc_items.append({
                    'WONo': row['WONo'],
                    'Description': row['Description'],
                    'Sell': float(row['Sell']) if row['Sell'] else 0,
                    'Type': row['Type']
                })
        
        return jsonify({
            'count': len(misc_items),
            'items': misc_items
        })
        
    except Exception as e:
        logger.error(f"Error in debug query: {str(e)}")
        return jsonify({'error': str(e)}), 500


@service_shop_bp.route('/api/reports/departments/service/shop-work-orders/debug-wo-fields', methods=['GET'])
@jwt_required()
def debug_wo_fields():
    """
    Debug: Check WO table for quote-related fields
    """
    try:
        db = get_tenant_db()
        
        # Get WO record for known quoted work order
        schema = get_tenant_schema()

        query = f"""
        SELECT TOP 5 *
        FROM [{schema}].WO
        WHERE Type = 'SH'
          AND WONo NOT LIKE '9%'
          AND ClosedDate IS NULL
        ORDER BY WONo DESC
        """
        
        results = db.execute_query(query)
        
        # Get column names
        cursor = db.get_connection().cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        
        work_orders = []
        for row in results:
            wo_dict = {}
            for i, col in enumerate(columns):
                wo_dict[col] = str(row[i]) if row[i] is not None else None
            work_orders.append(wo_dict)
        
        return jsonify({
            'columns': columns,
            'sample_work_orders': work_orders
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@service_shop_bp.route('/api/reports/departments/service/shop-work-orders/debug-find-quote', methods=['GET'])
@jwt_required()
def debug_find_quote():
    """
    Debug: Get ALL WOMisc records for WO 140000582 (known to have $3938 quote)
    """
    try:
        db = get_tenant_db()
        
        # Simple query - just get everything from WOMisc for this WO
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            WONo,
            Description,
            Sell
        FROM [{schema}].WOMisc
        WHERE WONo = '140000582'
        ORDER BY Sell DESC
        """
        
        results = db.execute_query(query)
        
        misc_items = []
        total = 0
        
        for row in results:
            sell_amount = float(row[2]) if row[2] else 0
            misc_items.append({
                'WONo': row[0],
                'Description': row[1],
                'Sell': sell_amount
            })
            total += sell_amount
        
        return jsonify({
            'wo_number': '140000582',
            'target_amount': 3938.00,
            'items_found': len(misc_items),
            'all_womisc_items': misc_items,
            'total_sell': total,
            'has_shop_repair_labor': any('SHOP' in item['Description'].upper() and 'REPAIR' in item['Description'].upper() for item in misc_items)
        })
        
    except Exception as e:
        logger.error(f"Error finding quote: {str(e)}")
        return jsonify({'error': str(e)}), 500


@service_shop_bp.route('/api/reports/departments/service/shop-work-orders/debug-tables', methods=['GET'])
@jwt_required()
def debug_tables():
    """
    Debug: List ALL tables in database (no schema filter)
    """
    try:
        db = get_tenant_db()
        
        # Just get ALL tables, no schema filter
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            SCHEMA_NAME(schema_id) as SchemaName,
            name as TableName
        FROM sys.tables 
        ORDER BY SchemaName, name
        """
        
        results = db.execute_query(query)
        
        all_tables = []
        for row in results:
            all_tables.append({
                'schema': row[0],
                'table': row[1]
            })
        
        # Filter for tenant schema
        schema = get_tenant_schema()
        tenant_tables = [t['table'] for t in all_tables if t['schema'] == schema]
        
        # Filter for relevant keywords
        rate_tables = [t for t in tenant_tables if any(keyword in t.lower() for keyword in ['flat', 'rate', 'quote', 'estimate', 'labor', 'service', 'charge'])]
        
        return jsonify({
            'total_tables': len(all_tables),
            'all_tables': all_tables,
            'tenant_tables': tenant_tables,
            'potentially_relevant': rate_tables
        })
        
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        return jsonify({'error': str(e)}), 500


@service_shop_bp.route('/api/reports/departments/service/shop-work-orders/debug-woquote', methods=['GET'])
@jwt_required()
def debug_woquote():
    """
    Debug: Get actual WOQuote column names from SQL Server metadata
    """
    try:
        db = get_tenant_db()

        # Query 1: Get all column names from SQL Server system tables
        columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
          AND TABLE_NAME = 'WOQuote'
        ORDER BY ORDINAL_POSITION
        """

        column_results = db.execute_query(columns_query)

        columns = []
        for row in column_results:
            columns.append({
                'name': row[0],
                'type': row[1]
            })

        # Query 2: Get actual data using the correct columns
        data_query = f"""
        SELECT TOP 3 *
        FROM [{schema}].WOQuote
        WHERE WONo = '140000582'
        """

        data_results = db.execute_query(data_query)

        return jsonify({
            'success': True,
            'columns': columns,
            'column_names': [c['name'] for c in columns],
            'record_count': len(data_results),
            'message': 'Check column_names to see all available columns'
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@service_shop_bp.route('/api/reports/departments/service/shop-work-orders/debug-labor-rates', methods=['GET'])
@jwt_required()
def debug_labor_rates():
    """
    Debug: Explore LaborRate view and WO labor rate fields
    Based on Softbase support recommendation
    """
    try:
        db = get_tenant_db()

        results = {}

        # Query 1: Get LaborRate view structure
        laborrate_structure_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
          AND TABLE_NAME = 'LaborRate'
        ORDER BY ORDINAL_POSITION
        """

        lr_columns = db.execute_query(laborrate_structure_query)
        results['laborrate_columns'] = [{'name': row[0], 'type': row[1]} for row in lr_columns]

        # Query 2: Sample LaborRate data
        laborrate_data_query = f"""
        SELECT TOP 10 *
        FROM [{schema}].LaborRate
        ORDER BY Code
        """

        lr_data = db.execute_query(laborrate_data_query)
        results['laborrate_sample'] = lr_data

        # Query 3: Check WO table for LaborRate and LaborDiscount columns
        wo_rate_structure_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
          AND TABLE_NAME = 'WO'
          AND COLUMN_NAME IN ('LaborRate', 'LaborDiscount')
        ORDER BY ORDINAL_POSITION
        """

        wo_rate_columns = db.execute_query(wo_rate_structure_query)
        results['wo_rate_columns'] = [{'name': row[0], 'type': row[1]} for row in wo_rate_columns]

        # Query 4: The query from Softbase support - sample of shop WOs with labor rates
        softbase_query = f"""
        SELECT TOP 10
            WO.WONO,
            WO.BillTo,
            WO.ShipName,
            WO.LaborRate as LaborRateCode,
            WO.LaborDiscount,
            LR.Rate as LaborRateAmount,
            LR.Code as RateCode,
            LR.Description as RateDescription
        FROM [{schema}].WO
        LEFT JOIN [{schema}].LaborRate LR on LR.Code = WO.LaborRate
        WHERE WO.Type = 'SH'
          AND WO.ClosedDate IS NULL
          AND WO.WONo NOT LIKE '9%'
        ORDER BY WO.WONo DESC
        """

        softbase_data = db.execute_query(softbase_query)
        results['wo_with_labor_rates'] = softbase_data

        # Query 5: Check WOLabor for SellRate field
        wolabor_structure_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
          AND TABLE_NAME = 'WOLabor'
          AND COLUMN_NAME IN ('Rate', 'SellRate', 'Hours', 'Sell', 'LaborRateType')
        ORDER BY ORDINAL_POSITION
        """

        wolabor_columns = db.execute_query(wolabor_structure_query)
        results['wolabor_columns'] = [{'name': row[0], 'type': row[1]} for row in wolabor_columns]

        # Query 6: Sample WOLabor with rates for open shop WOs
        wolabor_sample_query = f"""
        SELECT TOP 10
            WOL.WONo,
            WOL.MechanicNo,
            WOL.Hours,
            WOL.SellRate,
            WOL.Sell,
            WOL.LaborRateType
        FROM [{schema}].WOLabor WOL
        INNER JOIN [{schema}].WO W ON WOL.WONo = W.WONo
        WHERE W.Type = 'SH'
          AND W.ClosedDate IS NULL
          AND W.WONo NOT LIKE '9%'
        ORDER BY WOL.WONo DESC
        """

        wolabor_data = db.execute_query(wolabor_sample_query)
        results['wolabor_sample'] = wolabor_data

        return jsonify({
            'success': True,
            'results': results,
            'recommendation': 'Use LR.Rate joined via WO.LaborRate = LR.Code to get the actual labor rate per work order'
        })

    except Exception as e:
        logger.error(f"Error exploring labor rates: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500