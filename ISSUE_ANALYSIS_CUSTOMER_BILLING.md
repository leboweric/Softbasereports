# Root Cause Analysis: Missing Parts in Customer Billing Report

## Issue Summary

The "Customer Billing" report in the Softbase Reports app is not displaying parts costs for EDCO maintenance contract invoices. All 204 invoice rows show Parts = $0.00, even though the Comments field clearly indicates parts were used (batteries, hoses, water pumps, etc.).

## Root Cause

The SQL query and data processing logic in the `get_service_invoice_billing()` function **only retrieves `PartsTaxable`** and **completely omits `PartsNonTax`**. For EDCO maintenance contract invoices, parts are recorded as non-taxable (`PartsNonTax`), which explains why they don't appear in the report.

## Evidence

### 1. Backend SQL Query (Line 7620)
**Current (Broken):**
```sql
i.PartsTaxable,          -- ONLY taxable parts
i.LaborTaxable,          -- Labor includes both...
i.LaborNonTax,           -- ...taxable AND non-taxable ✓
i.MiscTaxable,
```

**Inconsistency:** The query correctly includes both `LaborTaxable` and `LaborNonTax` for labor, but only includes `PartsTaxable` for parts, missing `PartsNonTax`.

### 2. Backend Totals Calculation (Line 7661)
**Current (Broken):**
```python
totals = {
    'parts_taxable': sum(inv['PartsTaxable'] or 0 for inv in invoices),
    # Missing: 'parts_non_tax' calculation
    'labor_taxable': sum(inv['LaborTaxable'] or 0 for inv in invoices),
    'labor_non_tax': sum(inv['LaborNonTax'] or 0 for inv in invoices),
    ...
}
```

### 3. Frontend Excel Export (ServiceInvoiceBilling.jsx, Line 267)
**Current (Broken):**
```javascript
Number(inv.PartsTaxable || 0),  // ONLY taxable parts
parseFloat(inv.LaborTaxable || 0) + parseFloat(inv.LaborNonTax || 0),  // Labor correctly combines both ✓
```

### 4. Frontend Totals Row (Line 292)
**Current (Broken):**
```javascript
Number(reportData.totals.parts_taxable || 0),  // ONLY taxable
parseFloat(reportData.totals.labor_taxable || 0) + parseFloat(reportData.totals.labor_non_tax || 0),  // Labor correct ✓
```

## Correct Pattern (Used in Other Reports)

The codebase already has the correct pattern in other reports (e.g., Parts Counter Report at line 2181, Maintenance Contract Profitability at line 8782):

```sql
SELECT
    ISNULL(PartsTaxable, 0) as PartsTaxable,
    ISNULL(PartsNonTax, 0) as PartsNonTax,
    ISNULL(PartsTaxable, 0) + ISNULL(PartsNonTax, 0) as TotalParts,
    ISNULL(LaborTaxable, 0) + ISNULL(LaborNonTax, 0) as TotalLabor
```

## Required Fix

### Backend Changes (department_reports.py)

#### 1. Update SQL Query (Line 7620)
**Change from:**
```sql
i.PartsTaxable,
i.LaborTaxable,
i.LaborNonTax,
```

**Change to:**
```sql
i.PartsTaxable,
i.PartsNonTax,
i.LaborTaxable,
i.LaborNonTax,
```

#### 2. Update Totals Calculation (Line 7661)
**Change from:**
```python
totals = {
    'parts_taxable': sum(inv['PartsTaxable'] or 0 for inv in invoices),
    'labor_taxable': sum(inv['LaborTaxable'] or 0 for inv in invoices),
    'labor_non_tax': sum(inv['LaborNonTax'] or 0 for inv in invoices),
    ...
}
```

**Change to:**
```python
totals = {
    'parts_taxable': sum(inv['PartsTaxable'] or 0 for inv in invoices),
    'parts_non_tax': sum(inv['PartsNonTax'] or 0 for inv in invoices),
    'labor_taxable': sum(inv['LaborTaxable'] or 0 for inv in invoices),
    'labor_non_tax': sum(inv['LaborNonTax'] or 0 for inv in invoices),
    ...
}
```

### Frontend Changes (ServiceInvoiceBilling.jsx)

#### 3. Update Excel Export Data Row (Line 267)
**Change from:**
```javascript
Number(inv.PartsTaxable || 0),
parseFloat(inv.LaborTaxable || 0) + parseFloat(inv.LaborNonTax || 0),
```

**Change to:**
```javascript
parseFloat(inv.PartsTaxable || 0) + parseFloat(inv.PartsNonTax || 0),
parseFloat(inv.LaborTaxable || 0) + parseFloat(inv.LaborNonTax || 0),
```

#### 4. Update Excel Export Totals Row (Line 292)
**Change from:**
```javascript
Number(reportData.totals.parts_taxable || 0),
parseFloat(reportData.totals.labor_taxable || 0) + parseFloat(reportData.totals.labor_non_tax || 0),
```

**Change to:**
```javascript
parseFloat(reportData.totals.parts_taxable || 0) + parseFloat(reportData.totals.parts_non_tax || 0),
parseFloat(reportData.totals.labor_taxable || 0) + parseFloat(reportData.totals.labor_non_tax || 0),
```

#### 5. Update Table Display (if showing parts breakdown)
If the table displays parts in the UI (not just Excel), similar changes would be needed there.

## Testing Recommendations

1. **Verify the fix with EDCO data:**
   - Re-run the report for EDCO maintenance contract (2025-01-01 to 2025-12-09)
   - Confirm Parts column now shows non-zero values
   - Verify totals match expected amounts

2. **Test with other customers:**
   - Ensure the fix doesn't break reports for other customers
   - Test with customers that have taxable parts
   - Test with customers that have both taxable and non-taxable parts

3. **Compare with source data:**
   - Query the InvoiceReg table directly to verify PartsTaxable and PartsNonTax values
   - Confirm the report totals match the database totals

## Files to Modify

1. `/reporting-backend/src/routes/department_reports.py` (lines 7620, 7661)
2. `/reporting-frontend/src/components/ServiceInvoiceBilling.jsx` (lines 267, 292)

## Impact Assessment

- **Low risk:** This is a straightforward addition of a missing field
- **High value:** Fixes a critical reporting issue affecting year-end financial reporting
- **Pattern consistency:** Aligns with how Labor and other reports handle taxable/non-taxable amounts
