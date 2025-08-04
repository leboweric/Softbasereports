-- Simple AR Aging Query that matches source system
-- This calculates aging directly on ARDetail records without grouping by invoice

-- Total AR
SELECT SUM(Amount) as TotalAR
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL;

-- Aging Buckets
SELECT 
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30 THEN '1-30'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 31 AND 60 THEN '31-60'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90 THEN '61-90'
        WHEN DATEDIFF(day, Due, GETDATE()) > 90 THEN 'Over 90'
    END as AgingBucket,
    COUNT(*) as RecordCount,
    SUM(Amount) as TotalAmount
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL
GROUP BY 
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30 THEN '1-30'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 31 AND 60 THEN '31-60'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90 THEN '61-90'
        WHEN DATEDIFF(day, Due, GETDATE()) > 90 THEN 'Over 90'
    END
ORDER BY
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30 THEN '1-30'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 31 AND 60 THEN '31-60'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90 THEN '61-90'
        WHEN DATEDIFF(day, Due, GETDATE()) > 90 THEN 'Over 90'
    END;