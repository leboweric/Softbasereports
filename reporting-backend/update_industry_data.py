#!/usr/bin/env python3
"""
Update industry data in finance_clients table from Excel workbook.
This script reads the Industry column from the Excel file and updates
the corresponding records in the database.
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Get database connection"""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        # Local development fallback
        return psycopg2.connect(
            host=os.environ.get('POSTGRES_HOST', 'localhost'),
            port=os.environ.get('POSTGRES_PORT', '5432'),
            database=os.environ.get('POSTGRES_DB', 'reporting'),
            user=os.environ.get('POSTGRES_USER', 'postgres'),
            password=os.environ.get('POSTGRES_PASSWORD', '')
        )

def update_industry_data(excel_path: str):
    """
    Read industry data from Excel and update database.
    
    Args:
        excel_path: Path to the Excel workbook
    """
    print(f"Reading Excel file: {excel_path}")
    
    # Read the Billing Data Table sheet
    df = pd.read_excel(excel_path, sheet_name='Billing Data Table 2026', header=1)
    
    # Get relevant columns
    # Company Name and Industry
    company_col = 'Company Name'
    industry_col = 'Industry'
    
    if company_col not in df.columns or industry_col not in df.columns:
        print(f"Error: Required columns not found. Available columns: {df.columns.tolist()}")
        return
    
    # Create mapping of company name to industry
    industry_map = {}
    for _, row in df.iterrows():
        company = row[company_col]
        industry = row[industry_col]
        if pd.notna(company) and pd.notna(industry):
            # Clean company name (remove population suffix like "(248)")
            company_clean = str(company).strip()
            industry_map[company_clean] = str(industry).strip()
    
    print(f"Found {len(industry_map)} companies with industry data")
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all finance_clients
    cursor.execute("""
        SELECT id, billing_name, industry 
        FROM finance_clients 
        WHERE org_id = 6
    """)
    clients = cursor.fetchall()
    print(f"Found {len(clients)} clients in database")
    
    # Update each client
    updated = 0
    not_found = []
    
    for client in clients:
        client_name = client['billing_name']
        current_industry = client['industry']
        
        # Try to find matching industry
        new_industry = None
        
        # Direct match
        if client_name in industry_map:
            new_industry = industry_map[client_name]
        else:
            # Try partial match (company name might have different format)
            for excel_name, industry in industry_map.items():
                # Check if the billing name is contained in the excel name or vice versa
                if client_name.lower() in excel_name.lower() or excel_name.lower() in client_name.lower():
                    new_industry = industry
                    break
        
        if new_industry:
            if current_industry != new_industry:
                cursor.execute("""
                    UPDATE finance_clients 
                    SET industry = %s 
                    WHERE id = %s
                """, (new_industry, client['id']))
                updated += 1
                print(f"Updated: {client_name} -> {new_industry}")
        else:
            not_found.append(client_name)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\nSummary:")
    print(f"  Updated: {updated} clients")
    print(f"  Not found in Excel: {len(not_found)} clients")
    
    if not_found and len(not_found) <= 20:
        print(f"\nClients not found in Excel:")
        for name in not_found:
            print(f"  - {name}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = '/home/ubuntu/upload/2026BillingDataWorkbook-WORKING.xlsx'
    
    update_industry_data(excel_path)
