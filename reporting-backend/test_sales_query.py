#!/usr/bin/env python3
"""
Test script to connect to Azure SQL and query sales data from November 1, 2024 through today.
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
    print("=" * 60)
    print("Softbase Sales Query Test")
    print("=" * 60)
    
    # Initialize the Azure SQL service
    try:
        print("\nConnecting to Azure SQL Database...")
        service = AzureSQLService()
        print("Connection successful!")
    except Exception as e:
        print(f"Failed to initialize Azure SQL Service: {e}")
        return
    
    # Query 1: Get total sales from November 1, 2024 through today
    print("\n" + "-" * 60)
    print("QUERY 1: Total Sales from November 1, 2024 through today")
    print("-" * 60)
    
    total_sales_query = """
    SELECT 
        SUM(GrandTotal) as total_sales,
        COUNT(*) as invoice_count,
        MIN(InvoiceDate) as first_invoice_date,
        MAX(InvoiceDate) as last_invoice_date
    FROM ben002.InvoiceReg 
    WHERE InvoiceDate >= '2024-11-01'
    """
    
    try:
        results = service.execute_query(total_sales_query)
        if results and len(results) > 0:
            result = results[0]
            print(f"\nTotal Sales: {format_currency(result.get('total_sales'))}")
            print(f"Number of Invoices: {result.get('invoice_count', 0):,}")
            print(f"Date Range: {result.get('first_invoice_date')} to {result.get('last_invoice_date')}")
        else:
            print("No results found")
    except Exception as e:
        print(f"Error executing total sales query: {e}")
    
    # Query 2: Get sample invoice records
    print("\n" + "-" * 60)
    print("QUERY 2: Sample Invoice Records (First 10)")
    print("-" * 60)
    
    sample_invoices_query = """
    SELECT TOP 10
        InvoiceNo,
        InvoiceDate,
        CustomerCode,
        CustomerName,
        GrandTotal,
        TotalExclusive,
        TotalTax
    FROM ben002.InvoiceReg 
    WHERE InvoiceDate >= '2024-11-01'
    ORDER BY InvoiceDate DESC, InvoiceNo DESC
    """
    
    try:
        invoices = service.execute_query(sample_invoices_query)
        if invoices:
            print(f"\nFound {len(invoices)} sample invoices:")
            print("\n{:<15} {:<12} {:<15} {:<30} {:>15} {:>15} {:>12}".format(
                "Invoice No", "Date", "Customer Code", "Customer Name", "Total Excl", "Tax", "Grand Total"
            ))
            print("-" * 130)
            
            for invoice in invoices:
                print("{:<15} {:<12} {:<15} {:<30} {:>15} {:>15} {:>12}".format(
                    invoice.get('InvoiceNo', ''),
                    str(invoice.get('InvoiceDate', ''))[:10],
                    invoice.get('CustomerCode', '')[:15],
                    invoice.get('CustomerName', '')[:30],
                    format_currency(invoice.get('TotalExclusive')),
                    format_currency(invoice.get('TotalTax')),
                    format_currency(invoice.get('GrandTotal'))
                ))
        else:
            print("No invoice records found")
    except Exception as e:
        print(f"Error executing sample invoices query: {e}")
    
    # Query 3: Sales by month breakdown
    print("\n" + "-" * 60)
    print("QUERY 3: Sales Breakdown by Month")
    print("-" * 60)
    
    monthly_sales_query = """
    SELECT 
        YEAR(InvoiceDate) as Year,
        MONTH(InvoiceDate) as Month,
        COUNT(*) as InvoiceCount,
        SUM(GrandTotal) as TotalSales
    FROM ben002.InvoiceReg 
    WHERE InvoiceDate >= '2024-11-01'
    GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
    ORDER BY Year, Month
    """
    
    try:
        monthly_results = service.execute_query(monthly_sales_query)
        if monthly_results:
            print("\n{:<6} {:<10} {:>15} {:>20}".format(
                "Year", "Month", "Invoice Count", "Total Sales"
            ))
            print("-" * 55)
            
            for row in monthly_results:
                month_name = datetime(row['Year'], row['Month'], 1).strftime("%B")
                print("{:<6} {:<10} {:>15,} {:>20}".format(
                    row['Year'],
                    month_name,
                    row['InvoiceCount'],
                    format_currency(row['TotalSales'])
                ))
        else:
            print("No monthly data found")
    except Exception as e:
        print(f"Error executing monthly sales query: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()