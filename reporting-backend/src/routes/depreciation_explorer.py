"""
Depreciation data exploration endpoint
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

depreciation_explorer_bp = Blueprint('depreciation_explorer', __name__)

@depreciation_explorer_bp.route('/api/diagnostic/depreciation-fields', methods=['GET'])
@jwt_required()
def explore_depreciation_fields():
    """Explore database for depreciation-related fields and data"""
    try:
        db = AzureSQLService()
        results = {}
        
        # Find tables with depreciation-related names
        tables_query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE (TABLE_NAME LIKE '%deprec%' OR TABLE_NAME LIKE '%depr%'
               OR TABLE_NAME LIKE '%asset%' OR TABLE_NAME LIKE '%book%')
        AND TABLE_SCHEMA = 'ben002'
        ORDER BY TABLE_NAME
        """
        results['depreciation_tables'] = db.execute_query(tables_query)
        
        # Find columns with depreciation/book value keywords
        columns_query = """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE (COLUMN_NAME LIKE '%deprec%' OR COLUMN_NAME LIKE '%depr%' 
               OR COLUMN_NAME LIKE '%book%' OR COLUMN_NAME LIKE '%accum%'
               OR COLUMN_NAME LIKE '%asset%' OR COLUMN_NAME LIKE '%value%'
               OR COLUMN_NAME LIKE '%cost%' OR COLUMN_NAME LIKE '%basis%'
               OR COLUMN_NAME LIKE '%original%' OR COLUMN_NAME LIKE '%purchase%')
        AND TABLE_SCHEMA = 'ben002'
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
        results['financial_columns'] = db.execute_query(columns_query)
        
        # Get ALL Equipment table columns
        equipment_columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH,
               COLUMN_DEFAULT, NUMERIC_PRECISION, NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Equipment' AND TABLE_SCHEMA = 'ben002'
        ORDER BY ORDINAL_POSITION
        """
        results['equipment_columns'] = db.execute_query(equipment_columns_query)
        
        # Sample equipment financial data
        equipment_sample_query = """
        SELECT TOP 10 
            SerialNo,
            Make,
            Model,
            Cost,
            Sell,
            Retail,
            RentalYTD,
            RentalITD
        FROM ben002.Equipment 
        WHERE SerialNo IS NOT NULL
        AND (Cost IS NOT NULL OR Sell IS NOT NULL)
        ORDER BY Cost DESC
        """
        results['equipment_sample'] = db.execute_query(equipment_sample_query)
        
        # All tables in database
        all_tables_query = """
        SELECT TABLE_NAME, 
               (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = t.TABLE_NAME AND TABLE_SCHEMA = 'ben002') as COLUMN_COUNT
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        results['all_tables'] = db.execute_query(all_tables_query)
        
        # Database views
        views_query = """
        SELECT TABLE_NAME as VIEW_NAME
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_TYPE = 'VIEW'
        ORDER BY TABLE_NAME
        """
        results['database_views'] = db.execute_query(views_query)
        
        # Check if there are any specific financial/accounting tables
        accounting_tables = [table for table in results['all_tables'] 
                           if any(keyword in table['TABLE_NAME'].lower() for keyword in 
                                ['asset', 'deprec', 'book', 'cost', 'value', 'financial', 'account', 'ledger'])]
        results['potential_financial_tables'] = accounting_tables
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'depreciation_tables_found': len(results['depreciation_tables']),
                'financial_columns_found': len(results['financial_columns']),
                'equipment_columns_total': len(results['equipment_columns']),
                'equipment_sample_records': len(results['equipment_sample']),
                'total_tables': len(results['all_tables']),
                'total_views': len(results['database_views']),
                'potential_financial_tables': len(accounting_tables)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error exploring depreciation fields: {str(e)}'
        }), 500