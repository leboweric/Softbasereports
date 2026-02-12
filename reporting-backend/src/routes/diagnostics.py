"""
Database diagnostics endpoints for exploring schema and data
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
from flask_jwt_extended import get_jwt_identity
from src.models.user import User

diagnostics_bp = Blueprint('diagnostics', __name__)

@diagnostics_bp.route('/api/diagnostic/depreciation-view-details', methods=['GET'])
@jwt_required()
def get_depreciation_view_details():
    """Explore the Depreciation view structure and sample data"""
    try:
        sql_service = get_tenant_db()
        
        # Get columns from Depreciation view
        columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Depreciation' 
        AND TABLE_SCHEMA = '{schema}'
        ORDER BY ORDINAL_POSITION
        """
        columns = sql_service.execute_query(columns_query)
        
        # Get sample data from Depreciation view
        sample_query = f"""
        SELECT TOP 10 *
        FROM {schema}.Depreciation
        """
        sample_data = sql_service.execute_query(sample_query)
        
        # Get row count
        count_query = "SELECT COUNT(*) as total FROM {schema}.Depreciation"
        count = sql_service.execute_query(count_query)
        
        # Get sample data with specific equipment info if available
        equipment_sample_query = f"""
        SELECT TOP 5 *
        FROM {schema}.Depreciation
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
        sql_service = get_tenant_db()
        
        # Test join between Equipment and Depreciation
        join_query = f"""
        SELECT TOP 5
            e.SerialNo,
            e.Make,
            e.Model,
            e.Cost as EquipmentCost,
            d.*
        FROM {schema}.Equipment e
        INNER JOIN {schema}.Depreciation d ON e.SerialNo = d.SerialNo
        WHERE e.SerialNo IS NOT NULL
        ORDER BY e.SerialNo
        """
        join_results = sql_service.execute_query(join_query)
        
        # Count how many equipment records have depreciation data
        join_count_query = f"""
        SELECT 
            COUNT(DISTINCT e.SerialNo) as equipment_with_depreciation,
            (SELECT COUNT(*) FROM {schema}.Equipment WHERE SerialNo IS NOT NULL) as total_equipment
        FROM {schema}.Equipment e
        INNER JOIN {schema}.Depreciation d ON e.SerialNo = d.SerialNo
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

@diagnostics_bp.route('/api/diagnostic/gl-table-columns', methods=['GET'])
@jwt_required()
def get_gl_table_columns():
    """Get actual column names from GL-related tables"""
    try:
        sql_service = get_tenant_db()
        
        # Get column information for GL-related tables
        schema = get_tenant_schema()

        query = f"""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME IN ('GL', 'GLDetail', 'ChartOfAccounts', 'GLField', 'GLGroup')
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        
        columns = sql_service.execute_query(query)
        
        # Get sample data from GL table if it exists
        sample_data = []
        try:
            sample_query = "SELECT TOP 3 * FROM {schema}.GL WHERE AccountNo IN ('131000', '183000')"
            sample_data = sql_service.execute_query(sample_query)
        except Exception as e:
            # If AccountNo doesn't exist, try other common account field names
            try:
                sample_query = "SELECT TOP 3 * FROM {schema}.GL WHERE Account IN ('131000', '183000')"
                sample_data = sql_service.execute_query(sample_query)
            except Exception as e2:
                try:
                    sample_query = "SELECT TOP 3 * FROM {schema}.GL"
                    sample_data = sql_service.execute_query(sample_query)
                except Exception as e3:
                    sample_data = [{'error': f'Could not get GL sample data: {str(e3)}'}]
        
        # Get sample data from GLDetail table if it exists
        gldetail_sample = []
        try:
            gldetail_query = "SELECT TOP 3 * FROM {schema}.GLDetail"
            gldetail_sample = sql_service.execute_query(gldetail_query)
        except Exception as e:
            gldetail_sample = [{'error': f'Could not get GLDetail sample data: {str(e)}'}]
        
        # Organize columns by table
        tables_info = {}
        for col in columns:
            table_name = col['TABLE_NAME']
            if table_name not in tables_info:
                tables_info[table_name] = []
            tables_info[table_name].append({
                'name': col['COLUMN_NAME'],
                'type': col['DATA_TYPE'],
                'max_length': col['CHARACTER_MAXIMUM_LENGTH'],
                'nullable': col['IS_NULLABLE']
            })
        
        return jsonify({
            'success': True,
            'tables_found': list(tables_info.keys()),
            'columns_by_table': tables_info,
            'gl_sample_data': sample_data,
            'gldetail_sample_data': gldetail_sample,
            'total_columns': len(columns)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting GL table columns: {str(e)}'
        }), 500

@diagnostics_bp.route('/api/diagnostic/invoice-raw', methods=['GET'])
@jwt_required()
def get_invoice_raw():
    """Get ALL fields from a specific invoice (raw data dump)"""
    try:
        invoice_no = request.args.get('invoice_no')
        if not invoice_no:
            return jsonify({'error': 'invoice_no parameter required'}), 400

        sql_service = get_tenant_db()

        # Get ALL fields from the invoice
        query = "SELECT * FROM {schema}.InvoiceReg WHERE InvoiceNo = %s"
        results = sql_service.execute_query(query, [invoice_no])

        if not results:
            return jsonify({
                'found': False,
                'invoice_no': invoice_no,
                'message': 'Invoice not found'
            }), 404

        # Get column names and types
        columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = 'InvoiceReg'
        ORDER BY ORDINAL_POSITION
        """
        columns = sql_service.execute_query(columns_query)

        return jsonify({
            'found': True,
            'invoice_no': invoice_no,
            'data': results[0],
            'columns': columns,
            'total_columns': len(columns)
        })

    except Exception as e:
        return jsonify({
            'error': f'Error fetching invoice: {str(e)}'
        }), 500