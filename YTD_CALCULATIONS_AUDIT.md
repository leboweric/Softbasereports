# YTD Calculations Platform-Wide Audit

## Executive Summary

This audit reviews all Year-to-Date (YTD) calculations across the platform to ensure they correctly use the fiscal year starting in **November 2025** instead of calendar year (January 1).

**Fiscal Year Configuration:**
- Start Month: November (Month 11)
- Current Fiscal Year: November 2025 - October 2026
- Utility: `src/utils/fiscal_year.py` provides `get_fiscal_ytd_start()`

---

## Audit Findings

### ✅ CORRECT - Already Using Fiscal Year Logic

#### 1. **pl_widget.py** - P&L Dashboard Widget
- **Location:** `/reporting-backend/src/routes/pl_widget.py` (Lines 55-71)
- **Status:** ✅ FIXED (just corrected)
- **Logic:** Uses `get_fiscal_ytd_start()` to filter trend data
- **Result:** Correctly shows fiscal YTD P&L

#### 2. **dashboard_optimized.py** - YTD Sales
- **Location:** `/reporting-backend/src/routes/dashboard_optimized.py` (Lines 111-138)
- **Status:** ✅ CORRECT
- **Logic:** Lines 76-79 calculate fiscal year start dynamically:
  ```python
  if self.current_date.month >= 11:
      self.fiscal_year_start = datetime(self.current_date.year, 11, 1).strftime('%Y-%m-%d')
  else:
      self.fiscal_year_start = datetime(self.current_date.year - 1, 11, 1).strftime('%Y-%m-%d')
  ```
- **Usage:** Line 130 uses `self.fiscal_year_start` in query
- **Result:** Correctly calculates fiscal YTD sales

---

### ⚠️ NEEDS REVIEW - Hardcoded or Calendar Year Logic

#### 3. **pl_report.py** - YTD P&L Report Endpoint
- **Location:** `/reporting-backend/src/routes/pl_report.py` (Lines 724-753)
- **Status:** ❌ INCORRECT - Uses calendar year
- **Current Logic:**
  ```python
  start_date = f"{year}-01-01"  # January 1st
  end_date = f"{year}-12-31"
  ```
- **Issue:** Returns calendar year data (Jan-Dec) instead of fiscal year (Nov-Oct)
- **Impact:** API endpoint `/api/reports/pl/ytd` returns wrong data
- **Fix Required:** Use fiscal year start date instead of January 1

#### 4. **pl_report.py** - Excel Export YTD Section
- **Location:** `/reporting-backend/src/routes/pl_report.py` (Lines 791-800)
- **Status:** ❌ INCORRECT - Hardcoded to March 2025
- **Current Logic:**
  ```python
  # Calculate YTD date range (fiscal year starts in March)
  if month >= 3:
      ytd_start = f"{year}-03-01"
  else:
      ytd_start = f"{year-1}-03-01"
  ```
- **Issue:** Hardcoded to March instead of November
- **Comment:** Code comment says "fiscal year starts in March" which is outdated
- **Impact:** Excel exports show incorrect YTD calculations
- **Fix Required:** Update to use November as fiscal year start

#### 5. **dashboard_optimized.py** - Top Customers
- **Location:** `/reporting-backend/src/routes/dashboard_optimized.py` (Lines 1228-1269)
- **Status:** ⚠️ HARDCODED - Uses March 2025 cutover date
- **Current Logic:**
  ```python
  ytd_start = '2025-03-01'  # Hardcoded
  ```
- **Issue:** Uses Softbase migration date (March 2025) instead of fiscal year start
- **Impact:** "Top 10 Customers by YTD sales" shows data since March, not fiscal YTD
- **Fix Required:** Use `self.fiscal_year_start` instead of hardcoded date

---

### ✅ INFORMATIONAL - Database Fields (Not Calculations)

