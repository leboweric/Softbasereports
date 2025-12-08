"""
Quick script to check what RentalPeriod values exist in the WO table
"""
import sys
import os

# Add the reporting-backend to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'reporting-backend'))

from src.services.azure_sql_service import AzureSQLService

db = AzureSQLService()

# Get all distinct RentalPeriod values
query = """
SELECT DISTINCT
    wo.RentalPeriod,
    COUNT(*) as count
FROM ben002.WO wo
WHERE wo.RentalPeriod IS NOT NULL
    AND wo.RentalPeriod != ''
GROUP BY wo.RentalPeriod
ORDER BY count DESC
"""

print("=" * 80)
print("DISTINCT RENTAL PERIOD VALUES IN WO TABLE")
print("=" * 80)

results = db.execute_query(query)

for row in results:
    print(f"RentalPeriod: '{row['RentalPeriod']}' - Count: {row['count']}")

print(f"\nTotal distinct values: {len(results)}")
