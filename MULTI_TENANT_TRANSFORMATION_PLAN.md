# Multi-Tenant Transformation Analysis

## Executive Summary

This document analyzes the current Softbase Reports architecture and provides a comprehensive plan for transforming it into a multi-tenant SaaS platform that supports both **Softbase Evolution** (web-based) and **Softbase Legacy** platforms, enabling multiple forklift dealerships to leverage the BI Reporting package.

---

## Current Architecture Assessment

### Strengths

The current architecture already has several elements that will facilitate multi-tenancy:

1. **Existing Multi-Tenant Foundation**
   - `Organization` model already exists in the database
   - `TenantMiddleware` provides organization isolation
   - Users are already associated with organizations via `organization_id`
   - Subscription tiers and feature access controls are implemented

2. **Clean Separation of Concerns**
   - Frontend (React/Vite) is decoupled from backend
   - Backend uses service layer pattern (`AzureSQLService`, `SoftbaseService`)
   - Database access is centralized through service classes
   - API routes are well-organized by feature

3. **Flexible Database Architecture**
   - Primary database (Azure SQL) for Softbase Evolution data
   - Secondary database (PostgreSQL) for application data
   - Connection management is abstracted in `DatabaseConfig`

4. **Modern Tech Stack**
   - React 19 with component-based architecture
   - Flask with modular route structure
   - JWT-based authentication
   - RBAC (Role-Based Access Control) system

### Current Limitations for Multi-Tenancy

1. **Single Database Connection**
   - All organizations currently connect to the same Azure SQL database (`ben002` schema)
   - No mechanism to route different tenants to different databases
   - Hardcoded database credentials in environment variables

2. **No Platform Abstraction**
   - Code assumes Softbase Evolution data structure
   - SQL queries are specific to Evolution schema
   - No abstraction layer to support different Softbase versions

3. **Limited Tenant Isolation**
   - Row-level isolation exists for PostgreSQL tables
   - No isolation for Azure SQL data (all tenants see same data)
   - Tenant context not passed to database queries

4. **Hardcoded Business Logic**
   - Department codes, table names, and field names are hardcoded
   - No configuration system for tenant-specific customizations
   - Reports assume specific Softbase Evolution schema

---

## Multi-Tenancy Requirements Analysis

### Tenant Types and Platform Support

#### Type 1: Softbase Evolution Tenants
- **Database**: Azure SQL Server
- **Schema**: Modern web-based ERP structure
- **Current Support**: ✅ Fully supported (current implementation)
- **Key Tables**: Equipment, Customer, InvoiceReg, WO, WOParts, WOLabor, etc.

#### Type 2: Softbase Legacy Tenants
- **Database**: Unknown (likely SQL Server or older database)
- **Schema**: Legacy ERP structure (needs discovery)
- **Current Support**: ❌ Not supported
- **Key Challenges**:
  - Different table names and structures
  - Different field names and data types
  - Different business logic and calculations
  - May require data transformation layer

### Multi-Tenancy Isolation Levels

#### Level 1: Database-Level Isolation (Recommended for Production)
- **Approach**: Each tenant has their own Azure SQL database
- **Pros**:
  - Complete data isolation
  - Independent scaling and performance
  - Easier compliance and security
  - Tenant-specific backups and recovery
- **Cons**:
  - Higher infrastructure costs
  - More complex connection management
  - Schema migrations across multiple databases

#### Level 2: Schema-Level Isolation
- **Approach**: Shared database, separate schemas per tenant
- **Pros**:
  - Lower infrastructure costs
  - Easier management than separate databases
  - Good isolation
- **Cons**:
  - All tenants affected by database downtime
  - Schema migrations still complex
  - May hit database size limits

#### Level 3: Row-Level Isolation (Current Implementation)
- **Approach**: Shared database and schema, filter by `organization_id`
- **Pros**:
  - Lowest cost
  - Simplest to implement
  - Easy schema migrations
