from flask import jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from src.routes.reports import reports_bp
import logging

logger = logging.getLogger(__name__)

@reports_bp.route('/departments/rental/deep-search', methods=['GET'])
@jwt_required()
def rental_deep_search():
    """Deep search to find where rental customer data is actually stored"""
    try:
        db = AzureSQLService()
        results = {}
        
        # Test with a serial number that's on rent
        test_serial = '99W15913'  # One that shows RENTAL FLEET
        
        # 1. Check ALL columns in Equipment table for this serial
        try:
            query = """
            SELECT * FROM ben002.Equipment 
            WHERE SerialNo = %s
            """
            equip_result = db.execute_query(query, [test_serial])
            if equip_result:
                results['equipment_all_fields'] = equip_result[0]
        except Exception as e:
            results['equipment_all_fields'] = str(e)
        
        # 2. Find ALL tables that reference this serial number
        try:
            query = """
            SELECT DISTINCT 
                t.TABLE_NAME,
                c.COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS c
            JOIN INFORMATION_SCHEMA.TABLES t ON c.TABLE_NAME = t.TABLE_NAME
            WHERE c.TABLE_SCHEMA = 'ben002'
            AND c.DATA_TYPE IN ('nvarchar', 'varchar', 'char')
            AND c.CHARACTER_MAXIMUM_LENGTH >= 8
            ORDER BY t.TABLE_NAME, c.COLUMN_NAME
            """
            tables_to_check = db.execute_query(query)
            
            tables_with_serial = []
            for table_info in tables_to_check[:100]:  # Limit to first 100 to avoid timeout
                table = table_info['TABLE_NAME']
                column = table_info['COLUMN_NAME']
                try:
                    check_query = f"""
                    SELECT TOP 1 '{table}' as TableName, '{column}' as ColumnName
                    FROM ben002.[{table}]
                    WHERE [{column}] = %s
                    """
                    if db.execute_query(check_query, [test_serial]):
                        tables_with_serial.append(f"{table}.{column}")
                except:
                    pass
            
            results['tables_containing_serial'] = tables_with_serial
        except Exception as e:
            results['tables_containing_serial'] = str(e)
        
        # 3. Check for ANY work order with Type='R' (Rental) that has customer info
        try:
            query = """
            SELECT TOP 10
                wo.WONo,
                wo.Type,
                wo.SerialNo,
                wo.UnitNo,
                wo.BillTo,
                c1.Name as BillToName,
                wo.ShipTo,
                wo.ShipName,
                wo.RentalContractNo,
                wo.RentalPeriod,
                wo.RentalStart,
                wo.RentalEnd
            FROM ben002.WO wo
            LEFT JOIN ben002.Customer c1 ON wo.BillTo = c1.Number
            WHERE wo.Type = 'R'
            AND wo.SerialNo IS NOT NULL
            ORDER BY wo.OpenDate DESC
            """
            results['rental_work_orders'] = db.execute_query(query)
        except Exception as e:
            results['rental_work_orders'] = str(e)
        
        # 4. Check most recent invoices for this equipment
        try:
            query = """
            SELECT TOP 5
                i.InvoiceNo,
                i.InvoiceDate,
                i.BillTo,
                i.BillToName,
                i.ControlNo,
                i.SaleCode,
                i.Department
            FROM ben002.InvoiceReg i
            WHERE i.ControlNo IN (
                SELECT ControlNo FROM ben002.Equipment WHERE SerialNo = %s
            )
            ORDER BY i.InvoiceDate DESC
            """
            results['recent_invoices'] = db.execute_query(query, [test_serial])
        except Exception as e:
            results['recent_invoices'] = str(e)
        
        # 5. Check if there's a RentalEquipment or EquipmentRental table
        try:
            query = """
            SELECT TABLE_NAME, TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ben002'
            AND (
                TABLE_NAME LIKE '%RentalEquip%'
                OR TABLE_NAME LIKE '%EquipRental%'
                OR TABLE_NAME LIKE '%EquipmentRental%'
                OR TABLE_NAME LIKE '%RentalUnit%'
            )
            """
            results['rental_equipment_tables'] = db.execute_query(query)
        except Exception as e:
            results['rental_equipment_tables'] = str(e)
        
        # 6. Check WORental for customer linkage
        try:
            query = """
            SELECT TOP 10
                wr.*,
                wo.BillTo,
                c.Name as CustomerName
            FROM ben002.WORental wr
            INNER JOIN ben002.WO wo ON wr.WONo = wo.WONo
            LEFT JOIN ben002.Customer c ON wo.BillTo = c.Number
            WHERE wr.SerialNo = %s
            ORDER BY wo.OpenDate DESC
            """
            results['worental_details'] = db.execute_query(query, [test_serial])
        except Exception as e:
            results['worental_details'] = str(e)
        
        # 7. Look for a "current rental" or "active rental" view
        try:
            query = """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.VIEWS
            WHERE TABLE_SCHEMA = 'ben002'
            AND (
                TABLE_NAME LIKE '%Current%Rental%'
                OR TABLE_NAME LIKE '%Active%Rental%'
                OR TABLE_NAME LIKE '%Rental%Current%'
                OR TABLE_NAME LIKE '%Rental%Active%'
                OR TABLE_NAME LIKE '%OnRent%'
            )
            """
            results['rental_views'] = db.execute_query(query)
        except Exception as e:
            results['rental_views'] = str(e)
        
        # 8. Check if there's a ShipTo or Delivery address in Equipment
        try:
            query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002'
            AND TABLE_NAME = 'Equipment'
            AND (
                COLUMN_NAME LIKE '%Ship%'
                OR COLUMN_NAME LIKE '%Deliver%'
                OR COLUMN_NAME LIKE '%Current%'
                OR COLUMN_NAME LIKE '%Renter%'
            )
            """
            results['equipment_ship_columns'] = db.execute_query(query)
        except Exception as e:
            results['equipment_ship_columns'] = str(e)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in rental deep search: {str(e)}")
        return jsonify({'error': str(e)}), 500