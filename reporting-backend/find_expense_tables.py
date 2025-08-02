#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.database import get_db

def find_expense_tables():
    """Find G&A expense tables in the database"""
    db = get_db()
    
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
    )
    ORDER BY TABLE_NAME
    """
    
    tables = db.execute_query(table_query)
    
    print(f"Found {len(tables)} potential expense tables:")
    print("-" * 80)
    
    # For each table, get column information and sample data
    for table in tables[:20]:  # Limit to first 20 tables
        table_name = table['TABLE_NAME']
        print(f"\nTable: {table_name}")
        
        # Get columns
        column_query = f"""
        SELECT TOP 10
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        
        columns = db.execute_query(column_query)
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
            count_result = db.execute_query(count_query)
            print(f"  Row count: {count_result[0]['count']}")
            
            # Get sample data if table has rows
            if count_result[0]['count'] > 0:
                sample_query = f"SELECT TOP 3 * FROM ben002.{table_name}"
                sample_data = db.execute_query(sample_query)
                print(f"  Sample data (first row):")
                if sample_data:
                    for key, value in sample_data[0].items():
                        if value is not None:
                            print(f"    {key}: {str(value)[:50]}...")
        except Exception as e:
            print(f"  Error getting data: {str(e)}")
        
        print("-" * 80)

if __name__ == "__main__":
    find_expense_tables()