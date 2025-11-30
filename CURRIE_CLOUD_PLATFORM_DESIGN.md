# Currie Cloud Platform - Design Document

**Version:** 1.0
**Date:** November 2025
**Author:** Claude Code

---

## Executive Summary

The Currie Cloud Platform is a B2B SaaS solution that aggregates financial data from material handling dealerships across multiple ERP/DMS systems. The platform provides:

1. **For ERP/DMS Vendors** - A standardized integration point (charged monthly)
2. **For Dealers** - Access to their own financial reports and benchmarking (subscription)
3. **For Currie** - Aggregated industry insights across all participating dealers

---

## Business Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CURRIE CLOUD PLATFORM                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Softbase    │  │   DIS/Cai    │  │   e-Emphasys │   ...more    │
│  │  Evolution   │  │              │  │              │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         ▼                 ▼                 ▼                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              DATA INTEGRATION LAYER                          │   │
│  │         (Adapters for each ERP/DMS system)                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              NORMALIZED DATA WAREHOUSE                       │   │
│  │    (Standardized financial data across all dealers)         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│         ┌────────────────────┼────────────────────┐                │
│         ▼                    ▼                    ▼                │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐           │
│  │  Dealer    │      │  Currie    │      │  Industry  │           │
│  │  Reports   │      │  Analytics │      │ Benchmarks │           │
│  └────────────┘      └────────────┘      └────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Revenue Streams

| Customer | What They Pay For | Pricing Model |
|----------|-------------------|---------------|
| **ERP/DMS Vendors** | Integration certification & per-dealer data sync | Monthly per connected dealer |
| **Dealers** | Access to their reports + benchmarking | Monthly subscription (tiered) |
| **Currie Corporate** | Aggregate analytics & insights | Included / Premium tier |

---

## Current Currie Report Capabilities

The existing report extracts from Softbase Evolution:

### Financial Data
- **New Equipment** - Sales, COGS, Gross Profit, Units, Avg Sale Price
- **Used Equipment** - Sales, COGS, Gross Profit, Units
- **Rental** - Revenue, COGS, Gross Profit, Fleet Utilization
- **Service** - Labor Revenue, Parts on Service, COGS
- **Parts** - Counter Sales, COGS, Inventory Metrics
- **Trucking** - Revenue, COGS

### Expense Allocations
- Personnel Expenses (allocated by department)
- Operating Expenses
- Occupancy Expenses
- G&A Expenses

### Metrics
- AR Aging
- Service Calls Per Day
- Technician Count
- Parts Inventory Turnover
- Labor Efficiency Metrics

---

## Platform Architecture

### Option A: Centralized Cloud (Recommended)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRIE CLOUD (AWS/Azure)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   API       │     │   Web App   │     │   Admin     │       │
│  │   Gateway   │     │   (React)   │     │   Portal    │       │
│  └──────┬──────┘     └─────────────┘     └─────────────┘       │
│         │                                                       │
│  ┌──────▼──────────────────────────────────────────────┐       │
│  │              APPLICATION SERVICES                    │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │       │
│  │  │ Auth     │  │ Reports  │  │ Data     │          │       │
│  │  │ Service  │  │ Service  │  │ Sync     │          │       │
│  │  └──────────┘  └──────────┘  └──────────┘          │       │
│  └─────────────────────────────────────────────────────┘       │
│                          │                                      │
│  ┌───────────────────────▼─────────────────────────────┐       │
│  │              DATA LAYER                              │       │
│  │  ┌──────────────┐    ┌──────────────────────────┐  │       │
│  │  │ PostgreSQL   │    │ Data Warehouse           │  │       │
│  │  │ (App Data)   │    │ (Financial Data)         │  │       │
│  │  └──────────────┘    └──────────────────────────┘  │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Secure API / SFTP
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────┴─────┐       ┌─────┴─────┐       ┌─────┴─────┐
    │ Dealer A  │       │ Dealer B  │       │ Dealer C  │
    │ Softbase  │       │ DIS/Cai   │       │ e-Emphasys│
    └───────────┘       └───────────┘       └───────────┘
```

### Data Integration Options

#### Option 1: Direct Database Connection (Current Approach)
- **Pros:** Real-time data, full access
- **Cons:** Firewall issues, security concerns, requires VPN/IP whitelisting
- **Best for:** Dealers with IT staff who can configure access

#### Option 2: API Integration
- **Pros:** Secure, standardized, vendor-supported
- **Cons:** Depends on ERP vendor offering API
- **Best for:** Modern ERP systems with REST APIs

#### Option 3: File-Based Sync (SFTP)
- **Pros:** Works with any system, no firewall changes
- **Cons:** Not real-time, requires dealer to export files
- **Best for:** Legacy systems, dealers without IT

#### Option 4: Agent-Based Collection
- **Pros:** Automatic, works behind firewalls
- **Cons:** Requires installation at dealer
- **Best for:** High-volume dealers wanting automation

**Recommendation:** Support ALL options, let each dealer choose.

---

## Data Model

### Normalized Financial Schema

```sql
-- Core entities
CREATE TABLE dealers (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    currie_dealer_code VARCHAR(50),
    erp_system VARCHAR(50),  -- 'softbase_evolution', 'dis_cai', 'e_emphasys'
    subscription_tier VARCHAR(20),
    created_at TIMESTAMP
);

