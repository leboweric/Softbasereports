#!/usr/bin/env python3
import os
import pymssql

# Database connection parameters
server = os.environ.get('AZURE_SQL_SERVER', 'evo1-sql-replica.database.windows.net')
database = os.environ.get('AZURE_SQL_DATABASE', 'evo')
username = os.environ.get('AZURE_SQL_USERNAME', 'ben002user')
password = os.environ.get('AZURE_SQL_PASSWORD', 'g6O8CE5mT83mDYOW')

def find_expense_tables():
    """Find G&A expense tables in the database"""
    try:
        # Connect to database
        conn = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            as_dict=True,
            timeout=30
        )
        cursor = conn.cursor()
        
        print(f"Connected to {server}/{database}")
        print("=" * 80)
        
        # Query to find potential expense-related tables
        table_query = """
        SELECT 
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002'
        AND (
            TABLE_NAME LIKE '%expense%'
            OR TABLE_NAME LIKE '%payable%'
            OR TABLE_NAME LIKE '%AP%'
            OR TABLE_NAME LIKE '%GL%'
            OR TABLE_NAME LIKE '%ledger%'
            OR TABLE_NAME LIKE '%vendor%'
            OR TABLE_NAME LIKE '%payroll%'
            OR TABLE_NAME LIKE '%salary%'
            OR TABLE_NAME LIKE '%wage%'
            OR TABLE_NAME LIKE '%payment%'
            OR TABLE_NAME LIKE '%disbursement%'
            OR TABLE_NAME LIKE '%purchase%'
            OR TABLE_NAME LIKE '%journal%'
            OR TABLE_NAME LIKE '%transaction%'
            OR TABLE_NAME LIKE '%account%'
            OR TABLE_NAME LIKE '%cost%'
        )
        ORDER BY TABLE_NAME
        """
        
        cursor.execute(table_query)
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} potential expense tables:")
        print("-" * 80)
        
        # For each table, get column information and sample data
        for table in tables[:30]:  # Limit to first 30 tables
            table_name = table['TABLE_NAME']
            print(f"\nTable: {table_name}")
            
            # Get columns
            column_query = f"""
            SELECT TOP 15
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002'
            AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """
            
            cursor.execute(column_query)
            columns = cursor.fetchall()
            
            print("  Columns:")
            for col in columns:
                col_info = f"    - {col['COLUMN_NAME']} ({col['DATA_TYPE']}"
                if col['CHARACTER_MAXIMUM_LENGTH']:
                    col_info += f", {col['CHARACTER_MAXIMUM_LENGTH']}"
                col_info += f", {'NULL' if col['IS_NULLABLE'] == 'YES' else 'NOT NULL'})"
                print(col_info)
            
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM ben002.{table_name}"
            try:
                cursor.execute(count_query)
                count_result = cursor.fetchone()
                print(f"  Row count: {count_result['count']}")
                
                # Get sample data if table has rows and looks promising
                if count_result['count'] > 0 and any(keyword in table_name.lower() for keyword in ['gl', 'ledger', 'expense', 'payable', 'vendor', 'journal']):
                    sample_query = f"SELECT TOP 2 * FROM ben002.{table_name}"
                    cursor.execute(sample_query)
                    sample_data = cursor.fetchall()
                    print(f"  Sample data (first row):")
                    if sample_data:
                        for key, value in sample_data[0].items():
                            if value is not None:
                                value_str = str(value)[:50]
                                if len(str(value)) > 50:
                                    value_str += "..."
                                print(f"    {key}: {value_str}")
            except Exception as e:
                print(f"  Error getting data: {str(e)}")
            
            print("-" * 80)
        
        # Also look for specific G&A categories in GL accounts
        print("\n\nSearching for G&A expense accounts in GL...")
        print("=" * 80)
        
        # Look for GL account tables
        gl_query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002'
        AND (TABLE_NAME LIKE '%GL%Account%' OR TABLE_NAME LIKE '%Chart%Account%')
        """
        
        cursor.execute(gl_query)
        gl_tables = cursor.fetchall()
        
        for gl_table in gl_tables:
            table_name = gl_table['TABLE_NAME']
            print(f"\nGL Table: {table_name}")
            
            # Look for G&A expense accounts
            account_query = f"""
            SELECT TOP 20 *
            FROM ben002.{table_name}
            WHERE 1=1
            """
            
            try:
                cursor.execute(account_query)
                accounts = cursor.fetchall()
                if accounts:
                    print("  Sample accounts:")
                    for acc in accounts[:10]:
                        print(f"    {acc}")
            except Exception as e:
                print(f"  Error: {str(e)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    find_expense_tables()