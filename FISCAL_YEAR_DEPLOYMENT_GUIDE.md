# Fiscal Year Configuration - Deployment Guide

## Overview

This deployment implements per-organization fiscal year configuration for department charts. The changes fix the duplicate month label issue (e.g., "Nov 2024" and "Nov 2025" both showing as "Nov") and ensure charts display fiscal year periods instead of the last 12 calendar months.

## What Changed

### 1. Database Schema
- **New Column**: `fiscal_year_start_month` added to `organization` table
  - Type: INTEGER
  - Default: 11 (November)
  - Constraint: Must be between 1-12
  - Purpose: Store the fiscal year start month per organization

### 2. Backend Changes

#### New Files
- **`src/utils/fiscal_year.py`**: Fiscal year utility functions
  - `get_fiscal_year_start_month()`: Get fiscal year start month for current org
  - `get_current_fiscal_year_dates()`: Calculate fiscal year start/end dates
  - `get_fiscal_year_months()`: Generate 12 consecutive fiscal year months
  - `get_fiscal_ytd_start()`: Get fiscal YTD start date
  - `is_fiscal_year_end_month()`: Check if in fiscal year-end month
  - `format_fiscal_year_label()`: Format fiscal year label (e.g., "FY 2024-2025")

#### Modified Files
- **`src/models/user.py`**: Added `fiscal_year_start_month` field to Organization model
- **`src/routes/organization.py`**: 
  - GET `/api/organization/settings` now returns `fiscal_year_start_month`
  - PUT `/api/organization/settings` now accepts `fiscal_year_start_month` updates
- **`src/routes/department_reports.py`**: Updated 3 chart endpoints to use fiscal year periods:
  - `/api/reports/departments/service` (Service labor revenue charts)
  - `/api/reports/departments/parts` (Parts revenue charts)
  - `/api/reports/departments/rental/monthly-revenue` (Rental revenue charts)

### 3. Chart Behavior Changes

#### Before
- Charts showed "last 12 calendar months" (e.g., Dec 2024, Jan 2025, Feb 2025, ..., Nov 2025)
- Duplicate month names when spanning years (Nov 2024 and Nov 2025 both as "Nov")
- Months could appear out of order due to frontend re-sorting

#### After
- Charts show fiscal year periods (12 consecutive months starting with fiscal year start)
- For November fiscal year: Nov, Dec, Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct
- Month labels include year when spanning calendar years: "Nov '24", "Dec '24", "Jan '25", etc.
- No duplicate month labels
- Months always in correct fiscal year order

## Deployment Steps

### Step 1: Run Database Migration

**IMPORTANT**: Run this SQL migration in pgAdmin **BEFORE** deploying the code changes.

```sql
-- Migration: Add fiscal_year_start_month to Organization table
-- Purpose: Allow per-organization fiscal year configuration
-- Date: 2025-11-19

-- Add the fiscal_year_start_month column with default value of 11 (November)
ALTER TABLE organization 
ADD COLUMN fiscal_year_start_month INTEGER DEFAULT 11;

-- Add a comment to document the column
COMMENT ON COLUMN organization.fiscal_year_start_month IS 'Fiscal year start month (1-12, where 1=January, 11=November). Defaults to 11 for November fiscal year start.';

-- Add a check constraint to ensure valid month values (1-12)
ALTER TABLE organization 
ADD CONSTRAINT check_fiscal_year_start_month 
CHECK (fiscal_year_start_month >= 1 AND fiscal_year_start_month <= 12);

-- Update existing organizations to use November (11) as default if NULL
UPDATE organization 
SET fiscal_year_start_month = 11 
WHERE fiscal_year_start_month IS NULL;

-- Verify the migration
SELECT id, name, fiscal_year_start_month 
FROM organization 
ORDER BY id;
```

**Location**: The SQL script is also saved in `/fiscal_year_migration.sql`

### Step 2: Deploy Code to Railway

The code has been pushed to GitHub (`main` branch). Railway will automatically deploy the changes.

**Commit**: `a6c598e` - "Implement fiscal year configuration for department charts"

**Monitor deployment**:
1. Go to Railway dashboard
2. Check deployment logs for any errors
3. Verify the deployment completes successfully

### Step 3: Verify Deployment

After Railway deployment completes, verify the changes:

#### 3.1 Check Organization Settings API
```bash
# Test GET endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://your-api-domain.railway.app/api/organization/settings

# Expected response should include:
{
  "success": true,
  "settings": {
    "name": "Your Organization",
    "fiscal_year_start_month": 11,
    ...
  }
}
```

#### 3.2 Check Department Charts
1. Navigate to Service Department dashboard
2. Check the monthly revenue chart
3. Verify months are displayed as: Nov '24, Dec '24, Jan '25, Feb '25, ..., Oct '25
4. Verify no duplicate month names
5. Verify data is displayed for all 12 fiscal year months

Repeat for Parts and Rental department dashboards.

#### 3.3 Test Fiscal Year Configuration Update
```bash
# Test PUT endpoint to change fiscal year start month
curl -X PUT \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fiscal_year_start_month": 1}' \
  https://your-api-domain.railway.app/api/organization/settings

# Expected response:
{
  "success": true,
  "message": "Settings updated successfully"
}

# Verify charts now show Jan-Dec instead of Nov-Oct
```

## Configuration Examples

