-- Debug query for Polaris, Grede, and Owens AR over 90 days

-- First, let's see all customers with these names
SELECT DISTINCT c.Number, c.Name
FROM ben002.Customer c
WHERE UPPER(c.Name) LIKE '%POLARIS%' 
   OR UPPER(c.Name) LIKE '%GREDE%' 
   OR UPPER(c.Name) LIKE '%OWENS%'
ORDER BY c.Name;

-- Now let's see the AR balance for these customers
WITH InvoiceBalances AS (
    SELECT 
        ar.CustomerNo,
        ar.InvoiceNo,
        MIN(ar.Due) as Due,
        SUM(ar.Amount) as NetBalance
    FROM ben002.ARDetail ar
    WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
        AND ar.DeletionTime IS NULL
    GROUP BY ar.CustomerNo, ar.InvoiceNo
    HAVING SUM(ar.Amount) > 0.01
)
SELECT 
    c.Name as CustomerName,
    COUNT(CASE WHEN DATEDIFF(day, ib.Due, GETDATE()) > 90 THEN 1 END) as InvoicesOver90,
    SUM(CASE WHEN DATEDIFF(day, ib.Due, GETDATE()) > 90 THEN ib.NetBalance ELSE 0 END) as AmountOver90,
    COUNT(*) as TotalOpenInvoices,
    SUM(ib.NetBalance) as TotalARBalance
FROM InvoiceBalances ib
INNER JOIN ben002.Customer c ON ib.CustomerNo = c.Number
WHERE UPPER(c.Name) LIKE '%POLARIS%' 
   OR UPPER(c.Name) LIKE '%GREDE%' 
   OR UPPER(c.Name) LIKE '%OWENS%'
GROUP BY c.Name
ORDER BY SUM(CASE WHEN DATEDIFF(day, ib.Due, GETDATE()) > 90 THEN ib.NetBalance ELSE 0 END) DESC;

-- Detail view - show specific invoices over 90 days
WITH InvoiceBalances AS (
    SELECT 
        ar.CustomerNo,
        ar.InvoiceNo,
        MIN(ar.Due) as Due,
        SUM(ar.Amount) as NetBalance
    FROM ben002.ARDetail ar
    WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
        AND ar.DeletionTime IS NULL
    GROUP BY ar.CustomerNo, ar.InvoiceNo
    HAVING SUM(ar.Amount) > 0.01
)
SELECT TOP 20
    c.Name as CustomerName,
    ib.InvoiceNo,
    ib.Due,
    DATEDIFF(day, ib.Due, GETDATE()) as DaysOverdue,
    ib.NetBalance
FROM InvoiceBalances ib
INNER JOIN ben002.Customer c ON ib.CustomerNo = c.Number
WHERE DATEDIFF(day, ib.Due, GETDATE()) > 90
    AND (UPPER(c.Name) LIKE '%POLARIS%' 
         OR UPPER(c.Name) LIKE '%GREDE%' 
         OR UPPER(c.Name) LIKE '%OWENS%')
ORDER BY ib.NetBalance DESC;