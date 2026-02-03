from flask import Blueprint, jsonify
from src.utils.tenant_utils import get_tenant_db
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

invoice_columns_diagnostic_bp = Blueprint('invoice_columns_diagnostic', __name__)

@invoice_columns_diagnostic_bp.route('/api/diagnostics/invoice-columns', methods=['GET'])
@jwt_required()
def get_invoice_columns():
    """Get all columns from InvoiceReg table to find department/account field"""
    try:
        db = get_tenant_db()
        
        # Get all columns from InvoiceReg
        columns_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'InvoiceReg'
        ORDER BY ORDINAL_POSITION
        """
        
        columns = db.execute_query(columns_query)
        
        # Look for potential department/account columns
        potential_dept_columns = []
        for col in columns:
            col_name = col['COLUMN_NAME'].lower()
            if any(term in col_name for term in ['dept', 'department', 'account', 'code', 'sale']):
                potential_dept_columns.append({
                    'column': col['COLUMN_NAME'],
                    'data_type': col['DATA_TYPE'],
                    'position': col['ORDINAL_POSITION']
                })
        
        # Get a sample record to see actual data
        sample_query = """
        SELECT TOP 5 *
        FROM ben002.InvoiceReg
        WHERE GrandTotal < 0  -- Look for negative amounts (expenses)
        ORDER BY InvoiceDate DESC
        """
        
        try:
            samples = db.execute_query(sample_query)
        except:
            # If that fails, just get any sample
            sample_query = "SELECT TOP 5 * FROM ben002.InvoiceReg ORDER BY InvoiceDate DESC"
            samples = db.execute_query(sample_query)
        
        # Find columns that might contain account codes starting with 6
        expense_columns = []
        if samples and len(samples) > 0:
            first_sample = samples[0]
            for key, value in first_sample.items():
                if value and isinstance(value, str) and value.startswith('6'):
                    expense_columns.append({
                        'column': key,
                        'sample_value': value
                    })
        
        # Get columns that might be totals/amounts
        amount_columns = []
        for col in columns:
            col_name = col['COLUMN_NAME'].lower()
            if any(term in col_name for term in ['total', 'amount', 'grand', 'sale', 'cost']):
                amount_columns.append(col['COLUMN_NAME'])
        
        return jsonify({
            'total_columns': len(columns),
            'all_columns': [col['COLUMN_NAME'] for col in columns],
            'potential_dept_columns': potential_dept_columns,
            'expense_columns': expense_columns,
            'amount_columns': amount_columns,
            'sample_records': samples[:2] if samples else []
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get column info: {str(e)}'
        }), 500