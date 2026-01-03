"""
Comprehensive Database Schema Explorer
Allows querying table structures, relationships, and data samples
"""
from flask import Blueprint, jsonify, request
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



schema_explorer_bp = Blueprint('schema_explorer', __name__)

@schema_explorer_bp.route('/api/schema/tables', methods=['GET'])
@jwt_required()
def get_all_tables():
    """Get list of all tables in ben002 schema"""
    try:
        sql_service = AzureSQLService()

        schema = get_tenant_schema()


        query = f"""
        SELECT
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema}'
        ORDER BY TABLE_NAME
        """

        tables = sql_service.execute_query(query)

        return jsonify({
            'success': True,
            'schema': '{schema}',
            'tables': tables,
            'count': len(tables)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@schema_explorer_bp.route('/api/schema/table/<table_name>', methods=['GET'])
@jwt_required()
def get_table_structure(table_name):
    """Get complete structure of a specific table"""
    try:
        sql_service = AzureSQLService()

        # Get columns
        columns_query = f"""
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """

        columns = sql_service.execute_query(columns_query, [table_name])

        # Get primary keys
        pk_query = f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = %s
        AND CONSTRAINT_NAME LIKE 'PK_%'
        """

        primary_keys = sql_service.execute_query(pk_query, [table_name])

        # Get foreign keys
        fk_query = f"""
        SELECT
            fk.name AS FK_NAME,
            OBJECT_NAME(fk.parent_object_id) AS TABLE_NAME,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS COLUMN_NAME,
            OBJECT_NAME(fk.referenced_object_id) AS REFERENCED_TABLE,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS REFERENCED_COLUMN
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc
            ON fk.object_id = fkc.constraint_object_id
        WHERE OBJECT_NAME(fk.parent_object_id) = %s
        """

        foreign_keys = sql_service.execute_query(fk_query, [table_name])

        # Get row count
        count_query = f"SELECT COUNT(*) as total FROM {schema}.[{table_name}]"
        count_result = sql_service.execute_query(count_query)
        row_count = count_result[0]['total'] if count_result else 0

        return jsonify({
            'success': True,
            'table': table_name,
            'schema': '{schema}',
            'columns': columns,
            'column_count': len(columns),
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'row_count': row_count
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@schema_explorer_bp.route('/api/schema/table/<table_name>/sample', methods=['GET'])
@jwt_required()
def get_table_sample(table_name):
    """Get sample data from a table"""
    try:
        sql_service = AzureSQLService()

        limit = request.args.get('limit', 10, type=int)

        query = f"SELECT TOP {limit} * FROM {schema}.[{table_name}]"

        sample = sql_service.execute_query(query)

        return jsonify({
            'success': True,
            'table': table_name,
            'sample': sample,
            'count': len(sample)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@schema_explorer_bp.route('/api/schema/query', methods=['POST'])
@jwt_required()
def execute_custom_query():
    """Execute a custom SQL query for schema exploration"""
    try:
        sql_service = AzureSQLService()

        data = request.get_json()
        query = data.get('query')

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400

        # Security: Only allow SELECT statements
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            return jsonify({
                'success': False,
                'error': 'Only SELECT queries are allowed'
            }), 400

        # Prevent multiple statements
        if ';' in query.rstrip(';'):
            return jsonify({
                'success': False,
                'error': 'Multiple statements not allowed'
            }), 400

        results = sql_service.execute_query(query)

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@schema_explorer_bp.route('/api/schema/find-column', methods=['GET'])
@jwt_required()
def find_column():
    """Find which tables contain a column with a specific name pattern"""
    try:
        sql_service = AzureSQLService()

        column_pattern = request.args.get('pattern', '')

        if not column_pattern:
            return jsonify({
                'success': False,
                'error': 'Column pattern is required'
            }), 400

        schema = get_tenant_schema()


        query = f"""
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND COLUMN_NAME LIKE %s
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """

        results = sql_service.execute_query(query, [f'%{column_pattern}%'])

        return jsonify({
            'success': True,
            'pattern': column_pattern,
            'results': results,
            'count': len(results)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@schema_explorer_bp.route('/api/schema/relationships/<table_name>', methods=['GET'])
@jwt_required()
def get_table_relationships(table_name):
    """Get all foreign key relationships for a table (both incoming and outgoing)"""
    try:
        sql_service = AzureSQLService()

        # Outgoing FKs (this table references other tables)
        outgoing_query = f"""
        SELECT
            fk.name AS FK_NAME,
            OBJECT_NAME(fk.parent_object_id) AS FROM_TABLE,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS FROM_COLUMN,
            OBJECT_NAME(fk.referenced_object_id) AS TO_TABLE,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS TO_COLUMN
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc
            ON fk.object_id = fkc.constraint_object_id
        WHERE OBJECT_NAME(fk.parent_object_id) = %s
        """

        outgoing = sql_service.execute_query(outgoing_query, [table_name])

        # Incoming FKs (other tables reference this table)
        incoming_query = f"""
        SELECT
            fk.name AS FK_NAME,
            OBJECT_NAME(fk.parent_object_id) AS FROM_TABLE,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS FROM_COLUMN,
            OBJECT_NAME(fk.referenced_object_id) AS TO_TABLE,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS TO_COLUMN
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc
            ON fk.object_id = fkc.constraint_object_id
        WHERE OBJECT_NAME(fk.referenced_object_id) = %s
        """

        incoming = sql_service.execute_query(incoming_query, [table_name])

        return jsonify({
            'success': True,
            'table': table_name,
            'outgoing_fks': outgoing,
            'incoming_fks': incoming,
            'total_relationships': len(outgoing) + len(incoming)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@schema_explorer_bp.route('/api/schema/record/<table_name>/<record_id>', methods=['GET'])
@jwt_required()
def get_single_record(table_name, record_id):
    """Get a single record by its primary key or any unique identifier"""
    try:
        sql_service = AzureSQLService()

        # Allow specifying which column to use for lookup
        id_column = request.args.get('id_column', 'Number')

        query = f"SELECT * FROM {schema}.[{table_name}] WHERE [{id_column}] = %s"

        results = sql_service.execute_query(query, [record_id])

        if not results:
            return jsonify({
                'success': False,
                'error': 'Record not found'
            }), 404

        return jsonify({
            'success': True,
            'table': table_name,
            'record': results[0]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
