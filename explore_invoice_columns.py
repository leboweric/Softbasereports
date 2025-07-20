#!/usr/bin/env python3
"""
Explore InvoiceReg table structure to find how to filter for Service invoices
"""

import pymssql
import pandas as pd

# Database connection parameters
server = 'evo1-sql-replica.database.windows.net'
user = 'ben002user'
password = 'g6O8CE5mT83mDYOW'
database = 'evo'

print("Exploring InvoiceReg table structure...")
print("=" * 80)

try:
    # Connect to the database
    conn = pymssql.connect(
        server=server,
        user=user,
        password=password,
        database=database,
        timeout=30,
        login_timeout=30,
        as_dict=True
    )
    print("✓ Connection successful!")
    
    cursor = conn.cursor()
    
    # 1. Get all columns in InvoiceReg table
    print("\n1. All columns in ben002.InvoiceReg:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'InvoiceReg'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    print(f"Total columns: {len(columns)}\n")
    
    # Look for columns that might indicate department/type
    type_keywords = ['type', 'dept', 'department', 'category', 'class', 'division', 'source', 'origin']
    
    print("Columns that might indicate department/type:")
    potential_columns = []
    for col in columns:
        col_name_lower = col['COLUMN_NAME'].lower()
        if any(keyword in col_name_lower for keyword in type_keywords):
            print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
            potential_columns.append(col['COLUMN_NAME'])
    
    # Also check for any column with 'WO' in the name (might link to Work Orders)
    print("\nColumns that might link to Work Orders:")
    wo_columns = []
    for col in columns:
        if 'WO' in col['COLUMN_NAME'].upper() or 'WORK' in col['COLUMN_NAME'].upper():
            print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
            wo_columns.append(col['COLUMN_NAME'])
    
    # 2. Sample data from InvoiceReg
    print("\n2. Sample InvoiceReg data:")
    print("-" * 80)
    
    # Get all columns for analysis
    all_cols = [col['COLUMN_NAME'] for col in columns]
    
    # Create a query with the first 20 columns
    sample_cols = all_cols[:20]
    cols_str = ', '.join([f"[{col}]" for col in sample_cols])
    
    cursor.execute(f"""
        SELECT TOP 10 {cols_str}
        FROM ben002.InvoiceReg
        ORDER BY InvoiceDate DESC
    """)
    
    sample_data = cursor.fetchall()
    if sample_data:
        df_sample = pd.DataFrame(sample_data)
        print(df_sample.to_string(index=False))
    
    # 3. Check distinct values in potential type columns
    if potential_columns:
        print("\n3. Distinct values in potential type columns:")
        print("-" * 80)
        
        for col in potential_columns[:5]:  # Check first 5 potential columns
            try:
                cursor.execute(f"""
                    SELECT 
                        [{col}] as value,
                        COUNT(*) as count
                    FROM ben002.InvoiceReg
                    WHERE [{col}] IS NOT NULL
                    GROUP BY [{col}]
                    ORDER BY COUNT(*) DESC
                """)
                
                values = cursor.fetchall()
                if values:
                    print(f"\n{col} values:")
                    for val in values[:10]:  # Show top 10 values
                        print(f"  - {val['value']}: {val['count']:,} invoices")
                    if len(values) > 10:
                        print(f"  ... and {len(values) - 10} more values")
            except Exception as e:
                print(f"\nError checking {col}: {str(e)}")
    
    # 4. Check if invoices are linked to Work Orders
    if wo_columns:
        print("\n4. Checking Work Order linkage:")
        print("-" * 80)
        
        for col in wo_columns[:3]:
            try:
                # Check if this column has non-null values
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT([{col}]) as non_null
                    FROM ben002.InvoiceReg
                """)
                
                result = cursor.fetchone()
                print(f"\n{col}:")
                print(f"  - Total invoices: {result['total']:,}")
                print(f"  - With {col}: {result['non_null']:,} ({result['non_null']/result['total']*100:.1f}%)")
                
                # If significant linkage, check if we can join to WO table
                if result['non_null'] > result['total'] * 0.1:  # More than 10% have values
                    cursor.execute(f"""
                        SELECT TOP 5
                            i.[{col}],
                            i.InvoiceDate,
                            i.GrandTotal,
                            w.Type,
                            w.WONumber
                        FROM ben002.InvoiceReg i
                        LEFT JOIN ben002.WO w ON i.[{col}] = w.WONumber
                        WHERE i.[{col}] IS NOT NULL
                        AND w.Type IS NOT NULL
                        ORDER BY i.InvoiceDate DESC
                    """)
                    
                    join_test = cursor.fetchall()
                    if join_test:
                        print(f"\n  Sample join with WO table:")
                        for row in join_test:
                            print(f"    Invoice {col}: {row[col]}, WO Type: {row['Type']}, Amount: ${row['GrandTotal']}")
            except Exception as e:
                print(f"\nError checking {col}: {str(e)}")
    
    # 5. Look for any 'Type' or similar field in InvoiceReg
    print("\n5. Checking for Type field in InvoiceReg:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'InvoiceReg'
        AND UPPER(COLUMN_NAME) LIKE '%TYPE%'
    """)
    
    type_columns = cursor.fetchall()
    if type_columns:
        for col in type_columns:
            col_name = col['COLUMN_NAME']
            print(f"\nFound column: {col_name}")
            
            # Get distinct values
            cursor.execute(f"""
                SELECT 
                    [{col_name}] as type_value,
                    COUNT(*) as count
                FROM ben002.InvoiceReg
                GROUP BY [{col_name}]
                ORDER BY COUNT(*) DESC
            """)
            
            types = cursor.fetchall()
            for t in types[:10]:
                print(f"  - {t['type_value']}: {t['count']:,} invoices")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n✗ Error occurred!")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")

print("\nExploration complete.")