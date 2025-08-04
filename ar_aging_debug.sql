-- AR Aging Debug Query
-- This query helps diagnose discrepancies in AR aging calculations

-- First, let's check the raw AR totals
SELECT 'Total AR from ARDetail' as Description, SUM(Amount) as Amount
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL;

-- Check if there are any invoices with NULL due dates
SELECT 'Invoices with NULL Due Date' as Description, COUNT(*) as Count, SUM(Amount) as Amount
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL
    AND Due IS NULL;

-- Get the aging buckets with proper ranges
WITH InvoiceBalances AS (
    SELECT 
        ar.CustomerNo,
        ar.InvoiceNo,
        ar.Due,
        SUM(ar.Amount) as NetBalance
    FROM ben002.ARDetail ar
    WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
        AND ar.DeletionTime IS NULL
    GROUP BY ar.CustomerNo, ar.InvoiceNo, ar.Due
    HAVING SUM(ar.Amount) > 0.01
)
SELECT 
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 91 THEN '91-120'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 61 THEN '61-90'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 31 THEN '31-60'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 1 THEN '1-30'
        WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
    END as AgingBucket,
    COUNT(*) as InvoiceCount,
    SUM(NetBalance) as TotalAmount
FROM InvoiceBalances
GROUP BY 
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 91 THEN '91-120'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 61 THEN '61-90'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 31 THEN '31-60'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 1 THEN '1-30'
        WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
    END
ORDER BY 
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 91 THEN '91-120'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 61 THEN '61-90'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 31 THEN '31-60'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 1 THEN '1-30'
        WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
    END;

-- Check a sample of invoices around the 90-day boundary
WITH InvoiceBalances AS (
    SELECT 
        ar.CustomerNo,
        ar.InvoiceNo,
        ar.Due,
        SUM(ar.Amount) as NetBalance
    FROM ben002.ARDetail ar
    WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
        AND ar.DeletionTime IS NULL
    GROUP BY ar.CustomerNo, ar.InvoiceNo, ar.Due
    HAVING SUM(ar.Amount) > 0.01
)
SELECT TOP 20
    InvoiceNo,
    Due,
    DATEDIFF(day, Due, GETDATE()) as DaysOverdue,
    NetBalance,
    CASE 
        WHEN DATEDIFF(day, Due, GETDATE()) = 90 THEN '*** EXACTLY 90 DAYS ***'
        WHEN DATEDIFF(day, Due, GETDATE()) = 91 THEN '*** EXACTLY 91 DAYS ***'
        ELSE ''
    END as Note
FROM InvoiceBalances
WHERE DATEDIFF(day, Due, GETDATE()) BETWEEN 88 AND 92
ORDER BY DATEDIFF(day, Due, GETDATE());