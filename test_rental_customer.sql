-- Test query to understand rental customer relationships
-- Check specific units from the original report

-- Unit 15821 should show MINNESOTA CORRUGATED BOX
SELECT 
    e.UnitNo,
    e.SerialNo,
    e.Make,
    e.Model,
    e.CustomerNo as EquipmentCustomerNo,
    c1.Name as EquipmentCustomerName,
    -- Check RentalContract
    rc.RentalContractNo,
    rc.CustomerNo as RentalContractCustomerNo,
    c2.Name as RentalContractCustomerName,
    -- Check current WO
    wo.WONo,
    wo.BillTo as WOBillTo,
    c3.Name as WOCustomerName,
    -- Check RentalHistory
    rh.SerialNo as RHSerialNo,
    rh.Year,
    rh.Month,
    rh.DaysRented
FROM ben002.Equipment e
LEFT JOIN ben002.Customer c1 ON e.CustomerNo = c1.Number
LEFT JOIN ben002.RentalContract rc ON e.SerialNo = rc.SerialNo
LEFT JOIN ben002.Customer c2 ON rc.CustomerNo = c2.Number
LEFT JOIN ben002.WO wo ON e.UnitNo = wo.UnitNo AND wo.Type = 'R' AND wo.ClosedDate IS NULL
LEFT JOIN ben002.Customer c3 ON wo.BillTo = c3.Number
LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
    AND rh.Year = YEAR(GETDATE()) 
    AND rh.Month = MONTH(GETDATE())
WHERE e.UnitNo IN ('15821', '15821C', 'RTR253', '20357')

-- Also check if there's a RentalDetail or RentalLine table
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'ben002' 
AND TABLE_NAME LIKE '%Rental%'