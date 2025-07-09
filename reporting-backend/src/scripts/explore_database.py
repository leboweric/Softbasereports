#!/usr/bin/env python3
"""
Script to explore the Azure SQL database schema and understand the Softbase Evolution structure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.azure_sql_service import AzureSQLService
import pandas as pd
from datetime import datetime

def explore_database():
    """Explore the database schema and document findings"""
    
    db = AzureSQLService()
    
    print("=" * 80)
    print("SOFTBASE EVOLUTION DATABASE EXPLORATION")
    print("=" * 80)
    print(f"Server: {db.server}")
    print(f"Database: {db.database}")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 80)
    
    # Test connection
    print("\n1. Testing Connection...")
    if db.test_connection():
        print("✓ Connected successfully!")
    else:
        print("✗ Connection failed!")
        return
    
    # Get all tables
    print("\n2. Fetching All Tables...")
    tables = db.get_tables()
    print(f"Found {len(tables)} tables:")
    
    # Group tables by likely category
    categories = {
        'Customers': [],
        'Inventory': [],
        'Sales': [],
        'Service': [],
        'Parts': [],
        'Financial': [],
        'Other': []
    }
    
    for table in tables:
        table_lower = table.lower()
        if 'customer' in table_lower or 'client' in table_lower:
            categories['Customers'].append(table)
        elif 'inventory' in table_lower or 'equipment' in table_lower or 'forklift' in table_lower:
            categories['Inventory'].append(table)
        elif 'sale' in table_lower or 'order' in table_lower or 'invoice' in table_lower:
            categories['Sales'].append(table)
        elif 'service' in table_lower or 'repair' in table_lower or 'maintenance' in table_lower:
            categories['Service'].append(table)
        elif 'part' in table_lower or 'component' in table_lower:
            categories['Parts'].append(table)
        elif 'financial' in table_lower or 'payment' in table_lower or 'account' in table_lower:
            categories['Financial'].append(table)
        else:
            categories['Other'].append(table)
    
    # Display categorized tables
    for category, table_list in categories.items():
        if table_list:
            print(f"\n{category} Tables ({len(table_list)}):")
            for table in sorted(table_list):
                print(f"  - {table}")
    
    # Explore key tables in detail
    print("\n" + "=" * 80)
    print("3. DETAILED TABLE ANALYSIS")
    print("=" * 80)
    
    # Look for main tables to analyze
    key_patterns = [
        ('customer', 'Customer/Client Information'),
        ('equipment', 'Equipment/Forklift Inventory'),
        ('inventory', 'Inventory Management'),
        ('sales', 'Sales Transactions'),
        ('order', 'Orders/Invoices'),
        ('service', 'Service Records'),
        ('parts', 'Parts Inventory')
    ]
    
    analyzed_tables = []
    
    for pattern, description in key_patterns:
        matching_tables = [t for t in tables if pattern in t.lower()]
        if matching_tables:
            # Take the shortest matching table name (likely the main one)
            main_table = min(matching_tables, key=len)
            print(f"\n{description} - Table: {main_table}")
            print("-" * 60)
            
            # Get column information
            try:
                columns = db.get_table_columns(main_table)
                print(f"Columns ({len(columns)}):")
                for col in columns:
                    nullable = "NULL" if col.get('IS_NULLABLE') == 'YES' else "NOT NULL"
                    max_length = col.get('CHARACTER_MAXIMUM_LENGTH', '')
                    if max_length:
                        max_length = f"({max_length})"
                    print(f"  - {col['COLUMN_NAME']}: {col['DATA_TYPE']}{max_length} {nullable}")
                
                # Get sample data
                sample_query = f"SELECT TOP 5 * FROM [{main_table}]"
                sample_data = db.execute_query(sample_query)
                if sample_data:
                    print(f"\nSample data (first row):")
                    first_row = sample_data[0]
                    for key, value in first_row.items():
                        print(f"  {key}: {value}")
                
                analyzed_tables.append({
                    'table': main_table,
                    'description': description,
                    'columns': columns,
                    'sample': sample_data[0] if sample_data else {}
                })
                
            except Exception as e:
                print(f"  Error analyzing table: {str(e)}")
    
    # Look for relationships
    print("\n" + "=" * 80)
    print("4. POTENTIAL RELATIONSHIPS")
    print("=" * 80)
    
    # Find foreign key relationships
    fk_query = """
    SELECT 
        FK.TABLE_NAME as FK_Table,
        CU.COLUMN_NAME as FK_Column,
        PK.TABLE_NAME as PK_Table,
        PT.COLUMN_NAME as PK_Column,
        C.CONSTRAINT_NAME as Constraint_Name
    FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS C
    INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS FK ON C.CONSTRAINT_NAME = FK.CONSTRAINT_NAME
    INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS PK ON C.UNIQUE_CONSTRAINT_NAME = PK.CONSTRAINT_NAME
    INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE CU ON C.CONSTRAINT_NAME = CU.CONSTRAINT_NAME
    INNER JOIN (
        SELECT i1.TABLE_NAME, i2.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS i1
        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE i2 ON i1.CONSTRAINT_NAME = i2.CONSTRAINT_NAME
        WHERE i1.CONSTRAINT_TYPE = 'PRIMARY KEY'
    ) PT ON PT.TABLE_NAME = PK.TABLE_NAME
    ORDER BY FK_Table, FK_Column
    """
    
    try:
        relationships = db.execute_query(fk_query)
        if relationships:
            print(f"Found {len(relationships)} foreign key relationships:")
            for rel in relationships:
                print(f"  {rel['FK_Table']}.{rel['FK_Column']} -> {rel['PK_Table']}.{rel['PK_Column']}")
        else:
            print("No foreign key relationships found (may be managed in application layer)")
    except Exception as e:
        print(f"Could not retrieve foreign keys: {str(e)}")
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("5. SUMMARY RECOMMENDATIONS")
    print("=" * 80)
    
    print("\nKey tables identified for reporting:")
    for item in analyzed_tables:
        print(f"\n• {item['description']}:")
        print(f"  Table: {item['table']}")
        print(f"  Columns: {len(item['columns'])}")
    
    print("\n\nNext steps:")
    print("1. Update softbase_service.py with correct table names")
    print("2. Create specific query methods for each business area")
    print("3. Map table columns to user-friendly report fields")
    print("4. Test natural language queries against actual data")
    
    return {
        'tables': tables,
        'categories': categories,
        'analyzed': analyzed_tables
    }

if __name__ == "__main__":
    try:
        results = explore_database()
        
        # Save results to file
        output_file = os.path.join(os.path.dirname(__file__), 'database_schema_report.txt')
        with open(output_file, 'w') as f:
            # Redirect print to file as well
            import sys
            original_stdout = sys.stdout
            sys.stdout = f
            explore_database()
            sys.stdout = original_stdout
            
        print(f"\n\nReport saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()