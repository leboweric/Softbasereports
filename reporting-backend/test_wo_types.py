#!/usr/bin/env python3
"""
Test script to analyze work order types breakdown
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
    print("Work Order Types Analysis")
    print("=" * 80)
    
    # Initialize the Azure SQL service
    try:
        print("\nConnecting to Azure SQL Database...")
        db = AzureSQLService()
        print("Connection successful!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    # First, find type-related columns in WO table
    print("\n" + "-" * 80)
    print("STEP 1: Finding type-related columns in WO table")
    print("-" * 80)
    
    wo_columns_query = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'WO' 
    AND TABLE_SCHEMA = 'ben002'
    AND (
        COLUMN_NAME LIKE '%Type%' OR 
        COLUMN_NAME LIKE '%Category%' OR 
        COLUMN_NAME LIKE '%Class%' OR
        COLUMN_NAME LIKE '%Department%' OR
        COLUMN_NAME LIKE '%Service%'
    )
    ORDER BY ORDINAL_POSITION
    """
    
    try:
        type_columns = db.execute_query(wo_columns_query)
        print(f"\nFound {len(type_columns)} type-related columns:")
        for col in type_columns:
            print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
    except Exception as e:
        print(f"Error getting columns: {e}")
    
    # Get sample WO records to see type data
    print("\n" + "-" * 80)
    print("STEP 2: Sample open/in-progress work orders")
    print("-" * 80)
    
    sample_query = """
    SELECT TOP 5 *
    FROM ben002.WO
    WHERE CompletedDate IS NULL
    AND ClosedDate IS NULL
    ORDER BY WONo DESC
    """
    
    try:
        samples = db.execute_query(sample_query)
        if samples:
            print(f"\nShowing {len(samples)} sample work orders:")
            for i, rec in enumerate(samples):
                print(f"\n--- Work Order #{rec.get('WONo')} ---")
                # Show type-related fields
                for key, value in rec.items():
                    if any(term in key.lower() for term in ['type', 'category', 'class', 'dept', 'service', 'quote']):
                        if value:
                            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error getting samples: {e}")
    
    # Try to find and group by different type columns
    print("\n" + "-" * 80)
    print("STEP 3: Breakdown of open work orders by type")
    print("-" * 80)
    
    type_columns_to_try = ['WOType', 'Type', 'ServiceType', 'QuoteType', 'Category', 'Department']
    
    successful_column = None
    for col in type_columns_to_try:
        try:
            type_breakdown_query = f"""
            SELECT 
                {col} as type_value,
                COUNT(*) as count,
                SUM(labor_total + parts_total + misc_total) as total_value
            FROM (
                SELECT 
                    w.WONo,
                    w.{col},
                    COALESCE((SELECT SUM(Sell) FROM ben002.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
                    COALESCE((SELECT SUM(Sell) FROM ben002.WOParts WHERE WONo = w.WONo), 0) as parts_total,
                    COALESCE((SELECT SUM(Sell) FROM ben002.WOMisc WHERE WONo = w.WONo), 0) as misc_total
                FROM ben002.WO w
                WHERE w.CompletedDate IS NULL
                AND w.ClosedDate IS NULL
            ) as open_wo
            GROUP BY {col}
            ORDER BY total_value DESC
            """
            
            breakdown = db.execute_query(type_breakdown_query)
            if breakdown and len(breakdown) > 0:
                print(f"\nSuccessfully grouped by column: {col}")
                print(f"\n{'Type':<30} {'Count':>10} {'Total Value':>20}")
                print("-" * 62)
                
                total_count = 0
                total_value = 0
                
                for row in breakdown:
                    type_val = row['type_value'] or '(No Type)'
                    print(f"{type_val:<30} {row['count']:>10,} {format_currency(row['total_value']):>20}")
                    total_count += row['count']
                    total_value += row['total_value']
                
                print("-" * 62)
                print(f"{'TOTAL':<30} {total_count:>10,} {format_currency(total_value):>20}")
                
                successful_column = col
                break
        except Exception as e:
            continue
    
    if not successful_column:
        print("\nCould not find a suitable type column for grouping")
    
    # Get overall summary
    print("\n" + "-" * 80)
    print("STEP 4: Overall work order summary")
    print("-" * 80)
    
    summary_query = """
    SELECT 
        COUNT(*) as total_count,
        SUM(labor_total + parts_total + misc_total) as total_value
    FROM (
        SELECT 
            w.WONo,
            COALESCE((SELECT SUM(Sell) FROM ben002.WOLabor WHERE WONo = w.WONo), 0) as labor_total,
            COALESCE((SELECT SUM(Sell) FROM ben002.WOParts WHERE WONo = w.WONo), 0) as parts_total,
            COALESCE((SELECT SUM(Sell) FROM ben002.WOMisc WHERE WONo = w.WONo), 0) as misc_total
        FROM ben002.WO w
        WHERE w.CompletedDate IS NULL
        AND w.ClosedDate IS NULL
    ) as open_wo
    """
    
    try:
        summary = db.execute_query(summary_query)
        if summary:
            print(f"\nOpen/In Progress Work Orders:")
            print(f"  Count: {summary[0]['total_count']:,}")
            print(f"  Total Value: {format_currency(summary[0]['total_value'])}")
    except Exception as e:
        print(f"Error getting summary: {e}")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()