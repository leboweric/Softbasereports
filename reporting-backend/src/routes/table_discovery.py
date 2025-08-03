from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import logging
from datetime import datetime
from src.services.azure_sql_service import AzureSQLService

logger = logging.getLogger(__name__)
table_discovery_bp = Blueprint('table_discovery', __name__)

@table_discovery_bp.route('/api/database/list-tables', methods=['GET'])
@jwt_required()
def list_all_tables():
    """List all tables in the ben002 schema"""
    try:
        db = AzureSQLService()
        
        # Get all tables with basic info
        tables_query = """
        SELECT 
            t.TABLE_NAME,
            t.TABLE_TYPE,
            (
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS c 
                WHERE c.TABLE_SCHEMA = t.TABLE_SCHEMA 
                AND c.TABLE_NAME = t.TABLE_NAME
            ) as COLUMN_COUNT
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE t.TABLE_SCHEMA = 'ben002'
        ORDER BY t.TABLE_NAME
        """
        
        tables = db.execute_query(tables_query)
        
        # Group tables by type
        base_tables = []
        views = []
        
        for table in tables:
            table_info = {
                'name': table['TABLE_NAME'],
                'column_count': table['COLUMN_COUNT']
            }
            
            if table['TABLE_TYPE'] == 'BASE TABLE':
                base_tables.append(table_info)
            else:
                views.append(table_info)
        
        return jsonify({
            'success': True,
            'base_tables': base_tables,
            'views': views,
            'total_tables': len(base_tables),
            'total_views': len(views)
        })
        
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@table_discovery_bp.route('/api/database/table-details', methods=['POST'])
@jwt_required()
def get_table_details():
    """Get detailed schema for specific tables"""
    try:
        data = request.get_json()
        table_names = data.get('tables', [])
        
        if not table_names:
            return jsonify({
                'success': False,
                'error': 'No tables specified'
            }), 400
        
        db = AzureSQLService()
        table_details = {}
        
        for table_name in table_names:
            try:
                # Get columns
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
                WHERE TABLE_SCHEMA = 'ben002' 
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = db.execute_query(columns_query)
                
                # Get primary keys
                pk_query = f"""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = 'ben002' 
                AND TABLE_NAME = '{table_name}'
                AND CONSTRAINT_NAME LIKE 'PK%'
                """
                
                pk_results = db.execute_query(pk_query)
                primary_keys = [pk['COLUMN_NAME'] for pk in pk_results] if pk_results else []
                
                # Try to get row count (with timeout protection)
                row_count = None
                try:
                    # Only count for smaller tables to avoid timeouts
                    if len(columns) < 50:  # Arbitrary threshold
                        count_query = f"SELECT COUNT(*) as count FROM ben002.{table_name}"
                        count_result = db.execute_query(count_query)
                        if count_result:
                            row_count = count_result[0]['count']
                except:
                    row_count = 'Error counting'
                
                # Get sample data (first 3 rows)
                sample_data = []
                try:
                    sample_query = f"SELECT TOP 3 * FROM ben002.{table_name}"
                    sample_data = db.execute_query(sample_query)
                except:
                    sample_data = []
                
                table_details[table_name] = {
                    'columns': [
                        {
                            'name': col['COLUMN_NAME'],
                            'type': col['DATA_TYPE'],
                            'max_length': col['CHARACTER_MAXIMUM_LENGTH'],
                            'precision': col['NUMERIC_PRECISION'],
                            'scale': col['NUMERIC_SCALE'],
                            'nullable': col['IS_NULLABLE'] == 'YES',
                            'default': col['COLUMN_DEFAULT'],
                            'position': col['ORDINAL_POSITION'],
                            'is_primary_key': col['COLUMN_NAME'] in primary_keys
                        }
                        for col in columns
                    ],
                    'primary_keys': primary_keys,
                    'row_count': row_count,
                    'sample_data': sample_data
                }
                
            except Exception as e:
                table_details[table_name] = {
                    'error': str(e)
                }
                logger.error(f"Error getting details for table {table_name}: {str(e)}")
        
        return jsonify({
            'success': True,
            'tables': table_details
        })
        
    except Exception as e:
        logger.error(f"Error getting table details: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@table_discovery_bp.route('/api/database/export-selected-schema', methods=['POST'])
@jwt_required()
def export_selected_schema():
    """Export schema for selected tables as markdown"""
    try:
        data = request.get_json()
        table_names = data.get('tables', [])
        
        if not table_names:
            return jsonify({
                'success': False,
                'error': 'No tables specified'
            }), 400
        
        db = AzureSQLService()
        
        markdown_lines = [
            "# Softbase Database Schema Documentation",
            f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Database Structure",
            "\nSchema: `ben002`",
            f"\nTables documented: {len(table_names)}",
            "\n## Tables\n"
        ]
        
        for table_name in sorted(table_names):
            try:
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
                    WHERE TABLE_SCHEMA = 'ben002' 
                    AND TABLE_NAME = '{table_name}'
                    AND CONSTRAINT_NAME LIKE 'PK%'
                ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
                WHERE c.TABLE_SCHEMA = 'ben002' 
                AND c.TABLE_NAME = '{table_name}'
                ORDER BY c.ORDINAL_POSITION
                """
                
                columns = db.execute_query(columns_query)
                
                # Get row count
                row_count = 'Unknown'
                try:
                    count_result = db.execute_query(f"SELECT COUNT(*) as count FROM ben002.{table_name}")
                    if count_result:
                        row_count = f"{count_result[0]['count']:,}"
                except:
                    pass
                
                # Add table to markdown
                markdown_lines.append(f"\n### {table_name}")
                markdown_lines.append(f"Rows: {row_count}")
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
                
                markdown_lines.append(f"\nSample query:")
                markdown_lines.append(f"```sql")
                markdown_lines.append(f"SELECT TOP 10 * FROM ben002.{table_name}")
                markdown_lines.append(f"```")
                
            except Exception as e:
                markdown_lines.append(f"\n### {table_name}")
                markdown_lines.append(f"Error: {str(e)}")
        
        markdown_content = '\n'.join(markdown_lines)
        
        return jsonify({
            'success': True,
            'markdown': markdown_content
        })
        
    except Exception as e:
        logger.error(f"Error exporting schema: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500