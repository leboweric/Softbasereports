# Deployment Instructions: Invoice Salesman Fix

## Branch Information
- **Branch:** `investigation/invoice-110000014-house-assignment`
- **Commits:** 3 commits
  1. Investigation report and diagnostic query
  2. Design document
  3. Implementation of fix

## Changes Summary
- **Files Modified:** 1 (`reporting-backend/src/routes/department_reports.py`)
- **Lines Changed:** -138 deletions, +44 additions (net -94 lines)
- **Functions Modified:** 3
  - `get_sales_commissions()`
  - `get_sales_commission_details()`
  - Unassigned invoices query

## What Changed

### Before
Commission assignment used a complex 3-tier priority lookup:
1. Match invoice BillTo → Customer.Number → use Customer.Salesman1
2. Match invoice BillToName → Customer.Name → use Customer.Salesman1
3. Match first word of BillToName → Customer.Name → use Customer.Salesman1

**Problem:** Customer record data overrode invoice salesman information

### After
Commission assignment uses the invoice's `Salesman1` field directly:
- `SELECT ir.Salesman1` from InvoiceReg table
- No customer table lookups
- Invoice data is the source of truth

**Result:** Invoice 110000014 with `ir.Salesman1 = 'Kevin Buckman'` will assign to Kevin Buckman

## Deployment Steps

### 1. Pre-Deployment Testing
```bash
# Run in staging/test environment first
git checkout investigation/invoice-110000014-house-assignment
# Deploy to staging
# Test commission reports for current and previous months
# Verify invoice 110000014 appears under Kevin Buckman
```

### 2. Validation Checklist
- [ ] Commission report loads without errors
- [ ] Invoice 110000014 assigns to Kevin Buckman
- [ ] Total commission amounts are reasonable
- [ ] No invoices are missing from the report
- [ ] Unassigned section shows appropriate invoices
- [ ] All salesmen appear in the report
- [ ] Performance is acceptable (should be faster)

### 3. Production Deployment
```bash
# Merge to main branch
git checkout main
git merge investigation/invoice-110000014-house-assignment
git push origin main

# Deploy to production
# Monitor for errors
```

### 4. Post-Deployment Verification
- [ ] Run commission report for current month
- [ ] Compare results with previous month (expect some differences)
- [ ] Check application logs for errors
- [ ] Verify with sales team that assignments look correct
- [ ] Monitor performance metrics

## Expected Behavior Changes

### Invoices That Will Change Assignment
Any invoice where:
- `ir.Salesman1` (invoice salesman) ≠ Customer.Salesman1 (customer record salesman)

**Example:**
- Invoice has `ir.Salesman1 = 'Kevin Buckman'`
- Customer record has `Salesman1 = 'HOUSE'`
- **Before:** Assigned to HOUSE (unassigned section)
- **After:** Assigned to Kevin Buckman

### Invoices That Will NOT Change
- Invoices where `ir.Salesman1` matches customer record
- Invoices with NULL or empty `ir.Salesman1` (remain unassigned)
- Invoices with `ir.Salesman1 = 'HOUSE'` (remain unassigned)

## Performance Impact

### Expected Improvements
- **Faster queries:** No complex CTEs or joins
- **Reduced database load:** Fewer table scans
- **Simpler execution plans:** Direct field access

### Metrics to Monitor
- Query execution time (should decrease)
- Database CPU usage (should decrease)
- Page load time for commission reports (should improve)

## Rollback Plan

If issues arise:

### Immediate Rollback
```bash
# Revert the commit
git revert 2cdf54d
git push origin investigation/invoice-110000014-house-assignment

# Or reset to previous commit
git reset --hard 16cee29
git push --force origin investigation/invoice-110000014-house-assignment
```

### No Data Loss
- This is a query-only change
- No database schema modifications
- No data modifications
- Previous logic preserved in git history

## Communication Plan

### Notify Users
**Subject:** Sales Commission Report Update - Invoice Salesman Assignment

**Message:**
> We've updated the Sales Commission report to use the salesman recorded directly on each invoice, rather than looking up the salesman from customer records. 
>
> **What this means:**
> - Commissions will be assigned based on who is listed on the invoice
> - More accurate commission assignments
> - Fixes issues where customer records had outdated salesman information
>
> **What to expect:**
> - Some historical reports may show different results if re-run
> - Invoice 110000014 and similar cases will now assign correctly
> - No action needed on your part
>
> If you notice any issues or have questions, please contact support.

### Stakeholders to Notify
- [ ] Sales team
- [ ] Accounting team
- [ ] Sales managers
- [ ] System administrators

## Known Issues & Limitations

### Issue 1: Historical Data
**Impact:** Re-running historical commission reports will show different results
**Mitigation:** Document the change date, keep old reports for reference
**Severity:** Low (expected behavior)

### Issue 2: Null Salesman Field
**Impact:** Invoices with NULL `ir.Salesman1` will appear in unassigned section
**Mitigation:** Review and update invoice data if needed
**Severity:** Low (same as before)

### Issue 3: Name Variations
**Impact:** "Kevin Buckman" vs "K Buckman" treated as different
**Mitigation:** `normalize_salesman_name()` function handles common variations
**Severity:** Low (already handled)

## Success Metrics

### Primary Goals
✅ Invoice 110000014 assigns to Kevin Buckman automatically
✅ Code is simpler and more maintainable
✅ Performance improves
✅ No manual intervention required

### Monitoring
- [ ] Zero errors in application logs
- [ ] Query execution time < previous implementation
- [ ] User satisfaction (no complaints about incorrect assignments)
- [ ] Commission totals are reasonable

## Support

### Troubleshooting

**Problem:** Invoice not appearing in report
**Solution:** Check if `ir.Salesman1` is NULL or empty, check date range

**Problem:** Invoice assigned to wrong salesman
**Solution:** Check `ir.Salesman1` field value in database, verify it's correct on the invoice

**Problem:** Total commissions seem wrong
**Solution:** Compare with previous month, check for data quality issues in `ir.Salesman1` field

### Contact
- **Developer:** [Your Name]
- **Branch:** investigation/invoice-110000014-house-assignment
- **Documentation:** See validation and design documents in the branch

## Files in This Branch

1. **Invoice_110000014_Investigation_Report.md** - Full investigation of the issue
2. **commission_logic_analysis.md** - Technical analysis of old logic
3. **invoice_110000014_diagnostic.sql** - SQL query to diagnose specific invoices
4. **invoice_salesman_fix_design.md** - Design document for the fix
5. **validate_invoice_salesman_changes.md** - Validation checklist
6. **DEPLOYMENT_INSTRUCTIONS.md** - This file
7. **department_reports.py** - Modified code

## Next Steps

1. ✅ Code implemented and pushed
2. ⏳ Review this deployment guide
3. ⏳ Deploy to staging environment
4. ⏳ Run validation tests
5. ⏳ Get approval from stakeholders
6. ⏳ Deploy to production
7. ⏳ Monitor and verify
8. ⏳ Notify users
9. ⏳ Close the investigation branch

---

**Ready for deployment to staging environment for testing.**