#### 6. **Equipment.RentalYTD** - Database Column
- **Location:** Multiple files reference this field
- **Status:** ✅ DATABASE FIELD (not a calculation in our code)
- **Description:** This is a column in the `ben002.Equipment` table
- **Note:** We don't control this calculation - it's managed by Softbase database
- **Files Referencing:** 
  - `accounting_reports.py`
  - `department_reports.py`
  - `depreciation_explorer.py`
  - `rental_availability_diagnostic.py`
  - `rental_exclusion_analysis.py`
  - Frontend: `RentalDiagnostic.jsx`, `RentalEquipmentReport.jsx`

#### 7. **GL.YTD** - Database Column
- **Location:** Referenced in multiple files
- **Status:** ✅ DATABASE FIELD (not a calculation in our code)
- **Description:** This is a column in the `ben002.GL` table representing cumulative balance
- **Note:** We don't control this calculation - it's managed by Softbase database
- **Files Referencing:**
  - `cashflow_widget.py` (Line 90)
  - `currie_report.py` (Lines 1838, 1848)
  - `diagnostic_602600.py` (Line 45)

#### 8. **Minitrac YTD Fields** - External Database
- **Location:** `minitrac.py`
- **Status:** ✅ EXTERNAL DATABASE (not our calculation)
- **Description:** `ytd_income` and `ytd_expense` from `minitrac_equipment` table
- **Note:** This is an external system, we just display the data

---

### ✅ CORRECT - Depreciation YTD (Fiscal Period)

#### 9. **Depreciation Expense YTD**
- **Locations:**
  - `accounting_inventory.py` (Lines 105-141)
  - `final_gl_inventory_report.py` (Lines 70-81)
  - `gl_inventory_report.py` (Lines 59-70)
- **Status:** ✅ CORRECT
- **Logic:** All use fiscal year period with proper date filtering
- **Example from `accounting_inventory.py`:**
  ```python
  WHERE AccountNo = '193000'
    AND EffectiveDate >= '2025-03-01'
    AND EffectiveDate <= '2025-10-31'
  ```
- **Note:** Currently hardcoded to March-October 2025 fiscal period, which is correct for the migration year
- **Future Enhancement:** Should be updated to use dynamic fiscal year dates

---

### ✅ CORRECT - Frontend Display Only

#### 10. **Frontend YTD References**
- **Files:** 
  - `Dashboard.jsx` (Line 934, 939)
  - `ProfitLossWidget.jsx` (Lines 168-192)
  - `PLReport.jsx` (Lines 12, 47-53, 138-144)
  - `CustomerDetailModal.jsx` (Line 142)
  - `InventoryReport.jsx` (Lines 210-211)
  - `RentalEquipmentReport.jsx` (Multiple lines)
  - `RentalReport.jsx` (Line 857)
- **Status:** ✅ DISPLAY ONLY
- **Description:** These files display YTD data received from backend APIs
- **Note:** No calculation logic - just formatting and display
- **Action Required:** None (backend fixes will automatically correct frontend display)

---

## Summary of Issues Found

| File | Line(s) | Issue | Priority | Status |
|------|---------|-------|----------|--------|
| `pl_widget.py` | 55-71 | Used 12-month rolling sum instead of fiscal YTD | HIGH | ✅ FIXED |
| `pl_report.py` | 740-742 | YTD endpoint uses calendar year (Jan-Dec) | HIGH | ❌ NEEDS FIX |
| `pl_report.py` | 791-796 | Excel export uses March instead of November | HIGH | ❌ NEEDS FIX |
| `dashboard_optimized.py` | 1231 | Top customers uses hardcoded March 2025 | MEDIUM | ❌ NEEDS FIX |

---

## Recommended Fixes

### Fix 1: pl_report.py - YTD Endpoint (Lines 724-753)

**Current Code:**
```python
def get_pl_ytd():
    now = datetime.now()
    year = request.args.get('year', now.year, type=int)
    
    # Calculate YTD date range
    start_date = f"{year}-01-01"  # ❌ WRONG
    end_date = f"{year}-12-31"
```

