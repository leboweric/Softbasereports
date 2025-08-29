#!/usr/bin/env python3
"""Explore Equipment table to understand sold unit patterns"""
import os
import sys
import pymssql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
def get_connection():
    return pymssql.connect(
        server=os.getenv('DB_SERVER'),
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

def explore_equipment():
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)
    
    print("=== EQUIPMENT TABLE COLUMNS ===")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'Equipment'
        ORDER BY ORDINAL_POSITION
    """)
    columns = cursor.fetchall()
    
    print(f"Total columns: {len(columns)}")
    print("\nKey columns:")
    for col in columns:
        col_name = col['COLUMN_NAME']
        if col_name and any(keyword in col_name.upper() for keyword in ['STATUS', 'SOLD', 'DELETED', 'INVENTORY', 'DEPT', 'DISPOSAL', 'ACTIVE']):
            print(f"  {col_name:<30} {col['DATA_TYPE']}")
    
    print("\n=== UNIQUE RENTALSTATUS VALUES ===")
    cursor.execute("""
        SELECT RentalStatus, COUNT(*) as count
        FROM ben002.Equipment
        WHERE RentalStatus IS NOT NULL
        GROUP BY RentalStatus
        ORDER BY COUNT(*) DESC
    """)
    statuses = cursor.fetchall()
    for status in statuses:
        print(f"  {status['RentalStatus']:<30} ({status['count']} units)")
    
    print("\n=== ANALYZING PROBLEM UNITS (Manager's Sold List) ===")
    problem_units = ['15597', '17004', '17295B', '17636', '18552', '18808', '18823']
    units_str = "','".join(problem_units)
    
    cursor.execute(f"""
        SELECT UnitNo, SerialNo, RentalStatus, DeletionTime, InventoryDept, CustomerNo
        FROM ben002.Equipment
        WHERE UnitNo IN ('{units_str}')
    """)
    results = cursor.fetchall()
    
    for unit in results:
        print(f"  Unit {unit['UnitNo']}: Status={unit['RentalStatus']}, Dept={unit['InventoryDept']}, Deleted={unit['DeletionTime']}, Customer={unit['CustomerNo']}")
    
    print("\n=== COMPARING SOLD VS AVAILABLE UNITS ===")
    # Compare one sold unit with available units
    cursor.execute("""
        SELECT TOP 1 'Sold (15597)' as Category, UnitNo, RentalStatus, InventoryDept, CustomerNo, DeletionTime
        FROM ben002.Equipment WHERE UnitNo = '15597'
        UNION ALL
        SELECT TOP 3 'Available' as Category, UnitNo, RentalStatus, InventoryDept, CustomerNo, DeletionTime
        FROM ben002.Equipment 
        WHERE RentalStatus IN ('Available', 'Ready To Rent')
        AND (DayRent > 0 OR WeekRent > 0 OR MonthRent > 0)
    """)
    comparison = cursor.fetchall()
    
    for unit in comparison:
        print(f"  {unit['Category']:<15} Unit={unit['UnitNo']:<10} Status={unit['RentalStatus']:<20} Dept={unit['InventoryDept']:<5} Customer={unit['CustomerNo']}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        explore_equipment()
    except Exception as e:
        print(f"Error: {e}")