- **Cons**:
  - Risk of data leakage if queries miss filters
  - Performance degradation as data grows
  - Not suitable for Softbase data (read-only external databases)

### Recommended Approach: Hybrid Multi-Tenancy

**For Application Data (PostgreSQL)**:
- Continue using row-level isolation with `organization_id`
- Tables: users, work_order_notes, report_templates, etc.

**For Softbase Data (Azure SQL / Legacy)**:
- Use database-level isolation
- Each tenant connects to their own Softbase database
- Store connection credentials per organization

---

## Platform Integration Challenges

### Challenge 1: Schema Differences Between Platforms

**Softbase Evolution** (Known):
```sql
-- Equipment table structure
Equipment (SerialNo, UnitNo, Make, Model, RentalStatus, CustomerNo, InventoryDept, ...)

-- Invoice table structure  
InvoiceReg (InvoiceNo, InvoiceDate, BillTo, SaleCode, LaborTaxable, PartsTaxable, ...)

-- Work Order structure
WO (WONo, Type, BillTo, OpenDate, ClosedDate, ...)
```

**Softbase Legacy** (Unknown):
- Table names may be different (e.g., `tblEquipment` vs `Equipment`)
- Field names may be different (e.g., `EquipNo` vs `UnitNo`)
- Data types may be different
- Relationships may be structured differently
- Business logic calculations may differ

**Solution Approach**:
1. **Schema Discovery Phase**: Connect to sample Legacy database and map structure
2. **Abstraction Layer**: Create platform-agnostic data access layer
3. **Mapping Configuration**: Store field mappings per tenant
4. **Query Translation**: Translate generic queries to platform-specific SQL

### Challenge 2: Different Business Logic

**Example**: Revenue Calculation
- **Evolution**: `LaborTaxable + LaborNonTax` from `InvoiceReg`
- **Legacy**: May require joining to `InvoiceDetail` and summing line items

**Solution**: 
- Create platform-specific service classes
- Define common business logic interface
- Implement platform-specific calculations

### Challenge 3: Report Compatibility

**Current Reports** (Evolution-specific):
- Dashboard with KPIs
- Service Department Report
- Parts Department Report
- Rental Department Report
- Accounting Reports

**Compatibility Strategy**:
- **Core Reports**: Make compatible with both platforms (80% of functionality)
- **Platform-Specific Reports**: Create separate reports for unique features
- **Configuration**: Allow tenants to enable/disable reports based on their platform

### Challenge 4: Data Quality and Consistency

**Issues**:
- Legacy data may have quality issues
- Field formats may differ (dates, numbers, strings)
- Missing or null values may be more common
- Data validation rules may be different

**Solution**:
- Data validation layer before processing
- Configurable data transformation rules
- Error handling and logging
- Data quality dashboards for admins

---

## Key Technical Decisions

### Decision 1: Platform Detection and Routing

**Options**:

**A. Configuration-Based** (Recommended)
- Store platform type in `Organization` model (`platform_type: 'evolution' | 'legacy'`)
- Route to appropriate service class based on configuration
- Allows manual override and testing

**B. Auto-Detection**
- Query database schema on first connection
- Detect platform based on table structure
- Cache detection result
- More complex, but more automated

**Recommendation**: Start with Configuration-Based, add Auto-Detection later if needed

### Decision 2: Database Connection Management

**Current**: Single hardcoded connection
```python
AZURE_SQL_SERVER=evo1-sql-replica.database.windows.net
AZURE_SQL_DATABASE=evo
AZURE_SQL_USERNAME=ben002user
AZURE_SQL_PASSWORD=[encrypted]
```

**Proposed**: Per-tenant connection configuration
```python
class Organization(db.Model):
    # ... existing fields ...
    platform_type = db.Column(db.String(20))  # 'evolution' or 'legacy'
    db_server = db.Column(db.String(255))
    db_name = db.Column(db.String(255))
    db_username = db.Column(db.String(255))
    db_password_encrypted = db.Column(db.Text)  # Encrypted credentials
    db_connection_string = db.Column(db.Text)  # For complex connections
```

