-- Query to find control number field
-- Check Equipment table columns
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ben002'
AND TABLE_NAME = 'Equipment'
AND (
    COLUMN_NAME LIKE '%Control%'
    OR COLUMN_NAME LIKE '%Ctrl%'
    OR COLUMN_NAME LIKE '%Tag%'
    OR COLUMN_NAME LIKE '%Asset%'
    OR COLUMN_NAME LIKE '%Ref%'
)
ORDER BY COLUMN_NAME;

-- Check all tables for control-related columns
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ben002'
AND (
    COLUMN_NAME LIKE '%Control%'
    OR COLUMN_NAME LIKE '%Ctrl%'
)
ORDER BY TABLE_NAME, COLUMN_NAME;

-- Sample Equipment data to see all columns
SELECT TOP 5 *
FROM ben002.Equipment
WHERE SerialNo IS NOT NULL;