#!/usr/bin/env python3
"""
Quick script to check Equipment table schema
Run this locally to avoid firewall issues
"""

import os
import pymssql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get connection details from environment or use defaults
server = os.getenv('DB_SERVER', 'softbaseserver.database.windows.net')
database = os.getenv('DB_NAME', 'softbasedb')
username = os.getenv('DB_USERNAME', 'softbaseadmin')
password = os.getenv('DB_PASSWORD')

if not password:
    print("DB_PASSWORD not found in environment variables")
    exit(1)

try:
    # Connect to database
    print(f"Connecting to {server}/{database}...")
    conn = pymssql.connect(server=server, user=username, password=password, database=database)
    cursor = conn.cursor()
    
    # Get Equipment table columns
    print("\n=== Equipment Table Columns ===")
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'Equipment'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    if columns:
        print(f"\nFound {len(columns)} columns:")
        for col in columns:
            print(f"  - {col[0]:<30} {col[1]:<15} {f'({col[2]})' if col[2] else '':<10} {'NULL' if col[3] == 'YES' else 'NOT NULL'}")
    else:
        print("No columns found - table might not exist")
    
    # Get sample data
    print("\n=== Sample Equipment Data (first 3 rows) ===")
    cursor.execute("SELECT TOP 3 * FROM ben002.Equipment")
    
    # Get column names
    col_names = [desc[0] for desc in cursor.description]
    print("\nColumns:", ', '.join(col_names))
    
    # Print sample rows
    rows = cursor.fetchall()
    for i, row in enumerate(rows):
        print(f"\nRow {i+1}:")
        for j, (col_name, value) in enumerate(zip(col_names, row)):
            if value is not None:
                print(f"  {col_name}: {value}")
    
    # Test specific column names
    print("\n=== Testing Specific Column Names ===")
    test_columns = ['StockNo', 'Stock', 'StockNumber', 'EquipmentNo', 'EquipmentID', 'ID', 'SerialNo', 'Make', 'Model']
    
    for test_col in test_columns:
        try:
            cursor.execute(f"SELECT TOP 1 [{test_col}] FROM ben002.Equipment")
            cursor.fetchall()  # Clear results
            print(f"✓ {test_col} - EXISTS")
        except:
            print(f"✗ {test_col} - NOT FOUND")
    
    # Close connection
    cursor.close()
    conn.close()
    
    print("\n=== Summary ===")
    print("The Equipment table exists and we can query it.")
    print("Update the AI Query configuration to use the correct column names shown above.")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure you have:")
    print("1. Set DB_PASSWORD environment variable")
    print("2. pymssql installed (pip install pymssql)")
    print("3. Network access to Azure SQL Server")