**Security Considerations**:
- Encrypt database passwords using Fernet or similar
- Store encryption key in environment variable
- Never expose credentials in API responses
- Audit all database connection attempts

### Decision 3: Query Abstraction Strategy

**Option A: ORM-Based** (SQLAlchemy)
- Define models for each platform
- Use SQLAlchemy to generate queries
- Pros: Type-safe, easier to maintain
- Cons: Complex for legacy schema, performance overhead

**Option B: Query Builder Pattern** (Recommended)
- Create platform-agnostic query builder
- Translate to platform-specific SQL
- Pros: Flexible, performant, easier to optimize
- Cons: More code to write initially

**Option C: Dual Implementation**
- Separate query implementations per platform
- No abstraction, just duplication
- Pros: Simple, explicit
- Cons: High maintenance, code duplication

**Recommendation**: Query Builder Pattern with platform-specific implementations

---

## Architecture Design Principles

### 1. Platform Abstraction Layer

Create a clean abstraction between business logic and platform-specific code:

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│  - Platform-agnostic components         │
│  - Receives normalized data             │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         API Layer (Flask Routes)        │
│  - Platform-agnostic endpoints          │
│  - Uses PlatformService interface       │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      Platform Abstraction Layer         │
│  - PlatformServiceFactory               │
│  - Detects platform type                │
│  - Returns appropriate service          │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────────┐   ┌──────────────────┐
│ EvolutionService │   │  LegacyService   │
│  - Evolution SQL │   │  - Legacy SQL    │
│  - Evolution     │   │  - Legacy        │
│    business logic│   │    business logic│
└──────────────────┘   └──────────────────┘
        │                       │
        ▼                       ▼
┌──────────────────┐   ┌──────────────────┐
│ Evolution DB     │   │  Legacy DB       │
│ (Azure SQL)      │   │  (SQL Server)    │
└──────────────────┘   └──────────────────┘
```

### 2. Configuration-Driven Design

Store all platform-specific configurations in the database:

```python
class PlatformConfig(db.Model):
    organization_id = db.Column(db.Integer, primary_key=True)
    platform_type = db.Column(db.String(20))
    
    # Table name mappings
    table_mappings = db.Column(db.JSON)  # {"equipment": "Equipment", "customer": "Customer"}
    
    # Field name mappings
    field_mappings = db.Column(db.JSON)  # {"equipment.serial_no": "SerialNo"}
    
    # Business logic overrides
    calculation_rules = db.Column(db.JSON)  # Custom calculation formulas
    
    # Feature flags
    enabled_reports = db.Column(db.JSON)  # List of enabled report types
```

### 3. Graceful Degradation

Not all reports will work on all platforms:

- **Core Reports**: Work on both platforms (Dashboard, basic KPIs)
- **Platform-Specific Reports**: Only available when supported
- **UI Indication**: Show which reports are available for the tenant
- **Fallback**: Provide alternative reports when primary isn't available

---

## Data Flow Architecture

### Current (Single-Tenant)

```
User → Frontend → API → AzureSQLService → ben002 Database
```

### Proposed (Multi-Tenant)

```
User → Frontend → API → TenantMiddleware → PlatformServiceFactory
                                                    │
                            ┌───────────────────────┴────────────────────┐
                            ▼                                            ▼
                    EvolutionService                            LegacyService
                            │                                            │
                            ▼                                            ▼
                    Tenant A Database                          Tenant B Database
                    (Azure SQL - Evolution)                    (SQL Server - Legacy)
