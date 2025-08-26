-- Check which tables already exist in the database
-- Run this FIRST to see what needs to be created

-- Check for user management tables
SELECT 
    'User Management Tables' as category,
    table_name,
    CASE 
        WHEN table_name IS NOT NULL THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END as status
FROM (
    SELECT 'organization' as expected_table
    UNION SELECT 'user'
    UNION SELECT 'report_template'
) expected
LEFT JOIN information_schema.tables actual
    ON actual.table_name = expected.expected_table
    AND actual.table_schema = 'public'
ORDER BY expected_table;

-- Check for RBAC tables
SELECT 
    'RBAC Tables' as category,
    table_name,
    CASE 
        WHEN table_name IS NOT NULL THEN '✓ EXISTS'
        ELSE '✗ MISSING'
    END as status
FROM (
    SELECT 'department' as expected_table
    UNION SELECT 'role'
    UNION SELECT 'permission'
    UNION SELECT 'user_roles'
    UNION SELECT 'role_permissions'
) expected
LEFT JOIN information_schema.tables actual
    ON actual.table_name = expected.expected_table
    AND actual.table_schema = 'public'
ORDER BY expected_table;

-- Count existing records in key tables
SELECT 
    'Record Counts' as category,
    t.table_name,
    (xpath('/row/cnt/text()', 
           query_to_xml(format('select count(*) as cnt from %I.%I', 
                              t.table_schema, t.table_name), 
                        false, true, ''))
    )[1]::text::int as row_count
FROM information_schema.tables t
WHERE t.table_schema = 'public'
  AND t.table_name IN ('user', 'organization', 'role', 'permission', 
                       'department', 'user_roles', 'role_permissions')
ORDER BY t.table_name;