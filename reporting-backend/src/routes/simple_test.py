from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import re
from datetime import datetime

simple_test_bp = Blueprint('simple_test', __name__)

@simple_test_bp.route('/api/simple-test/azure-sql', methods=['GET'])
@jwt_required()
def simple_azure_test():
    """Simple test to demonstrate Azure SQL firewall error"""
    
    result = {
        'test': 'Azure SQL Connection',
        'credentials': {
            'server': 'evo1-sql-replica.database.windows.net',
            'database': 'evo',
            'username': 'ben002user',
            'status': 'Using provided credentials'
        }
    }
    
    try:
        import pymssql
        
        # Attempt connection
        conn = pymssql.connect(
            server='evo1-sql-replica.database.windows.net',
            user='ben002user',
            password='g6O8CE5mT83mDYOW',
            database='evo',
            timeout=30
        )
        conn.close()
        
        result['status'] = 'SUCCESS'
        result['message'] = 'Connected successfully!'
        
    except Exception as e:
        result['status'] = 'FAILED'
        result['error'] = {
            'type': type(e).__name__,
            'message': str(e),
            'error_code': getattr(e, 'args', [None])[0] if hasattr(e, 'args') else None
        }
        
        # Extract IP if present
        error_str = str(e)
        if "Client with IP address" in error_str:
            import re
            ip_match = re.search(r"Client with IP address '(\d+\.\d+\.\d+\.\d+)'", error_str)
            if ip_match:
                result['blocked_ip'] = ip_match.group(1)
                result['firewall_issue'] = True
                result['solution'] = "Please add this IP to Azure SQL firewall or enable 'Allow Azure services'"
    
    return jsonify(result), 200

