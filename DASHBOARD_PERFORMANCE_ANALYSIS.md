# Dashboard Performance Analysis & Optimization Recommendations

## Executive Summary

The main dashboard endpoint (`/api/reports/dashboard/summary-optimized`) takes approximately **30 seconds** on the first fetch. This analysis identifies the root causes and provides actionable optimization strategies.

## Current Architecture

### What's Already Good ✅

1. **Parallel Query Execution**: Using `ThreadPoolExecutor` with 10 workers to run queries concurrently
2. **Caching Layer**: Redis/in-memory cache with 1-hour TTL for all dashboard queries
3. **Cache Key Strategy**: Month-based cache keys (`dashboard:{key}:{YYYY-MM}`)
4. **Optimized CTEs**: Work order queries use CTEs to pre-aggregate labor, parts, and misc totals

### The Problem: First Load Performance

The 30-second delay occurs because:
1. **18 separate queries** are executed on first load (even in parallel)
2. **No warm-up mechanism** - cache is cold after server restart or month rollover
3. **Complex GL queries** scan large `GLDetail` table with many account filters
4. **Multiple table scans** - same tables (WOLabor, WOParts, WOMisc) are scanned repeatedly

---

## Optimization Strategies

### Strategy 1: Background Cache Warming (Recommended - High Impact)

**Problem**: First user of the day/month waits 30 seconds.

**Solution**: Pre-warm the cache on server startup and schedule periodic refreshes.

```python
# Add to app.py or create a new file: src/services/cache_warmer.py

from apscheduler.schedulers.background import BackgroundScheduler
from src.routes.dashboard_optimized import DashboardQueries
from src.services.azure_sql_service import AzureSQLService
from src.services.cache_service import cache_service
import logging

logger = logging.getLogger(__name__)

def warm_dashboard_cache():
    """Pre-warm all dashboard cache entries"""
    logger.info("🔥 Starting dashboard cache warm-up...")
    try:
        db = AzureSQLService()
        queries = DashboardQueries(db)
        
        # Force refresh all cached queries
        cache_service.cache_query('dashboard:total_sales:...', queries.get_current_month_sales, 3600, force_refresh=True)
        cache_service.cache_query('dashboard:ytd_sales:...', queries.get_ytd_sales, 3600, force_refresh=True)
        # ... repeat for all 18 queries
        
        logger.info("✅ Dashboard cache warm-up complete")
    except Exception as e:
        logger.error(f"Cache warm-up failed: {str(e)}")

def init_cache_warmer(app):
    """Initialize background cache warmer"""
    scheduler = BackgroundScheduler()
    
    # Warm cache on startup (after 30 second delay to let server fully start)
    scheduler.add_job(warm_dashboard_cache, 'date', run_date=datetime.now() + timedelta(seconds=30))
    
    # Refresh cache every 55 minutes (before 1-hour TTL expires)
    scheduler.add_job(warm_dashboard_cache, 'interval', minutes=55)
    
    # Warm cache at midnight for new day's data
    scheduler.add_job(warm_dashboard_cache, 'cron', hour=0, minute=5)
    
    scheduler.start()
```

**Expected Impact**: Eliminates 30-second wait for most users.

---

### Strategy 2: Consolidated GL Query (High Impact)

**Problem**: Multiple queries hit the `GLDetail` table with similar filters.

**Current**: 4 separate GL queries for:
- `get_monthly_sales` (all departments)
- `get_monthly_sales_excluding_equipment` (non-equipment)
- `get_monthly_equipment_sales` (equipment only)
- `get_monthly_sales_by_stream` (service/parts/rental breakdown)

**Solution**: Single consolidated query that returns all breakdowns at once.

