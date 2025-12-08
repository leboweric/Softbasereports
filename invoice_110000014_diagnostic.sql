-- Diagnostic Query for Invoice 110000014
-- This query shows exactly how the salesman was determined for this invoice

-- Step 1: Get the invoice details
SELECT 
    'Invoice Details' as Section,
    ir.InvoiceNo,
    ir.InvoiceDate,
    ir.BillTo as BillToNumber,
    ir.BillToName,
    ir.SaleCode,
    ir.GrandTotal
FROM ben002.InvoiceReg ir
WHERE ir.InvoiceNo = '110000014';

-- Step 2: Check Priority 1 - BillTo Number Match
SELECT 
    'Priority 1: BillTo Number Match' as Section,
    c.Number as CustomerNumber,
    c.Name as CustomerName,
    c.Salesman1,
    'This is the customer record matched by BillTo number' as Note
FROM ben002.InvoiceReg ir
INNER JOIN ben002.Customer c ON ir.BillTo = c.Number
WHERE ir.InvoiceNo = '110000014';

-- Step 3: Check Priority 2 - Exact BillToName Match
SELECT 
    'Priority 2: Exact BillToName Match' as Section,
    c.Number as CustomerNumber,
    c.Name as CustomerName,
    c.Salesman1,
    'These customer records have exact name match' as Note
FROM ben002.InvoiceReg ir
INNER JOIN ben002.Customer c ON ir.BillToName = c.Name
WHERE ir.InvoiceNo = '110000014'
    AND c.Salesman1 IS NOT NULL;

-- Step 4: Check Priority 3 - First Word Match
SELECT 
    'Priority 3: First Word Match' as Section,
    c.Number as CustomerNumber,
    c.Name as CustomerName,
    c.Salesman1,
    CASE 
        WHEN CHARINDEX(' ', ir.BillToName) > 0 
        THEN LEFT(ir.BillToName, CHARINDEX(' ', ir.BillToName) - 1)
        ELSE ir.BillToName
    END as InvoiceFirstWord,
    CASE 
        WHEN CHARINDEX(' ', c.Name) > 0 
        THEN LEFT(c.Name, CHARINDEX(' ', c.Name) - 1)
        ELSE c.Name
    END as CustomerFirstWord,
    'These customer records match on first word' as Note
FROM ben002.InvoiceReg ir
INNER JOIN ben002.Customer c ON 
    c.Salesman1 IS NOT NULL
    AND LEN(ir.BillToName) >= 4
    AND LEN(c.Name) >= 4
    AND UPPER(
        CASE 
            WHEN CHARINDEX(' ', ir.BillToName) > 0 
            THEN LEFT(ir.BillToName, CHARINDEX(' ', ir.BillToName) - 1)
            ELSE ir.BillToName
        END
    ) = UPPER(
        CASE 
            WHEN CHARINDEX(' ', c.Name) > 0 
            THEN LEFT(c.Name, CHARINDEX(' ', c.Name) - 1)
            ELSE c.Name
        END
    )
WHERE ir.InvoiceNo = '110000014';

-- Step 5: Show ALL customer records that might be related
SELECT 
    'All Related Customer Records' as Section,
    c.Number as CustomerNumber,
    c.Name as CustomerName,
    c.Salesman1,
    CASE 
        WHEN c.Number = ir.BillTo THEN 'Matches BillTo Number'
        WHEN c.Name = ir.BillToName THEN 'Matches BillToName Exactly'
        ELSE 'Other'
    END as MatchType
FROM ben002.InvoiceReg ir
LEFT JOIN ben002.Customer c ON (
    c.Number = ir.BillTo 
    OR c.Name = ir.BillToName
    OR (
        LEN(ir.BillToName) >= 4
        AND LEN(c.Name) >= 4
        AND UPPER(
            CASE 
                WHEN CHARINDEX(' ', ir.BillToName) > 0 
                THEN LEFT(ir.BillToName, CHARINDEX(' ', ir.BillToName) - 1)
                ELSE ir.BillToName
            END
        ) = UPPER(
            CASE 
                WHEN CHARINDEX(' ', c.Name) > 0 
                THEN LEFT(c.Name, CHARINDEX(' ', c.Name) - 1)
                ELSE c.Name
            END
        )
    )
)
WHERE ir.InvoiceNo = '110000014'
ORDER BY 
    CASE 
        WHEN c.Number = ir.BillTo THEN 1
        WHEN c.Name = ir.BillToName THEN 2
        ELSE 3
    END;

