from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

def get_db():
    """Get database connection"""
    return AzureSQLService()

employee_diagnostic_bp = Blueprint('employee_diagnostic', __name__)

@employee_diagnostic_bp.route('/api/diagnostic/employee-mapping', methods=['GET'])
@jwt_required()
def diagnose_employee_mapping():
    """Diagnostic endpoint to figure out employee ID mapping"""
    try:
        db = get_db()
        
        results = {}
        
        # 1. Check what CreatorUserId values look like
        creator_query = """
        SELECT DISTINCT TOP 20
            CreatorUserId,
            COUNT(*) as InvoiceCount
        FROM ben002.InvoiceReg
        WHERE CreatorUserId IS NOT NULL
        GROUP BY CreatorUserId
        ORDER BY COUNT(*) DESC
        """
        
        creator_result = db.execute_query(creator_query)
        results['top_creator_ids'] = []
        if creator_result:
            for row in creator_result:
                results['top_creator_ids'].append({
                    'id': str(row.get('CreatorUserId', '')),
                    'count': row.get('InvoiceCount', 0)
                })
        
        # 2. Find all tables with 'User' in the name
        user_tables_query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
             WHERE TABLE_NAME = t.TABLE_NAME AND TABLE_SCHEMA = t.TABLE_SCHEMA) as ColumnCount
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE TABLE_TYPE = 'BASE TABLE'
            AND (TABLE_NAME LIKE '%User%' OR TABLE_NAME LIKE '%Employee%' OR TABLE_NAME LIKE '%Staff%')
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        
        tables_result = db.execute_query(user_tables_query)
        results['user_tables'] = []
        if tables_result:
            for row in tables_result:
                results['user_tables'].append({
                    'schema': row.get('TABLE_SCHEMA', ''),
                    'table': row.get('TABLE_NAME', ''),
                    'columns': row.get('ColumnCount', 0)
                })
        
        # 3. Check AbpUsers table specifically (common in ASP.NET Boilerplate)
        abp_check_query = """
        IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'AbpUsers')
        BEGIN
            SELECT TOP 10
                Id,
                UserName,
                Name,
                Surname,
                EmailAddress
            FROM AbpUsers
            ORDER BY Id
        END
        """
        
        abp_result = db.execute_query(abp_check_query)
        results['abp_users_sample'] = []
        if abp_result:
            for row in abp_result:
                results['abp_users_sample'].append({
                    'id': str(row.get('Id', '')),
                    'username': row.get('UserName', ''),
                    'name': row.get('Name', ''),
                    'surname': row.get('Surname', ''),
                    'email': row.get('EmailAddress', '')
                })
        
        # 4. Try to find if there's a specific mapping for these IDs (2316, 2334, etc.)
        specific_ids_query = """
        -- Check if these are in WOLabor as mechanic codes
        SELECT DISTINCT TOP 10
            MechanicName
        FROM ben002.WOLabor
        WHERE MechanicName IN ('2316', '2334', '2293', '2318')
           OR MechanicName LIKE '%2316%'
           OR MechanicName LIKE '%2334%'
        """
        
        mechanic_result = db.execute_query(specific_ids_query)
        results['mechanic_matches'] = []
        if mechanic_result:
            for row in mechanic_result:
                results['mechanic_matches'].append(row.get('MechanicName', ''))
        
        # 5. Check if there's a User table in dbo schema
        dbo_user_query = """
        IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'Users')
        BEGIN
            SELECT TOP 10
                *
            FROM dbo.Users
        END
        """
        
        dbo_result = db.execute_query(dbo_user_query)
        results['dbo_users_exists'] = dbo_result is not None and len(dbo_result) > 0
        
        # 6. Check what schemas exist
        schema_query = """
        SELECT DISTINCT TABLE_SCHEMA
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA
        """
        
        schema_result = db.execute_query(schema_query)
        results['schemas'] = []
        if schema_result:
            for row in schema_result:
                results['schemas'].append(row.get('TABLE_SCHEMA', ''))
        
        # 7. Look for any table with ID values like 2316
        id_search_query = """
        SELECT TOP 5
            c.TABLE_SCHEMA,
            c.TABLE_NAME,
            c.COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS c
        INNER JOIN INFORMATION_SCHEMA.TABLES t 
            ON c.TABLE_SCHEMA = t.TABLE_SCHEMA 
            AND c.TABLE_NAME = t.TABLE_NAME
        WHERE t.TABLE_TYPE = 'BASE TABLE'
            AND (c.COLUMN_NAME LIKE '%Id%' OR c.COLUMN_NAME LIKE '%ID%' OR c.COLUMN_NAME LIKE '%Number%')
            AND c.DATA_TYPE IN ('int', 'bigint', 'smallint')
            AND (t.TABLE_NAME LIKE '%User%' OR t.TABLE_NAME LIKE '%Employee%' OR t.TABLE_NAME LIKE '%Person%')
        """
        
        id_columns_result = db.execute_query(id_search_query)
        results['potential_id_columns'] = []
        if id_columns_result:
            for row in id_columns_result:
                results['potential_id_columns'].append({
                    'schema': row.get('TABLE_SCHEMA', ''),
                    'table': row.get('TABLE_NAME', ''),
                    'column': row.get('COLUMN_NAME', '')
                })
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': 'diagnostic_error'
        }), 500