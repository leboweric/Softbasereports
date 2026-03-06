# Softbase Evolution Database Schema Documentation

**Database**: Azure SQL Server  
**Schema**: ben002  
**Last Updated**: 2026-03-02 - Comprehensive audit: added 25+ missing Azure SQL tables, 12+ PostgreSQL tables, undocumented columns, and Depreciation view

## CRITICAL ACCESS INFORMATION
- **Azure SQL has IP firewall restrictions** - NO local access allowed
- **All queries must go through Railway-deployed backend**
- **Use web interface or deployed API endpoints only**

## Complete Table Documentation

### Core Business Tables

#### Equipment (21,291 rows)
**Purpose**: Equipment inventory master  
**Primary Key**: SerialNo or UnitNo (both unique identifiers)

| Column | Type | Notes |
|--------|------|-------|
| UnitNo | nvarchar | Unit number identifier |
| SerialNo | nvarchar | Serial number (primary identifier) |
| Make | nvarchar | Equipment manufacturer |
| Model | nvarchar | Equipment model |
| ModelYear | int | Year of manufacture |
| RentalStatus | nvarchar | Current rental status (see values below) |
| Cost | decimal | Purchase cost |
| Sell | decimal | Selling price |
| Retail | decimal | Retail price |
| Customer | bit | Boolean flag (not the customer ID!) |
| CustomerNo | nvarchar | Actual customer number (join to Customer.Number) |
| DayRent | decimal | Daily rental rate |
| WeekRent | decimal | Weekly rental rate |
| MonthRent | decimal | Monthly rental rate |
| Location | nvarchar | Current location |
| InventoryDept | int | Inventory department code |
| DeletionTime | datetime | Soft delete timestamp |
| IsDeleted | bit | Deletion flag |
| WebRentalFlag | bit | Available for web rental |
| RentalYTD | decimal | Year-to-date rental revenue |
| RentalITD | decimal | Inception-to-date rental revenue |
| ControlNo | nvarchar | Control number |

**Important Notes**:
- NO Description field exists
- NO StockNo field exists  
- Customer field is a boolean, CustomerNo is the actual reference
- Join to Customer table using CustomerNo = Customer.Number

**Common RentalStatus Values**:
- 'Available'
- 'Ready To Rent'
- 'On Rent'
- 'Hold'
- 'Sold' (needs filtering)
- 'Disposed' (needs filtering)
- 'Transferred' (needs filtering)

**CRITICAL DISCOVERY**: RentalStatus field is NOT reliable for determining actual rental status!

**Inventory Department Categories** (Updated 2025-10-17):
- **Department 60**: Rental Equipment (Primary rental inventory)
- **Department 10**: New Equipment 
- **Department 20**: Used Equipment (includes batteries/chargers by keyword)
- **Department 30**: Allied Equipment

**Actual Rental Status Detection**:
The RentalStatus field is unreliable. Use this pattern instead:
```sql
-- CORRECT way to find equipment on rental
SELECT e.*, c.Name as customer_name, c.State as location_state
FROM Equipment e
LEFT JOIN Customer c ON e.CustomerNo = c.Number
LEFT JOIN (
    SELECT DISTINCT wr.SerialNo, 1 as is_on_rental
    FROM WORental wr
    INNER JOIN WO wo ON wr.WONo = wo.WONo
    WHERE wo.Type = 'R' 
    AND wo.ClosedDate IS NULL
    AND wo.WONo NOT LIKE '9%'  -- CRITICAL: Exclude quotes!
) rental_check ON e.SerialNo = rental_check.SerialNo
WHERE e.InventoryDept = 60  -- Rental department only
AND (e.Customer = 0 OR e.Customer IS NULL)  -- Customer-owned filter
```

**Equipment Categorization Business Rules** (Updated 2025-10-17):
1. **Allied Equipment**: Keyword 'allied' in Make/Model OR InventoryDept = 30
2. **Batteries & Chargers**: Keywords 'battery', 'charger', 'batt', 'charge' in Model
3. **Rental Equipment**: InventoryDept = 60 (overrides keywords)
4. **New Equipment**: InventoryDept = 10 
5. **Used Equipment**: InventoryDept = 20 (minus batteries caught by keywords)

**QUOTES vs WORK ORDERS** (Critical Discovery):
- **Quotes**: WO numbers starting with '9' (e.g., 91600003) - NOT actual rentals
- **Work Orders**: Numbers starting with '13', '16', etc. (e.g., 130000713, 16001378)
- **Impact**: Quotes can appear in WORental with Type='R' but aren't real rentals
- **Solution**: Always filter `wo.WONo NOT LIKE '9%'` when finding rentals

---

#### Customer (2,227 rows)
**Purpose**: Customer master records  
**Primary Key**: Id (bigint)  
**Business Key**: Number (nvarchar) - USE THIS FOR JOINS

