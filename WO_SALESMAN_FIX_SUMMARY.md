# Commission Report Fix: Use WO.Salesman Field

## Problem

Invoice 110000014 was incorrectly assigned to "House" in the commission report even though "Kevin Buckman" appeared on the printed invoice.

## Root Cause

The commission report was using a complex 3-tier customer lookup system:
1. Match by BillTo customer number
2. Match by exact BillToName
3. Match by first word of company name

This system ignored the actual salesman information stored on the work order (WO) record.

## Investigation Findings

- **InvoiceReg table**: Has `Salesman1 = "House"` (not reliable)
- **Customer table**: Has `Salesman1 = "House"` (not reliable)
- **WO table**: Has `Salesman = "Kevin Buckman"` ✅ (THIS is the source of truth!)

The printed invoice uses `WO.Salesman` to display the salesman name, but the commission report was not using this field.

## Solution

**Replace the complex customer lookup with a simple WO join:**

```sql
-- OLD (Complex, unreliable)
WITH SalesmanLookup AS (
    -- 50+ lines of complex CTE logic
    -- Joins to Customer table multiple ways
    -- Returns unpredictable results when multiple salesmen exist
)
SELECT ... FROM InvoiceReg ir
INNER JOIN SalesmanLookup sl ON ir.InvoiceNo = sl.InvoiceNo

-- NEW (Simple, reliable)
SELECT ... FROM InvoiceReg ir
LEFT JOIN ben002.WO wo ON ir.InvoiceNo = wo.InvoiceNo
WHERE COALESCE(wo.Salesman, 'House') != 'HOUSE'
```

## Changes Made

### Files Modified
- `reporting-backend/src/routes/department_reports.py`

### Functions Updated
1. `get_sales_commissions()` - Summary view
2. `get_sales_commission_details()` - Detailed view
3. Unassigned invoices query

### Code Impact
- **Removed**: ~135 lines of complex CTE logic
- **Added**: ~19 lines of simple WO join
- **Net reduction**: 116 lines of code

## Benefits

✅ **Accurate**: Uses the same salesman field as the printed invoice  
✅ **Simple**: Single LEFT JOIN instead of complex 3-tier lookup  
✅ **Fast**: No unnecessary customer table joins  
✅ **Reliable**: No ambiguity when multiple salesmen exist  
✅ **Consistent**: Commission report matches printed invoices  

## Testing

**Test Case**: Invoice 110000014
- **Before**: Assigned to "House" (unassigned section)
- **After**: Should assign to "Kevin Buckman"

**Verification Query**:
```sql
SELECT 
    ir.InvoiceNo,
    ir.InvoiceDate,
    ir.BillToName,
    wo.Salesman,
    ir.SaleCode,
    ir.GrandTotal
FROM ben002.InvoiceReg ir
LEFT JOIN ben002.WO wo ON ir.InvoiceNo = wo.InvoiceNo
WHERE ir.InvoiceNo = 110000014;
```

Expected Result:
- InvoiceNo: 110000014
- Salesman: Kevin Buckman
- Should appear in Kevin Buckman's commission report

## Deployment

**Branch**: `fix/use-wo-salesman-for-commissions`

**Steps**:
1. Review changes in this branch
2. Merge to main
3. Railway will auto-deploy
4. Verify invoice 110000014 appears under Kevin Buckman
5. Check that no other invoices were incorrectly reassigned

## Rollback Plan

If issues occur:
```bash
git revert HEAD
git push origin main
```

Railway will auto-deploy the revert.

## Notes

- This fix assumes all commission-eligible invoices have corresponding WO records
- Invoices without WO records will have `Salesman = NULL` and appear in "Unassigned"
- The `COALESCE(wo.Salesman, 'House')` handles NULL cases gracefully
