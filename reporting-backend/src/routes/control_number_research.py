from flask import jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from src.routes.reports import reports_bp
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

@reports_bp.route('/departments/accounting/find-control-fields', methods=['GET'])
@jwt_required()
def find_control_fields():
    """Find all control-related fields in the database"""
    try:
        logger.info("Starting control fields search")
        db = AzureSQLService()
        schema = get_tenant_schema()
        # Check Equipment table for control-related columns
        equipment_cols_query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = 'Equipment'
        ORDER BY ORDINAL_POSITION
        """
        
        equipment_cols = db.execute_query(equipment_cols_query)
        
        # Look for control/tag/asset related columns
        control_related = []
        all_columns = []
        
        if equipment_cols:
            for col in equipment_cols:
                col_name = col.get('COLUMN_NAME', '')
                all_columns.append(col_name)
                
                # Check if column might be control-related
                lower_name = col_name.lower()
                if any(term in lower_name for term in ['control', 'ctrl', 'tag', 'asset', 'ref', 'stock', 'inv']):
                    control_related.append({
                        'column': col_name,
                        'type': col.get('DATA_TYPE', ''),
                        'length': col.get('CHARACTER_MAXIMUM_LENGTH', '')
                    })
        
        # Get sample equipment data with basic fields we know exist
        sample_query = f"""
        SELECT TOP 10
            UnitNo,
            SerialNo,
            Make,
            Model,
            Location,
            CustomerNo,
            RentalStatus
        FROM {schema}.Equipment
        WHERE SerialNo IS NOT NULL
        """
        
        sample_data = db.execute_query(sample_query)
        
        # Check all tables for control number columns
        all_control_query = f"""
        SELECT DISTINCT
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND (
            COLUMN_NAME LIKE '%Control%'
            OR COLUMN_NAME LIKE '%Ctrl%'
            OR COLUMN_NAME = 'ControlNo'
            OR COLUMN_NAME = 'ControlNumber'
        )
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
        
        all_control_cols = db.execute_query(all_control_query)
        
        return jsonify({
            'equipment_columns': all_columns[:50] if all_columns else [],  # First 50 columns
            'control_related_columns': control_related if control_related else [],
            'sample_equipment': sample_data if sample_data else [],
            'all_control_columns': all_control_cols if all_control_cols else [],
            'message': 'Search completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error finding control fields: {str(e)}")
        return jsonify({'error': str(e)}), 500