@simple_test_bp.route('/api/test/azure-connection', methods=['GET'])
def public_azure_test():
    """Public endpoint to test Azure SQL connection - no auth required"""
    
    result = {
        'test': 'Azure SQL Connection Check',
        'timestamp': datetime.now().isoformat(),
        'server': 'evo1-sql-replica.database.windows.net'
    }
    
    try:
        import pymssql
        
        # Attempt connection
        conn = pymssql.connect(
            server='evo1-sql-replica.database.windows.net',
            user='ben002user',
            password='g6O8CE5mT83mDYOW',
            database='evo',
            timeout=10
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        result['status'] = 'SUCCESS'
        result['message'] = 'Connected successfully to Azure SQL!'
        result['sql_version'] = version[:50] + '...' if len(version) > 50 else version
        
    except Exception as e:
        result['status'] = 'FAILED'
        result['error'] = str(e)
        
        # Extract IP if firewall error
        error_str = str(e)
        if "Client with IP address" in error_str:
            import re
            ip_match = re.search(r"Client with IP address '(\d+\.\d+\.\d+\.\d+)'", error_str)
            if ip_match:
                blocked_ip = ip_match.group(1)
                result['blocked_ip'] = blocked_ip
                result['is_railway_ip'] = blocked_ip.startswith('162.220.234.')
                result['message'] = f"Firewall blocking IP: {blocked_ip}"
    
    return jsonify(result), 200

@simple_test_bp.route('/api/test/schema-analysis', methods=['GET'])
def public_schema_analysis():
    """Public endpoint for temporary schema analysis - no auth required"""
    
    result = {
        'analysis': 'Database Schema Analysis',
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Direct connection test first
        import pymssql
        
        result['pymssql_version'] = getattr(pymssql, '__version__', 'unknown')
        
        # Try direct connection
        try:
            conn = pymssql.connect(
                server='evo1-sql-replica.database.windows.net',
                user='ben002user',
                password='g6O8CE5mT83mDYOW',
                database='evo',
                timeout=30
            )
            
            cursor = conn.cursor()
            
            # Get tables from ben002 schema
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA = 'ben002'
                ORDER BY TABLE_NAME
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            result['total_tables'] = len(tables)
            result['tables'] = tables[:20]  # First 20 tables
            
            # Categorize tables
            categories = {
                'customers': [t for t in tables if any(x in t.lower() for x in ['customer', 'client'])],
                'inventory': [t for t in tables if any(x in t.lower() for x in ['inventory', 'equipment', 'forklift'])],
                'sales': [t for t in tables if any(x in t.lower() for x in ['sale', 'order', 'invoice'])],
                'service': [t for t in tables if any(x in t.lower() for x in ['service', 'repair', 'maintenance'])],
                'parts': [t for t in tables if any(x in t.lower() for x in ['part', 'component'])]
            }
            
            result['categories'] = {k: v[:5] for k, v in categories.items() if v}  # Top 5 per category
            
            # Get sample table structure
            sample_tables = {}
            for category, table_list in categories.items():
                if table_list:
                    sample_table = table_list[0]
                    try:
                        cursor.execute(f"""
                            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
                            FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE TABLE_NAME = '{sample_table}'
                            AND TABLE_SCHEMA = 'ben002'
                            ORDER BY ORDINAL_POSITION
                        """)
                        columns = []
                        for row in cursor.fetchall():
                            col_info = {
                                'name': row[0],
                                'type': row[1],
                                'nullable': row[3] == 'YES'
                            }
                            if row[2]:
                                col_info['max_length'] = row[2]
                            columns.append(col_info)
                        
                        sample_tables[sample_table] = {
                            'category': category,
                            'column_count': len(columns),
                            'columns': columns[:10]  # First 10 columns
                        }
                    except Exception as e:
                        sample_tables[sample_table] = {'error': str(e)}
            
            result['sample_structures'] = sample_tables
            result['status'] = 'SUCCESS'
            
            cursor.close()
            conn.close()
            
        except Exception as conn_error:
            result['connection_error'] = {
                'type': type(conn_error).__name__,
                'message': str(conn_error),
                'args': getattr(conn_error, 'args', [])
            }
            result['status'] = 'FAILED'
        
    except Exception as e:
        result['status'] = 'FAILED'
        result['error'] = str(e)
        result['error_type'] = type(e).__name__
    
    return jsonify(result), 200

@simple_test_bp.route("/api/test/db-diagnostics", methods=["GET"])
def db_diagnostics():
    """Comprehensive database diagnostics"""
    
    result = {
        "diagnostics": "Azure SQL Database Check",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        import pymssql
        
        conn = pymssql.connect(
            server="evo1-sql-replica.database.windows.net",
            user="ben002user",
            password="g6O8CE5mT83mDYOW",
            database="evo",
            timeout=30
        )
        
        cursor = conn.cursor()
        
        # 1. Check current database
        cursor.execute("SELECT DB_NAME()")
        result["current_database"] = cursor.fetchone()[0]
        
        # 2. Check user permissions
        cursor.execute("""
            SELECT 
                p.permission_name,
                p.state_desc
            FROM sys.database_permissions p
            WHERE p.grantee_principal_id = USER_ID()
            AND p.state_desc = 'GRANT'
        """)
        permissions = cursor.fetchall()
        result["permissions"] = [{"permission": row[0], "state": row[1]} for row in permissions]
        
        # 3. Try different ways to get tables
        queries = {
            "information_schema": """
                SELECT TABLE_SCHEMA, TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA = 'ben002'
            """,
            "sys_tables": """
                SELECT 
                    s.name AS schema_name,
                    t.name AS table_name
                FROM sys.tables t
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE t.type = 'U'
                AND s.name = 'ben002'
            """,
            "all_tables": """
                SELECT 
                    s.name AS schema_name,
                    t.name AS table_name
                FROM sys.tables t
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE t.type = 'U'
                AND s.name IN ('ben002', 'dbo')
            """
        }
        
        table_results = {}
        for query_name, query in queries.items():
            try:
                cursor.execute(query)
                tables = cursor.fetchall()
                # Convert any bytes to strings
                sample_tables = []
                for table in tables[:5]:
                    if isinstance(table, tuple):
                        sample_tables.append([str(col) if isinstance(col, bytes) else col for col in table])
                    else:
                        sample_tables.append(str(table) if isinstance(table, bytes) else table)
                
                table_results[query_name] = {
                    "count": len(tables),
                    "sample": sample_tables
                }
            except Exception as e:
                table_results[query_name] = {"error": str(e)}
        
        result["table_queries"] = table_results
        
        # 4. Check schemas
        cursor.execute("""
            SELECT 
                schema_name,
                schema_owner
            FROM INFORMATION_SCHEMA.SCHEMATA
            ORDER BY schema_name
        """)
        schemas = cursor.fetchall()
        result["schemas"] = [{"name": row[0], "owner": row[1]} for row in schemas]
        
        # 5. Get database metadata
        cursor.execute("""
            SELECT 
                SERVERPROPERTY('ProductVersion') AS version,
                SERVERPROPERTY('Edition') AS edition,
                SERVERPROPERTY('EngineEdition') AS engine
        """)
        metadata = cursor.fetchone()
        result["server_info"] = {
            "version": str(metadata[0]) if metadata[0] else None,
            "edition": str(metadata[1]) if metadata[1] else None,
            "engine": int(metadata[2]) if metadata[2] else None
        }
        
        result["status"] = "SUCCESS"
        cursor.close()
        conn.close()
        
    except Exception as e:
        result["status"] = "FAILED"
        result["error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "args": getattr(e, "args", [])
        }
    
    return jsonify(result), 200


@simple_test_bp.route("/api/test/permissions-check", methods=["GET"])
def permissions_check():
    """Check user permissions and accessible objects"""
    
    result = {
        "permissions_check": "User Access Analysis",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        import pymssql
        
        conn = pymssql.connect(
            server="evo1-sql-replica.database.windows.net",
            user="ben002user",
            password="g6O8CE5mT83mDYOW",
            database="evo",
            timeout=30
        )
        
        cursor = conn.cursor()
        
        # 1. Current user info
        cursor.execute("SELECT USER_NAME(), SCHEMA_NAME()")
        user_info = cursor.fetchone()
        result["current_user"] = user_info[0] if user_info else None
        result["default_schema"] = user_info[1] if user_info and len(user_info) > 1 else None
        
        # 2. Check what schemas user can access
        cursor.execute("""
            SELECT DISTINCT s.name as schema_name
            FROM sys.schemas s
            WHERE s.principal_id = USER_ID()
            OR EXISTS (
                SELECT 1 FROM sys.database_permissions p
                WHERE p.grantee_principal_id = USER_ID()
                AND p.permission_name = 'SELECT'
                AND p.state_desc = 'GRANT'
                AND p.major_id = s.schema_id
            )
            OR s.name = 'ben002'
            ORDER BY s.name
        """)
        accessible_schemas = [row[0] for row in cursor.fetchall()]
        result["accessible_schemas"] = accessible_schemas
        
        # 3. Try to query tables with explicit schema prefix
        test_queries = {
            "direct_query": "SELECT name FROM ben002.sysobjects WHERE xtype = 'U'",
            "prefixed_tables": """
                SELECT 
                    TABLE_SCHEMA,
                    TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_CATALOG = 'evo'
                AND TABLE_SCHEMA = 'ben002'
            """,
            "all_user_tables": """
                SELECT 
                    s.name AS schema_name,
                    o.name AS table_name
                FROM sys.objects o
                JOIN sys.schemas s ON o.schema_id = s.schema_id
                WHERE o.type = 'U'
                AND HAS_PERMS_BY_NAME(s.name + '.' + o.name, 'OBJECT', 'SELECT') = 1
            """,
            "test_access": """
                SELECT TOP 5
                    s.name AS schema_name,
                    o.name AS object_name,
                    o.type_desc
                FROM sys.objects o
                JOIN sys.schemas s ON o.schema_id = s.schema_id
                WHERE s.name = 'ben002'
            """
        }
        
        query_results = {}
        for query_name, query in test_queries.items():
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
                query_results[query_name] = {
                    "success": True,
                    "count": len(rows),
                    "sample": rows[:5] if rows else []
                }
            except Exception as e:
                query_results[query_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        result["query_tests"] = query_results
        
        # 4. Check if we need to use different table names or views
        cursor.execute("""
            SELECT TOP 10 name, type_desc 
            FROM sys.objects 
            WHERE schema_id = SCHEMA_ID('ben002')
            ORDER BY name
        """)
        ben002_objects = cursor.fetchall()
        result["ben002_objects"] = [{"name": row[0], "type": row[1]} for row in ben002_objects]
        
        result["status"] = "SUCCESS"
        cursor.close()
        conn.close()
        
    except Exception as e:
        result["status"] = "FAILED"
        result["error"] = {
            "type": type(e).__name__,
            "message": str(e)
        }
    
    return jsonify(result), 200
