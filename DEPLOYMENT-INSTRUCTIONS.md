# Deployment Instructions - Customer Profitability Report

## What Was Built

A comprehensive **Customer Profitability Analysis** report that shows:
- All customers (not just maintenance contracts)
- Revenue vs. costs with margin analysis
- Health status indicators (Healthy/Warning/Critical)
- Actionable recommendations (price increases or termination)
- "Fire List" of unprofitable small accounts

## Files Changed

### Backend
- `reporting-backend/src/routes/department_reports.py` - Added new endpoint at line ~9311

### Frontend
- `reporting-frontend/src/components/CustomerProfitability.jsx` - New component
- `reporting-frontend/src/components/departments/ServiceReport.jsx` - Added new tab

### Documentation
- `customer-profitability-design.md` - Technical design document
- `CUSTOMER-PROFITABILITY-README.md` - User guide and features

## Deployment Steps

### 1. Backend Deployment
```bash
# Backend is already deployed - just needs restart
# The code is in the main branch (commit e475a42)
```

**Action Required**: Restart the backend service to load the new endpoint.

### 2. Frontend Deployment
```bash
cd reporting-frontend
npm run build
# Deploy build/ directory to Netlify
```

**Action Required**: Deploy the frontend to Netlify (or your hosting platform).

## Testing

### 1. Verify Backend Endpoint
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-backend-url/api/reports/departments/customer-profitability
```

Should return JSON with:
- `summary` object with metrics
- `customers` array with profitability data
- `fire_list` array with termination candidates

### 2. Verify Frontend
1. Log in to Softbase Reporting
2. Navigate to **Service** department
3. Click **Customer Profitability** tab
4. Should see:
   - Executive dashboard cards
   - Health distribution chart
   - Fire list (if any unprofitable small accounts)
   - Customer profitability table

## What to Expect

### Executive Dashboard
- Shows total customers, revenue, margin, and revenue at risk
- Color-coded metrics (green = good, yellow = warning, red = critical)

### Customer Table
Each customer shows:
- Revenue and costs
- Profit and margin %
- Health badge (Healthy/Warning/Critical)
- Action recommendation (Maintain/Monitor/Raise Prices/Urgent/Terminate)
- Specific price increase recommendation if applicable

### Fire List
- Customers with negative margin AND revenue < $10,000
- Shows loss amount per customer
- Sorted by worst losses first
- Collapsible to reduce clutter

## Key Features

### 1. Intelligent Recommendations
- **Margin ≥ 30%**: "Maintain current pricing"
- **Margin 15-30%**: "Consider X% price increase"
- **Margin 0-15%**: "X% price increase recommended"
- **Margin < 0% (large account)**: "Urgent - immediate X% increase required"
- **Margin < 0% (small account)**: "Consider termination"

### 2. Filters
- Date range: Trailing 12 months (default) or custom range
- Health status: All / Healthy / Warning / Critical
- Sortable columns: Click any header to sort

### 3. Data Quality
- Uses ShipTo customer (service location) as primary
- Falls back to BillTo customer name if ShipTo not in Customer table
- Same logic as Maintenance Contract Profitability report

## Known Issues

### Westrock Customer #77521
- This customer showed as "Unknown" in Maintenance Contract report
- Now shows as "Westrock (Location #77521)" with BillTo fallback
- Should be added to Customer table for proper tracking

### Missing Work Order Costs
- Customers with no work orders show $0 cost (100% margin)
- This is accurate but may be misleading for new customers
- Consider filtering by minimum invoice count if needed

## Next Steps

1. **Deploy backend** - Restart service to load new endpoint
2. **Deploy frontend** - Build and deploy to Netlify
3. **Test report** - Verify data looks correct
4. **Share with Jake** - Get feedback on recommendations
5. **Monitor usage** - Track which customers get price increases

## Support

For questions or issues:
- Review `CUSTOMER-PROFITABILITY-README.md` for features and use cases
- Review `customer-profitability-design.md` for technical details
- Check backend logs for API errors
- Check browser console for frontend errors

## Commits

- **e475a42**: Add Customer Profitability Analysis report
- **998072b**: Fix missing first_invoice and last_invoice fields
- **960c168**: Add BillTo customer name fallback for ShipTo locations

All changes are in the `main` branch and ready to deploy.