```

### Connection Pooling Strategy

**Challenge**: Managing connections to multiple tenant databases

**Solution**: Per-tenant connection pools with limits

```python
class TenantConnectionManager:
    def __init__(self):
        self.pools = {}  # {org_id: connection_pool}
        self.max_pools = 50  # Limit total number of pools
        self.max_connections_per_pool = 5
    
    def get_connection(self, organization_id):
        if organization_id not in self.pools:
            if len(self.pools) >= self.max_pools:
                self._evict_least_used_pool()
            self.pools[organization_id] = self._create_pool(organization_id)
        return self.pools[organization_id].get_connection()
```

---

## Security and Compliance Considerations

### 1. Data Isolation

**Requirements**:
- Tenant A cannot access Tenant B's data
- Queries must be scoped to tenant's database
- Connection credentials must be isolated

**Implementation**:
- Middleware enforces tenant context on every request
- Database connections are tenant-specific
- No cross-tenant queries allowed
- Audit logging for all data access

### 2. Credential Management

**Challenge**: Storing database credentials for multiple tenants

**Solution**: Encrypted credential storage

```python
from cryptography.fernet import Fernet

class CredentialManager:
    def __init__(self, encryption_key):
        self.cipher = Fernet(encryption_key)
    
    def encrypt_password(self, password):
        return self.cipher.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password):
        return self.cipher.decrypt(encrypted_password.encode()).decode()
