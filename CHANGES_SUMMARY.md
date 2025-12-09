# Changes Summary: Fix Customer Billing Missing Parts

## Files Modified

### 1. Backend: `reporting-backend/src/routes/department_reports.py`

#### Change 1: Added PartsNonTax to SQL Query (Line 7621)
**Before:**
```python
i.PartsTaxable,
i.LaborTaxable,
i.LaborNonTax,
```

**After:**
```python
i.PartsTaxable,
i.PartsNonTax,
i.LaborTaxable,
i.LaborNonTax,
```

#### Change 2: Added parts_non_tax to Totals Calculation (Line 7663)
**Before:**
```python
totals = {
    'parts_taxable': sum(inv['PartsTaxable'] or 0 for inv in invoices),
    'labor_taxable': sum(inv['LaborTaxable'] or 0 for inv in invoices),
    'labor_non_tax': sum(inv['LaborNonTax'] or 0 for inv in invoices),
```

**After:**
```python
totals = {
    'parts_taxable': sum(inv['PartsTaxable'] or 0 for inv in invoices),
    'parts_non_tax': sum(inv['PartsNonTax'] or 0 for inv in invoices),
    'labor_taxable': sum(inv['LaborTaxable'] or 0 for inv in invoices),
    'labor_non_tax': sum(inv['LaborNonTax'] or 0 for inv in invoices),
```

---

### 2. Frontend: `reporting-frontend/src/components/ServiceInvoiceBilling.jsx`

#### Change 1: Fixed Excel Export Data Row (Line 267)
**Before:**
```javascript
Number(inv.PartsTaxable || 0),
parseFloat(inv.LaborTaxable || 0) + parseFloat(inv.LaborNonTax || 0),
```

**After:**
```javascript
parseFloat(inv.PartsTaxable || 0) + parseFloat(inv.PartsNonTax || 0),
parseFloat(inv.LaborTaxable || 0) + parseFloat(inv.LaborNonTax || 0),
```

#### Change 2: Fixed Excel Export Totals Row (Line 292)
**Before:**
```javascript
Number(reportData.totals.parts_taxable || 0),
parseFloat(reportData.totals.labor_taxable || 0) + parseFloat(reportData.totals.labor_non_tax || 0),
```

**After:**
```javascript
parseFloat(reportData.totals.parts_taxable || 0) + parseFloat(reportData.totals.parts_non_tax || 0),
parseFloat(reportData.totals.labor_taxable || 0) + parseFloat(reportData.totals.labor_non_tax || 0),
```

#### Change 3: Fixed Table Display for Individual Invoices (Lines 566-571)
**Before:**
```javascript
<TableCell className="text-right">
  {invoice.PartsTaxable ? formatCurrency(invoice.PartsTaxable) : '-'}
</TableCell>
```

**After:**
```javascript
<TableCell className="text-right">
  {(() => {
    const partsTax = parseFloat(invoice.PartsTaxable) || 0;
    const partsNonTax = parseFloat(invoice.PartsNonTax) || 0;
    const total = partsTax + partsNonTax;
    return total > 0 ? formatCurrency(total) : '$0.00';
  })()}
</TableCell>
```

#### Change 4: Fixed Table Totals Row (Line 604)
**Before:**
```javascript
{formatCurrency(reportData.totals.parts_taxable)}
```

**After:**
```javascript
{formatCurrency((parseFloat(reportData.totals.parts_taxable) || 0) + (parseFloat(reportData.totals.parts_non_tax) || 0))}
```

---

## What This Fixes

1. **Excel Export**: Parts column will now show combined taxable + non-taxable parts
2. **Web Table Display**: Parts column in the UI will show combined parts
3. **Totals Row**: Both Excel and web table totals will include all parts
4. **Backend API**: Now returns both parts_taxable and parts_non_tax in the response

## Expected Result

For EDCO maintenance contract invoices:
- Parts column will show actual parts costs instead of $0.00
- Totals will accurately reflect all parts used
- Report will match the pattern used for Labor (which already combines taxable + non-taxable)

## Testing Checklist

- [ ] Backend syntax validation: ✓ PASSED
- [ ] Frontend file structure: ✓ VALID
- [ ] Re-run EDCO report (2025-01-01 to 2025-12-09)
- [ ] Verify Parts column shows non-zero values
- [ ] Verify totals are correct
- [ ] Test with other customers to ensure no regression
