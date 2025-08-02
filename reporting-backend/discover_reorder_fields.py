#!/usr/bin/env python3
"""
Discover reorder point and inventory management fields in Parts table
"""
import os
from dotenv import load_dotenv
from src.services.azure_sql_service import AzureSQLService

def discover_reorder_fields():
    """Find inventory management columns in Parts table"""
    load_dotenv()
    
    try:
        db = AzureSQLService()
        
        # Get ALL columns from Parts table first
        all_columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'Parts'
        ORDER BY ORDINAL_POSITION
        """
        
        print("Fetching all Parts table columns...")
        all_columns = db.execute_query(all_columns_query)
        
        print(f"\nTotal columns in Parts table: {len(all_columns)}")
        print("\nLooking for inventory management related columns:")
        print("-" * 60)
        
        # Keywords to look for
        keywords = ['reorder', 'min', 'max', 'lead', 'safety', 'stock', 'order', 'qty', 'level', 'point']
        
        relevant_columns = []
        for col in all_columns:
            col_name_lower = col['COLUMN_NAME'].lower()
            for keyword in keywords:
                if keyword in col_name_lower:
                    relevant_columns.append(col)
                    print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
                    break
        
        # Also check for average usage data
        print("\n\nChecking WOParts for historical usage data...")
        usage_query = """
        SELECT TOP 10
            wp.PartNo,
            COUNT(*) as TimesOrdered,
            SUM(wp.Qty) as TotalQtyOrdered,
            MIN(w.OpenDate) as FirstOrder,
            MAX(w.OpenDate) as LastOrder,
            DATEDIFF(day, MIN(w.OpenDate), MAX(w.OpenDate)) as DaysBetween
        FROM ben002.WOParts wp
        INNER JOIN ben002.WO w ON wp.WONo = w.WONo
        WHERE w.OpenDate >= DATEADD(month, -12, GETDATE())
        GROUP BY wp.PartNo
        HAVING COUNT(*) > 5
        ORDER BY COUNT(*) DESC
        """
        
        usage_data = db.execute_query(usage_query)
        print(f"\nFound usage data for {len(usage_data)} parts with 5+ orders in last 12 months")
        
        # Check if we have supplier/vendor data
        print("\n\nChecking for supplier/vendor tables...")
        supplier_query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002'
        AND (TABLE_NAME LIKE '%Vendor%' OR TABLE_NAME LIKE '%Supplier%')
        """
        
        supplier_tables = db.execute_query(supplier_query)
        if supplier_tables:
            print("Found supplier/vendor tables:")
            for table in supplier_tables:
                print(f"  - {table['TABLE_NAME']}")
        else:
            print("No dedicated supplier/vendor tables found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    discover_reorder_fields()