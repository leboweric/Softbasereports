from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

check_invoice_type_bp = Blueprint('check_invoice_type', __name__)

@check_invoice_type_bp.route('/api/diagnostics/check-invoice-type', methods=['GET'])
@jwt_required()
def check_invoice_type():
    """Check if InvoiceType column exists and what columns are available"""
    try:
        db = AzureSQLService()
        
        # Get all columns from InvoiceReg
        columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_NAME = 'InvoiceReg'
        ORDER BY ORDINAL_POSITION
        """
        
        columns = db.execute_query(columns_query)
        
        # Check for invoice type related columns
        type_columns = [col for col in columns if 'type' in col['COLUMN_NAME'].lower() or 'kind' in col['COLUMN_NAME'].lower()]
        
        # Get sample data to see how to identify equipment sales
        sample_query = """
        SELECT TOP 5 
            InvoiceNo,
            COALESCE(EquipmentTaxable, 0) as EquipmentTaxable,
            COALESCE(EquipmentNonTax, 0) as EquipmentNonTax,
            GrandTotal,
            GrandTotal - COALESCE(EquipmentTaxable, 0) - COALESCE(EquipmentNonTax, 0) as NonEquipmentTotal
        FROM ben002.InvoiceReg
        WHERE EquipmentTaxable > 0 OR EquipmentNonTax > 0
        """
        
        samples = db.execute_query(sample_query)
        
        return jsonify({
            'all_columns': columns,
            'type_related_columns': type_columns,
            'equipment_samples': samples
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500