#!/usr/bin/env python3
"""
Discover tables in the Softbase database
"""
import os
from dotenv import load_dotenv
from src.services.azure_sql_service import AzureSQLService

def discover_tables():
    """List all tables in the database"""
    load_dotenv()
    
    try:
        db = AzureSQLService()
        
        # Query to get all tables in the ben002 schema
        tables_query = """
        SELECT 
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002'
        ORDER BY TABLE_NAME
        """
        
        print("Discovering tables in ben002 schema...")
        tables = db.execute_query(tables_query)
        
        if tables:
            print(f"\nFound {len(tables)} tables:")
            for table in tables:
                print(f"  - {table['TABLE_NAME']} ({table['TABLE_TYPE']})")
            
            # Look for parts-related tables
            print("\nParts-related tables:")
            for table in tables:
                table_name = table['TABLE_NAME'].lower()
                if 'part' in table_name or 'inventory' in table_name or 'stock' in table_name:
                    print(f"  - {table['TABLE_NAME']}")
            
            # Check if specific tables exist
            print("\nChecking for specific tables:")
            check_tables = ['NationalParts', 'Parts', 'PartsMaster', 'PartsInventory', 'Inventory', 'Stock']
            for check_table in check_tables:
                exists = any(table['TABLE_NAME'].lower() == check_table.lower() for table in tables)
                print(f"  - {check_table}: {'EXISTS' if exists else 'NOT FOUND'}")
                
        else:
            print("No tables found or unable to query INFORMATION_SCHEMA")
            
            # Try alternative query
            print("\nTrying alternative query...")
            alt_query = """
            SELECT name 
            FROM sys.tables 
            WHERE schema_id = SCHEMA_ID('ben002')
            ORDER BY name
            """
            alt_tables = db.execute_query(alt_query)
            if alt_tables:
                print(f"Found {len(alt_tables)} tables:")
                for table in alt_tables:
                    print(f"  - {table[0]}")
        
    except Exception as e:
        print(f"Error: {e}")
        
        # Try to at least test WOParts
        print("\nTrying to query WOParts directly...")
        try:
            test_query = "SELECT TOP 1 * FROM ben002.WOParts"
            result = db.execute_query(test_query)
            if result:
                print("WOParts table exists!")
                print("Columns:", list(result[0].keys()) if result else "No data")
        except Exception as e2:
            print(f"WOParts query failed: {e2}")

if __name__ == "__main__":
    discover_tables()