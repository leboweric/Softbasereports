from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import logging
from src.services.azure_sql_service import AzureSQLService

logger = logging.getLogger(__name__)
equipment_diagnostic_bp = Blueprint('equipment_diagnostic', __name__)

@equipment_diagnostic_bp.route('/api/diagnostics/equipment-columns', methods=['GET'])
@jwt_required()
def check_equipment_columns():
    """Check the actual columns in the Equipment table"""
    try:
        db = AzureSQLService()
        
        # Get column information
        columns_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'Equipment'
        ORDER BY ORDINAL_POSITION
        """
        
        columns = db.execute_query(columns_query)
        
        # Get sample data
        sample_query = """
        SELECT TOP 5 *
        FROM ben002.Equipment
        """
        
        sample_data = db.execute_query(sample_query)
        
        # Check if specific columns exist
        column_names = [col['COLUMN_NAME'] for col in columns] if columns else []
        
        # Test queries for different column possibilities
        test_results = {}
        
        # Test StockNo
        if 'StockNo' in column_names:
            test_results['StockNo'] = "Column exists"
        else:
            test_results['StockNo'] = "Column NOT found"
            
        # Test other potential column names
        potential_columns = ['Stock', 'StockNumber', 'Stock_No', 'EquipmentNo', 'EquipmentID', 'ID']
        for col in potential_columns:
            if col in column_names:
                test_results[col] = "Column exists"
        
        return jsonify({
            'success': True,
            'table_exists': len(columns) > 0,
            'columns': columns,
            'column_names': column_names,
            'sample_data': sample_data,
            'test_results': test_results,
            'total_columns': len(columns) if columns else 0
        })
        
    except Exception as e:
        logger.error(f"Error checking equipment columns: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500