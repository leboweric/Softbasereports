-- Investigation query to understand AR aging discrepancies

-- 1. Check records in 1-30 bucket (why is it negative?)
SELECT 
    EntryType,
    COUNT(*) as RecordCount,
    SUM(Amount) as TotalAmount
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL
    AND DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30
GROUP BY EntryType
ORDER BY EntryType;

-- 2. Sample of payments in 1-30 bucket
SELECT TOP 10
    InvoiceNo,
    CustomerNo,
    EntryType,
    Amount,
    Due,
    EntryDate,
    DATEDIFF(day, Due, GETDATE()) as DaysOld
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL
    AND DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30
    AND Amount < 0  -- Payments/Credits
ORDER BY Amount;

-- 3. Check records in 60-90 bucket (why is it so large?)
SELECT 
    EntryType,
    COUNT(*) as RecordCount,
    SUM(Amount) as TotalAmount
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL
    AND DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90
GROUP BY EntryType
ORDER BY SUM(Amount) DESC;

-- 4. Your source system bucket query - what are you using?
-- This shows aging by invoice balance (grouping payments with their invoices)
WITH InvoiceBalances AS (
    SELECT 
        ar.InvoiceNo,
        ar.CustomerNo,
        MIN(ar.Due) as Due,  -- Use earliest due date for the invoice
        SUM(ar.Amount) as NetBalance
    FROM ben002.ARDetail ar
    WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
        AND ar.DeletionTime IS NULL
    GROUP BY ar.InvoiceNo, ar.CustomerNo
    HAVING SUM(ar.Amount) > 0.01  -- Only open invoices
)
SELECT 
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30 THEN '1-30'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 31 AND 60 THEN '31-60'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90 THEN '61-90'
        WHEN DATEDIFF(day, Due, GETDATE()) > 90 THEN 'Over 90'
    END as AgingBucket,
    COUNT(*) as InvoiceCount,
    SUM(NetBalance) as TotalAmount
FROM InvoiceBalances
GROUP BY 
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30 THEN '1-30'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 31 AND 60 THEN '31-60'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90 THEN '61-90'
        WHEN DATEDIFF(day, Due, GETDATE()) > 90 THEN 'Over 90'
    END
ORDER BY AgingBucket;