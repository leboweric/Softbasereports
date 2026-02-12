from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
import logging
from datetime import datetime
from flask_jwt_extended import get_jwt_identity
from src.models.user import User

logger = logging.getLogger(__name__)
full_schema_export_bp = Blueprint('full_schema_export', __name__)

@full_schema_export_bp.route('/api/database/export-full-schema', methods=['GET'])
@jwt_required()
def export_full_schema():
    """Export complete database schema for all tables"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get all tables in ben002 schema
        tables_query = f"""
        SELECT 
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema}'
        ORDER BY TABLE_NAME
        """
        
        tables = db.execute_query(tables_query)
        
        if not tables:
            return jsonify({
                'success': False,
                'error': 'No tables found in ben002 schema'
            }), 404
        
        # Build comprehensive schema information
        schema_data = {
            'schema_name': '{schema}',
            'export_date': datetime.now().isoformat(),
            'tables': {}
        }
        
        for table in tables:
            table_name = table['TABLE_NAME']
            table_type = table['TABLE_TYPE']
            
            # Skip system views
            if table_type == 'VIEW' and table_name.startswith('sys'):
                continue
            
            # Get columns for this table
            columns_query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}' 
            AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """
            
            columns = db.execute_query(columns_query)
            
            # Get primary key information
            pk_query = f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{schema}' 
            AND TABLE_NAME = '{table_name}'
            AND CONSTRAINT_NAME LIKE 'PK%'
            """
            
            pk_columns = db.execute_query(pk_query)
            pk_list = [pk['COLUMN_NAME'] for pk in pk_columns] if pk_columns else []
            
            # Get foreign key information
            fk_query = f"""
            SELECT 
                fk.COLUMN_NAME,
                pk.TABLE_NAME as REFERENCED_TABLE,
                pk.COLUMN_NAME as REFERENCED_COLUMN
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk
                ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
                AND rc.CONSTRAINT_SCHEMA = fk.CONSTRAINT_SCHEMA
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk
                ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
                AND rc.UNIQUE_CONSTRAINT_SCHEMA = pk.CONSTRAINT_SCHEMA
            WHERE fk.TABLE_SCHEMA = '{schema}' 
            AND fk.TABLE_NAME = '{table_name}'
            """
            
            fk_results = db.execute_query(fk_query)
            fk_dict = {}
            if fk_results:
                for fk in fk_results:
                    fk_dict[fk['COLUMN_NAME']] = {
                        'references': f"{fk['REFERENCED_TABLE']}.{fk['REFERENCED_COLUMN']}"
                    }
            
            # Get row count (for small tables only)
            row_count = None
            try:
                count_query = f"SELECT COUNT(*) as count FROM {schema}.{table_name}"
                count_result = db.execute_query(count_query)
                if count_result:
                    row_count = count_result[0]['count']
            except:
                row_count = 'Error counting rows'
            
            # Build table info
            table_info = {
                'type': table_type,
                'row_count': row_count,
                'primary_keys': pk_list,
                'columns': []
            }
            
            # Build column info
            for col in columns:
                column_info = {
                    'name': col['COLUMN_NAME'],
                    'type': col['DATA_TYPE'],
                    'nullable': col['IS_NULLABLE'] == 'YES',
                    'position': col['ORDINAL_POSITION']
                }
                
                # Add length/precision info
                if col['CHARACTER_MAXIMUM_LENGTH']:
                    column_info['max_length'] = col['CHARACTER_MAXIMUM_LENGTH']
                if col['NUMERIC_PRECISION']:
                    column_info['precision'] = col['NUMERIC_PRECISION']
                    if col['NUMERIC_SCALE']:
                        column_info['scale'] = col['NUMERIC_SCALE']
                
                # Add default value if exists
                if col['COLUMN_DEFAULT']:
                    column_info['default'] = col['COLUMN_DEFAULT']
                
                # Mark if primary key
                if col['COLUMN_NAME'] in pk_list:
                    column_info['is_primary_key'] = True
                
                # Add foreign key info if exists
                if col['COLUMN_NAME'] in fk_dict:
                    column_info['foreign_key'] = fk_dict[col['COLUMN_NAME']]
                
                table_info['columns'].append(column_info)
            
            schema_data['tables'][table_name] = table_info
        
        # Count totals
        schema_data['summary'] = {
            'total_tables': len(schema_data['tables']),
            'total_columns': sum(len(t['columns']) for t in schema_data['tables'].values()),
            'views': len([t for t in schema_data['tables'].values() if t['type'] == 'VIEW']),
            'base_tables': len([t for t in schema_data['tables'].values() if t['type'] == 'BASE TABLE'])
        }
        
        return jsonify({
            'success': True,
            'schema': schema_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting schema: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@full_schema_export_bp.route('/api/database/export-schema-markdown', methods=['GET'])
@jwt_required()
def export_schema_markdown():
    """Export schema as formatted markdown for CLAUDE.md"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get all tables
        tables_query = f"""
        SELECT TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema}'
        ORDER BY TABLE_NAME
        """
        
        tables = db.execute_query(tables_query)
        
        # Build markdown content
        markdown_lines = [
            "# Softbase Database Schema Documentation",
            f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Database Structure",
            "\nSchema: `ben002`",
            "\n## Tables\n"
        ]
        
        for table in tables:
            table_name = table['TABLE_NAME']
            table_type = table['TABLE_TYPE']
            
            # Skip system views
            if table_type == 'VIEW' and table_name.startswith('sys'):
                continue
            
            # Add table header
            markdown_lines.append(f"\n### {table_name}")
            markdown_lines.append(f"Type: {table_type}")
            
            # Get columns
            columns_query = f"""
            SELECT 
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.CHARACTER_MAXIMUM_LENGTH,
                c.IS_NULLABLE,
                CASE 
                    WHEN pk.COLUMN_NAME IS NOT NULL THEN 'PK'
                    ELSE ''
                END as KEY_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN (
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = '{schema}' 
                AND TABLE_NAME = '{table_name}'
                AND CONSTRAINT_NAME LIKE 'PK%'
            ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
            WHERE c.TABLE_SCHEMA = '{schema}' 
            AND c.TABLE_NAME = '{table_name}'
            ORDER BY c.ORDINAL_POSITION
            """
            
            columns = db.execute_query(columns_query)
            
            # Get row count
            try:
                count_result = db.execute_query(f"SELECT COUNT(*) as count FROM {schema}.{table_name}")
                row_count = count_result[0]['count'] if count_result else 'Unknown'
            except:
                row_count = 'Error'
            
            markdown_lines.append(f"Rows: {row_count:,}" if isinstance(row_count, int) else f"Rows: {row_count}")
            markdown_lines.append("\nColumns:")
            
            for col in columns:
                # Format data type
                data_type = col['DATA_TYPE']
                if col['CHARACTER_MAXIMUM_LENGTH'] and col['CHARACTER_MAXIMUM_LENGTH'] > 0:
                    data_type += f"({col['CHARACTER_MAXIMUM_LENGTH']})"
                
                # Build column line
                nullable = "" if col['IS_NULLABLE'] == 'NO' else " NULL"
                key_marker = f" [{col['KEY_TYPE']}]" if col['KEY_TYPE'] else ""
                
                markdown_lines.append(f"- `{col['COLUMN_NAME']}` - {data_type}{nullable}{key_marker}")
            
            # Add sample queries
            markdown_lines.append(f"\nSample query:")
            markdown_lines.append(f"```sql")
            markdown_lines.append(f"SELECT TOP 10 * FROM {schema}.{table_name}")
            markdown_lines.append(f"```")
        
        # Add summary
        total_tables = len([t for t in tables if not (t['TABLE_TYPE'] == 'VIEW' and t['TABLE_NAME'].startswith('sys'))])
        markdown_lines.extend([
            "\n## Summary",
            f"- Total tables: {total_tables}",
            f"- Schema: ben002",
            "\n## Important Notes",
            "- All table names should be prefixed with '{schema}.' when querying",
            "- Use exact column names as shown above (case-sensitive)",
            "- Foreign key relationships may exist but are not always enforced at the database level"
        ])
        
        markdown_content = '\n'.join(markdown_lines)
        
        # Return as downloadable file
        return Response(
            markdown_content,
            mimetype='text/markdown',
            headers={
                'Content-Disposition': f'attachment; filename=softbase_schema_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting markdown: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500