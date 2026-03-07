# AIOP Platform Architecture Rules & Governance Framework

**Version**: 1.0
**Last Updated**: March 4, 2026
**Status**: MANDATORY — Every AIOP run MUST read this file before processing any ticket.

---

## Purpose

This document defines the architectural rules, coding standards, and governance framework for the AIOP platform. It exists because the platform serves multiple organizations with different data structures, and every code change has the potential to break functionality for tenants other than the one that reported the issue.

The rules in this document are not suggestions. They are derived from real production incidents that caused data leakage, broken reports, or silent failures across tenants. Each rule includes the incident(s) that motivated it.

---

## The Three-Lens Analysis

Every ticket — bug, enhancement, or question — MUST be analyzed through three lenses before any code is written.

### Lens 1: Ticket Lens (Does this fix the reported issue?)

This is the baseline. Understand what the user reported, reproduce the issue, and verify the fix addresses it. This is necessary but not sufficient.

### Lens 2: Platform Lens (Does this fix work for ALL tenants, current and future?)

After identifying a fix, ask:

- Does this code path serve other tenants?
- Will this fix produce correct results for Bennett? IPS? Sandia Plastics? A tenant that doesn't exist yet?
- Are there any hardcoded values that are specific to one tenant's data?
- If I add a new tenant tomorrow with completely different SaleCodes, Dept numbers, and Branch names, will this code still work?

### Lens 3: Architecture Lens (Does this fix follow established patterns, or create technical debt?)

After confirming the fix works across tenants, ask:

- Does this follow the same pattern used in similar components?
- Am I introducing a new pattern? If so, does it need to become the standard?
- Am I duplicating logic that already exists elsewhere?
- Will the next developer (or the next AIOP run) understand why this code exists?
- Does this change require updates to documentation, registries, or configuration?

---

## Golden Rules

These rules are non-negotiable. Violating any of them will cause production incidents.

### Rule 1: Never Hardcode SaleCodes

**Incident History**: MANUAL-004 (Invoiced Sales $0 for IPS), TKT-2026-0006 (Service Invoice Billing wrong departments), TKT-2026-0022 (Customer Profitability no data for IPS), TKT-2026-0021 (Maintenance Contract Profitability no data for IPS)

**The Problem**: Bennett uses SaleCodes like `LINDE`, `NEWEQ`, `USEDEQ`, `ALLIED`. IPS uses `C1`, `I4`, `V1`, `IR`. Future tenants will use entirely different codes. Hardcoding any SaleCode value guarantees the report will break for at least one tenant.

**The Rule**: Always query the `Dept` table dynamically and categorize by `Title` keywords.

```python
# WRONG — will break for non-Bennett tenants
WHERE SaleCode IN ('LINDE', 'NEWEQ', 'USEDEQ')

# RIGHT — works for any tenant
dept_query = f"SELECT SaleCode, Title FROM {schema}.Dept"
depts = db.execute_query(dept_query)
service_codes = [d['SaleCode'] for d in depts 
                 if any(kw in d['Title'].lower() for kw in ['service', 'shop'])]
```

**Verification**: After writing any SQL that filters by SaleCode, Dept, or department type, search the query for quoted string literals. If you find any that look like SaleCodes (e.g., `'SVE'`, `'PM'`, `'FMBILL'`), replace them with dynamic lookups.

---

### Rule 2: Never Hardcode Dept Numbers

**Incident History**: MANUAL-004 (Dept 20 = "Used Equipment" at Bennett but "Allied" at IPS)

**The Problem**: The same Dept number means different things at different tenants. Dept 20 is "Used Equipment" at Bennett but "Allied" at IPS.

**The Rule**: Always match by `Dept.Title` keywords, never by Dept number.

```python
# WRONG
WHERE SaleDept IN (10, 20, 70)

# RIGHT
new_depts = [d['Dept'] for d in depts 
             if 'new' in d['Title'].lower() and 'equip' in d['Title'].lower()]
```

---

### Rule 3: Always Use Schema Prefix on ALL Table References

**Incident History**: TKT-2026-0022 (missing schema prefix on WOLabor, WOParts, WOMisc caused silent failures)

**The Problem**: When writing SQL JOINs, the main table gets `{schema}.` prefix but sub-tables in subqueries are sometimes missed. This causes the query to either fail or silently return wrong data.

**The Rule**: Every table reference in every query MUST have `{schema}.` prefix.

