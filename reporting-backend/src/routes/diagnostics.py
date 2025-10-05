"""
Database diagnostics endpoints for exploring schema and data
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

diagnostics_bp = Blueprint('diagnostics', __name__)

@diagnostics_bp.route('/api/diagnostic/depreciation-view-details', methods=['GET'])
@jwt_required()
def get_depreciation_view_details():
    """Explore the Depreciation view structure and sample data"""
    try:
        sql_service = AzureSQLService()
        
        # Get columns from Depreciation view
        columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Depreciation' 
        AND TABLE_SCHEMA = 'ben002'
        ORDER BY ORDINAL_POSITION
        """
        columns = sql_service.execute_query(columns_query)
        
        # Get sample data from Depreciation view
        sample_query = """
        SELECT TOP 10 *
        FROM ben002.Depreciation
        """
        sample_data = sql_service.execute_query(sample_query)
        
        # Get row count
        count_query = "SELECT COUNT(*) as total FROM ben002.Depreciation"
        count = sql_service.execute_query(count_query)
        
        # Get sample data with specific equipment info if available
        equipment_sample_query = """
        SELECT TOP 5 *
        FROM ben002.Depreciation
        WHERE SerialNo IS NOT NULL
        ORDER BY SerialNo
        """
        equipment_sample = sql_service.execute_query(equipment_sample_query)
        
        return jsonify({
            'success': True,
            'view_name': 'Depreciation',
            'columns': columns,
            'sample_data': sample_data,
            'equipment_sample': equipment_sample,
            'total_rows': count[0]['total'] if count else 0,
            'column_count': len(columns)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error exploring Depreciation view: {str(e)}'
        }), 500

@diagnostics_bp.route('/api/diagnostic/equipment-depreciation-join', methods=['GET'])
@jwt_required()
def get_equipment_depreciation_join():
    """Test joining Equipment and Depreciation data"""
    try:
        sql_service = AzureSQLService()
        
        # Test join between Equipment and Depreciation
        join_query = """
        SELECT TOP 5
            e.SerialNo,
            e.Make,
            e.Model,
            e.Cost as EquipmentCost,
            d.*
        FROM ben002.Equipment e
        INNER JOIN ben002.Depreciation d ON e.SerialNo = d.SerialNo
        WHERE e.SerialNo IS NOT NULL
        ORDER BY e.SerialNo
        """
        join_results = sql_service.execute_query(join_query)
        
        # Count how many equipment records have depreciation data
        join_count_query = """
        SELECT 
            COUNT(DISTINCT e.SerialNo) as equipment_with_depreciation,
            (SELECT COUNT(*) FROM ben002.Equipment WHERE SerialNo IS NOT NULL) as total_equipment
        FROM ben002.Equipment e
        INNER JOIN ben002.Depreciation d ON e.SerialNo = d.SerialNo
        """
        join_count = sql_service.execute_query(join_count_query)
        
        return jsonify({
            'success': True,
            'join_sample': join_results,
            'join_statistics': join_count[0] if join_count else {},
            'sample_count': len(join_results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error testing Equipment-Depreciation join: {str(e)}'
        }), 500