#!/usr/bin/env python3
"""
Discover Equipment table columns
"""
import os
from dotenv import load_dotenv
from src.services.azure_sql_service import AzureSQLService

def discover_equipment_columns():
    """Find all columns in Equipment table"""
    load_dotenv()
    
    try:
        db = AzureSQLService()
        
        # Get ALL columns from Equipment table
        columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'Equipment'
        ORDER BY ORDINAL_POSITION
        """
        
        print("Fetching Equipment table columns...")
        columns = db.execute_query(columns_query)
        
        print(f"\nTotal columns in Equipment table: {len(columns)}")
        print("\nAll columns:")
        print("-" * 60)
        
        for col in columns:
            print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
            
        # Check for specific columns we need
        print("\n\nChecking for ID/Stock/Unit columns:")
        print("-" * 60)
        
        id_keywords = ['id', 'stock', 'unit', 'equip', 'no', 'num']
        
        for col in columns:
            col_name_lower = col['COLUMN_NAME'].lower()
            for keyword in id_keywords:
                if keyword in col_name_lower:
                    print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
                    break
                    
        # Try to get sample data to understand structure
        print("\n\nSample Equipment data:")
        print("-" * 60)
        
        sample_query = """
        SELECT TOP 5 *
        FROM ben002.Equipment
        """
        
        sample_data = db.execute_query(sample_query)
        if sample_data:
            # Print column names from first row
            print("Columns found in sample data:")
            for key in sample_data[0].keys():
                print(f"  - {key}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    discover_equipment_columns()