**Tables commonly missed**:
- `WOLabor` (in subqueries calculating labor hours/costs)
- `WOParts` (in subqueries calculating parts costs)
- `WOMisc` (in subqueries calculating miscellaneous costs)
- `WOQuote` (in subqueries calculating quoted amounts)
- `LaborRate` (in JOINs for labor rate lookup)
- `Equipment` (in JOINs for equipment details)

**Verification Checklist**: After writing any SQL query, scan every `FROM` and `JOIN` clause. Every table name must be prefixed with `{schema}.`. No exceptions.

---

### Rule 4: Always Scope Cache Keys by Tenant

**Incident History**: MANUAL-006 (Cross-tenant data pollution — Bennett users saw IPS data on PM Route Planner, QBR, and Rental Service Report)

**The Problem**: Cache keys without tenant identifiers cause Org A's data to be served to Org B. This is a data leakage incident, not just a bug.

**The Rule**: Every cache key for Azure SQL data MUST include `get_tenant_schema()`.

```python
# WRONG — cross-tenant data leakage
cache_key = 'pm_report_pms_due'

# RIGHT — tenant-isolated
schema = get_tenant_schema()
cache_key = f'pm_report_pms_due_{schema}'
```

**Exemption**: PostgreSQL routes (users, tickets, roles, visibility) are single-tenant by design and do not need tenant-scoped cache keys.

---

### Rule 5: WO Status Filtering — Open vs Total

**Incident History**: TKT-2026-0026 (Work Order Types showing 6,355 total instead of 537 open)

**The Problem**: Without status filters, WO queries count every work order ever created (open + closed + deleted), producing massively inflated numbers.

**The Rule**: When showing "current," "active," or "open" work orders, ALWAYS apply both filters:

```sql
WHERE ClosedDate IS NULL      -- open only
  AND DeletionTime IS NULL    -- not deleted
```

**Best Practice**: Return both `open_count` and `total_count` so users have context.

---

### Rule 6: Equipment Table JOINs Need Deduplication

**Incident History**: TKT-2026-0025 (Cash Stalled showing duplicate WOs), TKT-25 (earlier duplicate WO incident)

**The Problem**: The Equipment table can have multiple rows per UnitNo (e.g., a forklift and its charger share the same UnitNo). Any JOIN on `UnitNo` without deduplication will multiply rows.

**The Rule**: Always use ROW_NUMBER() deduplication when joining Equipment:

```sql
LEFT JOIN (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY UnitNo ORDER BY UnitNo) as rn
    FROM {schema}.Equipment
) e ON w.UnitNo = e.UnitNo AND e.rn = 1
```

**Defense in Depth**: Also add Python-level deduplication after query results as a safety net.

---

### Rule 7: Effective Rate, Not Base Rate

**Incident History**: TKT-2026-0023 (Cash Burn showing wrong billable rate and unbillable labor value)

**The Problem**: Work orders can have a `LaborDiscount` field (0-100%). Using the base `LaborRate.Rate` for dollar calculations produces incorrect values.

**The Rule**: Always calculate effective rate:

```python
effective_rate = labor_rate * (1 - labor_discount / 100)
```

Use `effective_rate` for all dollar calculations (unbillable labor value, quoted hours conversion, etc.). Display both base rate and effective rate in the UI so users understand the breakdown.

---

### Rule 8: Three Registries Must Stay In Sync

**Incident History**: MANUAL-001 (Invoiced Sales not in Report Visibility), MANUAL-002 (Invoiced Sales not in navigation), TKT-2026-0026 (Report Visibility not persisting for many tabs)

**The Problem**: Adding a new tab requires updating three separate registries. Missing any one causes the tab to be invisible in different contexts.

**The Rule**: When adding ANY new tab, update ALL THREE:

| Registry | File | Purpose |
|----------|------|---------|
| NAVIGATION_CONFIG | `rbac_config.py` | Controls which tabs appear in sidebar/page navigation |
| Backend REPORT_REGISTRY | `report_visibility.py` | Controls which tabs can be toggled in Report Visibility admin |
| Frontend REPORT_REGISTRY | `ReportVisibility.jsx` | Controls which tabs render in the Report Visibility admin UI |

**Verification**: After adding a tab, grep all three files for the new tab ID. All three must contain it.

---

### Rule 9: Report Visibility Defaults to Visible

**Incident History**: Documented in scheduler prompt — new tabs are visible to ALL orgs by default.

**The Problem**: The `report_visibility` table only stores explicit overrides. No row = visible. Adding a new tab without hiding it from non-requesting orgs means every org sees it immediately.

