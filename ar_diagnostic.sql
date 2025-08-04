-- Diagnostic query to understand AR discrepancy

-- 1. Total AR (should be $1,697k)
SELECT 'Total AR' as Description, SUM(Amount) as Amount
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL;

-- 2. Check if we have duplicate Due dates per invoice
SELECT 'Invoices with multiple due dates' as Description, 
    COUNT(*) as Count
FROM (
    SELECT InvoiceNo, COUNT(DISTINCT Due) as DueDateCount
    FROM ben002.ARDetail
    WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
        AND DeletionTime IS NULL
        AND InvoiceNo IS NOT NULL
    GROUP BY InvoiceNo
    HAVING COUNT(DISTINCT Due) > 1
) x;

-- 3. Sum of amounts when grouping by Due date (what our buckets are doing)
SELECT 'Sum grouped by Due' as Description, SUM(Amount) as Amount
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL;

-- 4. Check EntryType distribution
SELECT EntryType, COUNT(*) as RecordCount, SUM(Amount) as TotalAmount
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL
GROUP BY EntryType
ORDER BY SUM(Amount) DESC;

-- 5. Sample of records to see the data
SELECT TOP 10 
    InvoiceNo,
    CustomerNo,
    EntryType,
    Amount,
    Due,
    DATEDIFF(day, Due, GETDATE()) as DaysOld
FROM ben002.ARDetail
WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
    AND DeletionTime IS NULL
ORDER BY ABS(Amount) DESC;