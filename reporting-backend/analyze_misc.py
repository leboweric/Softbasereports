#!/usr/bin/env python3
from src.services.azure_sql_service import AzureSQLService
import pandas as pd

db = AzureSQLService()

# Query to analyze misc revenue
query = '''
SELECT TOP 100
    InvoiceNo,
    InvoiceDate,
    BillToName,
    Department,
    SaleCode,
    MiscTaxable,
    MiscNonTax,
    (MiscTaxable + MiscNonTax) as TotalMisc,
    PartsTaxable + PartsNonTax as TotalParts,
    LaborTaxable + LaborNonTax as TotalLabor,
    RentalTaxable + RentalNonTax as TotalRental,
    GrandTotal,
    InvoiceRemark
FROM ben002.InvoiceReg
WHERE (MiscTaxable > 0 OR MiscNonTax > 0)
AND InvoiceDate >= '2025-07-01'
ORDER BY (MiscTaxable + MiscNonTax) DESC
'''

print("Executing query...")
results = db.execute_query(query)

if results:
    df = pd.DataFrame(results)
    print('\n=== MISC REVENUE ANALYSIS ===')
    print(f'\nTotal invoices with misc revenue: {len(results)}')
    print(f'\nTop 10 invoices by misc amount:')
    
    for _, row in df.head(10).iterrows():
        print(f'\nInvoice: {row["InvoiceNo"]}')
        print(f'  Customer: {row["BillToName"]}')
        print(f'  Department: {row["Department"]} | SaleCode: {row["SaleCode"]}')
        print(f'  Misc Amount: ${row["TotalMisc"]:,.2f}')
        print(f'  Grand Total: ${row["GrandTotal"]:,.2f}')
        print(f'  Misc % of Total: {(row["TotalMisc"]/row["GrandTotal"]*100):.1f}%')
        if row.get("InvoiceRemark"):
            print(f'  Remark: {row["InvoiceRemark"][:50]}...' if len(str(row["InvoiceRemark"])) > 50 else f'  Remark: {row["InvoiceRemark"]}')
    
    print('\n\n=== DEPARTMENT/SALECODE BREAKDOWN ===')
    dept_summary = df.groupby(['Department', 'SaleCode']).agg({
        'TotalMisc': ['sum', 'count', 'mean']
    }).round(2)
    print("\nTop departments by total misc revenue:")
    print(dept_summary.sort_values(('TotalMisc', 'sum'), ascending=False).head(10))
    
    # Check for patterns in sale codes
    print('\n\n=== UNIQUE SALE CODES WITH MISC REVENUE ===')
    unique_codes = df[['SaleCode', 'Department']].drop_duplicates().sort_values('SaleCode')
    for _, row in unique_codes.iterrows():
        count = len(df[df['SaleCode'] == row['SaleCode']])
        total = df[df['SaleCode'] == row['SaleCode']]['TotalMisc'].sum()
        print(f"  {row['SaleCode']} ({row['Department']}): {count} invoices, ${total:,.2f} total")

# Also check invoice line items for more detail
print("\n\n=== CHECKING INVOICE SALES TABLE FOR MISC ITEMS ===")
query2 = '''
SELECT TOP 50
    i.InvoiceNo,
    i.BillToName,
    s.LineNo,
    s.SaleCode,
    s.ItemDescription,
    s.ExtendedPrice,
    s.ItemType
FROM ben002.InvoiceSales s
JOIN ben002.InvoiceReg i ON s.InvoiceNo = i.InvoiceNo
WHERE s.SaleCode NOT IN ('PRT', 'SVE', 'RNT')
AND s.ExtendedPrice > 0
AND i.InvoiceDate >= '2025-07-01'
ORDER BY s.ExtendedPrice DESC
'''

results2 = db.execute_query(query2)
if results2:
    print("\nNon-standard sale codes in InvoiceSales:")
    for row in results2[:20]:
        print(f"\nInvoice: {row['InvoiceNo']} - {row['BillToName']}")
        print(f"  SaleCode: {row['SaleCode']} | Type: {row.get('ItemType', 'N/A')}")
        print(f"  Description: {row['ItemDescription']}")
        print(f"  Amount: ${row['ExtendedPrice']:,.2f}")