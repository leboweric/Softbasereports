# Customer Profitability Analysis Report - Design Document

## Overview
Comprehensive profitability analysis for all customers showing revenue, costs, margins, and actionable recommendations.

## Data Model

### Revenue Sources
- **Table**: `ben002.InvoiceReg`
- **Key Fields**: ShipTo (customer), InvoiceDate, GrandTotal
- **Filter**: Last 12 months (trailing)
- **Grouping**: By ShipTo customer

### Cost Sources

#### Labor Costs
- **Table**: `ben002.WorkOrderLabor`
- **Join**: WorkOrder table for customer and date
- **Calculation**: Hours × LaborRate (or standard rate if not specified)
- **Filter**: Last 12 months matching revenue period

#### Parts Costs
- **Table**: `ben002.WorkOrderParts`
- **Join**: WorkOrder table for customer and date
- **Calculation**: Sum of part costs
- **Filter**: Last 12 months matching revenue period

### Customer Information
- **Table**: `ben002.Customer`
- **Join**: On ShipTo number
- **Fallback**: Use BillTo customer name if ShipTo not in Customer table

## Metrics & Calculations

### Core Metrics
```
Total Revenue = SUM(InvoiceReg.GrandTotal)
Total Labor Cost = SUM(WorkOrderLabor.Hours × LaborRate)
Total Parts Cost = SUM(WorkOrderParts.Cost)
Total Cost = Labor Cost + Parts Cost
Gross Profit = Revenue - Total Cost
Margin % = (Gross Profit / Revenue) × 100
```

### Health Status
- **Healthy**: Margin >= 30%
- **Warning**: Margin 0-30%
- **Critical**: Margin < 0%

### Action Recommendations

```python
if margin >= 30:
    action = "Maintain"
    message = "Healthy profit margin - maintain current pricing"
    
elif margin >= 15:
    action = "Monitor"
    message = "Acceptable margin but below industry standard (30%)"
    recommended_increase = calculate_increase_for_30_margin()
    
elif margin >= 0:
    action = "Raise Prices"
    message = "Below acceptable margin - price increase recommended"
    recommended_increase = calculate_increase_for_30_margin()
    
else:  # margin < 0
    if revenue > 10000:  # Threshold for "significant" customer
        action = "Urgent - Raise Prices"
        message = f"Losing ${abs(profit):,.2f} per year - immediate action required"
        recommended_increase = calculate_increase_for_30_margin()
    else:
        action = "Consider Termination"
        message = f"Unprofitable small account - losing ${abs(profit):,.2f} per year"
```

## SQL Query Structure

### Main Customer Query
```sql
SELECT
    i.ShipTo as customer_number,
    COALESCE(c.Name, bc.Name + ' (Location #' + i.ShipTo + ')', 'Unknown') as customer_name,
    COUNT(DISTINCT i.InvoiceNo) as invoice_count,
    MIN(i.InvoiceDate) as first_invoice,
    MAX(i.InvoiceDate) as last_invoice,
    SUM(i.GrandTotal) as total_revenue
FROM ben002.InvoiceReg i
LEFT JOIN ben002.Customer c ON i.ShipTo = c.Number
LEFT JOIN ben002.Customer bc ON i.BillTo = bc.Number
WHERE i.InvoiceDate >= DATEADD(month, -12, GETDATE())
    AND i.ShipTo IS NOT NULL
    AND i.ShipTo != ''
GROUP BY i.ShipTo, c.Name, bc.Name
ORDER BY total_revenue DESC
```

### Labor Costs by Customer
```sql
SELECT
    wo.ShipTo as customer_number,
    SUM(wol.Hours * COALESCE(wol.LaborRate, 75)) as total_labor_cost
FROM ben002.WorkOrder wo
INNER JOIN ben002.WorkOrderLabor wol ON wo.WorkOrder = wol.WorkOrder
WHERE wo.DateCompleted >= DATEADD(month, -12, GETDATE())
    AND wo.ShipTo IS NOT NULL
    AND wo.ShipTo != ''
GROUP BY wo.ShipTo
```

### Parts Costs by Customer
```sql
SELECT
    wo.ShipTo as customer_number,
    SUM(COALESCE(wop.Cost, 0) * COALESCE(wop.Quantity, 1)) as total_parts_cost
FROM ben002.WorkOrder wo
INNER JOIN ben002.WorkOrderParts wop ON wo.WorkOrder = wop.WorkOrder
WHERE wo.DateCompleted >= DATEADD(month, -12, GETDATE())
    AND wo.ShipTo IS NOT NULL
    AND wo.ShipTo != ''
GROUP BY wo.ShipTo
```

## Frontend Components

### Executive Summary Cards
- Total Customers Analyzed
- Healthy Customers (count + %)
- Warning Customers (count + %)
- Critical Customers (count + %)
- Total Revenue at Risk (from unprofitable customers)

### Customer Table
Columns:
- Customer Name & Number
- Total Revenue (12mo)
- Total Costs (12mo)
- Gross Profit
- Margin %
- Health Status Badge
- Action Recommendation
- Expandable details

### Filters & Controls
- Date range selector (default: trailing 12 months)
- Health status filter (All / Healthy / Warning / Critical)
- Sort options (Margin, Revenue, Profit)
- Search by customer name

### "Fire List" Section
Dedicated section showing customers meeting termination criteria:
- Margin < 0%
- Revenue < $10,000
- Sorted by loss amount (worst first)

## API Endpoint

**Route**: `/api/department-reports/customer-profitability`

**Method**: GET

**Query Parameters**:
- `start_date` (optional): Start of date range
- `end_date` (optional): End of date range
- `min_revenue` (optional): Filter customers by minimum revenue

**Response**:
```json
{
  "summary": {
    "total_customers": 150,
    "healthy_count": 90,
    "warning_count": 45,
    "critical_count": 15,
    "total_revenue": 2500000,
    "total_cost": 1800000,
    "total_profit": 700000,
    "overall_margin": 28.0,
    "revenue_at_risk": 125000
  },
  "customers": [
    {
      "customer_number": "12345",
      "customer_name": "ABC Company",
      "invoice_count": 24,
      "first_invoice": "2024-01-15",
      "last_invoice": "2024-12-08",
      "total_revenue": 45000,
      "total_labor_cost": 18000,
      "total_parts_cost": 8000,
      "total_cost": 26000,
      "gross_profit": 19000,
      "margin_percent": 42.2,
      "health_status": "healthy",
      "action": "Maintain",
      "message": "Healthy profit margin - maintain current pricing",
      "recommended_increase": null
    }
  ]
}
```

## Implementation Notes

1. **Default labor rate**: Use $75/hour if LaborRate not specified in WorkOrderLabor
2. **Date filtering**: Use trailing 12 months by default, allow custom ranges
3. **Customer fallback**: Same logic as Maintenance Contract report (BillTo fallback)
4. **Performance**: Consider adding indexes on ShipTo, InvoiceDate, DateCompleted
5. **Revenue threshold**: Use $10,000 as threshold for "significant" customer (configurable)

## Future Enhancements (v2)

- Trend analysis (3mo, 6mo, 12mo comparison)
- Customer segmentation by industry/region
- What-if pricing scenarios
- Customer lifetime value calculation
- Service call frequency analysis
- Comparison to industry benchmarks