```

**Best Practices**:
- Encryption key stored in environment variable (not in code)
- Rotate encryption keys periodically
- Use separate keys for different environments
- Never log decrypted credentials

### 3. Compliance (SOC 2, GDPR, HIPAA if needed)

**Requirements**:
- Data residency (tenant data stays in their region)
- Right to deletion (delete tenant data on request)
- Access logging (audit trail of all data access)
- Encryption at rest and in transit

**Implementation**:
- Tenant-specific database locations
- Soft delete with purge functionality
- Comprehensive audit logging
- SSL/TLS for all connections

---

## Performance Considerations

### 1. Connection Pool Management

**Challenge**: Each tenant needs their own connection pool

**Strategy**:
- Lazy initialization (create pool on first request)
- LRU eviction (remove least recently used pools)
- Configurable pool sizes per tenant tier
- Health checks to detect dead connections

### 2. Caching Strategy

**Current**: Redis caching for dashboard data

**Multi-Tenant Enhancement**:
- Tenant-scoped cache keys: `tenant:{org_id}:dashboard:summary`
- Per-tenant cache TTL configuration
- Cache invalidation on tenant data changes
- Separate cache namespaces for different platforms

### 3. Query Optimization

**Platform-Specific Optimizations**:
- Evolution: Use existing optimized queries
- Legacy: May need different optimization strategies
- Per-tenant query performance monitoring
- Automatic slow query detection and alerting

---

## Migration Path for Existing Tenant

**Current State**: Single tenant (ben002) using Evolution

**Goal**: Convert to multi-tenant without disruption

**Steps**:

1. **Add Organization Record**
   ```sql
   INSERT INTO organizations (name, platform_type, db_server, db_name, db_username, db_password_encrypted)
   VALUES ('Ben002', 'evolution', 'evo1-sql-replica.database.windows.net', 'evo', 'ben002user', '[encrypted]');
   ```

2. **Update Existing Users**
   ```sql
   UPDATE users SET organization_id = 1 WHERE organization_id IS NULL;
   ```

3. **Deploy Platform Abstraction Layer**
   - Add `PlatformServiceFactory`
   - Add `EvolutionService` (wraps existing `AzureSQLService`)
   - Update routes to use factory

4. **Test with Existing Tenant**
   - Verify all reports still work
   - Check performance hasn't degraded
   - Validate data isolation

5. **Enable New Tenant Onboarding**
   - Create admin UI for adding tenants
   - Test with second Evolution tenant
   - Then add Legacy support

---

## Risk Assessment

### High Risk

1. **Data Leakage Between Tenants**
   - **Mitigation**: Comprehensive testing, middleware enforcement, audit logging
   
2. **Performance Degradation**
   - **Mitigation**: Connection pooling, caching, performance monitoring

3. **Schema Discovery Failures (Legacy)**
   - **Mitigation**: Manual schema mapping as fallback, extensive testing

### Medium Risk

4. **Credential Security**
   - **Mitigation**: Encryption, key rotation, access controls

5. **Migration Complexity**
   - **Mitigation**: Phased rollout, extensive testing, rollback plan

### Low Risk

6. **UI Compatibility**
   - **Mitigation**: Platform-agnostic components, graceful degradation

---

## Next Steps

This analysis provides the foundation for the detailed architecture design and implementation roadmap, which will be covered in the next phases of this document.


---

# Multi-Tenant Architecture Design

This section details the proposed multi-tenant architecture, including database design, backend services, frontend components, and security enhancements.

## 1. Database Schema Enhancements

### 1.1. `organizations` Table

We will extend the existing `organizations` table in the PostgreSQL database to store tenant-specific configuration, including platform type and database credentials.

**Updated `organizations` Table Schema:**

| Column                  | Type        | Description                                                                 |
| ----------------------- | ----------- | --------------------------------------------------------------------------- |
| `id`                    | `Integer`   | Primary key                                                                 |
| `name`                  | `String`    | Name of the dealership/organization                                         |
| `platform_type`         | `String`    | Type of Softbase platform (`evolution` or `legacy`)                         |
| `db_server`             | `String`    | Database server hostname or IP address                                      |
| `db_name`               | `String`    | Database name                                                               |
| `db_username`           | `String`    | Database username                                                           |
| `db_password_encrypted` | `Text`      | Encrypted database password                                                 |
| `is_active`             | `Boolean`   | Whether the organization's account is active                                |
| `subscription_tier`     | `String`    | Subscription level (`basic`, `professional`, `enterprise`)                  |
| `created_at`            | `DateTime`  | Timestamp of creation                                                       |

### 1.2. `platform_configs` Table (Future Enhancement)

For more advanced customization, we can add a `platform_configs` table to store platform-specific mappings.

**`platform_configs` Table Schema:**

| Column            | Type      | Description                                                                 |
| ----------------- | --------- | --------------------------------------------------------------------------- |
| `organization_id` | `Integer` | Foreign key to `organizations.id`                                           |
| `table_mappings`  | `JSON`    | Mappings for table names (e.g., `{"equipment": "tblEquipment"}`)         |
| `field_mappings`  | `JSON`    | Mappings for field names (e.g., `{"equipment.serial_no": "SerialNo"}`) |
| `calculation_rules` | `JSON`    | Custom business logic formulas                                              |

## 2. Backend Architecture

### 2.1. Platform Abstraction Layer

The core of the new architecture is a **Platform Abstraction Layer** that isolates the main application from the specifics of each Softbase platform.

**Key Components:**

1.  **`PlatformServiceFactory`**: A factory that returns the correct service (`EvolutionService` or `LegacyService`) based on the tenant's `platform_type`.
2.  **`BasePlatformService`**: An abstract base class that defines the common interface for all platform services (e.g., `get_monthly_revenue`, `get_equipment_list`).
3.  **`EvolutionService`**: Implementation of `BasePlatformService` for Softbase Evolution. This will wrap the existing `AzureSQLService` and queries.
4.  **`LegacyService`**: Implementation of `BasePlatformService` for Softbase Legacy. This will contain the new queries and logic for the legacy platform.

**`PlatformServiceFactory` Implementation:**

```python
# src/services/platform_service_factory.py

from .evolution_service import EvolutionService
from .legacy_service import LegacyService

class PlatformServiceFactory:
    @staticmethod
    def get_service(organization):
        if organization.platform_type == 'evolution':
            return EvolutionService(organization)
        elif organization.platform_type == 'legacy':
            return LegacyService(organization)
        else:
            raise ValueError(f"Unsupported platform type: {organization.platform_type}")
