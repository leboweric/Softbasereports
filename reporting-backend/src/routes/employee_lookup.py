from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
from flask_jwt_extended import get_jwt_identity
from src.models.user import User

def get_db():
    """Get database connection"""
    return get_tenant_db()

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/api/employees/lookup', methods=['GET'])
@jwt_required()
def get_employee_names():
    """Get mapping of employee IDs to names from Softbase user table"""
    try:
        db = get_db()
        schema = get_tenant_schema()
        
        # Query to get employee ID to name mapping
        # We'll try multiple potential table/column names since we're not sure of exact structure
        schema = get_tenant_schema()

        query = f"""
        -- First try Users table
        IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Users' AND TABLE_SCHEMA = '{schema}')
        BEGIN
            SELECT 
                CAST(EmployeeNumber AS NVARCHAR(50)) as EmployeeId,
                FirstName,
                LastName,
                Email,
                FirstName + ' ' + LastName as FullName
            FROM {schema}.Users
            WHERE EmployeeNumber IS NOT NULL
        END
        -- Try User table (singular)
        ELSE IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'User' AND TABLE_SCHEMA = '{schema}')
        BEGIN
            SELECT 
                CAST(EmployeeNumber AS NVARCHAR(50)) as EmployeeId,
                FirstName,
                LastName,
                Email,
                FirstName + ' ' + LastName as FullName
            FROM {schema}.[User]
            WHERE EmployeeNumber IS NOT NULL
        END
        -- Try Employee table
        ELSE IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Employee' AND TABLE_SCHEMA = '{schema}')
        BEGIN
            SELECT 
                CAST(EmployeeId AS NVARCHAR(50)) as EmployeeId,
                FirstName,
                LastName,
                Email,
                FirstName + ' ' + LastName as FullName
            FROM {schema}.Employee
            WHERE EmployeeId IS NOT NULL
        END
        -- Try AbpUsers table (common in some systems)
        ELSE IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'AbpUsers' AND TABLE_SCHEMA = '{schema}')
        BEGIN
            SELECT 
                CAST(Id AS NVARCHAR(50)) as EmployeeId,
                Name as FirstName,
                Surname as LastName,
                EmailAddress as Email,
                Name + ' ' + Surname as FullName
            FROM {schema}.AbpUsers
            WHERE Id IS NOT NULL
        END
        ELSE
        BEGIN
            -- Return empty if no user table found
            SELECT 
                NULL as EmployeeId,
                NULL as FirstName,
                NULL as LastName,
                NULL as Email,
                NULL as FullName
            WHERE 1=0
        END
        """
        
        result = db.execute_query(query)
        
        # Create lookup dictionary
        employee_map = {}
        if result:
            for row in result:
                if row.get('EmployeeId'):
                    employee_map[str(row['EmployeeId'])] = {
                        'firstName': row.get('FirstName', ''),
                        'lastName': row.get('LastName', ''),
                        'fullName': row.get('FullName', ''),
                        'email': row.get('Email', '')
                    }
        
        return jsonify({
            'employees': employee_map,
            'count': len(employee_map)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'employees': {},
            'count': 0
        }), 500


@employee_bp.route('/api/employees/discover-table', methods=['GET'])
@jwt_required()
def discover_employee_table():
    """Discover which user/employee tables exist in the database"""
    try:
        db = get_db()
        schema = get_tenant_schema()
        
        # Query to find all tables that might contain user/employee data
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
             WHERE TABLE_NAME = t.TABLE_NAME AND TABLE_SCHEMA = t.TABLE_SCHEMA
             AND COLUMN_NAME IN ('EmployeeNumber', 'EmployeeId', 'UserId', 'FirstName', 'LastName')) as RelevantColumns
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE TABLE_TYPE = 'BASE TABLE'
            AND (
                TABLE_NAME LIKE '%User%' 
                OR TABLE_NAME LIKE '%Employee%'
                OR TABLE_NAME LIKE '%Staff%'
                OR TABLE_NAME LIKE '%Person%'
                OR TABLE_NAME LIKE '%Worker%'
            )
            AND TABLE_SCHEMA = '{schema}'
        ORDER BY RelevantColumns DESC, TABLE_NAME
        """
        
        tables_result = db.execute_query(query)
        
        discovered_tables = []
        for row in tables_result:
            # Get column details for each table
            columns_query = f"""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{row['TABLE_SCHEMA']}'
                AND TABLE_NAME = '{row['TABLE_NAME']}'
                AND COLUMN_NAME IN ('EmployeeNumber', 'EmployeeId', 'UserId', 'Id', 
                                   'FirstName', 'LastName', 'Name', 'Email', 'EmailAddress')
            ORDER BY ORDINAL_POSITION
            """
            
            columns_result = db.execute_query(columns_query)
            
            discovered_tables.append({
                'schema': row['TABLE_SCHEMA'],
                'tableName': row['TABLE_NAME'],
                'relevantColumns': [{'name': col['COLUMN_NAME'], 'type': col['DATA_TYPE']} 
                                   for col in columns_result] if columns_result else []
            })
        
        return jsonify({
            'tables': discovered_tables,
            'count': len(discovered_tables)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'tables': []
        }), 500