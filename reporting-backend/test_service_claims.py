#!/usr/bin/env python3
"""
Test script to explore ServiceClaim table structure and find uninvoiced work orders
"""

import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.azure_sql_service import AzureSQLService

def format_currency(value):
    """Format a number as currency"""
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"

def main():
    print("=" * 80)
    print("ServiceClaim Table Analysis")
    print("=" * 80)
    
    # Initialize the Azure SQL service
    try:
        print("\nConnecting to Azure SQL Database...")
        db = AzureSQLService()
        print("Connection successful!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    # Get column information
    print("\n" + "-" * 80)
    print("STEP 1: Analyzing ServiceClaim table structure")
    print("-" * 80)
    
    columns_query = """
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ServiceClaim' 
    AND TABLE_SCHEMA = 'ben002'
    ORDER BY ORDINAL_POSITION
    """
    
    try:
        columns = db.execute_query(columns_query)
        print(f"\nFound {len(columns)} columns in ServiceClaim table:")
        print("\n{:<35} {:<20} {:<10}".format("Column Name", "Data Type", "Nullable"))
        print("-" * 70)
        
        date_cols = []
        status_cols = []
        invoice_cols = []
        amount_cols = []
        
        for col in columns:
            print("{:<35} {:<20} {:<10}".format(
                col['COLUMN_NAME'], 
                col['DATA_TYPE'], 
                col['IS_NULLABLE']
            ))
            
            col_name_lower = col['COLUMN_NAME'].lower()
            if 'date' in col_name_lower or 'time' in col_name_lower:
                date_cols.append(col['COLUMN_NAME'])
            if 'status' in col_name_lower or 'complete' in col_name_lower or 'closed' in col_name_lower:
                status_cols.append(col['COLUMN_NAME'])
            if 'invoice' in col_name_lower or 'bill' in col_name_lower:
                invoice_cols.append(col['COLUMN_NAME'])
            if any(term in col_name_lower for term in ['total', 'amount', 'cost', 'price', 'labor', 'parts']):
                amount_cols.append(col['COLUMN_NAME'])
        
        print(f"\nDate columns found: {date_cols}")
        print(f"Status columns found: {status_cols}")
        print(f"Invoice columns found: {invoice_cols}")
        print(f"Amount columns found: {amount_cols}")
        
    except Exception as e:
        print(f"Error getting columns: {e}")
        return
    
    # Get sample records
    print("\n" + "-" * 80)
    print("STEP 2: Sample ServiceClaim records")
    print("-" * 80)
    
    sample_query = """
    SELECT TOP 3 *
    FROM ben002.ServiceClaim
    ORDER BY ServiceClaimID DESC
    """
    
    try:
        samples = db.execute_query(sample_query)
        if samples:
            print(f"\nShowing {len(samples)} sample records:")
            for i, record in enumerate(samples):
                print(f"\n--- Record {i+1} ---")
                for key, value in record.items():
                    if value is not None and str(value).strip():
                        print(f"{key}: {value}")
        else:
            print("No records found")
    except Exception as e:
        print(f"Error getting samples: {e}")
    
    # Test various queries to find uninvoiced work orders
    print("\n" + "-" * 80)
    print("STEP 3: Testing different approaches to find uninvoiced work orders")
    print("-" * 80)
    
    # Test 1: Look for records without invoice numbers
    test_queries = [
        {
            "name": "Count records with InvoiceNo field",
            "query": """
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN InvoiceNo IS NULL OR InvoiceNo = '' OR InvoiceNo = '0' THEN 1 END) as uninvoiced_count
            FROM ben002.ServiceClaim
            """
        },
        {
            "name": "Count records with InvoiceID field",
            "query": """
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN InvoiceID IS NULL OR InvoiceID = 0 THEN 1 END) as uninvoiced_count
            FROM ben002.ServiceClaim
            """
        },
        {
            "name": "Check for Completed/Closed status fields",
            "query": """
            SELECT TOP 5 
                ServiceClaimID,
                CASE 
                    WHEN Status IS NOT NULL THEN Status 
                    WHEN ClaimStatus IS NOT NULL THEN ClaimStatus
                    ELSE 'No Status Field'
                END as status_field
            FROM ben002.ServiceClaim
            """
        },
        {
            "name": "Look for work orders with labor/parts costs",
            "query": """
            SELECT TOP 5 *
            FROM ben002.ServiceClaim
            WHERE 1=1
            AND (
                (TotalLabor IS NOT NULL AND TotalLabor > 0) OR
                (TotalParts IS NOT NULL AND TotalParts > 0) OR
                (LaborAmount IS NOT NULL AND LaborAmount > 0) OR
                (PartsAmount IS NOT NULL AND PartsAmount > 0)
            )
            """
        }
    ]
    
    for test in test_queries:
        print(f"\n{test['name']}:")
        try:
            result = db.execute_query(test['query'])
            if result:
                for row in result:
                    print(f"  {row}")
            else:
                print("  No results")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Final attempt - get column names that might indicate completion/invoicing
    print("\n" + "-" * 80)
    print("STEP 4: Intelligent query based on available columns")
    print("-" * 80)
    
    # Build a query based on what columns we found
    try:
        # First, check if we have cost columns
        cost_condition = "1=0"  # Default false condition
        for col in amount_cols:
            test_query = f"SELECT TOP 1 {col} FROM ben002.ServiceClaim WHERE {col} > 0"
            try:
                test_result = db.execute_query(test_query)
                if test_result:
                    cost_condition = f"({col} > 0)"
                    print(f"Found cost column with data: {col}")
                    break
            except:
                pass
        
        # Check for invoice indicator
        invoice_condition = "1=1"  # Default true (no invoice info means uninvoiced)
        for col in invoice_cols:
            test_query = f"SELECT TOP 1 {col} FROM ben002.ServiceClaim"
            try:
                test_result = db.execute_query(test_query)
                if test_result:
                    # Determine if it's numeric or string
                    if 'int' in str(type(test_result[0][col])) or 'decimal' in str(type(test_result[0][col])):
                        invoice_condition = f"({col} IS NULL OR {col} = 0)"
                    else:
                        invoice_condition = f"({col} IS NULL OR {col} = '' OR {col} = '0')"
                    print(f"Found invoice column: {col}")
                    break
            except:
                pass
        
        # Build final query
        final_query = f"""
        SELECT 
            COUNT(*) as uninvoiced_count,
            SUM(CASE 
                WHEN TotalLabor IS NOT NULL AND TotalParts IS NOT NULL THEN TotalLabor + TotalParts
                WHEN LaborAmount IS NOT NULL AND PartsAmount IS NOT NULL THEN LaborAmount + PartsAmount
                ELSE 0
            END) as total_value
        FROM ben002.ServiceClaim
        WHERE {cost_condition}
        AND {invoice_condition}
        """
        
        print(f"\nFinal query:\n{final_query}")
        
        result = db.execute_query(final_query)
        if result:
            print(f"\nUninvoiced work orders: {result[0]['uninvoiced_count']}")
            print(f"Total value: {format_currency(result[0]['total_value'])}")
        
    except Exception as e:
        print(f"Error building intelligent query: {e}")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()