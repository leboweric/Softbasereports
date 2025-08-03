from src.services.azure_sql_service import AzureSQLService

db = AzureSQLService()

# Check for Dept column
query1 = '''
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'ben002' 
AND TABLE_NAME = 'InvoiceReg'
AND (COLUMN_NAME LIKE '%Dept%' OR COLUMN_NAME LIKE '%Department%')
ORDER BY COLUMN_NAME
'''

# Check for Department table
query2 = '''
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'ben002' 
AND (TABLE_NAME LIKE '%Department%' OR TABLE_NAME LIKE '%Dept%')
'''

# Check July revenue by Dept
query3 = '''
SELECT 
    Dept,
    COUNT(*) as invoice_count,
    SUM(GrandTotal) as revenue
FROM ben002.InvoiceReg
WHERE MONTH(InvoiceDate) = 7 AND YEAR(InvoiceDate) = 2025
AND Dept IN (40, 45)
GROUP BY Dept
'''

# Compare with SaleCode approach
query4 = '''
SELECT 
    CASE 
        WHEN SaleCode = 'RDCST' THEN 'Field (SaleCode)'
        WHEN SaleCode = 'SHPCST' THEN 'Shop (SaleCode)'
        ELSE 'Other'
    END as source,
    COUNT(*) as invoice_count,
    SUM(GrandTotal) as revenue
FROM ben002.InvoiceReg
WHERE MONTH(InvoiceDate) = 7 AND YEAR(InvoiceDate) = 2025
AND SaleCode IN ('RDCST', 'SHPCST')
GROUP BY SaleCode
'''

print('=== Department columns in InvoiceReg ===')
result1 = db.execute_query(query1)
for row in result1:
    print(row['COLUMN_NAME'])

print('\n=== Department tables ===')
result2 = db.execute_query(query2)
for row in result2:
    print(row['TABLE_NAME'])

print('\n=== July Service Revenue by Dept (40=Field, 45=Shop) ===')
try:
    result3 = db.execute_query(query3)
    total_dept = 0
    for row in result3:
        dept_name = 'Field Service' if row['Dept'] == 40 else 'Shop Service'
        revenue = row['revenue'] or 0
        total_dept += revenue
        print(f'Dept {row["Dept"]} ({dept_name}): {row["invoice_count"]} invoices, ${revenue:,.2f}')
    print(f'\nTotal Service Revenue (Dept method): ${total_dept:,.2f}')
except Exception as e:
    print(f'Error with Dept query: {e}')

print('\n=== July Service Revenue by SaleCode ===')
result4 = db.execute_query(query4)
total_salecode = 0
for row in result4:
    revenue = row['revenue'] or 0
    total_salecode += revenue
    print(f'{row["source"]}: {row["invoice_count"]} invoices, ${revenue:,.2f}')
print(f'\nTotal Service Revenue (SaleCode method): ${total_salecode:,.2f}')

# Check if Department table exists and has department info
query5 = '''
SELECT TOP 10 * FROM ben002.Department
WHERE DeptNo IN (40, 45)
'''

print('\n=== Department Table Info ===')
try:
    result5 = db.execute_query(query5)
    for row in result5:
        print(f'Dept {row["DeptNo"]}: {row.get("DeptName", "N/A")}')
except Exception as e:
    print(f'Error accessing Department table: {e}')