**The Rule**: When adding a tab requested by a specific org:
1. Add to all three registries
2. Immediately set `is_visible = false` for ALL OTHER orgs
3. Verify by logging in as each org

**Exception**: If the tab is intended for all orgs, leave the default and document it.

---

### Rule 10: Permission Decorators Must Match Page Resource

**Incident History**: MANUAL-005 (Sales Manager getting 403 on Invoiced Sales), TKT-2026-0008 (Sales Manager 403 due to empty DB permissions)

**The Problem**: Using the wrong permission decorator (e.g., `view_commissions` for a dashboard tab) blocks legitimate users.

**The Rule**: Match the decorator to the page, not the data type:

| Page | Decorator |
|------|-----------|
| Sales Dashboard tabs | `@require_permission('view_dashboard')` |
| Parts tabs | `@require_permission('view_parts')` |
| Service tabs | `@require_permission('view_service')` |
| Rental tabs | `@require_permission('view_rental')` |
| Accounting tabs | `@require_permission('view_commissions')` |
| Admin-only | `@require_role('Super Admin')` |

---

## Per-Org Configuration Pattern

When an organization has a unique business need (excluded branches, excluded customers, custom thresholds), it MUST go into the organization's settings JSON — never into if/else branches in the code.

### Current Per-Org Settings

| Setting | Purpose | Example |
|---------|---------|---------|
| `excluded_branches` | Hide specific branches from reports | IPS: `['3', '4']` (CH Steel, Dynamic Storage) |
| `excluded_bill_to_customers` | Exclude intercompany billing | IPS: `['IPS140', 'IPS145', 'IPC140', 'IPC145']` |
| `fiscal_year_start_month` | Fiscal year alignment | Bennett: November |

### Adding New Per-Org Settings

1. Add the setting to the organization's `settings` JSON column in PostgreSQL
2. Read it in the backend endpoint: `org_settings = current_user.organization.settings or {}`
3. Apply it conditionally: `if 'excluded_branches' in org_settings: ...`
4. Use parameterized SQL (NOT IN with `%s` placeholders) to prevent injection
5. Document the new setting in this table

**Never do this**:
```python
# WRONG — hardcoded org-specific logic
if schema == 'ind004':
    query += " AND BillTo NOT IN ('IPS140', 'IPS145')"
```

**Always do this**:
```python
# RIGHT — configurable per-org
excluded = org_settings.get('excluded_bill_to_customers', [])
if excluded:
    placeholders = ','.join(['%s'] * len(excluded))
    query += f" AND BillTo NOT IN ({placeholders})"
    params.extend(excluded)
```

---

## New Org Onboarding Checklist

When a new organization is added to the platform, run this checklist before declaring them "live":

### Data Validation

- [ ] Verify `get_tenant_schema()` returns the correct schema name
- [ ] Query `{schema}.Dept` — confirm departments exist and titles are parseable
- [ ] Query `{schema}.Branch` — confirm branches exist
- [ ] Query `{schema}.Customer` — confirm customer data exists
- [ ] Query `{schema}.WO` — confirm work order data exists
- [ ] Query `{schema}.InvoiceReg` — confirm invoice data exists
- [ ] Query `{schema}.Equipment` — confirm equipment data exists
- [ ] Query `{schema}.LaborRate` — confirm labor rates exist

### Report Validation

- [ ] Sales Dashboard loads with data
- [ ] Invoiced Sales shows non-zero revenue
- [ ] Parts page loads with data
- [ ] Service page loads with data (if applicable)
- [ ] Rental page loads with data (if applicable)
- [ ] Customer Profitability returns results
- [ ] Work Order Types shows correct open counts
- [ ] Cash Burn loads without errors

### RBAC Validation

- [ ] Admin user can access all pages
- [ ] Role-restricted users see only their permitted pages
- [ ] Report Visibility toggles work for the new org
- [ ] No cross-tenant data leakage (switch between orgs and verify data changes)

### Cache Validation

- [ ] Load a report as the new org
- [ ] Switch to another org and load the same report
- [ ] Verify data is different (not cached from the first org)

---

## Pre-Fix Impact Analysis Checklist

Before writing any code to fix a ticket, answer these questions:

### Multi-Tenant Impact

- [ ] Which tenants does this code path serve? (All? One? Some?)
- [ ] Are there hardcoded values (SaleCodes, Dept numbers, branch IDs, customer numbers)?
- [ ] Are there schema prefix references that could be missing?
- [ ] Does this endpoint use caching? If so, is the cache key tenant-scoped?
- [ ] Does this touch RBAC/permissions? If so, does it affect all roles?