| Column | Type | Notes |
|--------|------|-------|
| Id | bigint | Primary key (don't use for joins) |
| Number | nvarchar | Customer number (USE THIS for joins) |
| Name | nvarchar | Customer name |
| Address | nvarchar | Street address |
| City | nvarchar | City |
| State | nvarchar | State code |
| ZipCode | nvarchar | Postal code |
| Terms | nvarchar | Payment terms |
| CreditHoldFlag | bit | Credit hold status |
| Taxable | bit | Taxable customer |
| TaxCode | nvarchar | Tax code |
| Salesman1-6 | nvarchar | Sales rep assignments |
| Contact | nvarchar | Primary contact |
| Phone1 | nvarchar | Primary phone |

**Important Notes**:
- NO Balance field - use ARDetail for AR balances
- NO YTD fields - use Sales view for YTD sales
- Always join using Number field, not Id

---

#### InvoiceReg (5,148 rows)
**Purpose**: Invoice header/register  
**Primary Key**: InvoiceNo (int)

| Column | Type | Notes |
|--------|------|-------|
| InvoiceNo | int | Invoice number (PK) |
| InvoiceDate | datetime | Invoice date |
| GrandTotal | decimal | Total invoice amount |
| Customer | bit | Customer flag (NOT the ID!) |
| BillTo | nvarchar | Customer number |
| BillToName | nvarchar | Customer name |
| SaleCode | nvarchar | Department code (SVE, PRT, etc.) |
| SaleBranch | smallint | Branch code |
| SaleDept | smallint | Department number |
| LaborTaxable | decimal | Taxable labor revenue |
| LaborNonTax | decimal | Non-taxable labor revenue |
| PartsTaxable | decimal | Taxable parts revenue |
| PartsNonTax | decimal | Non-taxable parts revenue |
| MiscTaxable | decimal | Taxable misc revenue |
| MiscNonTax | decimal | Non-taxable misc revenue |
| EquipmentTaxable | decimal | Taxable equipment revenue |
| EquipmentNonTax | decimal | Non-taxable equipment revenue |
| RentalTaxable | decimal | Taxable rental revenue |
| RentalNonTax | decimal | Non-taxable rental revenue |
| EquipmentCost | decimal | Cost of equipment sold |
| LaborCost | decimal | Cost of labor |
| PartsCost | decimal | Cost of parts |
| MiscCost | decimal | Cost of misc items |
| RentalCost | decimal | Cost of rentals |
| TotalTax | decimal | Total tax amount |
| ControlNo | nvarchar | Control number (used for WO/Equipment cross-reference) |
| SerialNo | nvarchar | Equipment serial number |
| WONo | nvarchar | Work order number (sometimes same as InvoiceNo) |

**Important Notes**:
- Customer field is boolean, BillTo has actual customer number
- NO Department field - use SaleCode or SaleDept
- Cost fields enable gross profit calculations
- **Key Join**: InvoiceReg.InvoiceNo = WO.WONo links invoices to work orders (enables access to WO.Salesman, WO.Technician, etc.)
- **Key Join**: InvoiceReg.WONo also maps to WO.WONo (sometimes InvoiceNo and WONo are the same value)

---

#### WO (Work Orders) (6,879 rows)
**Purpose**: Work order headers  
**Primary Key**: WONo (nvarchar)

| Column | Type | Notes |
|--------|------|-------|
| WONo | nvarchar | Work order number (PK) |
| Type | char | Order type (S=Service, R=Rental, P=Parts, I=Internal) |
| BillTo | nvarchar | Customer number |
| UnitNo | nvarchar | Equipment unit number |
| SerialNo | nvarchar | Equipment serial number |
| OpenDate | datetime | Date opened |
| CompletedDate | datetime | Date completed |
| ClosedDate | datetime | Date closed/invoiced |
| Technician | nvarchar | Assigned technician |
| ShipTo | nvarchar | Ship-to customer number (join to Customer.Number) |
| RentalContractNo | int | Linked rental contract |
| ControlNo | nvarchar | Control number |
| DeletionTime | datetime | Soft delete timestamp |
| IsDeleted | bit | Deletion flag |

**Additional Columns Discovered**:
- **ShipTo**: Ship-to customer number — different from BillTo. Used in rental reports to find the physical location of rented equipment. Join to Customer.Number.
- **ControlNo**: Control number — used for cross-referencing with InvoiceReg.ControlNo
- **Salesman**: Assigned salesman code/name. Links to the Salesman lookup table. May be NULL for some WOs. Used in Parts Contest to determine which salesman is associated with each work order/invoice.
- **Writer**: The person who wrote/created the work order. Different from Salesman (who is the sales rep assigned to the customer).

**CRITICAL DISCOVERY (2025-10-17): Status and Location columns DO NOT EXIST!**
- ❌ **Status column**: Does not exist despite documentation
- ❌ **Location column**: Does not exist despite documentation  
- ✅ **Verified columns**: WONo, Type, BillTo, UnitNo, SerialNo, OpenDate, CompletedDate, ClosedDate, Technician

**Work Order Types**:
- **S** = Service (field service)
- **SH** = Shop (internal shop operations) - **USE THIS for shop work order filtering**
- **PM** = Preventive Maintenance (service)
- **P** = Parts only
- **R** = Rental 
- **E** = Equipment
- **I** = Internal

**🚨 CRITICAL: Quote vs Work Order Detection**
**Quotes are NOT work orders but appear in WO table!**
- **Quotes**: WONo starts with '9' (e.g., 94500009, 94500032, 94500036)
- **Work Orders**: WONo starts with '1' or other digits (e.g., 140000582, 140001000, 145000017)
- **ALWAYS filter**: `WHERE WONo NOT LIKE '9%'` to exclude quotes from work order queries
- **Impact**: Without quote exclusion, you get 3x more records than expected

**Lifecycle**:
- **Open**: OpenDate set, ClosedDate NULL
- **Completed**: CompletedDate set, ClosedDate NULL (awaiting invoice)
- **Closed**: ClosedDate set (invoiced)

**Shop Work Order Filtering (Updated 2025-10-17)**:
```sql
-- CORRECT pattern for shop work orders
WHERE Type = 'SH'                -- Shop work orders only (not 'S', 'PM')  
  AND ClosedDate IS NULL         -- Open work orders only
  AND WONo NOT LIKE '9%'         -- CRITICAL: Exclude quotes!
  
-- Expected result: ~41 open shop work orders (not 955 or 102)
```

---

#### Parts (11,413 rows)
**Purpose**: Parts inventory master  
**Primary Key**: Id (bigint)

| Column | Type | Notes |
|--------|------|-------|
| Id | bigint | Primary key |
| PartNo | nvarchar | Part number |
| Warehouse | nvarchar | Warehouse location |
| Description | nvarchar | Part description |
| OnHand | decimal | Current inventory on hand |
| Allocated | decimal | Allocated quantity |
| OnOrder | decimal | On order quantity |
| BackOrder | decimal | Backordered quantity |
| Cost | decimal | Unit cost |
| List | decimal | List price |
| MinStock | decimal | Minimum stock level |
| MaxStock | decimal | Maximum stock level |
| Bin | nvarchar | Primary bin location |

**Important Notes**:
- This is the actual parts table (NOT NationalParts which is empty!)
- NO Supplier field
- NO QtyOnHand - use OnHand field
- NO Price field - use List for list price

---

### Transaction Tables

#### WOLabor (6,401 rows)
**Purpose**: Work order labor details

| Column | Type | Notes |
|--------|------|-------|
| WONo | nvarchar | Work order number |
| MechanicName | nvarchar | Technician name |
| Hours | decimal | Labor hours |
| Cost | decimal | Labor cost |
| Sell | decimal | Labor sell price |
| DateOfLabor | datetime | Date work performed |

---

#### WOParts (10,381 rows)
**Purpose**: Parts used on work orders

| Column | Type | Notes |
|--------|------|-------|
| WONo | nvarchar | Work order number |
| PartNo | nvarchar | Part number |
| Description | nvarchar | Part description |
| Qty | decimal | Quantity used |
| BOQty | decimal | Backorder quantity |
| Cost | decimal | Unit cost |
| Sell | decimal | Unit sell price |

**Important**: Calculate extended amounts as Sell * Qty

---

#### WOMisc (7,832 rows)
**Purpose**: Miscellaneous work order charges

| Column | Type | Notes |
|--------|------|-------|
| WONo | nvarchar | Work order number |
| Description | nvarchar | Charge description |
| Cost | decimal | Cost amount |
| Sell | decimal | Sell amount |
| Taxable | bit | Taxable flag |

---

#### WOQuote (CRITICAL DISCOVERY - 2025-10-18)
**Purpose**: Stores quoted/estimated amounts for work orders  
**Critical**: This is where quoted labor amounts are stored, NOT in WOMisc!

| Column | Type | Notes |
|--------|------|-------|
| WONo | nvarchar | Work order number |
| Type | char | Quote type (L=Labor, P=Parts, M=Misc) |
| Description | nvarchar | Quote item description |
| Amount | decimal | Quoted amount (use this for calculations) |
| Branch | int | Branch code |
| Dept | int | Department code |
| SaleCode | nvarchar | Sale code |

**Important Discovery (2025-10-18)**:
- Quoted labor for shop work orders is stored here with Type = 'L'
- The Amount column contains the quoted dollar amount
- DO NOT look for quoted labor in WOMisc - it's not there!
- Standard shop labor rate: $189/hour

**Example Query for Shop Work Order Quotes**:
```sql
SELECT WONo, SUM(Amount) as QuotedAmount
FROM [ben002].WOQuote
WHERE Type = 'L'  -- L = Labor quotes only
GROUP BY WONo
```

---

#### WORental
**Purpose**: Links work orders to rental equipment

| Column | Type | Notes |
|--------|------|-------|
| WONo | nvarchar | Work order number |
| SerialNo | nvarchar | Equipment serial number |
| UnitNo | nvarchar | Equipment unit number |
| ControlNo | nvarchar | Control number |
| RentalContractNo | int | Rental contract reference |

---

### Financial Tables

#### ARDetail (8,413 rows)
**Purpose**: Accounts receivable transactions

| Column | Type | Notes |
|--------|------|-------|
| CustomerNo | nvarchar | Customer number |
| Amount | decimal | Transaction amount |
| InvoiceNo | int | Invoice number |
| CheckNo | nvarchar | Check number |
| Due | datetime | Due date |
| EntryType | nvarchar | Transaction type |
| EntryDate | datetime | Entry date |
| EffectiveDate | datetime | Effective date |
| ApplyToInvoiceNo | int | Applied to invoice |
| AccountNo | nvarchar | GL account |
| HistoryFlag | bit | Historical record flag |

**Important Notes**:
- NO Balance column - use Amount for outstanding
- Group by CustomerNo, InvoiceNo for aging (NOT by Due date!)
- Positive amounts are charges, negative are payments

---

#### APDetail (3,331 rows)
**Purpose**: Accounts payable transactions

| Column | Type | Notes |
|--------|------|-------|
| VendorNo | nvarchar | Vendor number |
| Amount | decimal | Transaction amount |
| APInvoiceNo | nvarchar | AP invoice number |
| CheckNo | nvarchar | Check number |
| DueDate | datetime | Due date |
| AccountNo | nvarchar | GL account |

---

#### GLDetail (64,180 rows)
**Purpose**: General ledger transactions

| Column | Type | Notes |
|--------|------|-------|
| AccountNo | nvarchar | GL account number |
| Amount | decimal | Transaction amount |
| EffectiveDate | datetime | Effective date |
| Journal | nvarchar | Journal type |
| Source | nvarchar | Transaction source |
| CustomerNo | nvarchar | Customer reference |
| VendorNo | nvarchar | Vendor reference |
| Posted | bit | Posted flag (1 = posted, filter required) |

**ACCOUNTING INVENTORY INSIGHTS** (Updated 2025-10-17):
**Key GL Accounts for Equipment Inventory:**
- **131000**: New Equipment (direct GL balance used)
- **131200**: Used Equipment + Batteries (requires split allocation)
- **131300**: Allied Equipment (direct GL balance used)
- **183000**: Rental Equipment Gross Value
- **193000**: Accumulated Depreciation (negative balance, subtract from 183000)

**Inventory Report Date Filtering** (Period: March 1, 2025 - October 31, 2025):
```sql
-- Standard inventory GL balance query
SELECT COALESCE(SUM(Amount), 0) as Balance
FROM GLDetail  
WHERE AccountNo = '131300'  -- or other account
  AND Posted = 1            -- CRITICAL: Only posted transactions
  AND EffectiveDate >= '2025-03-01'
  AND EffectiveDate <= '2025-10-31'
```

**GL Account Split Logic for 131200:**
- Total GL 131200 balance needs allocation between:
  - Used Equipment: ~$155,100.30 (75% allocation)
  - Batteries & Chargers: ~$52,116.39 (25% allocation)
- Logic: Based on equipment categorization by keyword analysis

**Rental Equipment Net Book Value Calculation:**
```sql
-- Rental equipment shows net book value
Rental_Net_Value = GL_183000_Balance - ABS(GL_193000_Balance)
```

**YTD Depreciation Calculation:**
```sql
-- YTD Depreciation for period March 1 - October 31, 2025
SELECT COALESCE(ABS(SUM(Amount)), 0) as YTD_Depreciation
FROM GLDetail
WHERE AccountNo = '193000'  -- Accumulated Depreciation
AND Posted = 1
AND EffectiveDate >= '2025-03-01' 
AND EffectiveDate <= '2025-10-31'
```

**CRITICAL**: Always use Posted = 1 filter and specific date ranges for accounting reports!

---

### Rental-Specific Tables

#### RentalHistory (11,568 rows)
**Purpose**: Monthly rental revenue by equipment

| Column | Type | Notes |
|--------|------|-------|
| Id | bigint | Primary key |
| SerialNo | nvarchar | Equipment serial number |
| Year | smallint | Rental year |
| Month | smallint | Rental month |
| DaysRented | int | Days rented in month |
| RentAmount | decimal | Rental revenue for month |
| DeletionTime | datetime | Soft delete timestamp |

**Usage**:
- Current rentals: Year = YEAR(GETDATE()) AND Month = MONTH(GETDATE()) AND DaysRented > 0
- Join to Equipment on SerialNo for equipment details
- Join Equipment.CustomerNo to Customer.Number for customer info

---

#### RentalContract (318 rows)
**Purpose**: Rental agreement headers

| Column | Type | Notes |
|--------|------|-------|
| RentalContractNo | int | Contract number |
| CustomerNo | nvarchar | Customer number (join to Customer.Number) |
| SerialNo | nvarchar | Equipment serial number |
| StartDate | datetime | Contract start |
| EndDate | datetime | Contract end |
| DeliveryCharge | decimal | Delivery fee |
| PickupCharge | decimal | Pickup fee |

**Additional Notes**:
- Join to Customer using CustomerNo = Customer.Number
- Join to Equipment using SerialNo = Equipment.SerialNo

---

#### RentalContractEquipment
**Purpose**: Links rental contracts to specific equipment items

| Column | Type | Notes |
|--------|------|-------|
| RentalContractNo | int | Rental contract number (join to RentalContract) |
| SerialNo | nvarchar | Equipment serial number |

---

### Reference / Lookup Tables

#### GL (General Ledger Summary)
**Purpose**: Monthly GL account balances (summary-level, different from GLDetail which has individual transactions)

| Column | Type | Notes |
|--------|------|-------|
| AccountNo | nvarchar | GL account number |
| Year | int | Fiscal year |
| Month | int | Fiscal month |
| Amount | decimal | Monthly amount |
| Balance | decimal | Account balance |

**Important Notes**:
- This is the **summary/balance** table — use for period-end balances
- **GLDetail** has individual transactions — use for date-range queries
- Join to ChartOfAccounts on AccountNo for account descriptions

---

#### ChartOfAccounts
**Purpose**: GL account master — descriptions and categorization

| Column | Type | Notes |
|--------|------|-------|
| AccountNo | nvarchar | GL account number (PK) |
| Description | nvarchar | Account description/name |

**Usage**: Join to GL or GLDetail on AccountNo to get human-readable account names

---

#### Branch
**Purpose**: Branch/location definitions

| Column | Type | Notes |
|--------|------|-------|
| Number | int | Branch number (PK) |
| Name | nvarchar | Branch name |

**Important**: Branch names differ between tenants (Bennett: Main/Shop; IPS: Canton/Cleveland). Always use dynamic lookups.

---

#### Dept
**Purpose**: Department definitions — **critical for multi-tenant dynamic lookups**

| Column | Type | Notes |
|--------|------|-------|
| Dept | int | Department number (PK) |
| Title | nvarchar | Department title/description |
| SaleGroup | int | Sale group reference |

**CRITICAL**: Dept numbers mean different things at different tenants. Always match by `Title` keywords, never hardcode Dept numbers.

---

#### Salesman
**Purpose**: Sales representative lookup table — maps salesman codes to names

| Column | Type | Notes |
|--------|------|-------|
| Name | nvarchar | Salesman name (e.g., "Rod Hauer", "Todd Auge", "Kevin Buckman") |
| SalesGroup | int | Sales group (links to Dept.SaleGroup) |
| DeletionTime | datetime | Soft delete timestamp (NULL = active) |

**Important Notes**:
- This table may NOT exist in all tenant schemas (confirmed in ben002/Bennett, may be missing in others)
- Always wrap queries in try/except for graceful degradation
- Filter by `DeletionTime IS NULL` to get only active salesmen
- To find which salesman is associated with an invoice: JOIN InvoiceReg.InvoiceNo = WO.WONo, then use WO.Salesman

---

#### Vendor
**Purpose**: Vendor/supplier master records

| Column | Type | Notes |
|--------|------|-------|
| VendorNo | nvarchar | Vendor number (PK, join from APDetail.VendorNo) |
| Name | nvarchar | Vendor name |

---

#### Company
**Purpose**: Company-level configuration and information

**Usage**: Referenced in control number reports for company-level data.

---

### Additional Transaction Tables

#### Sales
**Purpose**: Sales summary data by customer

| Column | Type | Notes |
|--------|------|-------|
| CustomerNo | nvarchar | Customer number (join to Customer.Number) |

**Usage**: Join from Customer for YTD sales data (Customer table has NO YTD fields).

---

#### PartsSales
**Purpose**: Parts sales transaction data

| Column | Type | Notes |
|--------|------|-------|
| PartNo | nvarchar | Part number (join to Parts.PartNo) |

---

#### InvDetail (Invoice Detail)
**Purpose**: Invoice line-item details

| Column | Type | Notes |
|--------|------|-------|
| InvoiceNo | int | Invoice number (join to InvoiceReg.InvoiceNo) |
| PartNo | nvarchar | Part number |
| Quantity | decimal | Quantity sold |

**Usage**: Join to InvoiceReg for invoice headers, join to Parts for part details. Used in parts inventory analysis.

---

#### InvoiceSales
**Purpose**: Invoice-level sales summary data

**Usage**: Referenced in dashboard and department reports as an alternative to InvoiceReg for certain sales aggregations.

---

#### InvoicePartsDetail
**Purpose**: Detailed parts information on invoices

**Usage**: Referenced in softbase_reports for parts-specific invoice analysis.

---

### Service / Warranty Tables

#### ServiceClaim
**Purpose**: Warranty/service claim records

| Column | Type | Notes |
|--------|------|-------|
| Id | bigint | Primary key |
| RepairCodeId | int | Repair code reference |

**Usage**: Used in service reports and warranty claim tracking.

---

#### ServiceClaimRepairCode
**Purpose**: Links service claims to repair codes (junction table)

| Column | Type | Notes |
|--------|------|-------|
| ServiceClaimId | bigint | Service claim ID (join to ServiceClaim.Id) |
| RepairCodeId | int | Repair code ID (join to RepairCode.Id) |

---

#### RepairCode
**Purpose**: Repair code definitions for service claims

| Column | Type | Notes |
|--------|------|-------|
| Id | int | Primary key |
| Description | nvarchar | Repair code description |

---

### Preventive Maintenance Tables

#### PM (Preventive Maintenance)
**Purpose**: Preventive maintenance schedule records

| Column | Type | Notes |
|--------|------|-------|
| ShipTo | nvarchar | Ship-to customer number (join to Customer.Number) |
| SerialNo | nvarchar | Equipment serial number (join to Equipment.SerialNo) |

**Usage**: Used in PM reports, joined to Customer and Equipment for full context.

---

#### LPM (Labor PM)
**Purpose**: Labor records specific to preventive maintenance

**Usage**: Referenced in PM diagnostics.

---

### Depreciation View

#### Depreciation (515 rows — view, not table)
**Purpose**: Asset depreciation schedules — contains all depreciation/book value data  
**Type**: View (not a base table)  
**Coverage**: Primarily rental equipment

| Column | Type | Notes |
|--------|------|-------|
| SerialNo | nvarchar(100) | Links to Equipment.SerialNo |
| StartingValue | decimal | Original/gross book value |
| NetBookValue | decimal | Current net book value |
| LastUpdatedAmount | decimal | Monthly depreciation amount |
| Method | nvarchar(50) | Depreciation method (typically "Straight Line") |
| TotalMonths | smallint | Total depreciation period |
| RemainingMonths | smallint | Months remaining |
| ResidualValue | decimal | Salvage value |
| DepreciationGroup | nvarchar(50) | Category (e.g., "Rental") |
| Inactive | bit (NOT NULL) | 0 = active, 1 = inactive |
| DebitAccount | nvarchar(50) | GL account for depreciation expense |
| CreditAccount | nvarchar(50) | GL account for accumulated depreciation |
| LastUpdated | datetime | Last depreciation update |
| LastUpdatedBy | nvarchar(50) | Who updated |

**Important Notes**:
- **NOT all equipment has depreciation records** — only ~515 of 21,000+ items
- Use `WHERE d.Inactive = 0` to filter active records (NOT `IsDeleted` which doesn't exist here)
- Accumulated Depreciation = StartingValue - NetBookValue
- Join: `LEFT JOIN {schema}.Depreciation d ON e.SerialNo = d.SerialNo AND d.Inactive = 0`

---

### Equipment History / Tracking Tables

#### EquipmentHistory
**Purpose**: Historical equipment transaction records

| Column | Type | Notes |
|--------|------|-------|
| WONo | nvarchar | Work order number |

**Usage**: Join to InvoiceReg for equipment sale/transaction history.

---

#### EquipmentRemoved
**Purpose**: Records of equipment removed from inventory

**Usage**: Referenced in rental availability diagnostics to track removed units.

---

#### EQControlNoChange
**Purpose**: Audit trail for equipment control number changes

**Usage**: Referenced in control number reports for tracking control number modifications.

---

### User / Employee Tables (Azure SQL)

#### Users
**Purpose**: Softbase user accounts

**Usage**: Referenced in employee lookup for user identification.

---

#### Employee
**Purpose**: Employee master records

**Usage**: Referenced in employee lookup and diagnostic routes.

---

#### AbpUsers
**Purpose**: ABP Framework user records (alternative user table)

**Usage**: Referenced in employee lookup as a fallback user source.

---

#### Accounts
**Purpose**: Account definitions (may overlap with ChartOfAccounts)

| Column | Type | Notes |
|--------|------|-------|
| AccountNo | nvarchar | Account number |

**Usage**: Referenced in January expense investigation. Relationship to ChartOfAccounts unclear — may be an alternative/legacy table.

---

### PostgreSQL Integration Tables (Railway)

#### minitrac_equipment (28,000+ rows)
**Purpose**: Self-hosted Minitrac equipment database (replaces $600/month subscription)  
**Database**: PostgreSQL on Railway  
**Last Import**: 2025-10-17

| Column | Type | Notes |
|--------|------|-------|
| id | serial | PostgreSQL primary key |
| equipment_id | varchar | Original Minitrac equipment ID |
| make | varchar | Equipment manufacturer |
| model | varchar | Equipment model |
| serial_number | varchar | Serial number |
| year | integer | Model year |
| category | varchar | Equipment category |
| subcategory | varchar | Equipment subcategory |
| description | text | Full description |
| specifications | jsonb | Technical specifications |
| attachments | jsonb | Available attachments |
| created_at | timestamp | Record creation |
| updated_at | timestamp | Last update |

**Usage Patterns**:
- Full-text search across make, model, description
- Category-based filtering for equipment types
- JSON specifications for technical details
- Replaces external Minitrac subscription service

#### work_order_notes (custom table)
**Purpose**: Custom work order notes not in Softbase  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| id | serial | Primary key |
| wo_no | varchar | Work order number (links to WO.WONo) |
| note_text | text | Note content |
| created_by | varchar | User who created note |
| created_at | timestamp | Creation timestamp |
| updated_at | timestamp | Last update |

**Usage**:
- Auto-save functionality with 1-second debounce
- Included in work order CSV exports
- Supplements Softbase work order data

#### knowledge_base
**Purpose**: Knowledge base articles for the support system  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| id | serial | Primary key |
| title | varchar | Article title |
| content | text | Article content |
| created_at | timestamp | Creation timestamp |
| updated_at | timestamp | Last update |

#### kb_attachments
**Purpose**: File attachments for knowledge base articles  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| id | serial | Primary key |
| kb_id | integer | Knowledge base article ID |

#### support_ticket
**Purpose**: Support ticket records  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| id | serial | Primary key |
| subject | varchar | Ticket subject |
| message | text | Ticket description |
| type | varchar | Ticket type (bug, enhancement, question) |
| status | varchar | Ticket status (open, in_progress, resolved, closed) |
| priority | varchar | Priority (low, medium, high, critical) |
| page_url | varchar | URL of the affected page |
| organization_id | integer | Organization FK |
| created_by | integer | User FK |
| reopened_count | integer | Number of times reopened |
| created_at | timestamp | Creation timestamp |
| updated_at | timestamp | Last update |

#### support_ticket_comment
**Purpose**: Comments on support tickets  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| id | serial | Primary key |
| ticket_id | integer | FK to support_ticket.id |
| message | text | Comment text |
| comment_type | varchar | Type (user_comment, system_note, system_resolution) |
| is_internal | boolean | Internal-only flag |
| created_by_name | varchar | Author name |
| created_at | timestamp | Creation timestamp |

#### support_ticket_attachment
**Purpose**: File attachments on support tickets  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| id | serial | Primary key |
| ticket_id | integer | FK to support_ticket.id |

#### manual_commissions
**Purpose**: Manually entered commission adjustments  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| id | serial | Primary key |

**Usage**: Used by the sales commission system for manual overrides.

#### sales_rep_comp_settings
**Purpose**: Sales representative compensation configuration  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| id | serial | Primary key |

**Usage**: Stores commission rates, thresholds, and rules per sales rep.

#### report_visibility
**Purpose**: Controls which reports/tabs are visible per organization  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| id | serial | Primary key |
| page_id | varchar | Page identifier |
| tab_id | varchar | Tab identifier |
| is_visible | boolean | Visibility flag |
| organization_id | integer | Organization FK |

**Usage**: Enables org-specific report visibility. Used to scope new reports to requesting orgs.

#### service_assistant_queries
**Purpose**: Logs of AI service assistant queries  
**Database**: PostgreSQL on Railway

**Usage**: Analytics tracking for the AI-powered service assistant feature.

#### mart_customer_activity
**Purpose**: Materialized/aggregated customer activity data for churn analysis  
**Database**: PostgreSQL on Railway

| Column | Type | Notes |
|--------|------|-------|
| org_id | integer | Organization ID |
| snapshot_date | date | Data snapshot date |

**Usage**: Pre-computed customer activity metrics. Query with `WHERE org_id = X AND snapshot_date = (SELECT MAX(snapshot_date) ...)`.

#### tenant_departments
**Purpose**: Tenant-specific department configuration for GL mapping  
**Database**: PostgreSQL on Railway

**Usage**: Used in GL mapping to configure department-to-GL-account relationships per tenant.

#### tenant_expense_categories
**Purpose**: Tenant-specific expense category definitions  
**Database**: PostgreSQL on Railway

**Usage**: Used in GL mapping for expense categorization per tenant.

---

## Multi-Tenant Architecture Schema (November 2024)

### Overview
The multi-tenant architecture was implemented to support multiple customer organizations within a single application instance, each with isolated data access and customized configurations.

### Core Multi-Tenant Tables

#### organizations
**Purpose**: Tenant organization master records  
**Database**: PostgreSQL on Railway (primary auth/metadata), SQLite (local development)  
**Primary Key**: id (serial/integer)

| Column | Type | Notes |
|--------|------|-------|
| id | serial/integer | Primary key |
| name | varchar(100) | Organization name (required, unique) |
| platform_type | varchar(50) | Platform type ('evolution', 'minitrac', etc.) |
| db_server | varchar(255) | Database server hostname |
| db_name | varchar(100) | Database name |
| db_username | varchar(100) | Database username |
| db_password_encrypted | text | Fernet-encrypted database password |
| subscription_tier | varchar(50) | Subscription level ('basic', 'professional', 'enterprise') |
| max_users | integer | Maximum allowed users |
| is_active | boolean | Organization active status |
| created_at | timestamp | Creation timestamp |
| updated_at | timestamp | Last update timestamp |

**Security Notes**:
- Database passwords encrypted using Fernet encryption
- Encryption key stored in environment variable `CREDENTIAL_ENCRYPTION_KEY`
- Never store plaintext database credentials

**Subscription Tiers**:
- **basic**: 5 users, 100 reports/month, 50 AI queries/month, 10MB exports
- **professional**: 25 users, 1000 reports/month, 500 AI queries/month, 100MB exports
- **enterprise**: Unlimited users/reports/AI, 1GB exports

#### users (enhanced)
**Purpose**: User accounts with organization association  
**Database**: PostgreSQL on Railway, SQLite (local)  
**Primary Key**: id

| Column | Type | Notes |
|--------|------|-------|
| id | serial/integer | Primary key |
| username | varchar(80) | Username (unique across all organizations) |
| email | varchar(120) | Email address (unique across all organizations) |
| password_hash | varchar(128) | Bcrypt password hash |
| first_name | varchar(50) | User's first name |
| last_name | varchar(50) | User's last name |
| organization_id | integer | Foreign key to organizations.id |
| is_active | boolean | User active status |
| created_at | timestamp | Account creation |
| updated_at | timestamp | Last update |

**Relationships**:
- `organization_id` → `organizations.id` (many-to-one)
- Many-to-many with `roles` via `user_roles` association table

**Multi-Tenant Isolation**:
- Users belong to exactly one organization
- Cannot access data from other organizations
- Username/email uniqueness enforced globally

#### roles (RBAC)
**Purpose**: Role-based access control system  
**Database**: PostgreSQL on Railway, SQLite (local)

| Column | Type | Notes |
|--------|------|-------|
| id | serial/integer | Primary key |
| name | varchar(64) | Role name (unique) |
| description | varchar(255) | Role description |

**Standard Roles**:
- **Super Admin**: Cross-tenant administration access
- **Organization Admin**: Full access within organization
- **Manager**: Department management access
- **User**: Standard application access
- **Read Only**: View-only access

#### user_roles (association table)
**Purpose**: Many-to-many relationship between users and roles

| Column | Type | Notes |
|--------|------|-------|
| user_id | integer | Foreign key to users.id |
| role_id | integer | Foreign key to roles.id |

**Constraints**:
- Primary key: (user_id, role_id)
- Unique combination enforced

### Multi-Tenant Security Implementation

#### Tenant Middleware
**File**: `src/middleware/tenant_middleware.py`

**Key Components**:
1. **@require_organization**: Ensures user belongs to active organization
2. **@require_super_admin**: Restricts access to Super Admin role only
3. **@require_feature**: Checks subscription tier feature access
4. **Tenant Context**: Sets `g.current_user`, `g.current_organization`, `g.tenant_id`

**Security Patterns**:
```python
# Tenant isolation at query level
def apply_tenant_filter(query, model_class):
    if hasattr(g, 'tenant_id') and hasattr(model_class, 'organization_id'):
        return query.filter(model_class.organization_id == g.tenant_id)
    return query
```

#### Credential Management
**File**: `src/services/credential_manager.py`

**Encryption Process**:
- Uses Fernet symmetric encryption
- 32-byte base64-encoded key from environment
- Automatic key generation if not provided
- Decrypt-on-demand for database connections

**Example Usage**:
```python
cm = get_credential_manager()
encrypted = cm.encrypt_password("plaintext_password")
decrypted = cm.decrypt_password(encrypted)
```

### Tenant Admin API Endpoints

#### Organization Management
**Base URL**: `/api/admin`  
**Authentication**: JWT + Super Admin role required

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/organizations` | GET | List all organizations |
| `/organizations` | POST | Create new organization |
| `/organizations/{id}` | GET | Get single organization |
| `/organizations/{id}` | PUT | Update organization |
| `/organizations/{id}` | DELETE | Soft delete organization |
| `/organizations/{id}/users` | GET | List organization users |
| `/organizations/{id}/test-connection` | POST | Test database connection |
| `/platforms` | GET | Get supported platforms |

**Security Features**:
- All endpoints require Super Admin role
- Automatic password encryption on create/update
- Soft delete preserves data integrity
- Connection testing validates credentials

### Database Connection Patterns

#### Platform Factory Pattern
**File**: `src/services/database_connections.py`

**Supported Platforms**:
- **evolution**: Azure SQL Server (Softbase Evolution)
- **minitrac**: PostgreSQL (Minitrac systems)
- **custom**: Generic SQL Server connections

**Connection Flow**:
1. Retrieve organization from tenant context
2. Decrypt database credentials
3. Create platform-specific connection
4. Apply tenant-specific configurations

#### Multi-Database Architecture
```
┌─────────────────┐     ┌──────────────────┐
│   App Database  │     │  Tenant Database │
│   (PostgreSQL)  │────▶│   (SQL Server)   │
│                 │     │                  │
│ • Users/Roles   │     │ • Business Data  │
│ • Organizations │     │ • Work Orders    │
│ • Metadata      │     │ • Invoices       │
└─────────────────┘     └──────────────────┘
```

### Schema Migration Strategy

#### Backward Compatibility
- Existing single-tenant installations continue working
- New `organization_id` fields added as nullable
- Default organization created for existing users
- Graceful degradation when multi-tenant features disabled

#### Migration Pattern
```python
# Example migration for existing table
def upgrade():
    # Add organization_id column
    op.add_column('existing_table', 
                  sa.Column('organization_id', sa.Integer(), nullable=True))
    
    # Create default organization
    default_org = Organization(name='Default Organization', ...)
    
    # Assign existing records to default organization
    op.execute("UPDATE existing_table SET organization_id = 1 WHERE organization_id IS NULL")
    
    # Make organization_id required after data migration
    op.alter_column('existing_table', 'organization_id', nullable=False)
```

### Performance Considerations

#### Query Optimization
- **Row-Level Security**: Filter by `organization_id` in all tenant data queries
- **Index Strategy**: Composite indexes on `(organization_id, primary_key)`
- **Connection Pooling**: Separate pools per tenant database
- **Caching**: Tenant metadata cached in application memory

#### Resource Isolation
- **Memory**: Separate connection pools per tenant
- **CPU**: Query governors prevent tenant monopolization  
- **Storage**: Database-level separation for enterprise customers
- **Network**: Rate limiting per organization

### Testing Strategy

#### Unit Tests
**File**: `tests/test_tenant_admin.py`

**Test Coverage**:
- Organization CRUD operations
- Password encryption/decryption
- Access control (Super Admin requirement)
- Feature-based authorization
- Database connection validation
- Error handling and edge cases

#### Manual Testing
**File**: `manual_test_tenant_admin.py`

**Test Scenarios**:
- End-to-end API workflow
- Authentication and authorization
- Data isolation verification
- Error condition handling
- Performance under load

### Security Best Practices

#### Data Isolation
- **Mandatory Filters**: All queries include organization_id filter
- **Connection Isolation**: Separate database connections per tenant
- **Session Management**: Tenant context in Flask's `g` object
- **Cross-Tenant Prevention**: Explicit checks prevent data leakage

#### Access Control
- **Role-Based**: Multiple permission levels
- **Feature-Based**: Subscription tier enforcement
- **API-Level**: Endpoint-specific authorization
- **Database-Level**: Query-level tenant filtering

#### Credential Security
- **Encryption at Rest**: Fernet encryption for all passwords
- **Encryption in Transit**: HTTPS for all API communications
- **Key Management**: Environment-based encryption keys
- **Audit Trail**: All admin actions logged

### Lessons Learned

#### Implementation Insights
1. **RBAC Complexity**: SQLAlchemy many-to-many relationships require careful setup
2. **Testing Challenges**: JWT authentication in test environment needs special configuration
3. **Import Dependencies**: RBAC models must be in separate module to avoid circular imports
4. **Role Assignment**: Use relationship properties, not manual association table entries

#### Security Discoveries
1. **Decorator Order**: `@require_organization` must come before `@require_super_admin`
2. **Context Availability**: Tenant context only available after middleware execution
3. **Error Handling**: Graceful degradation when tenant context unavailable
4. **Connection Validation**: Test credentials before storing in database

#### Performance Optimizations
1. **Lazy Loading**: Database connections created on-demand
2. **Connection Reuse**: Pool connections per tenant
3. **Metadata Caching**: Organization settings cached in memory
4. **Query Efficiency**: Tenant filters applied at query level, not application level

### Future Roadmap

#### Phase 2 Enhancements
- **Database-per-Tenant**: Separate databases for enterprise customers
- **Custom Domains**: Tenant-specific subdomains
- **White-Label UI**: Customizable branding per organization
- **Advanced Analytics**: Cross-tenant reporting for Super Admins

#### Scalability Improvements
- **Horizontal Scaling**: Microservices architecture
- **Data Partitioning**: Time-based and tenant-based partitioning
- **CDN Integration**: Static asset distribution
- **Monitoring**: Per-tenant performance metrics

---

### Reference Tables

#### SaleCodes (79 rows)
**Purpose**: Department and sale code definitions

| Column | Type | Notes |
|--------|------|-------|
| Branch | int | Branch code |
| Dept | int | Department number |
| Code | nvarchar | Sale code |
| Description | nvarchar | Description |

**Common Sale Codes**:
- SVE = Service
- PRT = Parts  
- RENTR = Rental Repairs
- NEWEQ = New Equipment
- USEDEQ = Used Equipment

---

## Key Relationships and Join Patterns

### Customer Lookups
```sql
-- Always join Customer using Number field
FROM Equipment e
JOIN Customer c ON e.CustomerNo = c.Number

FROM InvoiceReg i
JOIN Customer c ON i.BillTo = c.Number

FROM WO w
JOIN Customer c ON w.BillTo = c.Number
```

### Rental Customer Path
```sql
-- Find actual rental customer (not owner) - UPDATED 2025-10-17
Equipment → WORental → WO (Type='R' AND WONo NOT LIKE '9%' AND ClosedDate IS NULL) → Customer
```

### Equipment Rental Availability (CORRECTED PATTERN)
```sql
-- CORRECT way to determine rental availability
-- Based on "WIP > Open Rental Orders" logic in Softbase Equipment Setup
SELECT 
    e.SerialNo,
    e.Make,
    e.Model,
    CASE 
        WHEN rental_check.is_on_rental = 1 THEN 'On Rental'
        ELSE 'Available'
    END as rental_status,
    c.Name as customer_name,
    c.State as location_state
FROM Equipment e
LEFT JOIN Customer c ON e.CustomerNo = c.Number
LEFT JOIN (
    SELECT DISTINCT 
        wr.SerialNo,
        1 as is_on_rental
    FROM WORental wr
    INNER JOIN WO wo ON wr.WONo = wo.WONo
    WHERE wo.Type = 'R' 
    AND wo.ClosedDate IS NULL        -- Open work orders only
    AND wo.WONo NOT LIKE '9%'        -- Exclude quotes
) rental_check ON e.SerialNo = rental_check.SerialNo
WHERE e.InventoryDept = 60           -- Rental department equipment only
AND (e.Customer = 0 OR e.Customer IS NULL)  -- Exclude customer-owned
```

### Equipment Categorization for Inventory Reports
```sql
-- Business rules for equipment categorization (Updated 2025-10-17)
CASE 
    -- Keyword overrides (highest priority)
    WHEN LOWER(e.Make) LIKE '%allied%' OR LOWER(e.Model) LIKE '%allied%' THEN 'allied'
    WHEN LOWER(e.Model) LIKE '%battery%' OR LOWER(e.Model) LIKE '%charger%' 
         OR LOWER(e.Model) LIKE '%batt%' OR LOWER(e.Model) LIKE '%charge%' THEN 'batteries_chargers'
    
    -- Department-based categorization (secondary)
    WHEN e.InventoryDept = 60 THEN 'rental'
    WHEN e.InventoryDept = 10 THEN 'new'
    WHEN e.InventoryDept = 30 THEN 'allied'
    WHEN e.InventoryDept = 20 THEN 'used'
    
    -- Default fallback
    ELSE 'used'
END as equipment_category
```

### Work Order Costs
```sql
-- Get complete work order costs
SELECT 
    w.WONo,
    SUM(l.Sell * l.Hours) as LaborSell,
    SUM(p.Sell * p.Qty) as PartsSell,  -- Note: Multiply by Qty!
    SUM(m.Sell) as MiscSell
FROM WO w
LEFT JOIN WOLabor l ON w.WONo = l.WONo
LEFT JOIN WOParts p ON w.WONo = p.WONo
LEFT JOIN WOMisc m ON w.WONo = m.WONo
GROUP BY w.WONo
```

### Shop Work Order Cost Overrun Detection (NEW - 2025-10-18)
```sql
-- Monitor actual vs quoted labor hours for shop work orders
SELECT 
    w.WONo,
    w.BillTo as CustomerNo,
    c.Name as CustomerName,
    
    -- Quoted labor from WOQuote table (NOT WOMisc!)
    COALESCE(quoted.QuotedAmount, 0) as QuotedAmount,
    CASE 
        WHEN quoted.QuotedAmount > 0 THEN quoted.QuotedAmount / 189.0
        ELSE 0
    END as QuotedHours,
    
    -- Actual labor hours from WOLabor
    COALESCE(SUM(l.Hours), 0) as ActualHours,
    
    -- Cost overrun percentage
    CASE 
        WHEN quoted.QuotedAmount IS NULL OR quoted.QuotedAmount = 0 THEN 0
        ELSE (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100
    END as PercentUsed

FROM [ben002].WO w
LEFT JOIN [ben002].Customer c ON w.BillTo = c.Number
LEFT JOIN (
    SELECT WONo, SUM(Amount) as QuotedAmount
    FROM [ben002].WOQuote
    WHERE Type = 'L'  -- L = Labor quotes
    GROUP BY WONo
) quoted ON w.WONo = quoted.WONo
LEFT JOIN [ben002].WOLabor l ON w.WONo = l.WONo

WHERE w.Type = 'SH'  -- Shop work orders only
  AND w.ClosedDate IS NULL
  AND w.WONo NOT LIKE '9%'  -- Exclude quotes

GROUP BY w.WONo, w.BillTo, c.Name, quoted.QuotedAmount
```

**Key Insights**:
- Standard shop labor rate: $189/hour
- Quoted amounts stored in WOQuote.Amount column, NOT WOMisc.Sell
- Alert levels: CRITICAL ≥100%, RED ≥90%, YELLOW ≥80%, GREEN <80%
- Hours at Risk = Sum of (ActualHours - QuotedHours) for CRITICAL/RED work orders
- Unbillable Labor Value = Hours at Risk × $189
```

### Current Rentals
```sql
-- Find equipment currently on rent
SELECT e.*, rh.DaysRented, rh.RentAmount
FROM Equipment e
JOIN RentalHistory rh ON e.SerialNo = rh.SerialNo
WHERE rh.Year = YEAR(GETDATE())
  AND rh.Month = MONTH(GETDATE())
  AND rh.DaysRented > 0
```

### AR Aging
```sql
-- Correct AR aging pattern
WITH InvoiceBalances AS (
    SELECT 
        CustomerNo,
        InvoiceNo,
        MIN(Due) as DueDate,  -- Use MIN to get single date
        SUM(Amount) as Balance
    FROM ARDetail
    WHERE HistoryFlag IS NULL OR HistoryFlag = 0
    GROUP BY CustomerNo, InvoiceNo  -- NOT by Due date!
    HAVING SUM(Amount) > 0.01
)
-- Then calculate aging buckets...
```

## Common Gotchas and Important Notes (UPDATED 2025-10-17)

### Critical Database Rules
1. **Customer Joins**: ALWAYS use Customer.Number, never Customer.Id
2. **Parts Calculations**: Always multiply WOParts.Sell * Qty for extended amounts
3. **AR Grouping**: Group by CustomerNo and InvoiceNo only, NOT by Due date
4. **Equipment.Customer**: This is a boolean flag, not the customer reference
5. **InvoiceReg.Customer**: Also a boolean flag, use BillTo for customer number
6. **Parts Table**: Use Parts table, NOT NationalParts (which is empty)
7. **Deletion Flags**: Check both DeletionTime and IsDeleted fields
8. **Work Order Status**: Use ClosedDate IS NULL for open orders

### NEW CRITICAL DISCOVERIES (2025-10-17)
9. **🚨 RentalStatus Field is UNRELIABLE**: Don't trust Equipment.RentalStatus for rental detection
10. **🚨 Quotes vs Work Orders**: ALWAYS filter `WONo NOT LIKE '9%'` to exclude quotes from rental detection
11. **🚨 GLDetail Filtering**: ALWAYS include `Posted = 1` filter for accounting reports
12. **🚨 Inventory Department Logic**: Department 60 = Rental, 10 = New, 20 = Used, 30 = Allied
13. **🚨 Equipment Categorization**: Keywords override department for Allied/Batteries classification
14. **🚨 GL Account 131200**: Requires manual split between Used Equipment and Batteries (~75%/25%)
15. **🚨 Rental Net Book Value**: Use GL 183000 - ABS(GL 193000) for accurate rental asset values
16. **🚨 Date Range Filtering**: Accounting reports use March 1, 2025 - October 31, 2025 period
17. **🚨 Excel Export Issues**: Avoid variable name conflicts in iteration loops (category_info vs category_definitions)
18. **🚨 WO.Status Column DOESN'T EXIST**: Despite documentation, Status column is not in WO table
19. **🚨 WO.Location Column DOESN'T EXIST**: Despite documentation, Location column is not in WO table
20. **🚨 Shop Work Order Detection**: Use Type = 'SH' for shop work orders (not Type IN ('S', 'SH', 'PM'))
21. **🚨 Quote Contamination in WO Table**: WONo starting with '9' are quotes, not work orders - ALWAYS exclude
22. **🚨 Quoted Labor Location**: Quoted labor amounts are in WOQuote table (Type='L'), NOT in WOMisc!
23. **🚨 WOQuote Column Names**: Use 'Amount' column for quoted values, not 'Sell' or 'ExtendedPrice'
24. **🚨 Standard Shop Labor Rate**: $189/hour used for converting quoted amounts to hours

### Work Order Query Rules (NEW - 2025-10-17)
- **NEVER** assume Status or Location columns exist in WO table
- **ALWAYS** exclude quotes with `WONo NOT LIKE '9%'` for ANY work order query
- **ALWAYS** use Type = 'SH' specifically for shop work orders (not broader Type filters)
- **ALWAYS** verify column existence before using in queries
- **Quote Impact**: Without quote exclusion, work order counts can be 2-3x higher than expected

### Rental Availability Detection Rules
- **NEVER** use Equipment.RentalStatus alone
- **ALWAYS** check for open rental work orders in WORental/WO join
- **ALWAYS** exclude quotes with `WONo NOT LIKE '9%'`
- **ALWAYS** filter to InventoryDept = 60 for rental equipment
- **ALWAYS** exclude customer-owned equipment with Customer = 0 filter

### GL Account Balance Rules for Inventory
- Use specific date ranges (not "current balance")
- Always filter Posted = 1 transactions
- Account for depreciation in rental equipment calculations
- Split GL 131200 between Used Equipment and Batteries categories
- Use net book value for rental equipment display totals

## Data Quality Issues (UPDATED 2025-10-17)

### Legacy Issues (Still Present)
- Some equipment marked as "Sold" still appears in inventory
- RentalStatus values are inconsistent and unreliable
- Not all sold units have consistent status marking
- Some units have rental rates but aren't actually for rent

### RESOLVED Issues (Solutions Found)
- ✅ **Equipment.InventoryDept**: NOW RELIABLE for primary categorization (Dept 60=Rental, 10=New, 20=Used, 30=Allied)
- ✅ **Rental Detection**: Solution found using WORental + WO join with quote exclusion
- ✅ **GL Account Balancing**: Proper date filtering and Posted=1 requirements documented
- ✅ **Equipment Categorization**: Business rules established with keyword overrides

### NEW Issues Discovered (2025-10-17)
- **Quote Contamination**: Quotes appear in WORental table and must be filtered out
- **GL 131200 Split**: No systematic way to split between Used Equipment and Batteries (manual allocation required)
- **Depreciation Calculation**: Complex interaction between GL 183000 and 193000 for rental assets
- **Date Range Dependencies**: Accounting reports depend on specific fiscal period filters

## Major System Insights (2025-10-17)

### Rental Availability Discovery
**Key Learning**: "Never assume data values - always verify actual database content"
- The RentalStatus field was completely unreliable for rental detection
- Solution required analysis of actual Softbase Equipment Setup screen logic
- Critical discovery: Quotes vs Work Orders distinction essential for accuracy

### Equipment Categorization Discovery  
**Key Learning**: Department-based categorization works but requires keyword overrides
- Department 60 provides clean data for rental equipment
- Keyword analysis required for Allied equipment and Batteries/Chargers
- Categorization used for display lists, GL balances used for financial totals

### GL Account Balance Discovery
**Key Learning**: Equipment book values ≠ GL account balances for financial reporting
- Dollar amounts MUST come from GL account balances, not equipment Cost fields
- Different logic for different categories (direct GL vs calculated net book value)
- Specific date range filtering essential for period-accurate reporting

### Excel Export Technical Discovery
**Key Learning**: Variable name conflicts can cause silent failures
- Python iteration variable name conflicts caused corrupted Excel files
- BytesIO handling requires proper stream positioning
- Flask send_file requires specific MIME types and headers

### WO Table Schema Discovery (NEW - 2025-10-17)
**Key Learning**: Documentation severely mismatches actual table structure
- **Status Column**: Documented but DOESN'T EXIST - caused SQL errors
- **Location Column**: Documented but DOESN'T EXIST - caused SQL errors  
- **Quote Contamination**: WONo starting with '9' are quotes masquerading as work orders
- **Shop Work Orders**: Type = 'SH' specifically (not broader Type IN ('S', 'SH', 'PM'))
- **Impact**: Without proper filtering, work order counts 2-3x higher than expected

### WOQuote Table Discovery (NEW - 2025-10-18)  
**Key Learning**: Quoted labor amounts are NOT stored where expected
- **Initial Assumption**: Quoted labor would be in WOMisc table - WRONG!
- **Discovery Process**: Created multiple debug endpoints to search for $3,938 quote
- **Solution Found**: WOQuote table stores all quoted amounts with Type codes
- **Type Codes**: L=Labor, P=Parts, M=Miscellaneous
- **Column Name**: Use 'Amount' column, not 'Sell' or other common names
- **Business Impact**: Enabled Cash Burn report with unbillable labor value calculations
- **Hours at Risk**: Can now calculate exact hours over budget and dollar impact

**Pattern Recognition**: Same quote exclusion logic needed across the system:
- ✅ **Rental Work Orders**: Fixed with `WONo NOT LIKE '9%'`
- ✅ **Shop Work Orders**: Fixed with `WONo NOT LIKE '9%'`
- 🎯 **Future Work Order Queries**: ALWAYS exclude quotes

**Column Verification Process**: 
1. Never trust documentation for column existence
2. Test queries with minimal column sets first
3. Add columns incrementally to verify existence
4. Document actual working column combinations

## Last Known Row Counts (as of 2025-10-17, refresh via API)

> **Note**: These counts were last verified on 2025-10-17. Use `POST /api/database/execute-query` with `SELECT COUNT(*) FROM {schema}.TableName` to get current counts.

### Azure SQL Server (Softbase Evolution - ben002)
- Equipment: 21,291
- Customer: 2,227
- InvoiceReg: 5,148
- WO: 6,879
- Parts: 11,413
- RentalHistory: 11,568
- ARDetail: 8,413
- APDetail: 3,331
- GLDetail: 64,180
- SaleCodes: 79
- RentalContract: 318
- Depreciation: 515 (view)
- WOLabor: 6,401
- WOParts: 10,381
- WOMisc: 7,832

### PostgreSQL (Railway - Custom Data)
- minitrac_equipment: ~28,000
- work_order_notes: ~500+ (growing)
- support_ticket: growing
- knowledge_base: growing
- report_visibility: per-org settings
- mart_customer_activity: snapshot-based

## Recent Major Features Implemented

### Dashboard Trendline and Chart Standardization (2024-10-31)

#### Linear Trendline Implementation
- **Mathematical Foundation**: Linear regression using least squares method
- **Cross-Platform Consistency**: Standardized calculateLinearTrend function across all charts
- **Visual Standards**: Purple dashed trendlines (#8b5cf6) with consistent styling
- **Data Processing**: Simple data arrays prevent index corruption issues

#### Pacing Calculation Standardization
- **Unified Logic**: All charts use simple pace_percentage instead of complex adaptive comparisons
- **Visual Consistency**: Green/Red color scheme across Dashboard and all departments
- **User Experience**: Eliminated confusing percentage differences between similar charts
- **Performance**: Simplified data processing improves chart rendering speed

#### Chart Architecture Lessons
- **Complexity Reduction**: Removed complex IIFE data processing that corrupted calculations
- **Dashboard as Standard**: Established Dashboard implementations as template for all charts
- **Mathematical Accuracy**: Direct data approach yields correct trendline directions
- **Debugging Process**: Systematic comparison of working vs broken implementations

#### Technical Achievements
- **Code Reduction**: Eliminated 285 lines of complex, broken chart processing
- **Consistency**: Unified chart margins, colors, and formatting across all reports
- **Reliability**: Fixed trendlines showing incorrect downward trends despite business growth
- **Maintainability**: Simple pattern easy to replicate for future chart development

### Inventory Report System (2024-10-17)
- **Year-End Inventory Report**: GL-based inventory categorization
- **Equipment Categorization**: 5-category system (Allied, New, Rental, Used, Batteries)
- **Excel Export**: Multi-sheet Excel generation with proper formatting
- **GL Account Integration**: Real-time GL account balance queries

### Rental Availability System  
- **Corrected Rental Detection**: Fixed quote contamination issues
- **Department 60 Focus**: Rental equipment properly identified
- **Customer Location Tracking**: Current rental customer and state information
- **Equipment Status Logic**: Matches Softbase Equipment Setup screen

### Minitrac Integration
- **Self-Hosted Database**: 28,000+ equipment records imported
- **Full-Text Search**: Advanced search capabilities across specifications
- **Cost Savings**: $600/month subscription replaced with self-hosted solution
- **JSON Specifications**: Structured technical data storage

### Work Order Enhancement
- **Custom Notes System**: PostgreSQL-based note storage
- **Auto-Save Functionality**: 1-second debounce for seamless UX  
- **CSV Export Integration**: Notes included in work order exports
- **User Attribution**: Track note creation and modification