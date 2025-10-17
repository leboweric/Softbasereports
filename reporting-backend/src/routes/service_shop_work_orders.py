from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
import logging

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
        db = AzureSQLService()
        
        # DEBUG QUERY 1: Investigate work order types
        debug_type_query = """
        SELECT DISTINCT 
            Type,
            COUNT(*) as Count
        FROM [ben002].WO
        WHERE ClosedDate IS NULL
        GROUP BY Type
        ORDER BY COUNT(*) DESC
        """
        
        debug_results = db.execute_query(debug_type_query)
        logger.info("=== DEBUG: Work Order Types ===")
        for row in debug_results:
            logger.info(f"Type: {row['Type']}, Count: {row['Count']}")
        
        # DEBUG QUERY 2: Investigate WOMisc descriptions for labor
        debug_misc_query = """
        SELECT DISTINCT TOP 30 Description 
        FROM [ben002].WOMisc 
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
        debug_quotes_query = """
        SELECT TOP 20
            wm.WONo,
            wm.Description,
            wm.Sell,
            w.Type
        FROM [ben002].WOMisc wm
        INNER JOIN [ben002].WO w ON wm.WONo = w.WONo
        LEFT JOIN [ben002].Customer c ON w.BillTo = c.Number
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
        
        query = """
        SELECT 
            w.WONo,
            w.BillTo as CustomerNo,
            c.Name as CustomerName,
            w.UnitNo,
            w.SerialNo,
            w.OpenDate,
            
            -- Quoted labor
            COALESCE(quoted.QuotedAmount, 0) as QuotedAmount,
            CASE 
                WHEN quoted.QuotedAmount > 0 THEN quoted.QuotedAmount / 189.0
                ELSE 0
            END as QuotedHours,
            
            -- Actual labor hours
            COALESCE(SUM(l.Hours), 0) as ActualHours,
            
            -- Percentage used
            CASE 
                WHEN quoted.QuotedAmount IS NULL OR quoted.QuotedAmount = 0 THEN 0
                ELSE (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100
            END as PercentUsed,
            
            -- Alert level
            CASE 
                WHEN quoted.QuotedAmount IS NULL OR quoted.QuotedAmount = 0 THEN 'NO_QUOTE'
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 100 THEN 'CRITICAL'
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 90 THEN 'RED'
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 80 THEN 'YELLOW'
                ELSE 'GREEN'
            END as AlertLevel

        FROM [ben002].WO w
        
        LEFT JOIN [ben002].Customer c ON w.BillTo = c.Number
        
        LEFT JOIN (
            SELECT 
                WONo,
                SUM(Sell) as QuotedAmount
            FROM [ben002].WOQuote
            WHERE Type = 'L'  -- L = Labor quotes
            GROUP BY WONo
        ) quoted ON w.WONo = quoted.WONo
        
        LEFT JOIN [ben002].WOLabor l ON w.WONo = l.WONo
        
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
        
        GROUP BY 
            w.WONo, w.BillTo, c.Name, w.UnitNo, w.SerialNo, 
            w.OpenDate, quoted.QuotedAmount
        
        ORDER BY 
            CASE 
                WHEN quoted.QuotedAmount IS NULL THEN 4
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 100 THEN 1
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 90 THEN 2
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 80 THEN 3
                ELSE 5
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
                    'quoted_amount': float(row['QuotedAmount']) if row['QuotedAmount'] else 0,
                    'quoted_hours': float(row['QuotedHours']) if row['QuotedHours'] else 0,
                    'actual_hours': float(row['ActualHours']) if row['ActualHours'] else 0,
                    'percent_used': float(row['PercentUsed']) if row['PercentUsed'] else 0,
                    'alert_level': row['AlertLevel']
                })
        
        # Calculate summary stats
        total_work_orders = len(work_orders)
        critical_count = len([wo for wo in work_orders if wo['alert_level'] == 'CRITICAL'])
        red_count = len([wo for wo in work_orders if wo['alert_level'] == 'RED'])
        yellow_count = len([wo for wo in work_orders if wo['alert_level'] == 'YELLOW'])
        warning_count = red_count + yellow_count
        
        # Calculate hours at risk (RED + CRITICAL)
        hours_at_risk = sum(wo['actual_hours'] for wo in work_orders 
                          if wo['alert_level'] in ['RED', 'CRITICAL'])
        
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
                'warning_count': warning_count,
                'hours_at_risk': hours_at_risk
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
        db = AzureSQLService()
        
        # Get actual WOMisc records for open shop WOs
        query = """
        SELECT DISTINCT TOP 50
            wm.WONo,
            wm.Description,
            wm.Sell,
            w.Type
        FROM [ben002].WOMisc wm
        INNER JOIN [ben002].WO w ON wm.WONo = w.WONo
        LEFT JOIN [ben002].Customer c ON w.BillTo = c.Number
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
        db = AzureSQLService()
        
        # Get WO record for known quoted work order
        query = """
        SELECT TOP 5 *
        FROM [ben002].WO
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
        db = AzureSQLService()
        
        # Simple query - just get everything from WOMisc for this WO
        query = """
        SELECT 
            WONo,
            Description,
            Sell
        FROM [ben002].WOMisc
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
        db = AzureSQLService()
        
        # Just get ALL tables, no schema filter
        query = """
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
        
        # Filter for ben002 schema
        ben002_tables = [t['table'] for t in all_tables if t['schema'] == 'ben002']
        
        # Filter for relevant keywords
        rate_tables = [t for t in ben002_tables if any(keyword in t.lower() for keyword in ['flat', 'rate', 'quote', 'estimate', 'labor', 'service', 'charge'])]
        
        return jsonify({
            'total_tables': len(all_tables),
            'all_tables': all_tables,
            'ben002_tables': ben002_tables,
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
        db = AzureSQLService()
        
        # Query 1: Get all column names from SQL Server system tables
        columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
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
        data_query = """
        SELECT TOP 3 *
        FROM [ben002].WOQuote
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