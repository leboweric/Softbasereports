#!/usr/bin/env python3
"""
Test script to debug monthly work orders query
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
    print("Monthly Work Orders Analysis")
    print("=" * 80)
    
    # Initialize the Azure SQL service
    try:
        print("\nConnecting to Azure SQL Database...")
        db = AzureSQLService()
        print("Connection successful!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    # First, check what date fields exist in WO table
    print("\n" + "-" * 80)
    print("STEP 1: Checking date fields in WO table")
    print("-" * 80)
    
    date_columns_query = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'WO' 
    AND TABLE_SCHEMA = 'ben002'
    AND (
        COLUMN_NAME LIKE '%Date%' OR 
        COLUMN_NAME LIKE '%Time%' OR
        COLUMN_NAME LIKE '%Created%' OR
        COLUMN_NAME LIKE '%Open%'
    )
    ORDER BY ORDINAL_POSITION
    """
    
    try:
        date_columns = db.execute_query(date_columns_query)
        print(f"\nFound {len(date_columns)} date-related columns:")
        for col in date_columns:
            print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
    except Exception as e:
        print(f"Error getting columns: {e}")
    
    # Get sample work orders to see date values
    print("\n" + "-" * 80)
    print("STEP 2: Sample work orders with dates")
    print("-" * 80)
    
    sample_query = """
    SELECT TOP 10 
        WONo,
        OpenDate,
        CreatedDate,
        CompletedDate,
        ClosedDate,
        ShopQuoteDate
    FROM ben002.WO
    ORDER BY WONo DESC
    """
    
    try:
        samples = db.execute_query(sample_query)
        if samples:
            print(f"\nShowing {len(samples)} recent work orders:")
            for wo in samples[:5]:
                print(f"\nWO #{wo.get('WONo')}:")
                print(f"  OpenDate: {wo.get('OpenDate')}")
                print(f"  CreatedDate: {wo.get('CreatedDate')}")
                print(f"  CompletedDate: {wo.get('CompletedDate')}")
                print(f"  ClosedDate: {wo.get('ClosedDate')}")
                print(f"  ShopQuoteDate: {wo.get('ShopQuoteDate')}")
    except Exception as e:
        print(f"Error getting samples: {e}")
    
    # Check for work orders since March 2025
    print("\n" + "-" * 80)
    print("STEP 3: Work orders since March 2025")
    print("-" * 80)
    
    count_query = """
    SELECT 
        COUNT(*) as total_count,
        COUNT(CASE WHEN OpenDate >= '2025-03-01' THEN 1 END) as since_march_open,
        COUNT(CASE WHEN CreatedDate >= '2025-03-01' THEN 1 END) as since_march_created,
        MIN(OpenDate) as earliest_open,
        MAX(OpenDate) as latest_open,
        MIN(CreatedDate) as earliest_created,
        MAX(CreatedDate) as latest_created
    FROM ben002.WO
    """
    
    try:
        count_result = db.execute_query(count_query)
        if count_result:
            result = count_result[0]
            print(f"\nTotal work orders: {result['total_count']:,}")
            print(f"Work orders with OpenDate >= March 2025: {result['since_march_open']:,}")
            print(f"Work orders with CreatedDate >= March 2025: {result['since_march_created']:,}")
            print(f"\nOpenDate range: {result['earliest_open']} to {result['latest_open']}")
            print(f"CreatedDate range: {result['earliest_created']} to {result['latest_created']}")
    except Exception as e:
        print(f"Error counting work orders: {e}")
    
    # Try the actual monthly query with different date fields
    print("\n" + "-" * 80)
    print("STEP 4: Monthly work orders breakdown")
    print("-" * 80)
    
    # Try with different date fields
    date_fields_to_try = ['OpenDate', 'CreatedDate']
    
    for date_field in date_fields_to_try:
        print(f"\n--- Using {date_field} ---")
        try:
            # First check if the column exists
            check_query = f"SELECT TOP 1 {date_field} FROM ben002.WO WHERE {date_field} IS NOT NULL"
            check_result = db.execute_query(check_query)
            
            if check_result:
                # Try monthly query with a wider date range
                monthly_query = f"""
                SELECT 
                    YEAR(w.{date_field}) as year,
                    MONTH(w.{date_field}) as month,
                    COUNT(DISTINCT w.WONo) as wo_count,
                    SUM(labor_total + parts_total + misc_total) as total_value
                FROM (
                    SELECT 
                        w.WONo,
                        w.{date_field},
                        COALESCE((SELECT SUM(Sell) FROM ben002.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                        COALESCE((SELECT SUM(Sell) FROM ben002.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                        COALESCE((SELECT SUM(Sell) FROM ben002.WOMisc WHERE WONo = w.WONo), 0) as misc_total
                    FROM ben002.WO w
                    WHERE w.{date_field} >= '2024-01-01'  -- Using wider date range
                    AND w.{date_field} IS NOT NULL
                ) as wo_with_values
                GROUP BY YEAR({date_field}), MONTH({date_field})
                ORDER BY year DESC, month DESC
                LIMIT 12
                """
                
                monthly_results = db.execute_query(monthly_query)
                
                if monthly_results:
                    print(f"\n{'Year':<6} {'Month':<10} {'Count':>10} {'Total Value':>20}")
                    print("-" * 48)
                    
                    for row in monthly_results:
                        month_name = datetime(row['year'], row['month'], 1).strftime("%B")
                        print(f"{row['year']:<6} {month_name:<10} {row['wo_count']:>10,} {format_currency(row['total_value']):>20}")
                else:
                    print("No monthly data found")
                    
        except Exception as e:
            print(f"Error with {date_field}: {e}")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()