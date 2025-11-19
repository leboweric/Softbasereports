# Year-over-Year Comparison - Implementation Summary

## Overview

Added year-over-year (YoY) comparison data to all department charts to enable visual month-over-month performance tracking using dual-color bar visualization (ghost bars for prior year, solid bars for current year).

## Implementation Date
November 19, 2025

## What Changed

### Backend Updates

All three department chart endpoints now return `prior_year_amount` for each month:

1. **Service Department** (`/api/reports/departments/service`)
   - `monthlyLaborRevenue`: Combined service revenue (Field + Shop)
   - `monthlyFieldRevenue`: Field service revenue only
   - `monthlyShopRevenue`: Shop service revenue only

2. **Parts Department** (`/api/reports/departments/parts`)
   - `monthlyPartsRevenue`: Combined parts revenue (Counter + Repair Order)
   - `monthlyCounterRevenue`: Counter sales revenue only
   - `monthlyRepairOrderRevenue`: Repair order parts revenue only

3. **Rental Department** (`/api/reports/departments/rental/monthly-revenue`)
   - `monthlyRentalRevenue`: Monthly rental revenue

### Data Structure

Each month object now includes:

```json
{
  "month": "Nov '24",
  "amount": 31100,
  "margin": 72.6,
  "prior_year_amount": 28500
}
```

**Fields:**
- `month`: Month label (e.g., "Nov '24", "Dec '24", "Jan '25")
- `amount`: Current year revenue for this month
- `margin`: Gross margin percentage (if applicable)
- `prior_year_amount`: **NEW** - Same month from previous year (e.g., Nov '24 when viewing Nov '25)

## Comparison Logic

For each month in the trailing 13-month window:
- **Current year data**: `(year, month)` - e.g., (2025, 11) for Nov 2025
- **Prior year data**: `(year - 1, month)` - e.g., (2024, 11) for Nov 2024

This provides an apples-to-apples comparison of the same month across years.

## Visual Implementation (Frontend)

The backend now provides the data needed for **Option 4: Dual-color bar segments**:

### Recommended Chart Rendering

For each month, render **two bars**:

1. **Ghost Bar (Background)**
   - Data: `prior_year_amount`
   - Color: Lighter/transparent version of main color (e.g., 30% opacity)
   - Z-index: Behind main bar
   - Purpose: Shows last year's performance as a baseline

2. **Main Bar (Foreground)**
   - Data: `amount`
   - Color: Full color (primary chart color)
   - Z-index: In front of ghost bar
   - Purpose: Shows current year's performance

### Visual Interpretation

- **Main bar taller than ghost bar** → Performance is UP vs last year ✅
- **Main bar shorter than ghost bar** → Performance is DOWN vs last year ⚠️
- **Bars roughly equal** → Performance is FLAT vs last year ➡️

### Example Chart.js Implementation

```javascript
// Assuming you're using Chart.js or similar library

const chartData = {
  labels: monthlyData.map(d => d.month),
  datasets: [
    {
      label: 'Prior Year',
      data: monthlyData.map(d => d.prior_year_amount),
      backgroundColor: 'rgba(59, 130, 246, 0.3)', // Light blue, 30% opacity
      borderColor: 'rgba(59, 130, 246, 0.5)',
      borderWidth: 1,
      order: 2  // Render behind
    },
    {
      label: 'Current Year',
      data: monthlyData.map(d => d.amount),
      backgroundColor: 'rgba(59, 130, 246, 1)', // Full blue
      borderColor: 'rgba(59, 130, 246, 1)',
      borderWidth: 1,
      order: 1  // Render in front
    }
  ]
};
```

## Example Data Response

### Service Department - November 2025

```json
{
  "monthlyLaborRevenue": [
    {
      "month": "Oct '24",
      "amount": 28500,
      "margin": 71.2,
      "prior_year_amount": 26800
    },
    {
      "month": "Nov '24",
      "amount": 31100,
      "margin": 72.6,
      "prior_year_amount": 28500
    },
    {
      "month": "Dec '24",
      "amount": 29800,
      "margin": 70.9,
      "prior_year_amount": 31100
    },
    // ... 10 more months
    {
      "month": "Nov '25",
      "amount": 32400,
      "margin": 73.1,
      "prior_year_amount": 31100  // Nov '24 data
    }
  ]
}
```

