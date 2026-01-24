#!/usr/bin/env python3
"""
Update industry data in finance_clients table from Excel workbook.
Version 2: Improved matching logic for company names.
"""

import os
import sys
import re
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

def normalize_name(name):
    """Normalize company name for matching"""
    if pd.isna(name):
        return ''
    name = str(name).lower()
    # Remove population numbers like (248), (17,394)
    name = re.sub(r'\s*\([0-9,]+\)\s*', ' ', name)
    # Remove #2, #3 suffixes
    name = re.sub(r'\s*#\d+\s*$', '', name)
    # Remove common suffixes
    name = re.sub(r'\s*(inc\.?|llc|corp\.?|co\.?)\s*$', '', name)
    # Remove extra whitespace
    name = ' '.join(name.split())
    return name.strip()

def extract_base_name(name):
    """Extract the base company name (first part before dash or parenthesis)"""
    name = normalize_name(name)
    # Split on dash and take first part
    parts = name.split(' - ')
    base = parts[0].strip()
    # Also try splitting on common prefixes
    if base.startswith('msv '):
        base = base[4:]
    if base.startswith('optumcdo '):
        base = base[9:]
    return base

def update_industry_data(excel_path: str):
    """
    Read industry data from Excel and update database with improved matching.
    """
    print(f"Reading Excel file: {excel_path}")
    
    df = pd.read_excel(excel_path, sheet_name='Billing Data Table 2026', header=1)
    
    company_col = 'Company Name'
    industry_col = 'Industry'
    
    # Build multiple lookup dictionaries for different matching strategies
    # 1. Exact normalized name -> industry
    exact_map = {}
    # 2. Base name -> industry (for partial matches)
    base_map = {}
    # 3. Contains mapping for fuzzy matching
    
    for _, row in df.iterrows():
        company = row[company_col]
        industry = row[industry_col]
        if pd.notna(company) and pd.notna(industry):
            norm_name = normalize_name(company)
            base_name = extract_base_name(company)
            
            exact_map[norm_name] = str(industry).strip()
            
            # For base name, prefer Healthcare PWR over Healthcare if multiple
            if base_name not in base_map or 'PWR' in str(industry):
                base_map[base_name] = str(industry).strip()
    
    print(f"Built lookup with {len(exact_map)} exact entries and {len(base_map)} base entries")
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all finance_clients with blank industry
    cursor.execute("""
        SELECT id, billing_name, industry 
        FROM finance_clients 
        WHERE org_id = 6 AND (industry IS NULL OR industry = '')
    """)
    clients = cursor.fetchall()
    print(f"Found {len(clients)} clients with blank industry")
    
    updated = 0
    not_found = []
    
    for client in clients:
        client_name = client['billing_name']
        norm_client = normalize_name(client_name)
        base_client = extract_base_name(client_name)
        
        new_industry = None
        match_type = None
        
        # Strategy 1: Exact normalized match
        if norm_client in exact_map:
            new_industry = exact_map[norm_client]
            match_type = 'exact'
        
        # Strategy 2: Base name match
        if not new_industry and base_client in base_map:
            new_industry = base_map[base_client]
            match_type = 'base'
        
        # Strategy 3: Partial match - check if client base name is contained in any Excel base name
        if not new_industry:
            for excel_base, industry in base_map.items():
                if base_client in excel_base or excel_base in base_client:
                    new_industry = industry
                    match_type = 'partial'
                    break
        
        # Strategy 4: Word overlap matching
        if not new_industry:
            client_words = set(base_client.split())
            best_overlap = 0
            for excel_base, industry in base_map.items():
                excel_words = set(excel_base.split())
                overlap = len(client_words & excel_words)
                if overlap > best_overlap and overlap >= 2:  # At least 2 words must match
                    best_overlap = overlap
                    new_industry = industry
                    match_type = f'word_overlap({overlap})'
        
        if new_industry:
            cursor.execute("""
                UPDATE finance_clients 
                SET industry = %s 
                WHERE id = %s
            """, (new_industry, client['id']))
            updated += 1
            print(f"Updated ({match_type}): {client_name} -> {new_industry}")
        else:
            not_found.append(client_name)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\nSummary:")
    print(f"  Updated: {updated} clients")
    print(f"  Still not found: {len(not_found)} clients")
    
    if not_found:
        print(f"\nClients still without industry:")
        for name in not_found:
            print(f"  - {name}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = '/home/ubuntu/upload/2026BillingDataWorkbook-WORKING.xlsx'
    
    update_industry_data(excel_path)
