# Sales Commission Assignment Logic Analysis

## Overview
The Sales Commissions report uses a priority-based lookup system to assign invoices to salesmen.

## Salesman Lookup Logic (Lines 7088-7139)

The system performs a **three-tier priority lookup** to find the salesman for each invoice:

### Priority 1: BillTo Customer Number Match
```sql
LEFT JOIN ben002.Customer c1 ON ir.BillTo = c1.Number
```
- Matches invoice's `BillTo` field (customer number) with Customer table's `Number` field
- If `c1.Salesman1` is found, this takes highest priority

### Priority 2: Exact BillToName Match
```sql
LEFT JOIN ben002.Customer c2 ON ir.BillToName = c2.Name AND c2.Salesman1 IS NOT NULL
```
- Matches invoice's `BillToName` field with Customer table's `Name` field (exact match)
- Only considered if Priority 1 fails

### Priority 3: First Word of Company Name Match
```sql
LEFT JOIN ben002.Customer c3 ON 
    c3.Salesman1 IS NOT NULL
    AND LEN(ir.BillToName) >= 4
    AND LEN(c3.Name) >= 4
    AND UPPER(
        CASE 
            WHEN CHARINDEX(' ', ir.BillToName) > 0 
            THEN LEFT(ir.BillToName, CHARINDEX(' ', ir.BillToName) - 1)
            ELSE ir.BillToName
        END
    ) = UPPER(
        CASE 
            WHEN CHARINDEX(' ', c3.Name) > 0 
            THEN LEFT(c3.Name, CHARINDEX(' ', c3.Name) - 1)
            ELSE c3.Name
        END
    )
```
- Matches the first word of the invoice's `BillToName` with the first word of customer names
- Case-insensitive comparison
- Only considered if Priority 1 and 2 fail

## Filtering Logic (Line 7198)

After the salesman is determined, the query **excludes** invoices where:
```sql
AND UPPER(sl.Salesman1) != 'HOUSE'
```

This means invoices assigned to "HOUSE" are:
- **Excluded from individual salesman commission calculations**
- **Included in the "Unassigned" section** (Line 7406)

## Unassigned Invoices Section (Lines 7326-7450)

A separate query captures invoices that are:
```sql
WHERE (sl.Salesman1 IS NULL OR sl.Salesman1 = '' OR UPPER(sl.Salesman1) = 'HOUSE')
```

These invoices appear in the "Unassigned" section of the report.

## Why Invoice 110000014 Was Assigned to House

Based on this logic, invoice 110000014 was assigned to "HOUSE" because:

1. **Priority 1 Match**: The `BillTo` customer number on the invoice matched a customer record where `Salesman1 = 'HOUSE'`
   - OR -
2. **Priority 2 Match**: The `BillToName` on the invoice exactly matched a customer record where `Salesman1 = 'HOUSE'`
   - OR -
3. **Priority 3 Match**: The first word of `BillToName` matched a customer record where `Salesman1 = 'HOUSE'`

## Key Issue

Even though Kevin Buckman's name appears on the invoice, the system does **NOT** look at:
- Invoice line item details
- Sales rep fields on the invoice itself
- Any text fields containing salesman names

It **ONLY** looks at the `Salesman1` field in the Customer table records that match the invoice's billing information.

## Possible Root Causes

1. **Customer Record Issue**: The customer record associated with this invoice has `Salesman1 = 'HOUSE'` in the database
2. **Multiple Customer Records**: There may be multiple customer records for the same customer, and the one being matched has 'HOUSE' as the salesman
3. **BillTo vs BillToName Mismatch**: The invoice's `BillTo` number points to a different customer record than expected

## Solution Paths

1. **Update Customer Record**: Change the `Salesman1` field in the customer record from 'HOUSE' to 'Kevin Buckman'
2. **Manual Reassignment**: Use the commission settings reassignment feature to manually assign this invoice to Kevin Buckman
3. **Fix Invoice Data**: If the `BillTo` number is incorrect, update the invoice to point to the correct customer record
