import os
import sys
sys.path.insert(0, '/home/ubuntu/Softbasereports/reporting-backend')

from src.services.azure_sql_service import AzureSQLService

db = AzureSQLService()

# Look for the equipment from the screenshot
serial_no = '35955'

query = f"""
SELECT TOP 5 *
FROM ben002.Equipment
WHERE SerialNo = '{serial_no}' OR UnitNo = '{serial_no}'
"""

print(f"=== Looking for equipment {serial_no} ===")
results = db.execute_query(query)

if results:
    print(f"\nFound {len(results)} record(s)")
    for row in results:
        print("\n--- Equipment Record ---")
        for key, value in row.items():
            if value is not None and str(value).strip() != '':
                print(f"{key:30} = {value}")
else:
    print("No equipment found")

# Also check if there's a separate PM schedule table
print("\n\n=== Checking for PM-related tables ===")
tables_query = """
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'ben002'
AND (
    TABLE_NAME LIKE '%PM%'
    OR TABLE_NAME LIKE '%Service%'
    OR TABLE_NAME LIKE '%Maint%'
    OR TABLE_NAME LIKE '%Schedule%'
)
ORDER BY TABLE_NAME
"""

table_results = db.execute_query(tables_query)
if table_results:
    print("Found PM-related tables:")
    for row in table_results:
        print(f"  - {row['TABLE_NAME']}")
else:
    print("No PM-related tables found")
