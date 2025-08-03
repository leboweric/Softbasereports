from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import logging
from src.services.azure_sql_service import AzureSQLService

logger = logging.getLogger(__name__)
simple_schema_export_bp = Blueprint('simple_schema_export', __name__)

# Essential tables to document
ESSENTIAL_TABLES = [
    'Customer',
    'Equipment', 
    'InvoiceReg',
    'WO',
    'WOLabor',
    'WOParts',
    'WOMisc',
    'Parts',
    'ServiceClaim',
    'ARDetail',
    'InvoiceSales',
    'WOQuote'
]

@simple_schema_export_bp.route('/api/database/simple-schema', methods=['GET'])
@jwt_required()
def get_simple_schema():
    """Get schema for essential tables only"""
    try:
        db = AzureSQLService()
        schema_info = {}
        
        for table_name in ESSENTIAL_TABLES:
            try:
                # Get columns for this table
                columns_query = f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'ben002' 
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = db.execute_query(columns_query)
                
                if columns:
                    # Get row count (with timeout protection)
                    row_count = 'Unknown'
                    try:
                        count_query = f"SELECT COUNT(*) as count FROM ben002.{table_name}"
                        count_result = db.execute_query(count_query)
                        if count_result:
                            row_count = count_result[0]['count']
                    except:
                        pass
                    
                    schema_info[table_name] = {
                        'columns': [
                            {
                                'name': col['COLUMN_NAME'],
                                'type': col['DATA_TYPE'],
                                'max_length': col['CHARACTER_MAXIMUM_LENGTH'],
                                'nullable': col['IS_NULLABLE'] == 'YES'
                            }
                            for col in columns
                        ],
                        'row_count': row_count
                    }
                else:
                    schema_info[table_name] = {'error': 'Table not found'}
                    
            except Exception as e:
                schema_info[table_name] = {'error': str(e)}
                logger.error(f"Error getting schema for {table_name}: {str(e)}")
        
        return jsonify({
            'success': True,
            'schema': schema_info,
            'tables_checked': len(ESSENTIAL_TABLES)
        })
        
    except Exception as e:
        logger.error(f"Error in simple schema export: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500