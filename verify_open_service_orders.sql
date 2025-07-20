-- SQL Queries to Verify Open Service Work Orders
-- Database: evo, Schema: ben002, Table: WO

-- ============================================
-- 1. Check the structure of the WO table
-- ============================================
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ben002' 
AND TABLE_NAME = 'WO'
ORDER BY ORDINAL_POSITION;

-- ============================================
-- 2. Sample data to understand the table
-- ============================================
SELECT TOP 10 
    WONumber,
    Type,
    ClosedDate,
    CreatedDate,
    Status,
    CustomerID,
    EquipmentID
FROM ben002.WO
WHERE Type = 'S'
ORDER BY CreatedDate DESC;

-- ============================================
-- 3. Total Service Work Orders (Type = 'S')
-- ============================================
SELECT 
    COUNT(*) as TotalServiceOrders
FROM ben002.WO
WHERE Type = 'S';

-- ============================================
-- 4. Open Service Work Orders (Type = 'S' AND ClosedDate IS NULL)
-- ============================================
SELECT 
    COUNT(*) as OpenServiceOrders
FROM ben002.WO
WHERE Type = 'S' 
AND ClosedDate IS NULL;

-- ============================================
-- 5. Check unique Status values (if Status column exists)
-- ============================================
SELECT 
    Status,
    COUNT(*) as Count
FROM ben002.WO
WHERE Type = 'S'
GROUP BY Status
ORDER BY Count DESC;

-- ============================================
-- 6. Cross-check ClosedDate and Status
-- ============================================
SELECT 
    CASE 
        WHEN ClosedDate IS NULL THEN 'ClosedDate IS NULL'
        ELSE 'ClosedDate IS NOT NULL'
    END as ClosedDateStatus,
    Status,
    COUNT(*) as Count
FROM ben002.WO
WHERE Type = 'S'
GROUP BY 
    CASE 
        WHEN ClosedDate IS NULL THEN 'ClosedDate IS NULL'
        ELSE 'ClosedDate IS NOT NULL'
    END,
    Status
ORDER BY ClosedDateStatus, Count DESC;

-- ============================================
-- 7. Summary with percentages
-- ============================================
WITH ServiceOrderCounts AS (
    SELECT 
        COUNT(*) as TotalService,
        SUM(CASE WHEN ClosedDate IS NULL THEN 1 ELSE 0 END) as OpenService,
        SUM(CASE WHEN ClosedDate IS NOT NULL THEN 1 ELSE 0 END) as ClosedService
    FROM ben002.WO
    WHERE Type = 'S'
)
SELECT 
    TotalService,
    OpenService,
    ClosedService,
    CAST(ROUND(100.0 * OpenService / TotalService, 2) AS DECIMAL(5,2)) as PercentOpen,
    CAST(ROUND(100.0 * ClosedService / TotalService, 2) AS DECIMAL(5,2)) as PercentClosed
FROM ServiceOrderCounts;

-- ============================================
-- 8. Work Order Types Distribution
-- ============================================
SELECT 
    Type,
    CASE Type
        WHEN 'S' THEN 'Service'
        WHEN 'R' THEN 'Rental'
        WHEN 'P' THEN 'Parts'
        WHEN 'D' THEN 'Delivery'
        ELSE 'Other'
    END as TypeDescription,
    COUNT(*) as TotalCount,
    SUM(CASE WHEN ClosedDate IS NULL THEN 1 ELSE 0 END) as OpenCount,
    SUM(CASE WHEN ClosedDate IS NOT NULL THEN 1 ELSE 0 END) as ClosedCount
FROM ben002.WO
GROUP BY Type
ORDER BY TotalCount DESC;

-- ============================================
-- 9. Recent Open Service Orders with Details
-- ============================================
SELECT TOP 20
    WONumber,
    Type,
    Status,
    CustomerID,
    EquipmentID,
    CreatedDate,
    ClosedDate,
    DATEDIFF(day, CreatedDate, GETDATE()) as DaysOpen
FROM ben002.WO
WHERE Type = 'S'
AND ClosedDate IS NULL
ORDER BY CreatedDate DESC;

-- ============================================
-- 10. Open Service Orders by Age
-- ============================================
SELECT 
    CASE 
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 7 THEN '0-7 days'
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 30 THEN '8-30 days'
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 60 THEN '31-60 days'
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 90 THEN '61-90 days'
        ELSE 'Over 90 days'
    END as AgeRange,
    COUNT(*) as Count
FROM ben002.WO
WHERE Type = 'S'
AND ClosedDate IS NULL
GROUP BY 
    CASE 
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 7 THEN '0-7 days'
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 30 THEN '8-30 days'
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 60 THEN '31-60 days'
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 90 THEN '61-90 days'
        ELSE 'Over 90 days'
    END
ORDER BY 
    CASE 
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 7 THEN 1
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 30 THEN 2
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 60 THEN 3
        WHEN DATEDIFF(day, CreatedDate, GETDATE()) <= 90 THEN 4
        ELSE 5
    END;