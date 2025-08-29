# Softbase Evolution Database Schema Documentation

**Database**: Azure SQL Server  
**Schema**: ben002  
**Last Updated**: 2025-08-29

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

**Important Notes**:
- Customer field is boolean, BillTo has actual customer number
- NO Department field - use SaleCode or SaleDept
- Cost fields enable gross profit calculations

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
| RentalContractNo | int | Linked rental contract |
| Status | nvarchar | Current status |
| Location | nvarchar | Service location |

**Work Order Types**:
- S = Service
- SH = Shop (Service)
- PM = Preventive Maintenance (Service)
- P = Parts
- R = Rental
- E = Equipment
- I = Internal

**Lifecycle**:
- Open: OpenDate set, ClosedDate NULL
- Completed: CompletedDate set, ClosedDate NULL (awaiting invoice)
- Closed: ClosedDate set (invoiced)

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
| StartDate | datetime | Contract start |
| EndDate | datetime | Contract end |
| DeliveryCharge | decimal | Delivery fee |
| PickupCharge | decimal | Pickup fee |

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
-- Find actual rental customer (not owner)
Equipment → WORental → WO (Type='R') → Customer
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

## Common Gotchas and Important Notes

1. **Customer Joins**: ALWAYS use Customer.Number, never Customer.Id
2. **Parts Calculations**: Always multiply WOParts.Sell * Qty for extended amounts
3. **AR Grouping**: Group by CustomerNo and InvoiceNo only, NOT by Due date
4. **Equipment.Customer**: This is a boolean flag, not the customer reference
5. **InvoiceReg.Customer**: Also a boolean flag, use BillTo for customer number
6. **Parts Table**: Use Parts table, NOT NationalParts (which is empty)
7. **Deletion Flags**: Check both DeletionTime and IsDeleted fields
8. **Work Order Status**: Use ClosedDate IS NULL for open orders
9. **Rental Status**: Multiple fields affect rental availability (RentalStatus, rental rates, rental history)

## Data Quality Issues

- Some equipment marked as "Sold" still appears in inventory
- RentalStatus values are inconsistent 
- Not all sold units have consistent status marking
- Some units have rental rates but aren't actually for rent
- Equipment.InventoryDept may or may not indicate rental department

## Last Known Row Counts (as of 2025-08-03)

- Equipment: 21,291
- Customer: 2,227
- InvoiceReg: 5,148
- WO: 6,879
- Parts: 11,413
- RentalHistory: 11,568
- ARDetail: 8,413
- APDetail: 3,331
- GLDetail: 64,180