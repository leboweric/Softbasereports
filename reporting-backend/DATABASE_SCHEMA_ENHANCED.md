# Softbase Database Schema - Enhanced Documentation

**Last Updated:** October 5, 2025  
**Based on:** Investigation for year-end inventory report

## Critical Connection Information

- **Server:** evo1-sql-replica.database.windows.net
- **Database:** evo
- **Schema:** ben002
- **Access:** READ ONLY via Railway backend only (Azure SQL firewall blocks direct access)

## Key Tables and Views Discovered

### Equipment Table
Primary table for all equipment/inventory data.

**Key Columns:**
- `SerialNo` (nvarchar) - Primary identifier, used for joins
- `Make` (nvarchar) - Equipment manufacturer
- `Model` (nvarchar) - Equipment model
- `Cost` (decimal) - Purchase cost
- `Sell` (decimal) - Selling price
- `Retail` (decimal) - Retail price
- `RentalStatus` (nvarchar) - Current rental status
- `InventoryDept` (int) - Department code (60 = Rental)
- `RentalYTD` (decimal) - Year-to-date rental revenue
- `RentalITD` (decimal) - Inception-to-date rental revenue
- `CustomerNo` - Current customer (links to Customer.Number)

**Notes:**
- ❌ NO `IsDeleted` column (common mistake)
- ❌ NO `EquipmentId` column (use SerialNo)
- ❌ NO `BookValue` or depreciation fields (see Depreciation view)

### Depreciation View
**CRITICAL:** Contains all depreciation/asset value data.

**View Name:** `ben002.Depreciation`  
**Total Records:** 515 (as of Oct 2025)  
**Coverage:** Primarily rental equipment

**Key Columns:**
- `SerialNo` (nvarchar, 100) - Links to Equipment.SerialNo
- `StartingValue` (decimal) - Original/gross book value
- `NetBookValue` (decimal) - Current net book value
- `LastUpdatedAmount` (decimal) - Monthly depreciation amount
- `Method` (nvarchar, 50) - Depreciation method (typically "Straight Line")
- `TotalMonths` (smallint) - Total depreciation period
- `RemainingMonths` (smallint) - Months remaining
- `ResidualValue` (decimal) - Salvage value
- `DepreciationGroup` (nvarchar, 50) - Category (e.g., "Rental")
- `Inactive` (bit, NOT NULL) - 0 = active, 1 = inactive
- `DebitAccount` (nvarchar, 50) - GL account for depreciation expense
- `CreditAccount` (nvarchar, 50) - GL account for accumulated depreciation
- `LastUpdated` (datetime) - Last depreciation update
- `LastUpdatedBy` (nvarchar, 50) - Who updated

**Important:**
- ❌ NO `IsDeleted` column (use `Inactive` instead)
- ✅ Filter with: `WHERE d.Inactive = 0`
- ✅ Accumulated Depreciation = StartingValue - NetBookValue

**Sample Join:**
```sql
LEFT JOIN ben002.Depreciation d ON e.SerialNo = d.SerialNo
    AND d.Inactive = 0
```

### Customer Table
Customer/location information.

**Key Columns:**
- `Number` (links to Equipment.CustomerNo)
- `Name` - Customer name
- `State` - Customer state
- `BillTo` - Billing address details
- `ShipTo` - Shipping address details

### WORental Table
Work order/rental transaction data.

**Key Columns:**
- `Equipment` - Links to Equipment.SerialNo
- `Status` - 'O' = Open, 'A' = Active, 'C' = Closed
- `BillTo` - Customer number for billing
- `ShipTo` - Customer number for shipping

## Common Join Patterns

### Equipment with Current Location
```sql
SELECT e.*, c.State, c.Name
FROM ben002.Equipment e
LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
WHERE e.SerialNo IS NOT NULL
```

### Equipment with Depreciation Data
```sql
SELECT 
    e.SerialNo,
    e.Make,
    e.Model,
    d.StartingValue as gross_book_value,
    d.NetBookValue as net_book_value,
    (d.StartingValue - d.NetBookValue) as accumulated_depreciation
FROM ben002.Equipment e
LEFT JOIN ben002.Depreciation d ON e.SerialNo = d.SerialNo
    AND d.Inactive = 0
WHERE e.SerialNo IS NOT NULL
```

### Active Rental Equipment
```sql
SELECT e.*, wo.Status, c.State
FROM ben002.Equipment e
LEFT JOIN ben002.WORental wo ON e.SerialNo = wo.Equipment
    AND wo.Status IN ('O', 'A')
LEFT JOIN ben002.Customer c ON wo.ShipTo = c.Number
WHERE e.InventoryDept = 60
```

## Equipment Categorization Logic
Based on analysis for year-end inventory report:

1. **Rental Equipment:** InventoryDept = 60 AND has active work order
2. **Used Equipment:** InventoryDept = 60 AND RentalITD > 0 AND available
3. **New Equipment:** InventoryDept = 60 AND RentalITD = 0
4. **Batteries/Chargers:** Model contains 'battery', 'charger', 'batt'
5. **Allied Equipment:** Make = 'Allied'

## Common Pitfalls

1. **Don't use `IsDeleted`** - This column doesn't exist. Use `Inactive` in Depreciation view.
2. **Don't use `EquipmentId`** - Primary key is SerialNo, not an ID field.
3. **Don't assume all equipment has depreciation** - Only 515 of 21,342 items have depreciation records.
4. **Azure SQL firewall** - Can only query through deployed Railway backend, not directly.
5. **Case sensitivity** - Table/column names in Azure SQL require exact case matching.

## Views Available (Partial List)
Discovered from schema exploration (515+ views total):

- `Depreciation` - Asset depreciation schedules ✅ Documented
- `Equipment` - Equipment/inventory master
- `Customer` - Customer master
- `WORental` - Rental work orders
- `Invoice` - Invoice headers
- `InvoiceDetail` - Invoice line items
- `Parts` - Parts inventory
- `GL` - General ledger
- `GLDetail` - GL transactions
- *(Many more exist - explore as needed)*

## Future Investigation Needed

- Parts inventory structure
- Service work order details
- Complete GL account mappings
- Invoice/revenue recognition logic
- Rental rate structures
- Equipment maintenance history

## Usage Notes
When building new reports:

1. Always start with Equipment table
2. LEFT JOIN other tables (not INNER JOIN) to avoid losing equipment records
3. Filter Depreciation with `Inactive = 0`
4. Use SerialNo for all equipment joins
5. Test queries with `TOP 10` before full execution
6. Document new discoveries here

---

**Contributors:**
- Eric LeBow - Initial documentation from inventory report investigation
- Claude Code - Schema exploration and query testing