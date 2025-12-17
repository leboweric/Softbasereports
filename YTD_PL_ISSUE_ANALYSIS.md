# YTD P&L Calculation Issue Analysis

## Problem Statement

The Financial Overview dashboard is showing an incorrect YTD P&L of **$183,860** as of November 30, 2025.

Since the fiscal year starts in **November 2025**, the YTD P&L should only reflect November 2025 data, which is **$41,032** (the Current Month P&L).

## Root Cause Analysis

### Current Implementation

Located in `/reporting-backend/src/routes/pl_widget.py`:

**Lines 56-57:**
```python
# Calculate trailing 12-month total (sum of all months in trend)
ytd_pl = sum(item['profit_loss'] for item in trend_data) if trend_data else 0
```

**Problem:** The code is calculating YTD as the sum of ALL months in the trend data (12 months), not just the months within the current fiscal year.

### How the Trend Data Works

The `get_pl_trend()` function (lines 176-224) returns the last 12 months of data:
- It goes back 12 months from the current month (November 2025)
- This includes: December 2024, January 2025, February 2025, March 2025... through November 2025
- The sum of these 12 months = $183,860

### Why This Is Wrong

For a fiscal year starting in **November 2025**:
- **Fiscal YTD** should only include: November 2025
- **Current calculation** includes: 12 months (Dec 2024 - Nov 2025)

The fiscal year configuration exists in `fiscal_year.py`:
- `get_fiscal_year_start_month()` returns 11 (November)
- `get_fiscal_ytd_start()` returns the start of the current fiscal year
- But the `pl_widget.py` is NOT using these fiscal year utilities

## Solution

The YTD calculation needs to:

1. **Use fiscal year awareness** instead of summing all trend data
2. **Calculate from fiscal year start** (November 2025) to current month (November 2025)
3. **Use the existing fiscal year utilities** from `src/utils/fiscal_year.py`

### Proposed Fix

Replace the simple sum with a fiscal-year-aware calculation:

```python
from src.utils.fiscal_year import get_fiscal_ytd_start

# In get_pl_widget():
# Calculate fiscal YTD (from fiscal year start to current month)
fiscal_ytd_start = get_fiscal_ytd_start()
ytd_pl = sum(
    item['profit_loss'] 
    for item in trend_data 
    if datetime.strptime(item['month'], '%Y-%m').replace(day=1) >= fiscal_ytd_start
)
```

This will:
- Filter trend data to only include months >= fiscal year start (Nov 2025)
- Sum only those months that fall within the current fiscal year
- Result in $41,032 for November 2025 (only one month in the fiscal year so far)

## Impact

- **Current behavior:** Shows 12-month rolling total as "YTD"
- **Fixed behavior:** Shows actual fiscal year-to-date total
- **For November 2025:** Changes from $183,860 → $41,032

## Files to Modify

1. `/reporting-backend/src/routes/pl_widget.py` - Update YTD calculation logic (line 56)

## Testing

After the fix:
- As of November 30, 2025: YTD should be $41,032 (November only)
- As of December 31, 2025: YTD should be November + December
- As of October 31, 2026: YTD should be sum of Nov 2025 - Oct 2026 (full fiscal year)
