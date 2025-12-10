# Maintenance Contract Sale Code Fix

## Problem Discovered

The Maintenance Contract Profitability report was only showing invoices with sale code **FMBILL**, but there are actually **4 different maintenance contract sale codes** in use:

| Sale Code | Description | Customers | Invoices | Revenue (13mo) |
|-----------|-------------|-----------|----------|----------------|
| **FMROAD** | Road service maintenance | 21 | 799 | $335,982 |
| **FMBILL** | Billing maintenance | 24 | 476 | $589,534 |
| **PM-FM** | Preventive maintenance | 17 | 383 | $84,750 |
| **FMSHOP** | Shop work maintenance | 3 | 6 | $8,591 |

**Total**: 65 customers, 1,664 invoices, $1,018,857 revenue

## What Was Missing

The report was only showing:
- FMBILL: 24 customers, 476 invoices, $589,534 revenue

**Missing from report:**
- FMROAD: 799 invoices, $335,982 revenue (37% of total!)
- PM-FM: 383 invoices, $84,750 revenue (includes EDCO customer)
- FMSHOP: 6 invoices, $8,591 revenue

**Total missing: ~$430,000 in revenue!**

## Example: EDCO Customer

Customer #9244 (EDCO) has 127 invoices:
- **PM-FM**: 85 invoices, $11,201
- **EDCO**: 39 invoices, $16,001 (custom sale code)
- **FMSHOP**: 3 invoices, $3,333

This customer was completely missing from the Maintenance Contract report because they don't use FMBILL.

## Root Cause

The backend queries were filtering for:
```sql
WHERE SaleCode = 'FMBILL'
```

This excluded all other maintenance contract sale codes.

## Fix Applied

Updated all 4 queries in the backend to include all maintenance sale codes:
```sql
WHERE SaleCode IN ('FMBILL', 'FMROAD', 'PM-FM', 'FMSHOP')
```

### Files Changed

**Backend**: `reporting-backend/src/routes/department_reports.py`
- Line 8809: Revenue by month query
- Line 8822: Maintenance customers query
- Line 9059: Revenue by customer query
- Line 9078: Summary query
- Updated docstring and comments
- Added sale code descriptions to notes

**Frontend**: `reporting-frontend/src/components/MaintenanceContractProfitability.jsx`
- Line 766: Updated "About This Report" description

## Expected Impact

After deployment, the report will show:
- **~2.7x more customers** (65 vs 24)
- **~3.5x more invoices** (1,664 vs 476)
- **~1.7x more revenue** ($1,018,857 vs $589,534)
- **More accurate profitability** (includes all maintenance work)

The overall margin will likely **decrease** because we're now including all the service costs that were already being counted, but we're adding the missing revenue.

## Testing

After deployment, verify:
1. EDCO customer (#9244) appears in the report
2. Total invoices increases from ~476 to ~1,664
3. Total revenue increases from ~$590k to ~$1,019k
4. Customer count increases from ~24 to ~65

## Sale Code Descriptions

- **FMBILL**: Standard full maintenance billing
- **FMROAD**: Road service maintenance contracts
- **PM-FM**: Preventive maintenance contracts
- **FMSHOP**: Shop work maintenance contracts

All four represent different types of maintenance agreements and should be included in the profitability analysis.

## Deployment

1. **Backend**: Already committed - restart service to load changes
2. **Frontend**: Already committed - rebuild and deploy to Netlify

## Commits

- Main fix commit with all 4 sale codes included
- Documentation and testing notes
