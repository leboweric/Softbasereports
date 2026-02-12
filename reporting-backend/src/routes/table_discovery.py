from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
import logging
from datetime import datetime
from flask_jwt_extended import get_jwt_identity
from src.models.user import User

logger = logging.getLogger(__name__)
table_discovery_bp = Blueprint('table_discovery', __name__)

@table_discovery_bp.route('/api/database/list-tables', methods=['GET'])
@jwt_required()
def list_all_tables():
    """List all tables in the ben002 schema"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get all tables with basic info
        tables_query = f"""
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
        WHERE t.TABLE_SCHEMA = '{schema}'
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
        
        db = get_tenant_db()
        schema = get_tenant_schema()
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
                WHERE TABLE_SCHEMA = '{schema}' 
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = db.execute_query(columns_query)
                
                # Get primary keys
                pk_query = f"""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = '{schema}' 
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
                        count_query = f"SELECT COUNT(*) as count FROM {schema}.{table_name}"
                        count_result = db.execute_query(count_query)
                        if count_result:
                            row_count = count_result[0]['count']
                except:
                    row_count = 'Error counting'
                
                # Get sample data (first 3 rows)
                sample_data = []
                try:
                    sample_query = f"SELECT TOP 3 * FROM {schema}.{table_name}"
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
        
        db = get_tenant_db()
        schema = get_tenant_schema()
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
                row_count = 'Unknown'
                try:
                    count_result = db.execute_query(f"SELECT COUNT(*) as count FROM {schema}.{table_name}")
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
                markdown_lines.append(f"SELECT TOP 10 * FROM {schema}.{table_name}")
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

@table_discovery_bp.route('/api/database/column-values', methods=['POST'])
@jwt_required()
def get_column_values():
    """Get distinct values and counts for a specific column"""
    try:
        data = request.get_json()
        table_name = data.get('table')
        column_name = data.get('column')
        filter_column = data.get('filter_column')  # Optional: filter by another column
        filter_value = data.get('filter_value')    # Optional: value to filter by
        
        if not table_name or not column_name:
            return jsonify({
                'success': False,
                'error': 'Table and column names are required'
            }), 400
        
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Build the WHERE clause
        where_clause = ""
        if filter_column and filter_value is not None:
            where_clause = f"WHERE {filter_column} = '{filter_value}'"
        
        # Get value distribution
        distribution_query = f"""
        SELECT 
            {column_name} as Value,
            COUNT(*) as Count,
            CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as DECIMAL(5,2)) as Percentage
        FROM {schema}.{table_name}
        {where_clause}
        GROUP BY {column_name}
        ORDER BY COUNT(*) DESC
        """
        
        distribution = db.execute_query(distribution_query)
        
        # Get sample records for each value (limit to top 10 values)
        samples = {}
        if distribution and len(distribution) > 0:
            # Get top 10 values by count
            top_values = distribution[:10]
            
            for value_row in top_values:
                value = value_row['Value']
                # Get 3 sample records for this value
                sample_query = f"""
                SELECT TOP 3 *
                FROM {schema}.{table_name}
                WHERE {column_name} {'IS NULL' if value is None else f"= '{value}'"}
                {f"AND {where_clause[6:]}" if where_clause else ""}  # Add filter if exists
                """
                
                try:
                    sample_data = db.execute_query(sample_query)
                    samples[str(value) if value is not None else 'NULL'] = sample_data
                except:
                    samples[str(value) if value is not None else 'NULL'] = []
        
        # Get total count
        total_query = f"""
        SELECT COUNT(*) as total
        FROM {schema}.{table_name}
        {where_clause}
        """
        total_result = db.execute_query(total_query)
        total_count = total_result[0]['total'] if total_result else 0
        
        return jsonify({
            'success': True,
            'table': table_name,
            'column': column_name,
            'filter': {'column': filter_column, 'value': filter_value} if filter_column else None,
            'total_rows': total_count,
            'unique_values': len(distribution),
            'distribution': [
                {
                    'value': d['Value'],
                    'count': d['Count'],
                    'percentage': float(d['Percentage'])
                }
                for d in distribution
            ],
            'samples': samples
        })
        
    except Exception as e:
        logger.error(f"Error getting column values: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@table_discovery_bp.route('/api/database/gl-investigation', methods=['GET'])
@jwt_required()
def investigate_gl_structure():
    """Investigate GL table structure and find target accounts"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Step 1: Find GL-related tables
        gl_tables_query = f"""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME LIKE '%GL%'
        ORDER BY TABLE_NAME
        """
        
        gl_tables = db.execute_query(gl_tables_query)
        
        results = {
            'gl_tables': [table['TABLE_NAME'] for table in gl_tables],
            'accounts_found': {},
            'sample_data': {}
        }
        
        # Step 2: If we have GL tables, check for our target accounts
        target_accounts = ['131000', '131200', '131300', '183000', '193000']
        
        for table in gl_tables:
            table_name = table['TABLE_NAME']
            
            # Get table structure
            try:
                structure_query = f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{schema}' 
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = db.execute_query(structure_query)
                results['sample_data'][table_name] = {
                    'columns': columns,
                    'sample_rows': []
                }
                
                # Get sample data
                sample_query = f"SELECT TOP 5 * FROM {schema}.{table_name}"
                sample_data = db.execute_query(sample_query)
                results['sample_data'][table_name]['sample_rows'] = sample_data
                
                # Look for account number columns and check for our target accounts
                account_columns = [col['COLUMN_NAME'] for col in columns 
                                 if 'account' in col['COLUMN_NAME'].lower() or 
                                    'acct' in col['COLUMN_NAME'].lower() or
                                    'gl' in col['COLUMN_NAME'].lower()]
                
                if account_columns:
                    for account_col in account_columns:
                        # Check if any of our target accounts exist
                        target_check_query = f"""
                        SELECT DISTINCT {account_col} as AccountNumber, COUNT(*) as RecordCount
                        FROM {schema}.{table_name}
                        WHERE {account_col} IN ('131000', '131200', '131300', '183000', '193000')
                        GROUP BY {account_col}
                        ORDER BY {account_col}
                        """
                        
                        try:
                            target_results = db.execute_query(target_check_query)
                            if target_results:
                                results['accounts_found'][table_name] = {
                                    'account_column': account_col,
                                    'found_accounts': target_results
                                }
                        except:
                            pass
                            
            except Exception as e:
                results['sample_data'][table_name] = {'error': str(e)}
        
        # Step 3: Look for equipment linking patterns
        equipment_link_query = f"""
        SELECT TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND (COLUMN_NAME LIKE '%Serial%' OR COLUMN_NAME LIKE '%Equipment%' OR COLUMN_NAME LIKE '%Asset%')
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
        
        equipment_links = db.execute_query(equipment_link_query)
        results['equipment_linking_columns'] = equipment_links
        
        return jsonify({
            'success': True,
            'investigation_results': results
        })
        
    except Exception as e:
        logger.error(f"Error investigating GL structure: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@table_discovery_bp.route('/api/database/gl-detail-analysis', methods=['POST'])
@jwt_required()
def analyze_gl_detail():
    """Analyze GLDetail transactions for equipment linking and account balances"""
    try:
        data = request.get_json()
        fiscal_year_filter = data.get('fiscal_year', True)  # Default to current fiscal year
        
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Step 1: Check if GLDetail table exists and get its structure
        gldetail_check_query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}' 
        AND TABLE_NAME = 'GLDetail'
        ORDER BY ORDINAL_POSITION
        """
        
        gldetail_columns = db.execute_query(gldetail_check_query)
        if not gldetail_columns:
            return jsonify({
                'success': False,
                'error': 'GLDetail table not found'
            }), 404
        
        results = {
            'table_structure': gldetail_columns,
            'target_accounts': {},
            'equipment_links': {},
            'fiscal_year_data': {},
            'sample_transactions': {}
        }
        
        # Step 2: Get account balances for our target accounts
        target_accounts = ['131000', '131200', '131300', '183000', '193000']
        
        # First, find the account number column in GLDetail
        account_columns = [col['COLUMN_NAME'] for col in gldetail_columns 
                         if 'account' in col['COLUMN_NAME'].lower() or 
                            'acct' in col['COLUMN_NAME'].lower()]
        
        if not account_columns:
            return jsonify({
                'success': False,
                'error': 'No account number column found in GLDetail'
            }), 400
        
        account_col = account_columns[0]  # Use the first account column found
        
        # Get current balances for target accounts
        balance_query = f"""
        SELECT 
            {account_col} as AccountNumber,
            SUM(CASE WHEN Credit IS NOT NULL THEN -Credit ELSE 0 END + 
                CASE WHEN Debit IS NOT NULL THEN Debit ELSE 0 END) as CurrentBalance,
            COUNT(*) as TransactionCount,
            MIN(Date) as EarliestTransaction,
            MAX(Date) as LatestTransaction
        FROM {schema}.GLDetail
        WHERE {account_col} IN ('131000', '131200', '131300', '183000', '193000')
        GROUP BY {account_col}
        ORDER BY {account_col}
        """
        
        account_balances = db.execute_query(balance_query)
        results['target_accounts'] = account_balances
        
        # Step 3: Get fiscal year data (Nov 2024 - Oct 2025) if requested
        if fiscal_year_filter:
            fiscal_query = f"""
            SELECT 
                {account_col} as AccountNumber,
                SUM(CASE WHEN Credit IS NOT NULL THEN -Credit ELSE 0 END + 
                    CASE WHEN Debit IS NOT NULL THEN Debit ELSE 0 END) as FiscalYearActivity,
                COUNT(*) as FiscalYearTransactions
            FROM {schema}.GLDetail
            WHERE {account_col} IN ('131000', '131200', '131300', '183000', '193000')
            AND Date >= '2024-11-01' AND Date <= '2025-10-31'
            GROUP BY {account_col}
            ORDER BY {account_col}
            """
            
            fiscal_data = db.execute_query(fiscal_query)
            results['fiscal_year_data'] = fiscal_data
        
        # Step 4: Look for equipment linking patterns
        # Check if there are columns that might link to equipment
        equipment_link_columns = [col['COLUMN_NAME'] for col in gldetail_columns 
                                if 'serial' in col['COLUMN_NAME'].lower() or 
                                   'equipment' in col['COLUMN_NAME'].lower() or
                                   'asset' in col['COLUMN_NAME'].lower() or
                                   'reference' in col['COLUMN_NAME'].lower() or
                                   'description' in col['COLUMN_NAME'].lower()]
        
        if equipment_link_columns:
            # Sample transactions that might contain equipment references
            for link_col in equipment_link_columns[:3]:  # Limit to first 3 columns
                sample_query = f"""
                SELECT TOP 10 
                    {account_col} as AccountNumber,
                    {link_col} as LinkingField,
                    Date,
                    Debit,
                    Credit,
                    Description
                FROM {schema}.GLDetail
                WHERE {account_col} IN ('131000', '131200', '131300', '183000', '193000')
                AND {link_col} IS NOT NULL
                AND {link_col} != ''
                ORDER BY Date DESC
                """
                
                try:
                    link_samples = db.execute_query(sample_query)
                    results['equipment_links'][link_col] = link_samples
                except:
                    results['equipment_links'][link_col] = []
        
        # Step 5: Get sample recent transactions for each target account
        for account in target_accounts:
            sample_query = f"""
            SELECT TOP 5
                Date,
                Debit,
                Credit,
                Description,
                Reference
            FROM {schema}.GLDetail
            WHERE {account_col} = '{account}'
            ORDER BY Date DESC
            """
            
            try:
                samples = db.execute_query(sample_query)
                results['sample_transactions'][account] = samples
            except:
                results['sample_transactions'][account] = []
        
        return jsonify({
            'success': True,
            'analysis_results': results
        })
        
    except Exception as e:
        logger.error(f"Error analyzing GL detail: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@table_discovery_bp.route('/api/database/gl-column-check', methods=['GET'])
@jwt_required()
def check_gl_columns():
    """Check actual column names in GL-related tables"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get column names from GL-related tables
        column_check_query = f"""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME IN ('GL', 'GLDetail', 'ChartOfAccounts')
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        
        columns = db.execute_query(column_check_query)
        
        # Organize by table
        tables_info = {}
        for col in columns:
            table_name = col['TABLE_NAME']
            if table_name not in tables_info:
                tables_info[table_name] = {
                    'columns': [],
                    'sample_data': None
                }
            
            tables_info[table_name]['columns'].append({
                'name': col['COLUMN_NAME'],
                'type': col['DATA_TYPE'],
                'max_length': col['CHARACTER_MAXIMUM_LENGTH']
            })
        
        # Get sample data for each table
        for table_name in tables_info.keys():
            try:
                sample_query = f"SELECT TOP 3 * FROM {schema}.{table_name}"
                sample_data = db.execute_query(sample_query)
                tables_info[table_name]['sample_data'] = sample_data
            except Exception as e:
                tables_info[table_name]['sample_data'] = f"Error: {str(e)}"
        
        return jsonify({
            'success': True,
            'tables': tables_info
        })
        
    except Exception as e:
        logger.error(f"Error checking GL columns: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500