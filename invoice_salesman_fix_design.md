# Design: Use Invoice Salesman Field for Commission Assignment

## Problem Statement

Currently, the Sales Commission report uses a complex three-tier priority lookup system that matches invoice billing information against customer records to determine the salesman. This causes incorrect assignments when:
- Customer records have outdated or incorrect salesman information
- The invoice salesman differs from the customer's default salesman
- Multiple customer records exist with different salesman assignments

**Example:** Invoice 110000014 has Kevin Buckman as the salesman on the invoice, but was assigned to "HOUSE" because the customer record has `Salesman1 = "HOUSE"`.

## Solution

Use the `Salesman1` field **directly from the InvoiceReg table** instead of looking it up from customer records.

### Evidence that Invoice Has Salesman Field

Found in `dashboard_optimized.py` line 2523:
```python
ir.Salesman1,
```

The InvoiceReg table already contains a `Salesman1` field that represents the actual salesman on the invoice.

## Proposed Changes

### File: `/reporting-backend/src/routes/department_reports.py`

#### Function: `get_sales_commission_details()` (Lines 7064-7450)

**Current Logic:**
```sql
WITH SalesmanLookup AS (
    -- Complex 3-tier priority lookup from Customer table
    SELECT InvoiceNo, Salesman1
    FROM (
        -- Priority 1: BillTo number match
        -- Priority 2: Exact name match
        -- Priority 3: First word match
    )
)
SELECT ...
FROM ben002.InvoiceReg ir
INNER JOIN SalesmanLookup sl ON ir.InvoiceNo = sl.InvoiceNo
WHERE sl.Salesman1 IS NOT NULL
```

**New Logic:**
```sql
SELECT 
    ir.InvoiceNo,
    ir.InvoiceDate,
    ir.BillTo,
    ir.BillToName as CustomerName,
    ir.Salesman1,  -- Use invoice's salesman directly
    ir.SaleCode,
    ...
FROM ben002.InvoiceReg ir
WHERE ir.InvoiceDate >= %s
    AND ir.InvoiceDate <= %s
    AND ir.Salesman1 IS NOT NULL
    AND ir.Salesman1 != ''
    AND UPPER(ir.Salesman1) != 'HOUSE'
    AND ir.SaleCode IN ('RENTAL', 'USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL',
                        'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
    ...
```

**Changes:**
1. **Remove** the entire `SalesmanLookup` CTE (lines 7088-7139)
2. **Use** `ir.Salesman1` directly in the SELECT clause
3. **Remove** the `INNER JOIN SalesmanLookup sl` 
4. **Change** all references from `sl.Salesman1` to `ir.Salesman1`

#### Unassigned Invoices Query (Lines 7326-7450)

**Current Logic:**
```sql
WITH SalesmanLookup AS (
    -- Same complex lookup
)
SELECT ...
FROM ben002.InvoiceReg ir
LEFT JOIN SalesmanLookup sl ON ir.InvoiceNo = sl.InvoiceNo
WHERE (sl.Salesman1 IS NULL OR sl.Salesman1 = '' OR UPPER(sl.Salesman1) = 'HOUSE')
```

**New Logic:**
```sql
SELECT 
    ir.InvoiceNo,
    ir.InvoiceDate,
    ir.BillTo,
    ir.BillToName as CustomerName,
    COALESCE(ir.Salesman1, 'Unassigned') as Salesman,
    ir.SaleCode,
    ...
FROM ben002.InvoiceReg ir
WHERE ir.InvoiceDate >= %s
    AND ir.InvoiceDate <= %s
    AND (ir.Salesman1 IS NULL OR ir.Salesman1 = '' OR UPPER(ir.Salesman1) = 'HOUSE')
    AND ir.SaleCode IN ('RENTAL', 'USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL',
                        'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
    ...
```

**Changes:**
1. **Remove** the `SalesmanLookup` CTE
2. **Use** `ir.Salesman1` directly
3. **Simplify** the WHERE clause to check `ir.Salesman1` directly

### Function: `get_sales_commissions()` (Lines 6252-6455)

This function also uses a similar lookup pattern. Apply the same changes:

**Current:**
```sql
WITH SalesmanLookup AS (
    -- Complex lookup
)
SELECT 
    sl.Salesman,
    SUM(...) as TotalSales,
    SUM(...) as TotalCommission
FROM ben002.InvoiceReg ir
INNER JOIN SalesmanLookup sl ON ir.InvoiceNo = sl.InvoiceNo
GROUP BY sl.Salesman
```

**New:**
```sql
SELECT 
    ir.Salesman1 as Salesman,
    SUM(...) as TotalSales,
    SUM(...) as TotalCommission
FROM ben002.InvoiceReg ir
WHERE ir.Salesman1 IS NOT NULL
    AND ir.Salesman1 != ''
    AND UPPER(ir.Salesman1) != 'HOUSE'
    ...
GROUP BY ir.Salesman1
```

## Benefits

1. **Accuracy**: Uses the actual salesman recorded on the invoice at the time of sale
2. **Simplicity**: Eliminates 50+ lines of complex CTE logic
3. **Performance**: Removes unnecessary joins and subqueries
4. **Maintainability**: Easier to understand and debug
5. **Reliability**: No dependency on customer record data quality

## Potential Issues & Mitigation

### Issue 1: Invoice Salesman Field May Be Empty
**Mitigation:** Keep the unassigned invoices section to catch these cases

### Issue 2: Salesman Names May Have Variations
**Solution:** The existing `normalize_salesman_name()` function (line 7246) already handles this:
- "Tod Auge" → "Todd Auge"
- Handles common misspellings and variations

### Issue 3: Historical Data
**Impact:** This change will affect historical commission reports
**Mitigation:** 
- Document the change date
- Consider adding a feature flag if rollback is needed
- Test with multiple months of data before deploying

## Testing Plan

1. **Test with Invoice 110000014**: Verify it now assigns to Kevin Buckman
2. **Compare Results**: Run old vs new query for the same month and compare:
   - Total commission amounts per salesman
   - Number of invoices per salesman
   - Unassigned invoice counts
3. **Edge Cases**:
   - Invoices with NULL salesman
   - Invoices with empty string salesman
   - Invoices with "HOUSE" salesman
   - Invoices with salesman name variations

## Rollback Plan

If issues arise:
1. Revert the commit
2. The old customer-based lookup logic is preserved in git history
3. No database schema changes required

## Implementation Steps

1. ✅ Document the design (this file)
2. Create a new branch: `fix/use-invoice-salesman-field`
3. Modify `get_sales_commission_details()` function
4. Modify `get_sales_commissions()` function
5. Test locally with sample data
6. Commit and push for review
7. Deploy to staging/test environment
8. Validate with real data
9. Deploy to production

## Code Locations

- **File**: `/reporting-backend/src/routes/department_reports.py`
- **Functions to modify**:
  - `get_sales_commissions()` (lines 6252-6455)
  - `get_sales_commission_details()` (lines 7064-7450)
- **Lines to remove**: 
  - SalesmanLookup CTEs (~50 lines per function)
- **Lines to change**:
  - All `sl.Salesman1` → `ir.Salesman1`
  - All `sl.Salesman` → `ir.Salesman1`

## Expected Outcome

After this change:
- Invoice 110000014 will automatically assign to Kevin Buckman (from `ir.Salesman1`)
- All invoices will use the salesman recorded on the invoice itself
- No manual reassignment needed
- Customer record salesman field becomes irrelevant for commissions