### Example 1: November Fiscal Year (Default)
```json
{
  "fiscal_year_start_month": 11
}
```
**Chart months**: Nov '24, Dec '24, Jan '25, Feb '25, Mar '25, Apr '25, May '25, Jun '25, Jul '25, Aug '25, Sep '25, Oct '25

### Example 2: January Fiscal Year (Calendar Year)
```json
{
  "fiscal_year_start_month": 1
}
```
**Chart months**: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec

### Example 3: July Fiscal Year
```json
{
  "fiscal_year_start_month": 7
}
```
**Chart months**: Jul '24, Aug '24, Sep '24, Oct '24, Nov '24, Dec '24, Jan '25, Feb '25, Mar '25, Apr '25, May '25, Jun '25

## Technical Details

### How Fiscal Year Months Are Calculated

The `get_fiscal_year_months()` function:
1. Gets the fiscal year start month from organization settings (default: 11)
2. Determines the current fiscal year based on today's date
3. Generates 12 consecutive months starting with the fiscal year start month
4. Returns a list of (year, month) tuples in chronological order

Example for November fiscal year in December 2024:
```python
fiscal_year_months = [
    (2024, 11),  # Nov 2024
    (2024, 12),  # Dec 2024
    (2025, 1),   # Jan 2025
    (2025, 2),   # Feb 2025
    ...
    (2025, 10)   # Oct 2025
]
```

### Month Label Formatting

Month labels are formatted based on whether the fiscal year spans multiple calendar years:

**Single calendar year** (e.g., Jan-Dec fiscal year in 2025):
- Labels: "Jan", "Feb", "Mar", ..., "Dec"

**Multiple calendar years** (e.g., Nov-Oct fiscal year):
- Labels: "Nov '24", "Dec '24", "Jan '25", ..., "Oct '25"

This is handled automatically by checking if `fiscal_year_months[0][0] != fiscal_year_months[-1][0]`

### Data Source Logic (Unchanged)

The fiscal year implementation does NOT change the GL.MTD vs GLDetail logic:
- **Closed months**: Use `GL.MTD` for accurate P&L matching
- **Current month**: Use `GLDetail` for real-time data
- **Partial months**: Use `GLDetail` for custom date ranges

## Troubleshooting

### Issue: Charts still showing duplicate months
**Solution**: 
1. Verify the database migration ran successfully
2. Check that Railway deployment completed
3. Clear browser cache and refresh the page
4. Check browser console for API errors

### Issue: Fiscal year setting not saving
**Solution**:
1. Verify user has `organization_settings` permission
2. Check that the value is an integer between 1-12
3. Review API logs for validation errors

### Issue: Charts showing wrong months
**Solution**:
1. Check organization settings: `GET /api/organization/settings`
2. Verify `fiscal_year_start_month` is set correctly
3. Check that `g.current_organization` is properly set in request context
4. Review `fiscal_year.py` utility functions for logic errors

### Issue: Month labels not showing year
**Solution**:
This is expected behavior when the fiscal year doesn't span multiple calendar years (e.g., Jan-Dec fiscal year in the same year). Year labels are only shown when needed.

## Future Enhancements

### Potential Improvements
1. **YTD Calculations**: Update all YTD calculations to use fiscal year start instead of Jan 1
2. **Fiscal Year Selector**: Add UI dropdown to select fiscal year start month in organization settings
3. **Fiscal Year Reports**: Add dedicated fiscal year-end reports
4. **Historical Fiscal Years**: Add ability to view previous fiscal year data
5. **Fiscal Year Comparison**: Compare current fiscal year to prior fiscal year

### Files That May Need Future Updates
- `dashboard_optimized.py`: Currently has hardcoded Nov 1 fiscal year logic (lines 24-28)
- `pl_report.py`: YTD calculations may need fiscal year awareness
- `currie_report.py`: YTD calculations may need fiscal year awareness

## Rollback Plan

If issues occur after deployment:

### Option 1: Revert Code Changes
```bash
cd /home/ubuntu/Softbasereports
git revert a6c598e
git push origin main
```

### Option 2: Keep Database Column, Disable Feature
The `fiscal_year_start_month` column can remain in the database without causing issues. Simply revert the code changes and the system will fall back to the previous "last 12 months" behavior.

### Option 3: Remove Database Column
```sql
-- Only run if you want to completely remove the feature
ALTER TABLE organization 
DROP CONSTRAINT check_fiscal_year_start_month;

ALTER TABLE organization 
DROP COLUMN fiscal_year_start_month;
```

## Testing Checklist

- [ ] Database migration completed successfully
- [ ] Railway deployment completed without errors
- [ ] Service department chart shows fiscal year months
- [ ] Parts department chart shows fiscal year months
- [ ] Rental department chart shows fiscal year months
- [ ] No duplicate month labels in any chart
- [ ] Month labels include year when spanning multiple calendar years
- [ ] Organization settings GET endpoint returns `fiscal_year_start_month`
- [ ] Organization settings PUT endpoint accepts `fiscal_year_start_month` updates
- [ ] Changing fiscal year start month updates charts accordingly
- [ ] Invalid month values (0, 13, etc.) are rejected with error message
- [ ] Data accuracy matches Softbase (GL.MTD logic unchanged)

## Support

For questions or issues with this deployment, contact the development team or refer to:
- GitHub commit: `a6c598e`
- SQL migration: `/fiscal_year_migration.sql`
- Fiscal year utility: `/reporting-backend/src/utils/fiscal_year.py`
