#!/usr/bin/env python3
"""
Verify the count of open service work orders in the ben002.WO table
"""

import pymssql
import pandas as pd

# Database connection parameters
server = 'evo1-sql-replica.database.windows.net'
user = 'ben002user'
password = 'g6O8CE5mT83mDYOW'
database = 'evo'

print("Connecting to Softbase database...")
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
    
    # First, let's examine the structure of the WO table
    print("\n1. Examining ben002.WO table structure:")
    print("-" * 80)
    
    # Get column information
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'WO'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    print(f"Total columns in ben002.WO: {len(columns)}")
    print("\nRelevant columns for work order status:")
    
    # Look for columns that might indicate status
    status_keywords = ['status', 'closed', 'open', 'complete', 'active', 'state', 'type']
    for col in columns:
        col_name_lower = col['COLUMN_NAME'].lower()
        if any(keyword in col_name_lower for keyword in status_keywords):
            print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
    
    # Get a sample of data to understand the table better
    print("\n2. Sample data from ben002.WO:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT TOP 5 
            WONumber,
            Type,
            ClosedDate,
            CreatedDate,
            Status
        FROM ben002.WO
        WHERE Type = 'S'
        ORDER BY CreatedDate DESC
    """)
    
    sample_data = cursor.fetchall()
    if sample_data:
        df_sample = pd.DataFrame(sample_data)
        print(df_sample.to_string(index=False))
    
    # Query 1: Total service work orders
    print("\n3. Total Service Work Orders (Type = 'S'):")
    print("-" * 80)
    
    cursor.execute("""
        SELECT COUNT(*) as TotalServiceOrders
        FROM ben002.WO
        WHERE Type = 'S'
    """)
    
    result = cursor.fetchone()
    total_service = result['TotalServiceOrders']
    print(f"Total service work orders: {total_service:,}")
    
    # Query 2: Open service work orders (ClosedDate IS NULL)
    print("\n4. Open Service Work Orders (Type = 'S' AND ClosedDate IS NULL):")
    print("-" * 80)
    
    cursor.execute("""
        SELECT COUNT(*) as OpenServiceOrders
        FROM ben002.WO
        WHERE Type = 'S' 
        AND ClosedDate IS NULL
    """)
    
    result = cursor.fetchone()
    open_service = result['OpenServiceOrders']
    print(f"Open service work orders (ClosedDate IS NULL): {open_service:,}")
    
    # Query 3: Check if Status column exists and get unique values
    print("\n5. Checking for Status field values:")
    print("-" * 80)
    
    # Check if Status column exists
    cursor.execute("""
        SELECT COUNT(*) as HasStatusColumn
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'WO'
        AND COLUMN_NAME = 'Status'
    """)
    
    has_status = cursor.fetchone()['HasStatusColumn'] > 0
    
    if has_status:
        # Get unique Status values
        cursor.execute("""
            SELECT 
                Status,
                COUNT(*) as Count
            FROM ben002.WO
            WHERE Type = 'S'
            GROUP BY Status
            ORDER BY Count DESC
        """)
        
        status_values = cursor.fetchall()
        print("Status values for service work orders:")
        for status in status_values:
            print(f"  - {status['Status'] or 'NULL'}: {status['Count']:,} orders")
        
        # Check open orders by Status field
        cursor.execute("""
            SELECT 
                COUNT(*) as OpenByStatus
            FROM ben002.WO
            WHERE Type = 'S'
            AND Status IN ('Open', 'OPEN', 'O', 'Active', 'ACTIVE', 'A')
        """)
        
        open_by_status = cursor.fetchone()['OpenByStatus']
        print(f"\nOpen service orders by Status field: {open_by_status:,}")
    else:
        print("No Status column found in ben002.WO table")
    
    # Query 4: Cross-check with both ClosedDate and Status
    if has_status:
        print("\n6. Cross-checking ClosedDate and Status:")
        print("-" * 80)
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN ClosedDate IS NULL THEN 'ClosedDate IS NULL'
                    ELSE 'ClosedDate IS NOT NULL'
                END as ClosedDateStatus,
                Status,
                COUNT(*) as Count
            FROM ben002.WO
            WHERE Type = 'S'
            GROUP BY 
                CASE 
                    WHEN ClosedDate IS NULL THEN 'ClosedDate IS NULL'
                    ELSE 'ClosedDate IS NOT NULL'
                END,
                Status
            ORDER BY ClosedDateStatus, Count DESC
        """)
        
        cross_check = cursor.fetchall()
        print("Cross-check results:")
        for row in cross_check:
            print(f"  - {row['ClosedDateStatus']}, Status: {row['Status'] or 'NULL'} = {row['Count']:,} orders")
    
    # Query 5: Recent open service orders
    print("\n7. Sample of recent open service orders:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT TOP 10
            WONumber,
            CreatedDate,
            ClosedDate,
            Status,
            CustomerID,
            EquipmentID
        FROM ben002.WO
        WHERE Type = 'S'
        AND ClosedDate IS NULL
        ORDER BY CreatedDate DESC
    """)
    
    recent_open = cursor.fetchall()
    if recent_open:
        df_recent = pd.DataFrame(recent_open)
        print(df_recent.to_string(index=False))
    else:
        print("No open service orders found")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Total Service Work Orders: {total_service:,}")
    print(f"Open Service Work Orders (ClosedDate IS NULL): {open_service:,}")
    print(f"Percentage Open: {(open_service/total_service*100):.1f}%")
    if has_status:
        print(f"Open by Status field: {open_by_status:,}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n✗ Error occurred!")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")

print("\nVerification complete.")