-- Debug AR aging buckets to see actual values
WITH InvoiceBalances AS (
    SELECT 
        ar.InvoiceNo,
        ar.CustomerNo,
        MIN(ar.Due) as Due,
        SUM(ar.Amount) as NetBalance
    FROM ben002.ARDetail ar
    WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
        AND ar.DeletionTime IS NULL
        AND ar.InvoiceNo IS NOT NULL
    GROUP BY ar.InvoiceNo, ar.CustomerNo
    HAVING SUM(ar.Amount) > 0.01
)
SELECT 
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) < 30 THEN 'Current'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 30 AND 59 THEN '30-60'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 60 AND 89 THEN '60-90'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 90 AND 119 THEN '90-120'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 120 THEN '120+'
    END as AgingBucket,
    COUNT(*) as RecordCount,
    SUM(NetBalance) as TotalAmount
FROM InvoiceBalances
GROUP BY 
    CASE 
        WHEN Due IS NULL THEN 'No Due Date'
        WHEN DATEDIFF(day, Due, GETDATE()) < 30 THEN 'Current'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 30 AND 59 THEN '30-60'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 60 AND 89 THEN '60-90'
        WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 90 AND 119 THEN '90-120'
        WHEN DATEDIFF(day, Due, GETDATE()) >= 120 THEN '120+'
    END
ORDER BY 
    CASE AgingBucket
        WHEN 'Current' THEN 1
        WHEN '30-60' THEN 2
        WHEN '60-90' THEN 3
        WHEN '90-120' THEN 4
        WHEN '120+' THEN 5
        WHEN 'No Due Date' THEN 6
    END;

-- Show what the over 90 total should be
WITH InvoiceBalances AS (
    SELECT 
        ar.InvoiceNo,
        ar.CustomerNo,
        MIN(ar.Due) as Due,
        SUM(ar.Amount) as NetBalance
    FROM ben002.ARDetail ar
    WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
        AND ar.DeletionTime IS NULL
        AND ar.InvoiceNo IS NOT NULL
    GROUP BY ar.InvoiceNo, ar.CustomerNo
    HAVING SUM(ar.Amount) > 0.01
)
SELECT 
    'Over 90 Days Total' as Description,
    SUM(CASE 
        WHEN DATEDIFF(day, Due, GETDATE()) >= 90 THEN NetBalance
        ELSE 0
    END) as Amount
FROM InvoiceBalances;