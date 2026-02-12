from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
import logging

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

logger = logging.getLogger(__name__)

pm_table_diagnostic_bp = Blueprint('pm_table_diagnostic', __name__)

@pm_table_diagnostic_bp.route('/api/diagnostic/pm-table-structure', methods=['GET'])
@jwt_required()
def get_pm_table_structure():
    """
    Diagnostic endpoint to explore the PM table structure.
    This is the dedicated PM schedule table in Softbase Evolution.
    """
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        results_data = {
            'pm_columns': [],
            'sample_records': [],
            'lpm_columns': [],
            'lpm_sample': []
        }
        
        # Step 1: Get PM table columns
        pm_columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '{schema}' 
        AND TABLE_NAME = 'PM'
        ORDER BY ORDINAL_POSITION
        """
        
        logger.info("Fetching PM table columns...")
        pm_columns = db.execute_query(pm_columns_query)
        
        if pm_columns:
            results_data['pm_columns'] = [
                {
                    'name': col['COLUMN_NAME'],
                    'type': col['DATA_TYPE'],
                    'nullable': col['IS_NULLABLE'],
                    'max_length': col.get('CHARACTER_MAXIMUM_LENGTH')
                }
                for col in pm_columns
            ]
        
        # Step 2: Get sample PM records
        pm_sample_query = f"""
        SELECT TOP 20 *
        FROM {schema}.PM
        ORDER BY Id DESC
        """
        
        logger.info("Fetching sample PM records...")
        pm_records = db.execute_query(pm_sample_query)
        
        if pm_records:
            for record in pm_records:
                pm_data = {}
                for key, value in record.items():
                    if value is not None:
                        # Convert datetime to string
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        pm_data[key] = value
                results_data['sample_records'].append(pm_data)
        
        # Step 3: Get LPM table columns (Last PM)
        lpm_columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '{schema}' 
        AND TABLE_NAME = 'LPM'
        ORDER BY ORDINAL_POSITION
        """
        
        logger.info("Fetching LPM table columns...")
        lpm_columns = db.execute_query(lpm_columns_query)
        
        if lpm_columns:
            results_data['lpm_columns'] = [
                {
                    'name': col['COLUMN_NAME'],
                    'type': col['DATA_TYPE'],
                    'nullable': col['IS_NULLABLE']
                }
                for col in lpm_columns
            ]
        
        # Step 4: Get sample LPM records
        lpm_sample_query = f"""
        SELECT TOP 10 *
        FROM {schema}.LPM
        """
        
        logger.info("Fetching sample LPM records...")
        lpm_records = db.execute_query(lpm_sample_query)
        
        if lpm_records:
            for record in lpm_records:
                lpm_data = {}
                for key, value in record.items():
                    if value is not None:
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        lpm_data[key] = value
                results_data['lpm_sample'].append(lpm_data)
        
        # Summary
        results_data['summary'] = {
            'pm_columns_count': len(results_data['pm_columns']),
            'pm_records_count': len(results_data['sample_records']),
            'lpm_columns_count': len(results_data['lpm_columns']),
            'lpm_records_count': len(results_data['lpm_sample'])
        }
        
        return jsonify(results_data)
        
    except Exception as e:
        logger.error(f"PM table diagnostic failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Failed to retrieve PM table information'
        }), 500


@pm_table_diagnostic_bp.route('/api/diagnostic/pm-by-serial', methods=['GET'])
@jwt_required()
def get_pm_by_serial():
    """
    Look up PM records for specific equipment serial numbers from the screenshot.
    """
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Serial numbers from screenshot
        serial_numbers = ['35955', '35951', '38762', '61300', '900006']
        
        results = []
        
        for serial_no in serial_numbers:
            # Try to find PM records for this equipment
            query = f"""
            SELECT TOP 5 *
            FROM {schema}.PM
            WHERE SerialNo = '{serial_no}' 
               OR UnitNo = '{serial_no}'
               OR Equipment = '{serial_no}'
            """
            
            logger.info(f"Searching PM records for: {serial_no}")
            pm_records = db.execute_query(query)
            
            if pm_records and len(pm_records) > 0:
                for record in pm_records:
                    pm_data = {'serial_searched': serial_no, 'found': True}
                    for key, value in record.items():
                        if value is not None:
                            if hasattr(value, 'isoformat'):
                                value = value.isoformat()
                            pm_data[key] = value
                    results.append(pm_data)
            else:
                results.append({
                    'serial_searched': serial_no,
                    'found': False
                })
        
        return jsonify({
            'results': results,
            'total_found': len([r for r in results if r.get('found')])
        })
        
    except Exception as e:
        logger.error(f"PM by serial lookup failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Failed to lookup PM records by serial'
        }), 500
