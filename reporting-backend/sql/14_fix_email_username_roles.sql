-- Fix roles for users with email usernames

-- 1. Check current role assignments
SELECT 'Current role assignments:' as info;
SELECT 
    u.username,
    string_agg(r.name, ', ') as roles,
    COUNT(r.id) as role_count
FROM "user" u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
GROUP BY u.id, u.username
ORDER BY u.username;

-- 2. Assign Super Admin role to elebow@bmhmn.com
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u
CROSS JOIN role r
WHERE u.username = 'elebow@bmhmn.com'  -- Using email as username
  AND r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- 3. Assign Super Admin role to jchristensen@bmhmn.com
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u
CROSS JOIN role r
WHERE u.username = 'jchristensen@bmhmn.com'  -- Using email as username
  AND r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- 4. Also fix admin@bennettequipment.com
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u
CROSS JOIN role r
WHERE u.username = 'admin@bennettequipment.com'
  AND r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- 5. Verify roles are now assigned
SELECT '=== AFTER FIX - Users with roles ===' as info;
SELECT 
    u.id,
    u.username,
    string_agg(r.name, ', ') as roles,
    COUNT(DISTINCT p.id) as permission_count
FROM "user" u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permission p ON rp.permission_id = p.id
GROUP BY u.id, u.username
ORDER BY u.username;

-- 6. Specific check for elebow@bmhmn.com
SELECT 'Permissions for elebow@bmhmn.com:' as info;
SELECT COUNT(DISTINCT p.id) as total_permissions
FROM "user" u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permission p ON rp.permission_id = p.id
WHERE u.username = 'elebow@bmhmn.com';

-- Success message
SELECT '===========================================' as info
UNION ALL
SELECT '✅ Roles Fixed!' 
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'Login with these credentials:'
UNION ALL
SELECT ''
UNION ALL
SELECT 'Username: elebow@bmhmn.com'
UNION ALL
SELECT 'Password: abc123'
UNION ALL
SELECT ''
UNION ALL
SELECT 'Username: jchristensen@bmhmn.com'
UNION ALL
SELECT 'Password: abc123'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'Both users now have Super Admin role'
UNION ALL
SELECT 'with 36 permissions each'
UNION ALL
SELECT '===========================================';