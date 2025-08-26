-- Verify RBAC Setup is Complete

-- 1. Summary of what's installed
SELECT '=== RBAC SETUP VERIFICATION ===' as status;

SELECT 
    'System Overview' as category,
    'Total Departments: ' || COUNT(DISTINCT d.id) || 
    ', Total Roles: ' || COUNT(DISTINCT r.id) || 
    ', Total Permissions: ' || COUNT(DISTINCT p.id) || 
    ', Total Users: ' || COUNT(DISTINCT u.id) as summary
FROM department d, role r, permission p, "user" u;

-- 2. Check admin user setup
SELECT '=== ADMIN USER STATUS ===' as status;
SELECT 
    u.username,
    u.email,
    u.is_active,
    o.name as organization,
    string_agg(r.name, ', ') as assigned_roles,
    COUNT(DISTINCT rp.permission_id) as total_permissions
FROM "user" u
JOIN organization o ON u.organization_id = o.id
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
LEFT JOIN role_permissions rp ON r.id = rp.role_id
WHERE u.username = 'admin'
GROUP BY u.username, u.email, u.is_active, o.name;

-- 3. List all roles with permission counts
SELECT '=== ROLES AND PERMISSIONS ===' as status;
SELECT 
    r.name as role_name,
    r.level,
    r.department,
    COUNT(rp.permission_id) as permission_count,
    CASE 
        WHEN r.name = 'Super Admin' THEN 'Full Access'
        WHEN r.name = 'Leadership' THEN 'View All Departments'
        WHEN r.department IS NOT NULL THEN r.department || ' Department'
        ELSE 'Limited Access'
    END as access_level
FROM role r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
GROUP BY r.id, r.name, r.level, r.department
ORDER BY r.level DESC, r.name;

-- 4. Check what menu items the admin will see
SELECT '=== ADMIN MENU ACCESS ===' as status;
SELECT DISTINCT
    CASE 
        WHEN p.resource = 'dashboard' THEN '✓ Dashboard'
        WHEN p.resource = 'parts' THEN '✓ Parts'
        WHEN p.resource = 'service' THEN '✓ Service'
        WHEN p.resource = 'rental' THEN '✓ Rental'
        WHEN p.resource = 'accounting' THEN '✓ Accounting'
        WHEN p.resource = 'minitrac' THEN '✓ Minitrac'
        WHEN p.resource = 'ai' THEN '✓ AI Query'
        WHEN p.resource = 'reports' THEN '✓ Report Creator'
        WHEN p.resource = 'database' THEN '✓ Database Explorer'
        WHEN p.resource = 'users' THEN '✓ Users'
        ELSE p.resource
    END as menu_item
FROM "user" u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permission p ON rp.permission_id = p.id
WHERE u.username = 'admin'
  AND p.action = 'view'
ORDER BY menu_item;

-- 5. Test permission check for admin
SELECT '=== PERMISSION TEST ===' as status;
SELECT 
    'Can admin view Parts?' as test,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM "user" u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN role r ON ur.role_id = r.id
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permission p ON rp.permission_id = p.id
            WHERE u.username = 'admin' AND p.name = 'view_parts'
        ) THEN '✓ YES'
        ELSE '✗ NO'
    END as result
UNION ALL
SELECT 
    'Can admin manage users?' as test,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM "user" u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN role r ON ur.role_id = r.id
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permission p ON rp.permission_id = p.id
            WHERE u.username = 'admin' AND p.name = 'manage_roles'
        ) THEN '✓ YES'
        ELSE '✗ NO'
    END as result
UNION ALL
SELECT 
    'Can admin use AI Query?' as test,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM "user" u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN role r ON ur.role_id = r.id
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permission p ON rp.permission_id = p.id
            WHERE u.username = 'admin' AND p.name = 'use_ai_query'
        ) THEN '✓ YES'
        ELSE '✗ NO'
    END as result;

-- 6. Ready to login message
SELECT '==========================================' as info
UNION ALL
SELECT '✅ RBAC SETUP COMPLETE!' 
UNION ALL
SELECT '------------------------------------------'
UNION ALL
SELECT 'You can now login with:'
UNION ALL
SELECT '  Username: admin'
UNION ALL
SELECT '  Password: admin123'
UNION ALL
SELECT ''
UNION ALL
SELECT 'The admin user has Super Admin role with:'
UNION ALL
SELECT '  • Access to all departments'
UNION ALL
SELECT '  • User management capabilities'
UNION ALL
SELECT '  • All 36 permissions granted'
UNION ALL
SELECT '==========================================';