#!/usr/bin/env python3
"""Explore Equipment table to understand sold unit patterns - direct connection"""
import pymssql

# Direct connection using known credentials
def get_connection():
    return pymssql.connect(
        server='evo1-sql-replica.database.windows.net',
        user='ben002user',
        password='g6O8CE5mT83mDYOW',
        database='evo'
    )

def explore_equipment():
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)
    
    print("=== EQUIPMENT TABLE COLUMNS ===")
    cursor.execute("""
        SELECT TOP 50 COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'Equipment'
        ORDER BY ORDINAL_POSITION
    """)
    columns = cursor.fetchall()
    
    print(f"First 50 columns (of many):")
    for col in columns:
        col_name = col['COLUMN_NAME']
        if col_name and any(keyword in col_name.upper() for keyword in 
                           ['STATUS', 'SOLD', 'DELETED', 'INVENTORY', 'DEPT', 
                            'DISPOSAL', 'ACTIVE', 'AVAILABLE']):
            print(f"  ** {col_name:<30} {col['DATA_TYPE']}")
        else:
            print(f"     {col_name:<30} {col['DATA_TYPE']}")
    
    print("\n=== UNIQUE RENTALSTATUS VALUES ===")
    cursor.execute("""
        SELECT RentalStatus, COUNT(*) as count
        FROM ben002.Equipment
        WHERE RentalStatus IS NOT NULL
        GROUP BY RentalStatus
        ORDER BY COUNT(*) DESC
    """)
    statuses = cursor.fetchall()
    for status in statuses[:20]:  # Top 20 statuses
        print(f"  {status['RentalStatus']:<30} ({status['count']} units)")
    
    print("\n=== ANALYZING PROBLEM UNITS (Manager's Sold List) ===")
    # Units manager said are sold
    problem_units = ['15597', '17004', '17295B', '17636', '18552', '18808', '18823', 
                    '18835', '19060', '19420', '19890', '20457']
    units_str = "','".join(problem_units)
    
    cursor.execute(f"""
        SELECT UnitNo, SerialNo, RentalStatus, DeletionTime, InventoryDept, 
               CustomerNo, Location, DayRent, WeekRent, MonthRent
        FROM ben002.Equipment
        WHERE UnitNo IN ('{units_str}')
    """)
    results = cursor.fetchall()
    
    print(f"Found {len(results)} of {len(problem_units)} units")
    for unit in results:
        print(f"  Unit {unit['UnitNo']:<10} Status={unit['RentalStatus']:<20} "
              f"Dept={unit['InventoryDept']:<5} Deleted={unit['DeletionTime']} "
              f"Customer={unit['CustomerNo']:<10} Rates={unit['DayRent']}/{unit['WeekRent']}/{unit['MonthRent']}")
    
    # Check for recent rental history
    print("\n=== CHECKING RENTAL HISTORY FOR PROBLEM UNITS ===")
    cursor.execute(f"""
        SELECT e.UnitNo, 
               MAX(CAST(CAST(rh.Year AS VARCHAR(4)) + '-' + CAST(rh.Month AS VARCHAR(2)) + '-01' AS DATE)) as LastRentalMonth
        FROM ben002.Equipment e
        LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo AND rh.DaysRented > 0
        WHERE e.UnitNo IN ('{units_str}')
        GROUP BY e.UnitNo
    """)
    history = cursor.fetchall()
    for h in history:
        print(f"  Unit {h['UnitNo']:<10} Last Rental: {h['LastRentalMonth']}")
    
    print("\n=== COMPARING SOLD VS AVAILABLE UNITS ===")
    cursor.execute("""
        SELECT TOP 1 'Sold (15597)' as Category, UnitNo, RentalStatus, InventoryDept, 
               CustomerNo, DeletionTime, Location
        FROM ben002.Equipment WHERE UnitNo = '15597'
        UNION ALL
        SELECT TOP 5 'Available' as Category, UnitNo, RentalStatus, InventoryDept, 
               CustomerNo, DeletionTime, Location
        FROM ben002.Equipment 
        WHERE RentalStatus IN ('Available', 'Ready To Rent')
        AND (DayRent > 0 OR WeekRent > 0 OR MonthRent > 0)
    """)
    comparison = cursor.fetchall()
    
    for unit in comparison:
        print(f"  {unit['Category']:<15} Unit={unit['UnitNo']:<10} Status={unit['RentalStatus']:<20} "
              f"Dept={unit['InventoryDept']:<5} Location={unit['Location']}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        explore_equipment()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()