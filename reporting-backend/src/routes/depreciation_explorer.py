"""
Depreciation data exploration endpoint
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

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



depreciation_explorer_bp = Blueprint('depreciation_explorer', __name__)

@depreciation_explorer_bp.route('/api/diagnostic/depreciation-fields', methods=['GET'])
@jwt_required()
def explore_depreciation_fields():
    """Explore database for depreciation-related fields and data"""
    try:
        db = AzureSQLService()
        schema = get_tenant_schema()
        results = {}
        
        # Find tables with depreciation-related names
        tables_query = f"""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE (TABLE_NAME LIKE '%deprec%' OR TABLE_NAME LIKE '%depr%'
               OR TABLE_NAME LIKE '%asset%' OR TABLE_NAME LIKE '%book%')
        AND TABLE_SCHEMA = '{schema}'
        ORDER BY TABLE_NAME
        """
        results['depreciation_tables'] = db.execute_query(tables_query)
        
        # Find columns with depreciation/book value keywords
        columns_query = f"""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE (COLUMN_NAME LIKE '%deprec%' OR COLUMN_NAME LIKE '%depr%' 
               OR COLUMN_NAME LIKE '%book%' OR COLUMN_NAME LIKE '%accum%'
               OR COLUMN_NAME LIKE '%asset%' OR COLUMN_NAME LIKE '%value%'
               OR COLUMN_NAME LIKE '%cost%' OR COLUMN_NAME LIKE '%basis%'
               OR COLUMN_NAME LIKE '%original%' OR COLUMN_NAME LIKE '%purchase%')
        AND TABLE_SCHEMA = '{schema}'
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
        results['financial_columns'] = db.execute_query(columns_query)
        
        # Get ALL Equipment table columns
        equipment_columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH,
               COLUMN_DEFAULT, NUMERIC_PRECISION, NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Equipment' AND TABLE_SCHEMA = '{schema}'
        ORDER BY ORDINAL_POSITION
        """
        results['equipment_columns'] = db.execute_query(equipment_columns_query)
        
        # Sample equipment financial data
        equipment_sample_query = f"""
        SELECT TOP 10 
            SerialNo,
            Make,
            Model,
            Cost,
            Sell,
            Retail,
            RentalYTD,
            RentalITD
        FROM {schema}.Equipment 
        WHERE SerialNo IS NOT NULL
        AND (Cost IS NOT NULL OR Sell IS NOT NULL)
        ORDER BY Cost DESC
        """
        results['equipment_sample'] = db.execute_query(equipment_sample_query)
        
        # All tables in database
        all_tables_query = f"""
        SELECT TABLE_NAME, 
               (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = t.TABLE_NAME AND TABLE_SCHEMA = '{schema}') as COLUMN_COUNT
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        results['all_tables'] = db.execute_query(all_tables_query)
        
        # Database views
        views_query = f"""
        SELECT TABLE_NAME as VIEW_NAME
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = '{schema}'
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