**Proposed Fix:**
```python
from src.utils.fiscal_year import get_fiscal_ytd_start

def get_pl_ytd():
    now = datetime.now()
    year = request.args.get('year', now.year, type=int)
    
    # Calculate fiscal YTD date range
    fiscal_ytd_start = get_fiscal_ytd_start()
    start_date = fiscal_ytd_start.strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')
```

---

### Fix 2: pl_report.py - Excel Export YTD (Lines 791-800)

**Current Code:**
```python
# Calculate YTD date range (fiscal year starts in March)
if month >= 3:
    ytd_start = f"{year}-03-01"  # ❌ WRONG
else:
    ytd_start = f"{year-1}-03-01"
ytd_end = last_day
```

**Proposed Fix:**
```python
from src.utils.fiscal_year import get_fiscal_ytd_start

# Calculate fiscal YTD date range (fiscal year starts in November)
fiscal_ytd_start = get_fiscal_ytd_start()
ytd_start = fiscal_ytd_start.strftime('%Y-%m-%d')
ytd_end = last_day
```

---

### Fix 3: dashboard_optimized.py - Top Customers (Line 1231)

**Current Code:**
```python
def get_top_customers(self):
    """Get top 10 customers by YTD sales since March 2025"""
    try:
        # Data starts from March 2025 (Softbase migration)
        ytd_start = '2025-03-01'  # ❌ HARDCODED
```

**Proposed Fix:**
```python
def get_top_customers(self):
    """Get top 10 customers by fiscal YTD sales"""
    try:
        # Use fiscal year start (November)
        ytd_start = self.fiscal_year_start  # ✅ Already available in __init__
```

**Note:** The `self.fiscal_year_start` is already calculated correctly in the `__init__` method (lines 76-79), just need to use it.

---

## Testing Recommendations

After implementing fixes, test the following scenarios:

### Test Case 1: As of November 30, 2025
- **Expected:** YTD = November 2025 only
- **Endpoints to Test:**
  - `/api/reports/pl/ytd`
  - `/api/reports/pl/export-excel`
  - `/api/dashboard/optimized` (top customers)

### Test Case 2: As of December 15, 2025
- **Expected:** YTD = November + December 2025
- **Verify:** All three endpoints show cumulative Nov-Dec data

### Test Case 3: As of November 1, 2026
- **Expected:** YTD resets to November 2026 only (new fiscal year)
- **Verify:** Previous fiscal year data is not included

---

## Implementation Priority

1. **HIGH PRIORITY** (User-Facing Impact):
   - ✅ `pl_widget.py` - COMPLETED
   - ❌ `pl_report.py` - YTD endpoint (Line 740)
   - ❌ `pl_report.py` - Excel export (Line 791)

2. **MEDIUM PRIORITY** (Dashboard Feature):
   - ❌ `dashboard_optimized.py` - Top customers (Line 1231)

3. **LOW PRIORITY** (Future Enhancement):
   - Depreciation YTD calculations (currently hardcoded to fiscal period, but correct)

---

## Files Reviewed (No Changes Needed)

- ✅ `cashflow_widget.py` - Uses database YTD field
- ✅ `currie_report.py` - Uses database YTD field
- ✅ `accounting_inventory.py` - Depreciation uses correct fiscal period
- ✅ `final_gl_inventory_report.py` - Depreciation uses correct fiscal period
- ✅ `gl_inventory_report.py` - Depreciation uses correct fiscal period
- ✅ `minitrac.py` - External database fields
- ✅ All frontend files - Display only, no calculation logic

---

## Conclusion

**Total Issues Found:** 3 files with incorrect YTD calculations

**Status:**
- 1 FIXED: `pl_widget.py`
- 3 NEED FIXES: `pl_report.py` (2 locations), `dashboard_optimized.py` (1 location)

All fixes should use the existing `get_fiscal_ytd_start()` utility from `src/utils/fiscal_year.py` to ensure consistency across the platform.