-- Step 6: Check if Kevin Buckman exists as a salesman in ANY customer records
SELECT 
    'Kevin Buckman Customer Records' as Section,
    c.Number as CustomerNumber,
    c.Name as CustomerName,
    c.Salesman1,
    'These customers have Kevin Buckman as salesman' as Note
FROM ben002.Customer c
WHERE c.Salesman1 LIKE '%Kevin%Buckman%'
    OR c.Salesman1 LIKE '%Buckman%'
    OR c.Salesman1 LIKE '%Kevin%';

-- Step 7: Show the final salesman assignment using the same logic as the report
WITH SalesmanLookup AS (
    SELECT 
        InvoiceNo,
        Salesman1,
        Priority,
        MatchMethod
    FROM (
        SELECT 
            InvoiceNo,
            Salesman1,
            Priority,
            MatchMethod,
            ROW_NUMBER() OVER (PARTITION BY InvoiceNo ORDER BY Priority) as rn
        FROM (
            SELECT DISTINCT
                ir.InvoiceNo,
                CASE 
                    WHEN c1.Salesman1 IS NOT NULL THEN c1.Salesman1
                    WHEN c2.Salesman1 IS NOT NULL THEN c2.Salesman1
                    WHEN c3.Salesman1 IS NOT NULL THEN c3.Salesman1
                    ELSE NULL
                END as Salesman1,
                CASE 
                    WHEN c1.Salesman1 IS NOT NULL THEN 1
                    WHEN c2.Salesman1 IS NOT NULL THEN 2
                    WHEN c3.Salesman1 IS NOT NULL THEN 3
                    ELSE 4
                END as Priority,
                CASE 
                    WHEN c1.Salesman1 IS NOT NULL THEN 'Priority 1: BillTo Number'
                    WHEN c2.Salesman1 IS NOT NULL THEN 'Priority 2: Exact Name'
                    WHEN c3.Salesman1 IS NOT NULL THEN 'Priority 3: First Word'
                    ELSE 'No Match'
                END as MatchMethod
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c1 ON ir.BillTo = c1.Number
            LEFT JOIN ben002.Customer c2 ON ir.BillToName = c2.Name AND c2.Salesman1 IS NOT NULL
            LEFT JOIN ben002.Customer c3 ON 
                c3.Salesman1 IS NOT NULL
                AND LEN(ir.BillToName) >= 4
                AND LEN(c3.Name) >= 4
                AND UPPER(
                    CASE 
                        WHEN CHARINDEX(' ', ir.BillToName) > 0 
                        THEN LEFT(ir.BillToName, CHARINDEX(' ', ir.BillToName) - 1)
                        ELSE ir.BillToName
                    END
                ) = UPPER(
                    CASE 
                        WHEN CHARINDEX(' ', c3.Name) > 0 
                        THEN LEFT(c3.Name, CHARINDEX(' ', c3.Name) - 1)
                        ELSE c3.Name
                    END
                )
            WHERE ir.InvoiceNo = '110000014'
        ) AS SalesmanMatches
    ) AS RankedMatches
    WHERE rn = 1
)
SELECT 
    'Final Assignment Result' as Section,
    sl.InvoiceNo,
    sl.Salesman1 as AssignedSalesman,
    sl.Priority,
    sl.MatchMethod,
    CASE 
        WHEN UPPER(sl.Salesman1) = 'HOUSE' THEN 'This invoice will appear in UNASSIGNED section'
        WHEN sl.Salesman1 IS NULL THEN 'This invoice will appear in UNASSIGNED section'
        ELSE 'This invoice will appear under ' + sl.Salesman1
    END as ReportLocation
FROM SalesmanLookup sl;