CREATE TABLE reporting_periods (
    id UUID PRIMARY KEY,
    dealer_id UUID REFERENCES dealers(id),
    period_start DATE,
    period_end DATE,
    status VARCHAR(20),  -- 'draft', 'submitted', 'approved'
    submitted_at TIMESTAMP,
    submitted_by VARCHAR(100)
);

-- Standardized financial data (normalized across all ERP systems)
CREATE TABLE department_financials (
    id UUID PRIMARY KEY,
    reporting_period_id UUID REFERENCES reporting_periods(id),
    department VARCHAR(50),  -- 'new_equipment', 'used_equipment', 'rental', 'service', 'parts', 'trucking'

    -- Revenue
    gross_sales DECIMAL(15,2),
    discounts DECIMAL(15,2),
    net_sales DECIMAL(15,2),

    -- Cost
    cost_of_goods_sold DECIMAL(15,2),

    -- Calculated
    gross_profit DECIMAL(15,2),
    gross_profit_margin DECIMAL(8,4),

    -- Units (where applicable)
    units_sold INTEGER,
    average_sale_price DECIMAL(15,2)
);

CREATE TABLE expense_allocations (
    id UUID PRIMARY KEY,
    reporting_period_id UUID REFERENCES reporting_periods(id),
    expense_category VARCHAR(50),  -- 'personnel', 'operating', 'occupancy', 'ga'
    department VARCHAR(50),
    amount DECIMAL(15,2),
    allocation_method VARCHAR(50)  -- 'direct', 'headcount', 'revenue', 'custom'
);

CREATE TABLE operational_metrics (
    id UUID PRIMARY KEY,
    reporting_period_id UUID REFERENCES reporting_periods(id),
    metric_name VARCHAR(100),
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(50)
);
```

### ERP Adapter Interface

Each ERP system needs an adapter that maps to the normalized schema:

```python
class ERPAdapter(ABC):
    """Base adapter that all ERP integrations must implement"""

    @abstractmethod
    def get_department_financials(self, start_date, end_date) -> List[DepartmentFinancial]:
        """Extract revenue/COGS/GP by department"""
        pass

    @abstractmethod
    def get_expense_allocations(self, start_date, end_date) -> List[ExpenseAllocation]:
        """Extract expense data"""
        pass

    @abstractmethod
    def get_operational_metrics(self, start_date, end_date) -> List[OperationalMetric]:
        """Extract KPIs (AR aging, tech count, etc.)"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify connectivity to ERP"""
        pass


class SoftbaseEvolutionAdapter(ERPAdapter):
    """Adapter for Softbase Evolution - ALREADY BUILT (currie_report.py)"""
    pass


class DISCaiAdapter(ERPAdapter):
    """Adapter for DIS/Cai systems - TO BE BUILT"""
    pass


class EEmphasysAdapter(ERPAdapter):
    """Adapter for e-Emphasys - TO BE BUILT"""
    pass
```

---

## MVP Feature Set

### Phase 1: Foundation (8-12 weeks)

| Feature | Description |
|---------|-------------|
| **Multi-tenant Core** | Dealer signup, authentication, organization management |
| **Softbase Adapter** | Refactor existing currie_report.py into adapter pattern |
| **Manual Data Entry** | Web form for dealers without integration |
| **Basic Reports** | Sales/COGS/GP report, exportable to Excel |
| **Admin Portal** | Manage dealers, view submissions |

### Phase 2: Integrations (12-16 weeks)

| Feature | Description |
|---------|-------------|
| **DIS/Cai Adapter** | Integration with DIS dealer management system |
| **e-Emphasys Adapter** | Integration with e-Emphasys |
| **Scheduled Sync** | Automatic nightly data pulls |
| **Data Validation** | Automated checks for data quality |

### Phase 3: Analytics (8-12 weeks)

| Feature | Description |
|---------|-------------|
| **Benchmarking** | Compare dealer to industry averages |
| **Trend Analysis** | Year-over-year, quarter-over-quarter |
| **Currie Dashboard** | Aggregate view across all dealers |
| **Custom Reports** | Report builder for advanced users |

---

## Security & Compliance

### Data Isolation (Critical)

Each dealer's data MUST be completely isolated:

```python
# Every query must include dealer filter
@require_dealer_context
def get_financials(dealer_id, period_id):
    # Middleware automatically adds: WHERE dealer_id = {current_dealer}
    return DepartmentFinancial.query.filter_by(
        dealer_id=g.current_dealer.id,
        reporting_period_id=period_id
    ).all()