```python
def get_all_monthly_sales_data(self):
    """Consolidated query for all monthly sales breakdowns"""
    query = f"""
    SELECT 
        YEAR(EffectiveDate) as year,
        MONTH(EffectiveDate) as month,
        -- All departments revenue
        -SUM(CASE WHEN AccountNo IN ({all_revenue_list}) THEN Amount ELSE 0 END) as total_revenue,
        -SUM(CASE WHEN AccountNo IN ({all_cost_list}) THEN Amount ELSE 0 END) as total_cost,
        -- Non-equipment revenue
        -SUM(CASE WHEN AccountNo IN ({non_equip_revenue_list}) THEN Amount ELSE 0 END) as non_equip_revenue,
        -SUM(CASE WHEN AccountNo IN ({non_equip_cost_list}) THEN Amount ELSE 0 END) as non_equip_cost,
        -- Equipment only
        -SUM(CASE WHEN AccountNo IN ({equip_revenue_list}) THEN Amount ELSE 0 END) as equip_revenue,
        -SUM(CASE WHEN AccountNo IN ({equip_cost_list}) THEN Amount ELSE 0 END) as equip_cost,
        -- Service breakdown
        -SUM(CASE WHEN AccountNo IN ({service_rev_list}) THEN Amount ELSE 0 END) as service_revenue,
        -- Parts breakdown
        -SUM(CASE WHEN AccountNo IN ({parts_rev_list}) THEN Amount ELSE 0 END) as parts_revenue,
        -- Rental breakdown
        -SUM(CASE WHEN AccountNo IN ({rental_rev_list}) THEN Amount ELSE 0 END) as rental_revenue
    FROM ben002.GLDetail
    WHERE AccountNo IN ({all_accounts})
        AND EffectiveDate >= DATEADD(month, -13, GETDATE())
        AND Posted = 1
    GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
    ORDER BY year, month
    """
```

**Expected Impact**: Reduces 4 queries to 1, saving ~3-5 seconds.

---

### Strategy 3: Materialized Work Order Totals View (Medium-High Impact)

**Problem**: Multiple queries calculate `WOLabor + WOParts + WOMisc` totals.

**Solution**: Create a database view or indexed view that pre-calculates work order totals.

```sql
-- Create indexed view for work order totals (run once on database)
CREATE VIEW ben002.vw_WorkOrderTotals
WITH SCHEMABINDING
AS
SELECT 
    w.WONo,
    w.Type,
    w.OpenDate,
    w.CompletedDate,
    w.ClosedDate,
    w.InvoiceDate,
    w.BillTo,
    COALESCE(l.labor_total, 0) as labor_total,
    COALESCE(p.parts_total, 0) as parts_total,
    COALESCE(m.misc_total, 0) as misc_total,
    COALESCE(l.labor_total, 0) + COALESCE(p.parts_total, 0) + COALESCE(m.misc_total, 0) as total_value
FROM ben002.WO w
LEFT JOIN (
    SELECT WONo, SUM(Sell) as labor_total FROM ben002.WOLabor GROUP BY WONo
) l ON w.WONo = l.WONo
LEFT JOIN (
    SELECT WONo, SUM(Sell * Qty) as parts_total FROM ben002.WOParts GROUP BY WONo
) p ON w.WONo = p.WONo
LEFT JOIN (
    SELECT WONo, SUM(Sell) as misc_total FROM ben002.WOMisc GROUP BY WONo
) m ON w.WONo = m.WONo;

-- Create unique clustered index for indexed view
CREATE UNIQUE CLUSTERED INDEX IX_WorkOrderTotals_WONo 
ON ben002.vw_WorkOrderTotals(WONo);
```

**Expected Impact**: Reduces work order query time by 50-70%.

---

### Strategy 4: Database Index Recommendations (Medium Impact)

Add indexes on frequently filtered columns:

```sql
-- GLDetail indexes
CREATE INDEX IX_GLDetail_EffectiveDate_AccountNo 
ON ben002.GLDetail(EffectiveDate, AccountNo) 
INCLUDE (Amount, Posted);

-- InvoiceReg indexes
CREATE INDEX IX_InvoiceReg_InvoiceDate_BillToName 
ON ben002.InvoiceReg(InvoiceDate, BillToName) 
INCLUDE (GrandTotal, InvoiceNo);

-- WO indexes
CREATE INDEX IX_WO_OpenDate_Type 
ON ben002.WO(OpenDate, Type) 
INCLUDE (CompletedDate, ClosedDate, InvoiceDate);

CREATE INDEX IX_WO_CompletedDate_Type 
ON ben002.WO(CompletedDate, Type) 
WHERE CompletedDate IS NOT NULL;
```

