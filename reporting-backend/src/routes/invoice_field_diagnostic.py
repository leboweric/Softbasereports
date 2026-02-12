from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
from flask_jwt_extended import get_jwt_identity
from src.models.user import User

def get_db():
    """Get database connection"""
    return get_tenant_db()

invoice_field_diagnostic_bp = Blueprint('invoice_field_diagnostic', __name__)

@invoice_field_diagnostic_bp.route('/api/diagnostic/invoice-fields', methods=['GET'])
@jwt_required()
def diagnose_invoice_fields():
    """Diagnostic to find ALL fields in InvoiceReg that might identify employees"""
    try:
        db = get_db()
        schema = get_tenant_schema()
        
        results = {}
        
        # 1. Get ALL columns from InvoiceReg table
        try:
            columns_query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}' 
                AND TABLE_NAME = 'InvoiceReg'
            ORDER BY ORDINAL_POSITION
            """
            
            columns_result = db.execute_query(columns_query)
            results['all_columns'] = []
            if columns_result:
                for row in columns_result:
                    results['all_columns'].append({
                        'name': row.get('COLUMN_NAME', ''),
                        'type': row.get('DATA_TYPE', ''),
                        'length': row.get('CHARACTER_MAXIMUM_LENGTH', '')
                    })
        except Exception as e:
            results['all_columns'] = f"Error: {str(e)}"
        
        # 2. Look specifically for fields with 'Created', 'Changed', 'Closed', 'Modified' in the name
        try:
            name_fields_query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}' 
                AND TABLE_NAME = 'InvoiceReg'
                AND (
                    COLUMN_NAME LIKE '%Create%' 
                    OR COLUMN_NAME LIKE '%Change%' 
                    OR COLUMN_NAME LIKE '%Close%'
                    OR COLUMN_NAME LIKE '%Modif%'
                    OR COLUMN_NAME LIKE '%By%'
                    OR COLUMN_NAME LIKE '%User%'
                    OR COLUMN_NAME LIKE '%Employee%'
                    OR COLUMN_NAME LIKE '%Person%'
                    OR COLUMN_NAME LIKE '%Name%'
                )
            ORDER BY ORDINAL_POSITION
            """
            
            name_columns_result = db.execute_query(name_fields_query)
            results['employee_name_columns'] = []
            if name_columns_result:
                for row in name_columns_result:
                    results['employee_name_columns'].append({
                        'name': row.get('COLUMN_NAME', ''),
                        'type': row.get('DATA_TYPE', ''),
                        'length': row.get('CHARACTER_MAXIMUM_LENGTH', '')
                    })
        except Exception as e:
            results['employee_name_columns'] = f"Error: {str(e)}"
        
        # 2b. Get a sample invoice with ALL fields to see what data we have
        try:
            sample_query = f"""
            SELECT TOP 3 *
            FROM {schema}.InvoiceReg
            WHERE SaleCode = 'CSTPRT'
                AND (PartsTaxable > 0 OR PartsNonTax > 0)
            ORDER BY InvoiceDate DESC
            """
            
            sample_result = db.execute_query(sample_query)
            results['sample_invoices'] = []
            if sample_result:
                for row in sample_result:
                    # Convert row to dictionary, handling all data types
                    invoice_data = {}
                    for key, value in row.items():
                        if value is None:
                            invoice_data[key] = None
                        elif hasattr(value, 'strftime'):  # datetime
                            invoice_data[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            invoice_data[key] = str(value)
                    results['sample_invoices'].append(invoice_data)
        except Exception as e:
            results['sample_invoices'] = f"Error: {str(e)}"
        
        # 3. Check if there are text fields that might contain actual employee names
        try:
            # First, get all text columns that might contain names
            text_columns_query = f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}' 
                AND TABLE_NAME = 'InvoiceReg'
                AND DATA_TYPE IN ('nvarchar', 'varchar', 'char', 'nchar', 'text', 'ntext')
                AND (
                    COLUMN_NAME LIKE '%Create%' 
                    OR COLUMN_NAME LIKE '%Change%' 
                    OR COLUMN_NAME LIKE '%Close%'
                    OR COLUMN_NAME LIKE '%Modif%'
                    OR COLUMN_NAME LIKE '%By%'
                )
            """
            text_cols_result = db.execute_query(text_columns_query)
            
            if text_cols_result and len(text_cols_result) > 0:
                # Build dynamic query to check these columns for name-like values
                columns_to_check = [row['COLUMN_NAME'] for row in text_cols_result]
                column_selects = ', '.join([f"[{col}]" for col in columns_to_check])
                
                sample_with_names_query = f"""
                SELECT TOP 5 
                    InvoiceNo,
                    InvoiceDate,
                    CreatorUserId,
                    LastModifierUserId,
                    {column_selects}
                FROM {schema}.InvoiceReg
                WHERE SaleCode = 'CSTPRT'
                    AND InvoiceDate >= '2025-08-01'
                ORDER BY InvoiceDate DESC
                """
                
                sample_names_result = db.execute_query(sample_with_names_query)
                results['possible_name_fields'] = []
                if sample_names_result:
                    for row in sample_names_result:
                        invoice_data = {'invoiceNo': row.get('InvoiceNo', '')}
                        for col in columns_to_check:
                            value = row.get(col, '')
                            if value and value not in ['', 'NULL', None]:
                                invoice_data[col] = str(value)
                        results['possible_name_fields'].append(invoice_data)
            else:
                results['possible_name_fields'] = "No text columns found with name patterns"
                
        except Exception as e:
            results['possible_name_fields'] = f"Error: {str(e)}"
        
        # 3b. Look for any user/employee related fields
        try:
            user_fields_query = f"""
            SELECT DISTINCT
                CreatorUserId,
                LastModifierUserId,
                COUNT(*) as Count
            FROM {schema}.InvoiceReg
            WHERE SaleCode = 'CSTPRT'
            GROUP BY CreatorUserId, LastModifierUserId
            ORDER BY COUNT(*) DESC
            """
            
            user_fields_result = db.execute_query(user_fields_query)
            results['user_field_patterns'] = []
            if user_fields_result:
                for row in user_fields_result[:20]:  # Limit to top 20
                    results['user_field_patterns'].append({
                        'creatorId': str(row.get('CreatorUserId', '')),
                        'modifierId': str(row.get('LastModifierUserId', '')),
                        'count': row.get('Count', 0)
                    })
        except Exception as e:
            results['user_field_patterns'] = f"Error: {str(e)}"
        
        # 4. Check if there are any other tables linked to InvoiceReg
        try:
            linked_tables_query = f"""
            SELECT DISTINCT
                fk.TABLE_NAME as ForeignTable,
                fk.COLUMN_NAME as ForeignColumn,
                pk.TABLE_NAME as PrimaryTable,
                pk.COLUMN_NAME as PrimaryColumn
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk
                ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk
                ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
            WHERE pk.TABLE_NAME = 'InvoiceReg' OR fk.TABLE_NAME = 'InvoiceReg'
            """
            
            linked_result = db.execute_query(linked_tables_query)
            results['linked_tables'] = []
            if linked_result:
                for row in linked_result:
                    results['linked_tables'].append({
                        'foreignTable': row.get('ForeignTable', ''),
                        'foreignColumn': row.get('ForeignColumn', ''),
                        'primaryTable': row.get('PrimaryTable', ''),
                        'primaryColumn': row.get('PrimaryColumn', '')
                    })
        except Exception as e:
            results['linked_tables'] = f"Error: {str(e)}"
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': 'invoice_field_diagnostic_error',
            'message': 'Invoice field diagnostic failed'
        }), 500