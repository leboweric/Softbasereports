from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
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



def get_db():
    """Get database connection"""
    return get_tenant_db()

employee_diagnostic_bp = Blueprint('employee_diagnostic', __name__)

@employee_diagnostic_bp.route('/api/diagnostic/employee-mapping', methods=['GET'])
@jwt_required()
def diagnose_employee_mapping():
    """Diagnostic endpoint to figure out employee ID mapping"""
    try:
        db = get_db()
        schema = get_tenant_schema()
        
        results = {}
        
        # 1. Check what CreatorUserId values look like for CSTPRT sale code
        try:
            creator_query = f"""
            SELECT TOP 20
                CreatorUserId,
                COUNT(*) as InvoiceCount,
                SUM(ISNULL(PartsTaxable, 0) + ISNULL(PartsNonTax, 0)) as TotalPartsSales
            FROM {schema}.InvoiceReg
            WHERE CreatorUserId IS NOT NULL
                AND SaleCode = 'CSTPRT'
            GROUP BY CreatorUserId
            ORDER BY COUNT(*) DESC
            """
            
            creator_result = db.execute_query(creator_query)
            results['top_creator_ids'] = []
            if creator_result:
                for row in creator_result:
                    results['top_creator_ids'].append({
                        'id': str(row.get('CreatorUserId', '')),
                        'count': row.get('InvoiceCount', 0),
                        'totalSales': float(row.get('TotalPartsSales', 0))
                    })
        except Exception as e:
            results['top_creator_ids'] = f"Error: {str(e)}"
        
        # 2. Find all tables with 'User' in the name
        try:
            user_tables_query = f"""
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
        except Exception as e:
            results['user_tables'] = f"Error: {str(e)}"
        
        # 3. Check for AbpUsers table
        try:
            abp_query = f"""
            SELECT TOP 1 TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'AbpUsers'
            """
            abp_exists = db.execute_query(abp_query)
            
            if abp_exists and len(abp_exists) > 0:
                # Table exists, get sample data
                abp_data_query = f"""
                SELECT TOP 10
                    Id,
                    UserName,
                    Name,
                    Surname,
                    EmailAddress
                FROM AbpUsers
                ORDER BY Id
                """
                abp_result = db.execute_query(abp_data_query)
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
            else:
                results['abp_users_sample'] = "AbpUsers table not found"
        except Exception as e:
            results['abp_users_sample'] = f"Error checking AbpUsers: {str(e)}"
        
        # 4. Check what schemas exist
        try:
            schema_query = f"""
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
        except Exception as e:
            results['schemas'] = f"Error: {str(e)}"
        
        # 5. Look for any table with ID columns that might contain our employee IDs
        try:
            id_search_query = f"""
            SELECT TOP 20
                c.TABLE_SCHEMA,
                c.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS c
            INNER JOIN INFORMATION_SCHEMA.TABLES t 
                ON c.TABLE_SCHEMA = t.TABLE_SCHEMA 
                AND c.TABLE_NAME = t.TABLE_NAME
            WHERE t.TABLE_TYPE = 'BASE TABLE'
                AND (c.COLUMN_NAME LIKE '%Id%' OR c.COLUMN_NAME LIKE '%ID%' OR c.COLUMN_NAME LIKE '%Number%')
                AND c.DATA_TYPE IN ('int', 'bigint', 'smallint', 'nvarchar', 'varchar')
                AND (t.TABLE_NAME LIKE '%User%' OR t.TABLE_NAME LIKE '%Employee%' OR t.TABLE_NAME LIKE '%Person%' OR t.TABLE_NAME LIKE '%Staff%')
            ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.COLUMN_NAME
            """
            
            id_columns_result = db.execute_query(id_search_query)
            results['potential_id_columns'] = []
            if id_columns_result:
                for row in id_columns_result:
                    results['potential_id_columns'].append({
                        'schema': row.get('TABLE_SCHEMA', ''),
                        'table': row.get('TABLE_NAME', ''),
                        'column': row.get('COLUMN_NAME', ''),
                        'type': row.get('DATA_TYPE', '')
                    })
        except Exception as e:
            results['potential_id_columns'] = f"Error: {str(e)}"
        
        # 6. Get sample of parts invoices with creator info
        try:
            sample_query = f"""
            SELECT TOP 5
                InvoiceNo,
                CreatorUserId,
                LastModifierUserId,
                BillToName,
                InvoiceDate,
                PartsTaxable + PartsNonTax as PartsTotal
            FROM {schema}.InvoiceReg
            WHERE (PartsTaxable > 0 OR PartsNonTax > 0)
                AND CreatorUserId IN ('2316', '2334', '2293', '2318')
            ORDER BY InvoiceDate DESC
            """
            
            sample_result = db.execute_query(sample_query)
            results['sample_invoices'] = []
            if sample_result:
                for row in sample_result:
                    results['sample_invoices'].append({
                        'invoiceNo': row.get('InvoiceNo', ''),
                        'creatorId': str(row.get('CreatorUserId', '')),
                        'modifierId': str(row.get('LastModifierUserId', '')),
                        'customer': row.get('BillToName', ''),
                        'date': row.get('InvoiceDate').strftime('%Y-%m-%d') if row.get('InvoiceDate') else '',
                        'partsTotal': float(row.get('PartsTotal', 0))
                    })
        except Exception as e:
            results['sample_invoices'] = f"Error: {str(e)}"
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': 'diagnostic_error',
            'message': 'Main diagnostic failed'
        }), 500