**Expected Impact**: 20-40% improvement on individual queries.

---

### Strategy 5: Progressive Loading (Frontend - Medium Impact)

**Problem**: User sees nothing until all 18 queries complete.

**Solution**: Load critical metrics first, then load charts progressively.

```jsx
// Dashboard.jsx - Progressive loading approach
const fetchDashboardData = async () => {
  setLoading(true);
  
  // Phase 1: Load KPIs immediately (fast queries)
  const kpiResponse = await fetch(apiUrl('/api/reports/dashboard/kpis'));
  if (kpiResponse.ok) {
    const kpiData = await kpiResponse.json();
    setKpiData(kpiData);
    setLoading(false); // Show KPIs immediately
  }
  
  // Phase 2: Load charts in background
  setChartsLoading(true);
  const chartsResponse = await fetch(apiUrl('/api/reports/dashboard/charts'));
  if (chartsResponse.ok) {
    const chartsData = await chartsResponse.json();
    setChartsData(chartsData);
    setChartsLoading(false);
  }
};
```

**Backend**: Split endpoint into `/kpis` (fast) and `/charts` (slower).

**Expected Impact**: Perceived load time drops to 2-5 seconds.

---

### Strategy 6: Reduce Query Scope (Quick Win)

**Current**: Some queries look back 13 months or scan all historical data.

**Optimization**: For real-time dashboard, limit to current month + last month comparison.

```python
# Instead of 13 months for monthly_sales
AND EffectiveDate >= DATEADD(month, -13, GETDATE())

# Use 3 months for initial load, lazy-load more on demand
AND EffectiveDate >= DATEADD(month, -3, GETDATE())
```

**Expected Impact**: 30-50% reduction in query time for affected queries.

---

## Implementation Priority

| Priority | Strategy | Effort | Impact | Time Saved |
|----------|----------|--------|--------|------------|
| 1 | Background Cache Warming | Low | High | ~25-30s |
| 2 | Progressive Loading | Medium | High | Perceived: ~25s |
| 3 | Consolidated GL Query | Medium | Medium-High | ~3-5s |
| 4 | Database Indexes | Low | Medium | ~5-10s |
| 5 | Materialized View | Medium | Medium | ~3-5s |
| 6 | Reduce Query Scope | Low | Low-Medium | ~2-3s |

---

## Quick Win: Implement Cache Warming First

The fastest path to improvement:

1. **Add APScheduler dependency**: `pip install apscheduler`
2. **Create cache warmer service**
3. **Initialize on app startup**
4. **Schedule periodic refresh**

This alone should eliminate the 30-second wait for 95%+ of users.

---

## Files to Modify

| File | Changes |
|------|---------|
| `reporting-backend/requirements.txt` | Add `apscheduler` |
| `reporting-backend/src/services/cache_warmer.py` | New file - cache warming logic |
| `reporting-backend/src/app.py` | Initialize cache warmer on startup |
| `reporting-backend/src/routes/dashboard_optimized.py` | Consolidate GL queries (optional) |
| `reporting-frontend/src/components/Dashboard.jsx` | Progressive loading (optional) |

---

## Monitoring Recommendations

After implementing optimizations:

1. **Log query times**: Already implemented (`query_time` in response)
2. **Track cache hit rate**: Add metric for cache hits vs misses
3. **Monitor slow queries**: Set up alerts for queries > 5 seconds
4. **Database query plans**: Review execution plans for slowest queries

---

## Next Steps

1. **Approve Strategy 1 (Cache Warming)** - I can implement this immediately
2. **Review database indexes** - May need DBA approval for production
3. **Test progressive loading** - Requires frontend changes
4. **Consider materialized view** - Requires database schema change

Would you like me to implement the cache warming solution first?