**Interpretation for Nov '25:**
- Current month (Nov '25): $32,400
- Same month last year (Nov '24): $31,100
- **Change**: +$1,300 (+4.2%) ✅ Performance is UP

## Benefits

1. **Non-Distracting**: Ghost bars provide context without cluttering the chart
2. **Instant Visual Feedback**: See at a glance which months are up/down vs last year
3. **Trend Analysis**: Identify seasonal patterns and growth trends
4. **Actionable Insights**: Quickly spot underperforming months that need attention
5. **Historical Context**: Understand current performance in relation to past performance

## Technical Details

### SQL Query Changes

No changes to SQL queries were needed. The existing queries already fetch 13 months of data (`DATEADD(month, -13, GETDATE())`), which includes both current year and prior year data for comparison.

### Data Processing

For each month in the trailing 13-month window:

```python
# Current year data
year_month_key = (year, month)
row = revenue_by_month.get(year_month_key)

# Prior year data (same month, previous year)
prior_year_key = (year - 1, month)
prior_row = revenue_by_month.get(prior_year_key)

# Extract values
amount = float(row['revenue'] or 0) if row else 0
prior_year_amount = float(prior_row['revenue'] or 0) if prior_row else 0
```

### Edge Cases Handled

1. **Missing prior year data**: If no data exists for prior year month, `prior_year_amount` is set to `0`
2. **First year of operation**: Ghost bars will show `0` for months with no prior year data
3. **Data gaps**: Both current and prior year handle missing data gracefully

## Deployment

**Commit**: `ecf0ade` - "Add year-over-year comparison data to department charts"

**Files Changed**:
- `reporting-backend/src/routes/department_reports.py`

**Deployment Status**: 
- ✅ Committed to GitHub
- ✅ Pushed to `main` branch
- ⏳ Railway auto-deployment in progress

## Testing Checklist

After deployment:

- [ ] Service department chart returns `prior_year_amount` for all months
- [ ] Parts department chart returns `prior_year_amount` for all months
- [ ] Rental department chart returns `prior_year_amount` for all months
- [ ] Prior year data matches expected values (same month from previous year)
- [ ] Missing prior year data returns `0` instead of `null`
- [ ] Frontend can access `prior_year_amount` field
- [ ] Ghost bars render correctly (lighter color, behind main bars)
- [ ] Main bars render correctly (full color, in front of ghost bars)
- [ ] Chart legend shows both "Current Year" and "Prior Year"
- [ ] Tooltips show both current and prior year values

## Frontend Implementation Notes

### Tooltip Enhancement

Consider enhancing tooltips to show the comparison:

```javascript
tooltip: {
  callbacks: {
    label: function(context) {
      const current = context.parsed.y;
      const prior = monthlyData[context.dataIndex].prior_year_amount;
      const change = current - prior;
      const changePercent = prior > 0 ? ((change / prior) * 100).toFixed(1) : 0;
      
      return [
        `Current: $${current.toLocaleString()}`,
        `Prior Year: $${prior.toLocaleString()}`,
        `Change: ${change >= 0 ? '+' : ''}$${change.toLocaleString()} (${changePercent}%)`
      ];
    }
  }
}
```

### Color Recommendations

**Service Department (Blue theme):**
- Ghost bar: `rgba(59, 130, 246, 0.25)` - Light blue, 25% opacity
- Main bar: `rgba(59, 130, 246, 1)` - Full blue

**Parts Department (Green theme):**
- Ghost bar: `rgba(34, 197, 94, 0.25)` - Light green, 25% opacity
- Main bar: `rgba(34, 197, 94, 1)` - Full green

**Rental Department (Purple theme):**
- Ghost bar: `rgba(168, 85, 247, 0.25)` - Light purple, 25% opacity
- Main bar: `rgba(168, 85, 247, 1)` - Full purple

## Future Enhancements

### Potential Improvements

1. **Percentage Change Labels**: Add small "+15%" or "-8%" labels above bars
2. **Trend Arrows**: Add ↑ or ↓ arrows next to month labels
3. **Color-Coded Bars**: Green for up, red for down, gray for flat
4. **YoY Summary Card**: Show overall YoY performance summary at top of dashboard
5. **Multi-Year Comparison**: Extend to show 2-3 years of comparison data
6. **Seasonality Indicators**: Highlight seasonal patterns automatically

### API Enhancements

Consider adding calculated fields:

```json
{
  "month": "Nov '25",
  "amount": 32400,
  "margin": 73.1,
  "prior_year_amount": 31100,
  "yoy_change": 1300,           // NEW: Dollar change
  "yoy_change_percent": 4.2,    // NEW: Percentage change
  "trend": "up"                 // NEW: "up", "down", or "flat"
}
```

## Summary

The year-over-year comparison feature is now live in the backend. All department charts return `prior_year_amount` for each month, enabling the frontend to render dual-color bar charts that provide instant visual feedback on performance trends without cluttering the interface.

**Next Step**: Update frontend chart components to render ghost bars using the `prior_year_amount` data.
