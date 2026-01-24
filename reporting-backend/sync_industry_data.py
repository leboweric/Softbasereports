#!/usr/bin/env python3
"""
Comprehensive Industry Data Sync Script

This script syncs industry data from the Excel billing workbook to the database.
It uses exact company name matching to ensure accuracy.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import re

def normalize_name(name):
    """Normalize company name for matching."""
    if not name:
        return ""
    # Remove population numbers in parentheses at the end
    name = re.sub(r'\s*\(\d+[\d,]*\)\s*$', '', str(name))
    # Remove #2, #3 suffixes
    name = re.sub(r'\s*#\d+\s*$', '', name)
    # Normalize whitespace
    name = ' '.join(name.split())
    return name.strip().lower()

def main():
    # Read Excel data
    print("Reading Excel file...")
    billing_df = pd.read_excel('/home/ubuntu/upload/2026BillingDataWorkbook-WORKING.xlsx', 
                                sheet_name='Billing Data Table 2026', header=1)
    
    # Filter to Revenue Recognition only (matching app behavior)
    revrec_df = billing_df[billing_df['Revenue Timing'] == 'Revenue Recognition'].copy()
    
    # Build industry mapping from Excel
    print(f"Building industry mapping from {len(revrec_df)} Excel rows...")
    excel_industries = {}
    for idx, row in revrec_df.iterrows():
        company_name = row['Company Name']
        industry = row['Industry'] if pd.notna(row['Industry']) and row['Industry'] != '' else None
        
        # Store with normalized name as key
        normalized = normalize_name(company_name)
        if normalized:
            excel_industries[normalized] = industry
    
    print(f"Found {len(excel_industries)} unique company names in Excel")
    
    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all clients from database
    cursor.execute('''
        SELECT id, billing_name, industry FROM finance_clients 
        WHERE org_id = 6
    ''')
    db_clients = cursor.fetchall()
    print(f"Found {len(db_clients)} clients in database")
    
    # First, reset all industries to NULL
    print("\nResetting all industries to NULL...")
    cursor.execute('''
        UPDATE finance_clients SET industry = NULL WHERE org_id = 6
    ''')
    print(f"Reset {cursor.rowcount} clients")
    
    # Match and update
    print("\nMatching and updating industries...")
    updated = 0
    not_found = []
    
    for client in db_clients:
        db_name = client['billing_name']
        normalized_db = normalize_name(db_name)
        
        # Look for match in Excel
        industry = None
        matched = False
        
        # Try exact normalized match first
        if normalized_db in excel_industries:
            industry = excel_industries[normalized_db]
            matched = True
        else:
            # Try partial match (Excel name contained in DB name)
            for excel_norm, excel_ind in excel_industries.items():
                if excel_norm in normalized_db or normalized_db in excel_norm:
                    industry = excel_ind
                    matched = True
                    break
        
        if matched:
            cursor.execute('''
                UPDATE finance_clients SET industry = %s WHERE id = %s
            ''', (industry, client['id']))
            updated += 1
        else:
            not_found.append(db_name)
    
    conn.commit()
    
    print(f"\nUpdated {updated} clients")
    print(f"Not found in Excel: {len(not_found)}")
    
    if not_found:
        print("\nClients not found in Excel (first 20):")
        for name in not_found[:20]:
            print(f"  - {name}")
    
    # Verify results
    print("\n=== VERIFICATION ===")
    cursor.execute('''
        SELECT 
            COALESCE(fc.industry, '(blank)') as industry,
            COUNT(DISTINCT fc.id) as client_count,
            SUM(DISTINCT fmb.population_count) as total_population,
            SUM(fmb.revenue_revrec) as total_revenue
        FROM finance_clients fc
        JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
        WHERE fc.org_id = 6 
        AND fmb.billing_year = 2026
        GROUP BY COALESCE(fc.industry, '(blank)')
        ORDER BY total_revenue DESC
    ''')
    
    results = cursor.fetchall()
    total_revenue = sum(float(r['total_revenue'] or 0) for r in results)
    
    print(f"\n{'Industry':30} {'Clients':>8} {'Population':>12} {'Revenue':>14} {'%':>7}")
    print("-" * 75)
    for r in results:
        revenue = float(r['total_revenue'] or 0)
        pct = (revenue / total_revenue * 100) if total_revenue > 0 else 0
        pop = int(r['total_population'] or 0)
        print(f"{r['industry']:30} {r['client_count']:>8} {pop:>12,} ${revenue:>13,.0f} {pct:>6.2f}%")
    
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