### Regression Risk

- [ ] Does this change affect a shared component used by multiple pages?
- [ ] Does this change modify a SQL query that serves multiple endpoints?
- [ ] Does this change alter the response format of an API endpoint?
- [ ] Could this change cause empty results for a tenant with different data structure?

### Pattern Compliance

- [ ] Does this follow the same pattern used in similar components?
- [ ] Am I introducing a new pattern? If so, should it be documented here?
- [ ] Does this require updates to any of the three registries?
- [ ] Does this require a new per-org configuration setting?

---

## Post-Deployment Verification Protocol

After every deployment, the following checks MUST be performed:

### Immediate (within 5 minutes of deployment)

1. **Health check**: `GET /api/admin/logs/health` — verify status is "healthy"
2. **Error check**: `GET /api/admin/logs?since_hours=1` — verify no new errors from the deployment
3. **Affected endpoint**: Hit the specific endpoint that was modified, for the reporting org
4. **Cross-tenant check**: Hit the same endpoint for at least one other org

### Smoke Test (run the automated smoke test script)

The smoke test script (`smoke_test.py`) hits key endpoints for every active org and verifies:
- HTTP 200 responses (not 500)
- Non-empty data in responses
- No cross-tenant data leakage
- Key metrics are non-zero where expected

---

## Known Tenant Data Differences

This table documents known differences between tenants. It MUST be updated when a new tenant is onboarded or when new differences are discovered.

| Data Element | Bennett (`ben002`) | IPS (`ind004`) | Sandia Plastics (TBD) | Rule |
|-------------|-------------------|----------------|----------------------|------|
| SaleCodes (Equipment) | `LINDE`, `NEWEQ`, `USEDEQ`, `ALLIED` | `C1`, `I4`, `V1`, `IR` | Unknown | Use Dept table |
| SaleCodes (Service) | `PM` | Various | Unknown | Use Dept table |
| SaleCodes (Maintenance) | `FMBILL`, `FMROAD`, `PM-FM`, `FMSHOP` | Different | Unknown | Use Dept table |
| Dept Numbers | 10=New, 20=Used, 70=Allied | 10=New, 20=Allied, 30=Used | Unknown | Match by Title |
| Branch Names | `Main`, `Shop` | `Canton`, `Cleveland` | Unknown | Use Branch table |
| Excluded Branches | None | `3`, `4` (CH Steel, Dynamic Storage) | Unknown | Org settings JSON |
| Excluded Bill-To | None | `IPS140`, `IPS145`, `IPC140`, `IPC145` | Unknown | Org settings JSON |
| Fiscal Year Start | November | TBD | Unknown | Org settings |
| Labor Discount on WOs | Varies (0-100%) | Varies (0-100%) | Unknown | Always use effective rate |

---

## Incident Log

This section tracks architectural incidents — bugs that were caused by violating the rules above. It serves as a reminder of why these rules exist.

| Date | Incident | Rule Violated | Impact | Tickets |
|------|----------|--------------|--------|---------|
| 2026-03-02 | Invoiced Sales $0 for IPS | Rule 1 (Hardcoded SaleCodes) | IPS saw no revenue data | MANUAL-004 |
| 2026-03-02 | Invoiced Sales not in Report Visibility | Rule 8 (Three Registries) | Tab invisible in admin | MANUAL-001 |
| 2026-03-02 | Invoiced Sales not in navigation | Rule 8 (Three Registries) | Tab invisible on page | MANUAL-002 |
| 2026-03-02 | Sales Manager 403 on Invoiced Sales | Rule 10 (Permission Decorators) | Role blocked from tab | MANUAL-005 |
| 2026-03-03 | Cross-tenant data pollution | Rule 4 (Cache Key Scoping) | Bennett saw IPS data | MANUAL-006 |
| 2026-03-03 | Service Invoice Billing wrong depts | Rule 1 (Hardcoded SaleCodes) | Non-service invoices shown | TKT-2026-0006 |
| 2026-03-03 | Sales Manager 403 (DB permissions empty) | Rule 10 (Permission Decorators) | Role blocked from all endpoints | TKT-2026-0008 |
| 2026-03-03 | Cash Stalled duplicate WOs | Rule 6 (Equipment Dedup) | WOs appeared multiple times | TKT-25 |
| 2026-03-03 | Report Visibility not persisting | Rule 8 (Three Registries) | Toggles silently dropped | TKT-2026-0026 |
| 2026-03-04 | Customer Profitability no data for IPS | Rules 1, 3 (SaleCodes + Schema) | Empty report for IPS | TKT-2026-0022 |
| 2026-03-04 | Maintenance Contract no data for IPS | Rule 1 (Hardcoded SaleCodes) | Empty report for IPS | TKT-2026-0021 |
| 2026-03-04 | Cash Burn wrong billable rate | Rule 7 (Effective Rate) | Incorrect dollar values | TKT-2026-0023 |
| 2026-03-04 | WO counts showing total not open | Rule 5 (WO Status Filtering) | 6,355 shown instead of 537 | TKT-2026-0026 |
| 2026-03-07 | Pat Rudawsky (IPS) saw Bennett data | Rule 11 (User Org Assignment) | Wrong org, wrong data, wrong visibility | MANUAL-010 |
| 2026-03-07 | Parts Sold by Customer 'Invalid column name CustNo' | Rule 12 (column_mappings correctness) | Report failed for Bennett | MANUAL-012 |

