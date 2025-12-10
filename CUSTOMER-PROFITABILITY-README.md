# Customer Profitability Analysis Report

## Overview
Comprehensive profitability analysis for **all customers** (not just maintenance contracts) showing revenue vs costs, margin analysis, health indicators, and actionable recommendations for pricing decisions and customer management.

## Features

### Executive Dashboard
- **Total Customers**: Count with health status breakdown (Healthy/Warning/Critical %)
- **Total Revenue**: 12-month revenue with total costs
- **Overall Margin**: Company-wide margin percentage with profit amount
- **Revenue at Risk**: Total revenue from unprofitable customers

### Customer Health Distribution
Visual breakdown of customers by profitability status:
- **Healthy** (Green): Margin ≥ 30%
- **Warning** (Yellow): Margin 0-30%
- **Critical** (Red): Margin < 0% (unprofitable)

### "Fire List" - Termination Candidates
Dedicated section highlighting unprofitable small accounts:
- **Criteria**: Margin < 0% AND Revenue < $10,000
- Shows loss amount per customer
- Sorted by worst losses first
- Collapsible to reduce clutter

### Customer Profitability Table
Detailed table for each customer showing:
- Customer name and number
- Total revenue (12 months)
- Total costs (labor + parts + misc)
- Gross profit
- Margin %
- Health status badge
- **Action recommendation** (Maintain / Monitor / Raise Prices / Urgent / Consider Termination)
- **Specific recommendation message** with price increase % if applicable

### Action Recommendations

The report provides intelligent recommendations based on margin:

| Margin Range | Action | Recommendation |
|--------------|--------|----------------|
| ≥ 30% | **Maintain** | Healthy profit margin - maintain current pricing |
| 15-30% | **Monitor** | Below industry standard - consider X% price increase |
| 0-15% | **Raise Prices** | Below acceptable margin - X% price increase recommended |
| < 0% (Revenue ≥ $10k) | **Urgent - Raise Prices** | Losing $X/year - immediate X% price increase required |
| < 0% (Revenue < $10k) | **Consider Termination** | Unprofitable small account - losing $X/year |

All price increase recommendations target **30% margin** (industry best practice).

### Filters & Controls
- **Date Range**: Trailing 12 months (default) or custom date range
- **Health Filter**: Filter by All / Healthy / Warning / Critical
- **Sortable Columns**: Click any column header to sort
- **Expandable Details**: Click rows to see cost breakdowns

## Data Sources

### Revenue
- **Table**: `ben002.InvoiceReg`
- **Scope**: ALL sale codes (not just FMBILL)
- **Period**: Trailing 12 months by default

### Costs
- **Labor**: `ben002.WOLabor` (hours × rates)
- **Parts**: `ben002.WOParts` (actual costs)
- **Misc**: `ben002.WOMisc` (miscellaneous costs)
- **Period**: Same as revenue period

### Customer Attribution
- **Primary**: ShipTo customer (service location)
- **Fallback**: BillTo customer name + "(Location #ShipTo)" if ShipTo not in Customer table
- Same logic as Maintenance Contract Profitability report

## API Endpoint

**Route**: `/api/reports/departments/customer-profitability`

**Method**: GET

**Query Parameters**:
- `start_date` (optional): Start of custom date range (YYYY-MM-DD)
- `end_date` (optional): End of custom date range (YYYY-MM-DD)
- `min_revenue` (optional): Filter customers by minimum revenue

**Example**:
```
GET /api/reports/departments/customer-profitability
GET /api/reports/departments/customer-profitability?start_date=2024-01-01&end_date=2024-12-31
GET /api/reports/departments/customer-profitability?min_revenue=5000
```

## Frontend Integration

**Location**: Service Report → "Customer Profitability" tab

**Component**: `/src/components/CustomerProfitability.jsx`

**Navigation**: 
1. Log in to Softbase Reporting
2. Go to **Service** department
3. Click **Customer Profitability** tab

## Key Metrics Explained

### Margin %
```
Margin = (Revenue - Total Cost) / Revenue × 100
```

### Recommended Price Increase
To achieve 30% target margin:
```
Target Revenue = Total Cost / (1 - 0.30)
Recommended Increase = Target Revenue - Current Revenue
Increase % = (Recommended Increase / Current Revenue) × 100
```

### Health Status
- **Healthy**: Margin ≥ 30% (industry best practice)
- **Warning**: Margin 0-30% (profitable but below standard)
- **Critical**: Margin < 0% (losing money)

## Use Cases

### 1. Identify Customers to Raise Prices
Filter by "Warning" or "Critical" status to see customers with below-standard margins. The report shows exactly how much to increase prices to hit 30% margin.

### 2. Find Customers to Terminate
Click "Show Fire List" to see unprofitable small accounts. These are candidates for termination or major price restructuring.

### 3. Monitor Overall Business Health
Executive dashboard shows company-wide margin and revenue at risk. Track this over time to ensure profitability is improving.

### 4. Benchmark Customer Performance
Sort by margin % to see best and worst performing customers. Use top performers as benchmarks for pricing.

### 5. Quarterly Business Reviews
Use the report in QBRs to show leadership which customers are profitable and which need attention.

## Deployment

### Backend
```bash
cd reporting-backend
git pull origin main
# Restart backend service
```

### Frontend
```bash
cd reporting-frontend
git pull origin main
npm run build
# Deploy to Netlify or hosting platform
```

## Technical Notes

### Performance Considerations
- Report queries all invoices and work orders for the date range
- For large datasets (>10,000 customers), consider adding pagination
- Indexes on `ShipTo`, `InvoiceDate`, `DateCompleted` recommended

### Data Quality
- Customers with no work orders show $0 cost (100% margin)
- Work orders without labor/parts show $0 cost
- Missing customer records use BillTo fallback

### Future Enhancements (v2)
- Trend analysis (3mo, 6mo, 12mo comparison)
- Customer segmentation by industry/region
- What-if pricing scenarios
- Customer lifetime value calculation
- Export to Excel/PDF
- Email alerts for critical customers

## Support

For questions or issues:
- Check the design document: `customer-profitability-design.md`
- Review the backend code: `reporting-backend/src/routes/department_reports.py` (line ~9311+)
- Review the frontend code: `reporting-frontend/src/components/CustomerProfitability.jsx`

## Changelog

### v1.0 (December 2024)
- Initial release
- Executive dashboard with health metrics
- Customer profitability table with action recommendations
- Fire list for termination candidates
- Date range filtering
- Health status filtering
- Sortable columns
- BillTo customer name fallback