```

### Access Control Matrix

| Role | See Own Data | See Aggregate | Manage Users | Manage All Dealers |
|------|--------------|---------------|--------------|-------------------|
| Dealer User | ✓ | ✗ | ✗ | ✗ |
| Dealer Admin | ✓ | ✗ | ✓ | ✗ |
| Currie Analyst | ✗ | ✓ | ✗ | ✗ |
| Currie Admin | ✓ | ✓ | ✓ | ✓ |

### Encryption

- Data at rest: AES-256
- Data in transit: TLS 1.3
- Database credentials: HashiCorp Vault or AWS Secrets Manager
- API keys: Rotated quarterly

---

## Technology Stack Recommendation

### Backend
- **Python/Flask** (leverage existing codebase) OR **Node.js/Express**
- **PostgreSQL** for application data
- **Snowflake/BigQuery** for analytics warehouse (optional, for scale)
- **Redis** for caching
- **Celery** for background jobs (data sync)

### Frontend
- **React** (leverage existing codebase)
- **Tailwind CSS**
- **Recharts** for visualizations

### Infrastructure
- **AWS** or **Azure**
- **Docker/Kubernetes** for deployment
- **Terraform** for infrastructure as code

### Integrations
- **Stripe** for billing
- **Auth0** or **AWS Cognito** for authentication
- **SendGrid** for email notifications

---

## Pricing Model Recommendation

### For ERP/DMS Vendors

| Tier | Monthly Fee | Includes |
|------|-------------|----------|
| Integration Partner | $500/month | API access, certification, support |
| Per Dealer Sync | $25-50/dealer/month | Data sync fees passed to vendor |

### For Dealers

| Tier | Monthly Fee | Features |
|------|-------------|----------|
| Basic | $99/month | Own reports, Excel export |
| Professional | $249/month | + Benchmarking, trend analysis |
| Enterprise | $499/month | + API access, custom reports, multiple locations |

### For Currie Corporate

- Platform hosting/maintenance fees
- OR percentage of dealer subscriptions
- OR flat annual license

---

## Migration Path from Current System

### Step 1: Refactor Currie Report (2-4 weeks)
```
currie_report.py → SoftbaseEvolutionAdapter
```
- Extract data fetching into adapter pattern
- Keep existing functionality working
- Add multi-tenant support

### Step 2: Build Platform Core (4-6 weeks)
- New database schema
- Dealer management
- Reporting period workflow
- Basic authentication

### Step 3: Deploy Alongside Existing (2 weeks)
- Run new platform in parallel
- Validate data matches existing reports
- Onboard pilot dealers

### Step 4: Scale (Ongoing)
- Add ERP adapters as vendors sign up
- Onboard dealers
- Build analytics features

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ERP vendor doesn't cooperate | Can't integrate | Offer file-based fallback |
| Data quality varies by dealer | Bad reports | Validation rules, manual review |
| Low dealer adoption | No revenue | Start with existing Currie dealers, offer free trial |
| Security breach | Reputation damage | SOC2 compliance, regular audits |
| Competitor builds similar | Market share | First mover advantage, deep integrations |

---

## Success Metrics

| Metric | Year 1 Target | Year 3 Target |
|--------|---------------|---------------|
| Connected Dealers | 50 | 500 |
| ERP Integrations | 3 | 10 |
| Monthly Recurring Revenue | $25K | $250K |
| Data Accuracy Rate | 95% | 99% |
| Dealer Retention | 80% | 90% |

---

## Next Steps

1. **Validate with Currie** - Review this design, confirm business model
2. **Identify Pilot Dealers** - 5-10 dealers across different ERP systems
3. **Contact ERP Vendors** - Gauge interest in integration partnership
4. **Build MVP** - Start with Softbase (already done) + manual entry
5. **Pilot Launch** - 3-month pilot with select dealers
6. **Iterate** - Refine based on feedback before broader launch

---

## Appendix: Currie Report Data Mapping

### Current Softbase → Normalized Schema

| Softbase Source | Normalized Field | Notes |
|-----------------|------------------|-------|
| `GLDetail` (410xxx accounts) | `gross_sales` | Revenue accounts |
| `GLDetail` (510xxx accounts) | `cost_of_goods_sold` | COGS accounts |
| `InvoiceReg` | `units_sold` | Count of invoices by type |
| `Employee` (Dept 40) | `technician_count` | Service techs |
| `ben002.GLMTD` | `expense_allocations` | Monthly totals by GL |

### Data Freshness Requirements

| Data Type | Minimum Frequency | Ideal |
|-----------|-------------------|-------|
| Financial (P&L) | Monthly | Weekly |
| AR Aging | Weekly | Daily |
| Inventory Metrics | Monthly | Weekly |
| Operational KPIs | Monthly | Real-time |