---

### Rule 11: Always Verify User Org and Role Org When Creating Users

**Incident History**: MANUAL-010 (Pat Rudawsky created in Bennett's org instead of IPS)

**The Problem**: The `create_user` admin endpoint assigns new users to `current_user.organization_id`. The support bot (`aiop-support-bot`) lives in **org 4 (Bennett)**. Any user it creates without an explicit `organization_id` override ends up in Bennett's org — seeing Bennett data, Bennett Report Visibility settings, and assigned Bennett roles.

**The Rule**: When creating users for a non-Bennett org via the support bot or any Super Admin account:
1. Always pass `organization_id` explicitly in the create_user request body
2. Always assign a role that belongs to the **target org** — roles are org-scoped and have different IDs per org
3. Verify after creation: `SELECT u.organization_id, o.name, r.name, r.organization_id FROM user u JOIN organization o ON u.organization_id=o.id JOIN user_roles ur ON ur.user_id=u.id JOIN role r ON r.id=ur.role_id WHERE u.id=<new_user_id>`

**Known Role IDs**:

| Role | Bennett (org 4) | IPS (org 7) |
|------|----------------|-------------|
| Parts Manager | 4 | 22 |
| Sales Manager | 3 | 32 |
| Service Manager | 2 | 21 |
| Admin | 1 | 20 |

**Diagnostic**: If a user reports seeing another org's data, immediately check their `organization_id` in PostgreSQL:
```sql
SELECT u.id, u.email, u.organization_id, o.name 
FROM "user" u JOIN organization o ON u.organization_id = o.id 
WHERE u.email = '<email>';
```

---

### Rule 12: column_mappings.py Must Reflect Actual Database Column Names

**Incident History**: MANUAL-012 (Parts Sold by Customer 'Invalid column name CustNo' on Bennett)

**The Problem**: `column_mappings.py` DEFAULT_COLUMNS (Bennett) had `Customer.cust_no` mapped to `'CustNo'`. But Bennett's actual Customer table uses `'Number'` as the customer number column. This caused the `get_parts_sold_by_customer` query to fail with `Invalid column name 'CustNo'`. The bug was masked in all other queries because they used `get_column() or 'Number'` fallback, which silently used the correct column name.

**The Rule**: The `column_mappings.py` DEFAULT_COLUMNS must reflect the **actual column names** in the database. Never assume a column name without verifying against the real schema.

**Known Correct Mappings**:

| Table | Column | Bennett (`ben002`) | IPS (`ind004`) |
|-------|--------|-------------------|----------------|
| Customer | cust_no (customer number) | `Number` | `Number` |
| InvoiceReg | cust_no | `CustNo` | `CustNo` |
| GLDetail | date column | `EffectiveDate` | `EffectiveDate` |

**Important Distinction**: `InvoiceReg.CustNo` EXISTS in Bennett (it's the customer number on the invoice). `Customer.CustNo` does NOT exist — the Customer table uses `Number`. These are different tables with different column names for the same concept.

**Verification**: When adding a new `get_column()` call, always cross-check against working queries in the codebase that join the same table. If every working query uses `c.Number` for Customer joins, the mapping should be `'Number'`, not `'CustNo'`.

---

**This document is a living artifact. Every time a new architectural rule is discovered through a production incident, it MUST be added here with the incident that motivated it.**
