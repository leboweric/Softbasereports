# New Tenant Onboarding Guide

This guide outlines the steps required to onboard a new dealership (tenant) to the Softbase Reports platform. The process is designed to be as automated as possible, with most functionality working out-of-the-box once the tenant is configured in the database.

---

## Onboarding Process

### Step 1: Create Organization Record (Database)

This is the only **required** step for a new tenant to get basic access and functionality. All other steps are for enabling advanced features or tenant-specific customizations.

Create a new record in the `organizations` table in the main PostgreSQL database. This can be done via the `/api/tenant-admin/organizations` POST endpoint or directly in the database.

#### Required Fields:

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `name` | `String` | `"ABC Forklift, Inc."` | The legal name of the dealership. |
| `platform_type` | `String` | `"evolution"` | Must be `"evolution"` for Softbase tenants. |
| `database_schema` | `String` | `"abc001"` | The tenant's unique schema name in the Azure SQL database. **This is critical.** |
| `db_server` | `String` | `"abc-sql.database.windows.net"` | The hostname of the tenant's Azure SQL server. |
| `db_name` | `String` | `"evo_abc"` | The name of the tenant's database on that server. |
| `db_username` | `String` | `"abc_user"` | The username for connecting to the tenant's database. |
| `db_password` | `String` | `"SuperSecret123!"` | The password for the database user. This will be encrypted at rest. |
| `fiscal_year_start_month` | `Integer` | `11` | The month the fiscal year starts (1=Jan, 11=Nov). Defaults to 11. |
| `data_start_date` | `Date` | `"2022-01-01"` | The earliest date to query for reports. If NULL, goes back 13 months. |
| `is_active` | `Boolean` | `true` | Must be `true` for the tenant to be active. |

Once this record is created, the system will automatically:
- **Discover the tenant** for ETL jobs (CEO dashboard mart, customer activity, etc.)
- **Discover the tenant** for the cache warmer service
- **Resolve the tenant** for all API requests, ensuring data isolation

### Step 2: Create User Accounts

Create user accounts in the `users` table and link them to the new organization's ID.

### Step 3: Configure GL Accounts (Code Change)

This step is required for the P&L and department-level financial reports to work correctly. Every dealership has a different chart of accounts.

1.  **Create a new GL config file** (e.g., `gl_accounts_abc.py`) in `reporting-backend/src/config/` by copying `gl_accounts_ips.py` as a template.
2.  **Update the account numbers** in the new file to match the new tenant's chart of accounts for revenue, COGS, and expenses for each department.
3.  **Import and map the new config** in `reporting-backend/src/config/gl_accounts_loader.py`:

    ```python
    # 1. Import the new config
    from src.config.gl_accounts_abc import GL_ACCOUNTS_ABC, OTHER_INCOME_ACCOUNTS_ABC, EXPENSE_ACCOUNTS_ABC

    # 2. Add to TENANT_GL_CONFIGS dictionary
    TENANT_GL_CONFIGS = {
        'ben002': { ... },
        'ind004': { ... },
        'abc001': {  # New tenant
            'gl_accounts': GL_ACCOUNTS_ABC,
            'other_income': OTHER_INCOME_ACCOUNTS_ABC,
            'expense_accounts': EXPENSE_ACCOUNTS_ABC,
        },
    }
    ```

> **Note:** If this step is skipped, financial reports will fall back to using Bennett's GL accounts and a loud warning will be logged (`No GL config for schema 'abc001' - falling back to ben002`).

### Step 4: Configure Dashboard Mart (Code Change)

For the main CEO dashboard to use the fast-path mart table, add the new tenant's schema and org ID to the `ORG_ID_MAP` in `reporting-backend/src/routes/dashboard_optimized.py`.

```python
ORG_ID_MAP = {
    'ben002': 4,
    'ind004': 7,
    'abc001': 12  # New tenant
}
```

### Step 5: Configure Tenant-Specific Logic (Code Change, Optional)

If the new tenant has unique business logic or data models, add tenant-specific branches where needed. The codebase is already structured to handle this.

-   **Example 1: Custom Excel Templates**
    -   In `reporting-backend/src/routes/evo_export.py`, add the tenant's schema and template file to the `TEMPLATE_MAP`.
-   **Example 2: Custom Data Joins**
    -   In `reporting-backend/src/routes/accounting_reports.py`, add an `if schema == 'abc001':` block to handle any custom SQL queries for that tenant.

---

## Technical Details

-   **Password Encryption:** Database passwords are encrypted using Fernet (AES-128) via the `CredentialManager` service. The encryption key is stored as an environment variable.
-   **Automatic Discovery:** The ETL and cache warmer services use `discover_softbase_tenants()` from `tenant_discovery.py`, which queries the `organizations` table to find all active tenants. No manual lists need to be updated for these systems.
-   **Data Isolation:** All API routes use `get_tenant_schema()` from `tenant_utils.py`, which resolves the tenant from the user's JWT token. If resolution fails, it raises a `ValueError`, preventing any data from being returned.
