# Mobile-Friendliness Improvements To-Do List

**Created:** Dec 31, 2025  
**Status:** In Progress

---

## Priority 1: Critical (Touch Targets & Accessibility)

### UI Component Updates

- [ ] **Update Button component touch targets**
  - File: `src/components/ui/button.jsx`
  - Change default height from `h-9` (36px) to `h-11` (44px) for mobile
  - Consider adding a mobile-specific size variant
  - Ensure all button variants meet 44x44px minimum touch target

- [ ] **Update Input component touch targets**
  - File: `src/components/ui/input.jsx`
  - Change height from `h-9` (36px) to `h-11` (44px) for mobile
  - Ensure adequate padding for touch interaction

- [ ] **Update Select component touch targets**
  - File: `src/components/ui/select.jsx`
  - Ensure SelectTrigger meets minimum touch target size
  - Verify SelectItem has adequate touch targets in dropdown

---

## Priority 2: High (Table Optimization)

### Table Mobile Improvements

- [ ] **Audit all table usages across components**
  - Identify tables with many columns that are problematic on mobile
  - Document which tables need mobile-specific treatment

- [ ] **Implement mobile-friendly table patterns**
  - [ ] Add column prioritization for mobile (show/hide columns)
  - [ ] Consider card-based layout transformation for key tables
  - [ ] Ensure all tables have `overflow-x-auto` wrapper

- [ ] **High-priority table components to address:**
  - [ ] `src/components/Dashboard.jsx` - Customer tables
  - [ ] `src/components/SalesCommissionReport.jsx` - Commission tables
  - [ ] `src/components/departments/ServiceReport.jsx` - Work order tables
  - [ ] `src/components/departments/PartsReport.jsx` - Parts tables
  - [ ] `src/components/departments/AccountingReport.jsx` - Financial tables
  - [ ] `src/components/ServiceInvoiceBilling.jsx` - Invoice table (min-w-[1800px])

---

## Priority 3: Medium (Layout & Navigation)

### Dashboard & Report Layouts

- [ ] **Simplify Dashboard mobile layout**
  - File: `src/components/Dashboard.jsx`
  - [ ] Review grid layouts (`md:grid-cols-2 lg:grid-cols-4`)
  - [ ] Ensure single-column layout on mobile
  - [ ] Prioritize critical metrics at top

- [ ] **Optimize TabsList for mobile**
  - Files: Multiple components using tabs
  - [ ] `Dashboard.jsx` - 5 tabs in grid
  - [ ] `AIQueryTester.jsx` - 6 tabs in grid
  - [ ] `KnowledgeBase.jsx` - 4 tabs in grid
  - [ ] Consider horizontal scrolling tabs or dropdown for mobile

- [ ] **Review header section on mobile**
  - File: `src/components/Dashboard.jsx` (lines 841-876)
  - [ ] Stack header elements vertically on mobile
  - [ ] Ensure action buttons are accessible

### Dialog & Modal Improvements

- [ ] **Audit dialog/modal mobile behavior**
  - [ ] `CustomerDetailModal.jsx` - max-w-5xl may be too wide
  - [ ] `MinitracSearch.jsx` - max-w-4xl dialog
  - [ ] Ensure modals are full-screen or near-full on mobile

---

## Priority 4: Standard (Text & Spacing)

### Text Readability

- [ ] **Audit text-xs usage**
  - Current count: 439 occurrences
  - [ ] Review and increase size where text is critical information
  - [ ] Ensure minimum 14px font size for body text on mobile

- [ ] **Review text-sm usage**
  - Current count: 923 occurrences
  - [ ] Verify readability on small mobile screens

### Spacing Standardization

- [ ] **Create consistent spacing system**
  - [ ] Document standard padding values for mobile
  - [ ] Document standard gap values for mobile
  - [ ] Apply consistently across components

---

## Priority 5: Enhancement (Charts & Visualization)

### Chart Mobile Optimization

- [ ] **Review chart configurations**
  - [ ] Ensure all charts use `ResponsiveContainer`
  - [ ] Verify chart labels are readable on mobile
  - [ ] Consider reducing data points shown on mobile

- [ ] **Chart components to review:**
  - [ ] `Dashboard.jsx` - Multiple charts
  - [ ] `departments/AccountingReport.jsx` - Financial charts
  - [ ] `departments/ServiceReport.jsx` - Service charts
  - [ ] `departments/PartsReport.jsx` - Parts charts
  - [ ] `ForecastAccuracy.jsx` - Forecast charts
  - [ ] `MaintenanceContractProfitability.jsx` - Profitability charts

---

## Priority 6: Future Enhancements

### Advanced Mobile Features

- [ ] **Consider implementing pull-to-refresh**
  - For dashboard and report pages

- [ ] **Add swipe gestures for tabs**
  - Allow swiping between tab panels on mobile

- [ ] **Implement progressive disclosure**
  - Show summary on mobile, expand for details

- [ ] **Add mobile-specific navigation shortcuts**
  - Quick access to frequently used features

---

## Testing Checklist

- [ ] Test on iPhone SE (smallest common iOS device)
- [ ] Test on iPhone 14/15 Pro Max (larger iOS device)
- [ ] Test on Samsung Galaxy S series (Android)
- [ ] Test on iPad (tablet)
- [ ] Test in landscape orientation
- [ ] Test with browser dev tools mobile emulation
- [ ] Verify touch targets with accessibility tools

---

## Files Reference

### Core UI Components
- `src/components/ui/button.jsx`
- `src/components/ui/input.jsx`
- `src/components/ui/select.jsx`
- `src/components/ui/table.jsx`
- `src/components/ui/tabs.jsx`
- `src/components/ui/dialog.jsx`

### Layout Components
- `src/components/Layout.jsx`
- `src/components/ui/sidebar.jsx`

### Major Report Components
- `src/components/Dashboard.jsx` (2336 lines)
- `src/components/SalesCommissionReport.jsx` (2184 lines)
- `src/components/departments/PartsReport.jsx` (1896 lines)
- `src/components/departments/ServiceReport.jsx` (1719 lines)
- `src/components/departments/AccountingReport.jsx` (1085 lines)

### Hooks
- `src/hooks/use-mobile.js`

---

## Notes

- The current mobile layout structure is considered good - preserve the existing layout patterns
- Focus on improving content presentation within the existing layout
- Test changes incrementally to avoid regressions
