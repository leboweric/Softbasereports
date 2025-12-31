# Mobile-Friendliness Improvements To-Do List

**Created:** Dec 31, 2025  
**Status:** In Progress

---

## Priority 1: Critical (Touch Targets & Accessibility)

### UI Component Updates

- [x] **Update Button component touch targets**
  - File: `src/components/ui/button.jsx`
  - Changed to mobile-first: `h-11 md:h-9` (44px on mobile, 36px on desktop)
  - All size variants updated with responsive sizing
  - Icon buttons also updated to `size-11 md:size-9`

- [x] **Update Input component touch targets**
  - File: `src/components/ui/input.jsx`
  - Changed to mobile-first: `h-11 md:h-9` (44px on mobile, 36px on desktop)
  - Added responsive padding: `py-2 md:py-1`

- [x] **Update Select component touch targets**
  - File: `src/components/ui/select.jsx`
  - SelectTrigger updated: `h-11 md:h-9` for default, `h-10 md:h-8` for small
  - SelectItem updated: `py-3 md:py-1.5` for larger touch targets on mobile

---

## Priority 2: High (Table Optimization)

### Table Mobile Improvements

- [ ] **Audit all table usages across components**
  - Identify tables with many columns that are problematic on mobile
  - Document which tables need mobile-specific treatment

- [x] **Implement mobile-friendly table patterns**
  - [x] Updated Table component with improved mobile styling
  - [x] Added column prioritization for ServiceInvoiceBilling (show/hide columns)
  - [x] Table component now has improved overflow handling

- [ ] **High-priority table components to address:**
  - [ ] `src/components/Dashboard.jsx` - Customer tables
  - [ ] `src/components/SalesCommissionReport.jsx` - Commission tables
  - [ ] `src/components/departments/ServiceReport.jsx` - Work order tables
  - [ ] `src/components/departments/PartsReport.jsx` - Parts tables
  - [ ] `src/components/departments/AccountingReport.jsx` - Financial tables
  - [x] `src/components/ServiceInvoiceBilling.jsx` - Invoice table (reduced min-width, hidden columns on mobile)

---

## Priority 3: Medium (Layout & Navigation)

### Dashboard & Report Layouts

- [x] **Simplify Dashboard mobile layout**
  - File: `src/components/Dashboard.jsx`
  - [x] Header now stacks vertically on mobile with `flex-col md:flex-row`
  - [x] Button text hidden on small screens, icons remain visible
  - [x] Responsive text sizes for title and description

- [x] **Optimize TabsList for mobile**
  - Files: Multiple components using tabs
  - [x] Updated Tabs component with horizontal scrolling on mobile
  - [x] TabsTrigger now has larger touch targets on mobile (h-10)
  - [x] Dashboard TabsList updated to flex-wrap on mobile

- [ ] **Review header section on mobile**
  - File: `src/components/Dashboard.jsx` (lines 841-876)
  - [ ] Stack header elements vertically on mobile
  - [ ] Ensure action buttons are accessible

### Dialog & Modal Improvements

- [x] **Audit dialog/modal mobile behavior**
  - [x] Updated Dialog component with better mobile sizing
  - [x] Dialogs now nearly full-screen on mobile with proper padding
  - [x] Close button has larger touch target on mobile
  - [ ] `CustomerDetailModal.jsx` - may need component-specific adjustments
  - [ ] `MinitracSearch.jsx` - may need component-specific adjustments

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
