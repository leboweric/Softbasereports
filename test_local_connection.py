#!/usr/bin/env python3
"""
Test Azure SQL connection from local environment
This will help determine if the issue is specific to Railway or general
"""

import sys
import os

print("Azure SQL Connection Test - Local Environment")
print("=" * 50)

# Test 1: Check if pymssql is available
try:
    import pymssql
    print("✓ pymssql is installed")
    print(f"  Version: {pymssql.__version__ if hasattr(pymssql, '__version__') else 'unknown'}")
except ImportError:
    print("✗ pymssql is not installed")
    print("  Installing pymssql...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymssql"])
    import pymssql
    print("✓ pymssql installed successfully")

print("\nConnection Details:")
print("-" * 50)
print("Server: evo1-sql-replica.database.windows.net")
print("Database: evo")
print("Username: ben002user")
print("Password: ***HIDDEN***")

print("\nAttempting connection...")
print("-" * 50)

try:
    # Attempt to connect
    conn = pymssql.connect(
        server='evo1-sql-replica.database.windows.net',
        user='ben002user',
        password='g6O8CE5mT83mDYOW',
        database='evo',
        timeout=30,
        login_timeout=30,
        as_dict=True
    )
    
    print("✓ CONNECTION SUCCESSFUL!")
    print("\nYour local IP is allowed to connect to Azure SQL.")
    
    cursor = conn.cursor()
    
    # Test 1: Get SQL Server version
    print("\n1. SQL Server Version:")
    cursor.execute("SELECT @@VERSION AS version")
    result = cursor.fetchone()
    print(f"   {result['version'][:80]}...")
    
    # Test 2: List databases
    print("\n2. Available Databases:")
    cursor.execute("SELECT name FROM sys.databases ORDER BY name")
    databases = cursor.fetchall()
    for db in databases[:5]:  # Show first 5
        print(f"   - {db['name']}")
    if len(databases) > 5:
        print(f"   ... and {len(databases) - 5} more")
    
    # Test 3: List tables in current database
    print("\n3. Tables in 'evo' database:")
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE' 
        ORDER BY TABLE_NAME
    """)
    tables = cursor.fetchall()
    
    # Categorize tables
    categories = {
        'Customer': [],
        'Equipment': [],
        'Sales': [],
        'Service': [],
        'Parts': [],
        'Other': []
    }
    
    for table in tables:
        table_name = table['TABLE_NAME']
        table_lower = table_name.lower()
        
        if 'customer' in table_lower:
            categories['Customer'].append(table_name)
        elif any(x in table_lower for x in ['equipment', 'forklift', 'inventory']):
            categories['Equipment'].append(table_name)
        elif any(x in table_lower for x in ['sale', 'order', 'invoice']):
            categories['Sales'].append(table_name)
        elif any(x in table_lower for x in ['service', 'work', 'repair']):
            categories['Service'].append(table_name)
        elif 'part' in table_lower:
            categories['Parts'].append(table_name)
        else:
            categories['Other'].append(table_name)
    
    print(f"   Total tables found: {len(tables)}")
    for category, table_list in categories.items():
        if table_list:
            print(f"\n   {category} Tables ({len(table_list)}):")
            for table in table_list[:3]:  # Show first 3
                print(f"      - {table}")
            if len(table_list) > 3:
                print(f"      ... and {len(table_list) - 3} more")
    
    # Test 4: Sample data from a customer table
    print("\n4. Sample Data:")
    # Try to find a customer table
    customer_tables = [t['TABLE_NAME'] for t in tables if 'customer' in t['TABLE_NAME'].lower()]
    if customer_tables:
        sample_table = customer_tables[0]
        print(f"   From table '{sample_table}':")
        cursor.execute(f"SELECT TOP 5 * FROM [{sample_table}]")
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        print(f"   Columns: {', '.join(columns[:5])}")
        if len(columns) > 5:
            print(f"            ... and {len(columns) - 5} more columns")
        
        # Show row count
        cursor.execute(f"SELECT COUNT(*) as count FROM [{sample_table}]")
        count = cursor.fetchone()
        print(f"   Total rows: {count['count']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 50)
    print("SUCCESS: Your local environment CAN connect to Softbase Azure SQL!")
    print("The issue is specific to Railway's IP addresses being blocked.")
    print("=" * 50)
    
except Exception as e:
    print(f"\n✗ CONNECTION FAILED!")
    print(f"\nError Type: {type(e).__name__}")
    print(f"Error Code: {e.args[0] if hasattr(e, 'args') and e.args else 'N/A'}")
    print(f"Error Message: {str(e)}")
    
    # Check if it's a firewall error
    if "40615" in str(e) or "Client with IP address" in str(e):
        import re
        ip_match = re.search(r"Client with IP address '(\d+\.\d+\.\d+\.\d+)'", str(e))
        if ip_match:
            blocked_ip = ip_match.group(1)
            print(f"\n⚠️  FIREWALL ISSUE DETECTED!")
            print(f"Your IP address ({blocked_ip}) is also blocked by Azure SQL firewall.")
            print("\nThis confirms the firewall is blocking external connections.")
    else:
        print("\nThis appears to be a different error than the Railway deployment.")
        print("It might be a credential or network issue.")

print("\nTest complete.")