#!/usr/bin/env python3
"""
Find columns containing 'Rental' or 'Period' in the schema
"""
import requests
import json

# Backend URL
BASE_URL = "https://softbasereports-production.up.railway.app"

def search_columns(pattern):
    """Search for columns matching a pattern"""
    url = f"{BASE_URL}/api/schema/find-column?pattern={pattern}"

    # Note: This endpoint requires JWT authentication
    # We'll make the request without auth to see what happens
    response = requests.get(url)

    return response.json()

print("=" * 80)
print("SEARCHING FOR 'RENTAL PERIOD' FIELD")
print("=" * 80)

# Search for columns with "Rental"
print("\n1. Searching for columns containing 'Rental'...")
try:
    rental_results = search_columns("Rental")
    print(f"   Found {rental_results.get('count', 0)} columns")
    if rental_results.get('success'):
        for col in rental_results.get('results', []):
            print(f"   - {col['TABLE_NAME']}.{col['COLUMN_NAME']} ({col['DATA_TYPE']})")
except Exception as e:
    print(f"   Error: {e}")

# Search for columns with "Period"
print("\n2. Searching for columns containing 'Period'...")
try:
    period_results = search_columns("Period")
    print(f"   Found {period_results.get('count', 0)} columns")
    if period_results.get('success'):
        for col in period_results.get('results', []):
            print(f"   - {col['TABLE_NAME']}.{col['COLUMN_NAME']} ({col['DATA_TYPE']})")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 80)
print("NOTE: This endpoint requires authentication.")
print("You can also search in the frontend at:")
print(f"{BASE_URL.replace('softbasereports-production.up.railway.app', 'softbasereports.netlify.app')}")
print("=" * 80)
