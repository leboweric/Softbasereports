-- Research queries to find Ship To customer for rental equipment

-- 1. Check RentalContract table structure and sample data
SELECT TOP 5 * FROM ben002.RentalContract;

-- 2. Check what fields exist in RentalContract
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ben002'
AND TABLE_NAME = 'RentalContract'
ORDER BY ORDINAL_POSITION;

-- 3. Check WO (Work Order) table for rental work orders
SELECT TOP 5 
    WONo,
    Type,
    BillTo,
    ShipTo,
    UnitNo,
    OpenDate,
    ClosedDate
FROM ben002.WO
WHERE Type = 'R'  -- R = Rental
AND ClosedDate IS NULL  -- Still open/active
ORDER BY OpenDate DESC;

-- 4. Check if there's a WORental table with more rental-specific info
SELECT TOP 5 * FROM ben002.WORental;

-- 5. Check columns in WORental
SELECT 
    COLUMN_NAME,
    DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ben002'
AND TABLE_NAME = 'WORental'
ORDER BY ORDINAL_POSITION;

-- 6. Find a specific piece of equipment that's on rent and trace it
-- Let's pick one that shows as "On Rent" and see all related records
DECLARE @TestSerialNo nvarchar(50);
DECLARE @TestUnitNo nvarchar(50);

-- Get a unit that's currently on rent
SELECT TOP 1 
    @TestSerialNo = e.SerialNo,
    @TestUnitNo = e.UnitNo
FROM ben002.Equipment e
JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo
WHERE rh.Year = YEAR(GETDATE()) 
AND rh.Month = MONTH(GETDATE())
AND rh.DaysRented > 0;

-- Now trace this equipment through all tables
SELECT 'Equipment' as Source, 
    UnitNo, SerialNo, CustomerNo, RentalStatus, Location
FROM ben002.Equipment 
WHERE SerialNo = @TestSerialNo;

SELECT 'RentalContract' as Source,
    RentalContractNo, SerialNo, CustomerNo, StartDate, EndDate
FROM ben002.RentalContract
WHERE SerialNo = @TestSerialNo;

SELECT 'WO-Rental' as Source,
    WONo, Type, UnitNo, BillTo, ShipTo, OpenDate, ClosedDate
FROM ben002.WO
WHERE UnitNo = @TestUnitNo
AND Type = 'R';

SELECT 'WORental' as Source,
    WONo, ControlNo, RentalContractNo
FROM ben002.WORental
WHERE WONo IN (
    SELECT WONo FROM ben002.WO 
    WHERE UnitNo = @TestUnitNo AND Type = 'R'
);

-- 7. Check InvoiceReg for rental invoices to see customer info
SELECT TOP 5
    InvoiceNo,
    InvoiceDate,
    BillTo,
    BillToName,
    ShipTo,  -- Does this field exist?
    ShipToName,  -- Does this field exist?
    SaleCode,
    ControlNo
FROM ben002.InvoiceReg
WHERE SaleCode LIKE 'RENT%'
ORDER BY InvoiceDate DESC;

-- 8. Look for any ShipTo related fields across all tables
SELECT DISTINCT
    TABLE_NAME,
    COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ben002'
AND (
    COLUMN_NAME LIKE '%Ship%'
    OR COLUMN_NAME LIKE '%Deliver%'
    OR COLUMN_NAME LIKE '%Location%'
)
ORDER BY TABLE_NAME, COLUMN_NAME;