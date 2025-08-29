"""
Investigate specific rental units to debug status detection issues
"""

import sys
import os
sys.path.append('/Users/ericlebow/Library/CloudStorage/OneDrive-PBN/Software Projects/Softbasereports/reporting-backend')

os.chdir('/Users/ericlebow/Library/CloudStorage/OneDrive-PBN/Software Projects/Softbasereports/reporting-backend')
from src.services.azure_sql_service import AzureSQLService as DatabaseService
from datetime import datetime

def investigate_units():
    db = DatabaseService()
    
    print("=" * 80)
    print("RENTAL UNIT INVESTIGATION")
    print("=" * 80)
    
    # Units to investigate
    units_to_check = ['21515', '21728', '21729']
    
    for unit_no in units_to_check:
        print(f"\n{'='*60}")
        print(f"UNIT {unit_no} INVESTIGATION")
        print(f"{'='*60}")
        
        # 1. Check Equipment table
        print("\n1. EQUIPMENT TABLE DATA:")
        equipment_query = f"""
        SELECT 
            UnitNo,
            SerialNo,
            Make,
            Model,
            CustomerNo,
            Customer as CustomerOwnedFlag,
            RentalStatus,
            Location,
            InventoryDept,
            DayRent,
            WeekRent,
            MonthRent,
            IsDeleted
        FROM ben002.Equipment
        WHERE UnitNo = '{unit_no}'
        """
        
        equipment = db.execute_query(equipment_query)
        if equipment:
            for row in equipment:
                for key, value in row.items():
                    print(f"  {key}: {value}")
        else:
            print("  No equipment record found")
            continue
            
        serial_no = equipment[0]['SerialNo'] if equipment else None
        
        # 2. Check current month RentalHistory
        print(f"\n2. RENTAL HISTORY (Current Month - {datetime.now().strftime('%B %Y')}):")
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        rental_history_query = f"""
        SELECT 
            SerialNo,
            UnitNo,
            Year,
            Month,
            DaysRented,
            RentAmount,
            CustomerNo,
            DeletionTime
        FROM ben002.RentalHistory
        WHERE (UnitNo = '{unit_no}' OR SerialNo = '{serial_no}')
        AND Year = {current_year}
        AND Month = {current_month}
        """
        
        rental_history = db.execute_query(rental_history_query)
        if rental_history:
            for row in rental_history:
                print(f"  Days Rented: {row['DaysRented']}")
                print(f"  Rent Amount: {row['RentAmount']}")
                print(f"  Customer: {row['CustomerNo']}")
                print(f"  Deletion Time: {row['DeletionTime']}")
        else:
            print("  No rental history for current month")
            
        # 3. Check recent WORental records
        print(f"\n3. RECENT WORK ORDER RENTALS (Last 30 days):")
        wo_rental_query = f"""
        SELECT TOP 5
            wr.WONo,
            wr.SerialNo,
            wr.UnitNo,
            wo.Type,
            wo.OpenDate,
            wo.CompletedDate,
            wo.ClosedDate,
            wo.RentalContractNo,
            wo.BillTo,
            c.Name as CustomerName
        FROM ben002.WORental wr
        JOIN ben002.WO wo ON wr.WONo = wo.WONo
        LEFT JOIN ben002.Customer c ON wo.BillTo = c.Number
        WHERE (wr.UnitNo = '{unit_no}' OR wr.SerialNo = '{serial_no}')
        AND wo.OpenDate >= DATEADD(day, -30, GETDATE())
        ORDER BY wo.OpenDate DESC
        """
        
        wo_rentals = db.execute_query(wo_rental_query)
        if wo_rentals:
            for row in wo_rentals:
                print(f"\n  WO#: {row['WONo']}")
                print(f"  Type: {row['Type']}")
                print(f"  Open Date: {row['OpenDate']}")
                print(f"  Completed: {row['CompletedDate']}")
                print(f"  Closed: {row['ClosedDate']}")
                print(f"  Contract#: {row['RentalContractNo']}")
                print(f"  Customer: {row['CustomerName']} ({row['BillTo']})")
        else:
            print("  No recent work order rentals")
            
        # 4. Check for specific document mentioned (16001378 for units 21728/21729)
        if unit_no in ['21728', '21729']:
            print(f"\n4. CHECKING FOR DOCUMENT #16001378:")
            doc_query = f"""
            SELECT 
                wo.WONo,
                wo.Type,
                wo.OpenDate,
                wo.ClosedDate,
                wo.BillTo,
                c.Name as CustomerName,
                wr.UnitNo,
                wr.SerialNo
            FROM ben002.WO wo
            LEFT JOIN ben002.WORental wr ON wo.WONo = wr.WONo
            LEFT JOIN ben002.Customer c ON wo.BillTo = c.Number
            WHERE wo.WONo LIKE '%16001378%'
            OR wo.RentalContractNo = '16001378'
            """
            
            doc_results = db.execute_query(doc_query)
            if doc_results:
                for row in doc_results:
                    print(f"  Found WO: {row['WONo']}")
                    print(f"  Type: {row['Type']}")
                    print(f"  Customer: {row['CustomerName']}")
                    print(f"  Unit: {row['UnitNo']}")
            else:
                print("  Document not found with that number")
                
        # 5. Check all rental history for last 3 months
        print(f"\n5. RENTAL HISTORY (Last 3 months):")
        history_query = f"""
        SELECT 
            Year,
            Month,
            DaysRented,
            RentAmount,
            CustomerNo,
            DeletionTime
        FROM ben002.RentalHistory
        WHERE (UnitNo = '{unit_no}' OR SerialNo = '{serial_no}')
        AND Year = {current_year}
        AND Month >= {current_month - 2}
        ORDER BY Year DESC, Month DESC
        """
        
        all_history = db.execute_query(history_query)
        if all_history:
            for row in all_history:
                month_name = datetime(row['Year'], row['Month'], 1).strftime('%B %Y')
                print(f"  {month_name}: {row['DaysRented']} days, ${row['RentAmount']}")
                if row['DeletionTime']:
                    print(f"    (Deleted: {row['DeletionTime']})")
        else:
            print("  No rental history in last 3 months")

if __name__ == "__main__":
    investigate_units()