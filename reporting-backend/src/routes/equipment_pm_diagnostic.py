from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
import logging

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

def get_tenant_schema():
    """Get the database schema for the current user's organization"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            if user and user.organization and user.organization.database_schema:
                return user.organization.database_schema
        return 'ben002'  # Fallback
    except:
        return 'ben002'



logger = logging.getLogger(__name__)

equipment_pm_diagnostic_bp = Blueprint('equipment_pm_diagnostic', __name__)

@equipment_pm_diagnostic_bp.route('/api/diagnostic/equipment-pm-fields', methods=['GET'])
@jwt_required()
def get_equipment_pm_fields():
    """
    Diagnostic endpoint to explore Equipment table structure for PM schedule fields.
    Looks for equipment from the Softbase PM report screenshot to find PM-related columns.
    """
    try:
        db = AzureSQLService()
        
        # Serial numbers from the Softbase report screenshot
        test_serial_numbers = ['35955', '35951', '38762', '61300', '900006']
        
        results_data = {
            'equipment_records': [],
            'all_columns': [],
            'pm_related_columns': [],
            'tables_found': []
        }
        
        # Step 1: Get ALL column names from Equipment table
        columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '{schema}' 
        AND TABLE_NAME = 'Equipment'
        ORDER BY ORDINAL_POSITION
        """
        
        logger.info("Fetching Equipment table columns...")
        columns = db.execute_query(columns_query)
        
        if columns:
            results_data['all_columns'] = [
                {
                    'name': col['COLUMN_NAME'],
                    'type': col['DATA_TYPE'],
                    'nullable': col['IS_NULLABLE'],
                    'max_length': col.get('CHARACTER_MAXIMUM_LENGTH')
                }
                for col in columns
            ]
            
            # Identify PM-related columns
            pm_keywords = ['pm', 'labor', 'service', 'maint', 'freq', 'next', 'last', 'schedule', 'date', 'interval']
            for col in columns:
                col_name_lower = col['COLUMN_NAME'].lower()
                if any(keyword in col_name_lower for keyword in pm_keywords):
                    results_data['pm_related_columns'].append({
                        'name': col['COLUMN_NAME'],
                        'type': col['DATA_TYPE']
                    })
        
        # Step 2: Look for equipment records from screenshot
        for serial_no in test_serial_numbers:
            query = f"""
            SELECT TOP 1 *
            FROM {schema}.Equipment e
            LEFT JOIN {schema}.Customer c ON e.CustomerNo = c.Number
            WHERE e.SerialNo = '{serial_no}' OR e.UnitNo = '{serial_no}'
            """
            
            logger.info(f"Searching for equipment: {serial_no}")
            equipment = db.execute_query(query)
            
            if equipment and len(equipment) > 0:
                record = equipment[0]
                
                # Convert to serializable format and filter out None/empty values
                equipment_data = {
                    'serial_no': serial_no,
                    'found': True,
                    'fields': {}
                }
                
                for key, value in record.items():
                    if value is not None and str(value).strip() != '':
                        # Convert datetime to string
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        equipment_data['fields'][key] = value
                
                results_data['equipment_records'].append(equipment_data)
                logger.info(f"Found equipment {serial_no} with {len(equipment_data['fields'])} populated fields")
            else:
                results_data['equipment_records'].append({
                    'serial_no': serial_no,
                    'found': False
                })
                logger.info(f"Equipment {serial_no} not found")
        
        # Step 3: Check for PM-related tables
        tables_query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = '{schema}'
        AND (
            TABLE_NAME LIKE '%PM%'
            OR TABLE_NAME LIKE '%Service%'
            OR TABLE_NAME LIKE '%Maint%'
            OR TABLE_NAME LIKE '%Schedule%'
            OR TABLE_NAME LIKE '%Contract%'
        )
        ORDER BY TABLE_NAME
        """
        
        logger.info("Searching for PM-related tables...")
        tables = db.execute_query(tables_query)
        
        if tables:
            results_data['tables_found'] = [row['TABLE_NAME'] for row in tables]
        
        # Step 4: Summary
        results_data['summary'] = {
            'total_columns': len(results_data['all_columns']),
            'pm_related_columns_count': len(results_data['pm_related_columns']),
            'equipment_found': len([r for r in results_data['equipment_records'] if r.get('found')]),
            'pm_tables_found': len(results_data['tables_found'])
        }
        
        return jsonify(results_data)
        
    except Exception as e:
        logger.error(f"Equipment PM diagnostic failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Failed to retrieve Equipment PM field information'
        }), 500


@equipment_pm_diagnostic_bp.route('/api/diagnostic/equipment-pm-sample', methods=['GET'])
@jwt_required()
def get_equipment_pm_sample():
    """
    Get a sample of equipment records that might have PM schedules.
    Looks for equipment with customers (not in stock).
    """
    try:
        db = AzureSQLService()
        
        schema = get_tenant_schema()

        
        query = f"""
        SELECT TOP 20
            e.SerialNo,
            e.UnitNo,
            e.Make,
            e.Model,
            e.CustomerNo,
            c.Name as CustomerName,
            c.City,
            c.State,
            e.RentalStatus,
            e.Location
        FROM {schema}.Equipment e
        LEFT JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE e.CustomerNo IS NOT NULL
        AND e.CustomerNo != ''
        AND e.SerialNo IS NOT NULL
        ORDER BY e.SerialNo
        """
        
        results = db.execute_query(query)
        
        equipment_list = []
        if results:
            for row in results:
                equipment_list.append({
                    'serial_no': row.get('SerialNo'),
                    'unit_no': row.get('UnitNo'),
                    'make': row.get('Make'),
                    'model': row.get('Model'),
                    'customer_no': row.get('CustomerNo'),
                    'customer_name': row.get('CustomerName'),
                    'city': row.get('City'),
                    'state': row.get('State'),
                    'rental_status': row.get('RentalStatus'),
                    'location': row.get('Location')
                })
        
        return jsonify({
            'count': len(equipment_list),
            'equipment': equipment_list
        })
        
    except Exception as e:
        logger.error(f"Equipment PM sample query failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Failed to retrieve equipment sample'
        }), 500