```

### 2.2. Tenant-Aware Database Connections

The `AzureSQLService` will be modified to be tenant-aware, creating connections based on the organization's stored credentials.

**Updated `AzureSQLService`:**

```python
# src/services/azure_sql_service.py

class AzureSQLService:
    def __init__(self, organization):
        self.server = organization.db_server
        self.database = organization.db_name
        self.username = organization.db_username
        self.password = self._decrypt_password(organization.db_password_encrypted)
        # ... rest of the implementation ...

    def _decrypt_password(self, encrypted_password):
        # Decryption logic using Fernet
        pass

    def get_connection(self):
        # Connection logic using tenant-specific credentials
        pass
```

### 2.3. API Route Modifications

API routes will be updated to use the `PlatformServiceFactory` instead of directly calling the `AzureSQLService`.

**Example API Route:**

```python
# src/routes/department_reports.py

from flask import Blueprint, jsonify, g
from src.middleware.tenant_middleware import TenantMiddleware
from src.services.platform_service_factory import PlatformServiceFactory

department_reports_bp = Blueprint('department_reports', __name__)

@department_reports_bp.route('/api/reports/departments/service/monthly-revenue', methods=['GET'])
@TenantMiddleware.require_organization
def get_service_monthly_revenue():
    organization = g.current_organization
    platform_service = PlatformServiceFactory.get_service(organization)
    
    try:
        revenue_data = platform_service.get_service_monthly_revenue()
        return jsonify(revenue_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## 3. Frontend Architecture

### 3.1. Platform-Agnostic Components

The frontend components will be designed to be platform-agnostic. They will receive normalized data from the backend and will not contain any platform-specific logic.

**Data Normalization Example:**

Both `EvolutionService` and `LegacyService` will return data in the same format, even if the underlying database schemas are different.

```json
// Normalized monthly revenue data format
[
  { "month": "Jan", "amount": 100000 },
  { "month": "Feb", "amount": 120000 },
  ...
]
```

### 3.2. Feature Flagging and UI Customization

The UI will adapt to the tenant's platform and subscription tier.

-   **Report Availability**: The navigation menu will only show reports that are available for the tenant's platform.
-   **Feature Access**: UI elements for premium features (e.g., AI queries, custom reports) will be hidden or disabled based on the tenant's subscription.
-   **Custom Branding**: The UI can be customized with the tenant's logo and color scheme (white-labeling for enterprise tier).

## 4. Security Architecture

### 4.1. Credential Encryption

Database passwords will be encrypted at rest using the `cryptography` library.

**Encryption Key Management:**

-   The encryption key will be stored as an environment variable (`CREDENTIAL_ENCRYPTION_KEY`).
-   The key will be rotated periodically.

### 4.2. Tenant Isolation in Middleware

The `TenantMiddleware` will be the single point of entry for all tenant-aware requests, ensuring that the correct organization context is always set.

### 4.3. Role-Based Access Control (RBAC)

RBAC will be enforced at both the API and UI levels, ensuring that users can only access the data and features they are authorized for.

## 5. Onboarding and Migration

### 5.1. New Tenant Onboarding Workflow

1.  **Admin UI**: An admin dashboard will be created for adding and managing tenants.
2.  **Configuration**: The admin will enter the new tenant's name, platform type, and database credentials.
3.  **Credential Encryption**: The backend will encrypt and store the database password.
4.  **User Creation**: The admin will create the first user for the new organization.
5.  **Activation**: The organization is marked as active and can now be used.

### 5.2. Migration of Existing Tenant

The existing single tenant (`ben002`) will be migrated to the new multi-tenant structure without any downtime.

1.  **Create Organization Record**: A new record will be created in the `organizations` table for the existing tenant.
2.  **Update Users**: All existing users will be associated with the new organization.
3.  **Deploy Code**: The new multi-tenant code will be deployed.
4.  **Verification**: The application will be tested to ensure that the existing tenant's experience is unchanged.


---

# Phased Implementation Roadmap

This roadmap outlines a phased approach to implementing the multi-tenant architecture, minimizing risk and allowing for iterative development and testing.

## Phase 1: Foundational Backend Changes (2-3 weeks)

**Goal**: Implement the core multi-tenant backend infrastructure without affecting the existing application.

**Key Tasks**:

1.  **Update Database Schema**:
    -   Add `platform_type`, `db_server`, `db_name`, `db_username`, and `db_password_encrypted` columns to the `organizations` table.
2.  **Implement Credential Encryption**:
    -   Create a `CredentialManager` service for encrypting and decrypting database passwords.
3.  **Develop Platform Abstraction Layer**:
    -   Create `BasePlatformService` abstract class.
    -   Create `EvolutionService` that wraps the existing `AzureSQLService`.
    -   Create `PlatformServiceFactory`.
4.  **Refactor `AzureSQLService`**:
    -   Modify it to accept organization-specific connection details.
5.  **Update API Routes**:
    -   Refactor a few non-critical API routes to use the new `PlatformServiceFactory`.
6.  **Testing**:
    -   Create a new organization record for the existing tenant.
    -   Thoroughly test the refactored routes to ensure they work correctly for the existing tenant.

## Phase 2: Legacy Platform Integration (3-4 weeks)

**Goal**: Add support for the Softbase Legacy platform.

**Key Tasks**:

1.  **Schema Discovery**:
    -   Connect to a sample Softbase Legacy database.
    -   Map the schema and identify key tables and fields.
2.  **Develop `LegacyService`**:
    -   Implement the `BasePlatformService` interface for the Legacy platform.
    -   Write new SQL queries for the Legacy schema.
3.  **Data Normalization**:
    -   Ensure that `LegacyService` returns data in the same format as `EvolutionService`.
4.  **Refactor Core Reports**:
    -   Update the backend logic for the core reports (Dashboard, Service, Parts, Rental) to use the `PlatformServiceFactory`.
5.  **Testing**:
    -   Create a test organization for the Legacy platform.
    -   Thoroughly test the core reports with the Legacy tenant.

## Phase 3: Frontend and UI Enhancements (2-3 weeks)

**Goal**: Update the frontend to be multi-tenant aware.

**Key Tasks**:

1.  **Dynamic Navigation**: 
    -   Update the navigation menu to only show reports available for the tenant's platform.
2.  **Feature Flagging**:
    -   Implement UI controls to hide or disable features based on the tenant's subscription tier.
3.  **Admin Dashboard**:
    -   Create a new admin section for managing tenants, users, and subscriptions.
4.  **Custom Branding**:
    -   Add support for custom logos and color schemes (for enterprise tier).
5.  **Testing**:
    -   Test the UI with different tenant configurations (Evolution vs. Legacy, different subscription tiers).

## Phase 4: Full Rollout and Go-Live (1-2 weeks)

**Goal**: Migrate the existing tenant and onboard new tenants.

**Key Tasks**:

1.  **Migrate Existing Tenant**:
    -   Run the migration scripts to associate the existing tenant with the new multi-tenant structure.
2.  **Final Testing**:
    -   Perform a full regression test of the entire application.
3.  **Onboard New Tenants**:
    -   Use the new admin dashboard to onboard the first new forklift dealerships.
4.  **Monitoring and Support**:
    -   Closely monitor the application for any performance or security issues.
    -   Provide support to new tenants during the onboarding process.

---

## Resource Allocation and Team Roles

This project can be executed by the existing team, with a clear division of responsibilities.

-   **You (as the Product Architect)**: 
    -   Oversee the entire project.
    -   Make key architectural decisions.
    -   Review and approve all code changes.
-   **Claude Code (as the AI Developer)**:
    -   Implement the backend and frontend code changes.
    -   Write and run unit and integration tests.
-   **Manus (as the AI Architect)**:
    -   Provide architectural guidance and best practices.
    -   Create detailed implementation plans and documentation.
    -   Assist with debugging and troubleshooting.
