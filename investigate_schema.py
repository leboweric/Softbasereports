#!/usr/bin/env python3
"""
Schema Investigation Script
Uses the Railway API schema explorer to investigate database structure
"""
import requests
import json
import sys
import os

API_BASE = "https://reporting-backend-production-52e0.up.railway.app"

# You'll need to set this - get a JWT token from your browser localStorage
TOKEN = os.environ.get('RAILWAY_TOKEN', '')

if not TOKEN:
    print("ERROR: Set RAILWAY_TOKEN environment variable")
    print("Get it from browser localStorage.getItem('token')")
    sys.exit(1)

HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}


def get_all_tables():
    """Get list of all tables"""
    response = requests.get(f'{API_BASE}/api/schema/tables', headers=HEADERS)
    return response.json()


def get_table_structure(table_name):
    """Get complete structure of a table"""
    response = requests.get(f'{API_BASE}/api/schema/table/{table_name}', headers=HEADERS)
    return response.json()


def get_table_sample(table_name, limit=10):
    """Get sample data from a table"""
    response = requests.get(f'{API_BASE}/api/schema/table/{table_name}/sample?limit={limit}', headers=HEADERS)
    return response.json()


def find_column(pattern):
    """Find which tables contain a column matching the pattern"""
    response = requests.get(f'{API_BASE}/api/schema/find-column?pattern={pattern}', headers=HEADERS)
    return response.json()


def execute_query(query):
    """Execute a custom SELECT query"""
    response = requests.post(f'{API_BASE}/api/schema/query', headers=HEADERS, json={'query': query})
    return response.json()


def get_record(table_name, record_id, id_column='Number'):
    """Get a single record"""
    response = requests.get(f'{API_BASE}/api/schema/record/{table_name}/{record_id}?id_column={id_column}', headers=HEADERS)
    return response.json()


def get_relationships(table_name):
    """Get all foreign key relationships for a table"""
    response = requests.get(f'{API_BASE}/api/schema/relationships/{table_name}', headers=HEADERS)
    return response.json()


# =============================================================================
# INVESTIGATION: Find how invoice links to salesman
# =============================================================================

print("=" * 80)
print("INVESTIGATING: How does Invoice 110000014 link to Kevin Buckman?")
print("=" * 80)

# Step 1: Get the InvoiceReg record for invoice 110000014
print("\n1. Getting InvoiceReg record for invoice 110000014...")
invoice = get_record('InvoiceReg', '110000014', id_column='InvoiceNo')

print(f"   API Response: {json.dumps(invoice, indent=2)}")

if invoice.get('success'):
    print(f"   Found invoice record")
    record = invoice['record']

    # Print all fields that might be relevant
    print("\n   Key fields from invoice:")
    for key, value in record.items():
        if value and str(value).strip():  # Only non-empty fields
            if any(term in key.lower() for term in ['sale', 'dept', 'rep', 'man', 'code', 'billto', 'customer']):
                print(f"     {key}: {value}")

    saledept = record.get('SaleDept')
    billto = record.get('BillTo')

    print(f"\n   SaleDept: {saledept}")
    print(f"   BillTo: {billto}")
else:
    print(f"   ERROR: {invoice.get('error', invoice)}")
    print("\n   Trying direct query instead...")

    # Try direct query
    query = "SELECT * FROM ben002.InvoiceReg WHERE InvoiceNo = '110000014'"
    invoice = execute_query(query)

    if invoice.get('success') and invoice.get('results'):
        record = invoice['results'][0]
        print(f"   Found invoice via direct query")
        saledept = record.get('SaleDept')
        billto = record.get('BillTo')
    else:
        print(f"   Direct query also failed: {invoice}")
        sys.exit(1)

# Step 2: Get Dept table structure and find dept 10
if saledept:
    print(f"\n2. Looking up Dept {saledept}...")
    dept = get_record('Dept', str(saledept), id_column='Dept')

    if dept.get('success'):
        print(f"   Found Dept record")
        dept_record = dept['record']

        print(f"\n   All fields in Dept {saledept}:")
        for key, value in dept_record.items():
            print(f"     {key}: {value}")

        salegroup = dept_record.get('SaleGroup')
        print(f"\n   SaleGroup: {salegroup}")
    else:
        print(f"   ERROR: {dept.get('error')}")

# Step 3: Find all salesmen with that SaleGroup
if salegroup:
    print(f"\n3. Finding all salesmen with SalesGroup {salegroup}...")
    query = f"SELECT Number, Name, SalesGroup FROM ben002.Salesman WHERE SalesGroup = {salegroup}"
    salesmen = execute_query(query)

    if salesmen.get('success'):
        print(f"   Found {len(salesmen['results'])} salesmen:")
        for s in salesmen['results']:
            marker = " <-- THIS IS WHO WE WANT" if s['Name'] == 'Kevin Buckman' else ""
            print(f"     {s['Number']}: {s['Name']} (SalesGroup {s['SalesGroup']}){marker}")
    else:
        print(f"   ERROR: {salesmen.get('error')}")

# Step 4: Find columns that might link invoice to specific salesman
print("\n4. Searching for columns that might link invoice to salesman...")
salesman_cols = find_column('Salesman')

if salesman_cols.get('success'):
    print(f"\n   Tables with 'Salesman' columns:")
    tables_found = {}
    for col in salesman_cols['results']:
        table = col['TABLE_NAME']
        if table not in tables_found:
            tables_found[table] = []
        tables_found[table].append(col['COLUMN_NAME'])

    for table, cols in tables_found.items():
        print(f"     {table}: {', '.join(cols)}")

# Step 5: Check if InvoiceReg has ANY salesman-related fields
print("\n5. Getting full InvoiceReg structure...")
inv_structure = get_table_structure('InvoiceReg')

if inv_structure.get('success'):
    print(f"\n   InvoiceReg has {inv_structure['column_count']} columns")
    print("\n   Columns with 'sale' or 'rep' or 'man' in name:")
    for col in inv_structure['columns']:
        col_name = col['COLUMN_NAME']
        if any(term in col_name.lower() for term in ['sale', 'rep', 'man']):
            print(f"     {col_name} ({col['DATA_TYPE']})")

# Step 6: Check relationships
print("\n6. Checking InvoiceReg foreign key relationships...")
inv_rels = get_relationships('InvoiceReg')

if inv_rels.get('success'):
    print(f"\n   InvoiceReg references these tables:")
    for fk in inv_rels['outgoing_fks']:
        print(f"     {fk['FROM_COLUMN']} -> {fk['TO_TABLE']}.{fk['TO_COLUMN']}")

    print(f"\n   These tables reference InvoiceReg:")
    for fk in inv_rels['incoming_fks']:
        print(f"     {fk['FROM_TABLE']}.{fk['FROM_COLUMN']} -> {fk['TO_COLUMN']}")

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
