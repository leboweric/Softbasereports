-- Fix user access issues

-- 1. Check what users exist and their roles
SELECT 
    u.username,
    u.email,
    u.is_active,
    string_agg(r.name, ', ') as roles,
    COUNT(r.id) as role_count
FROM "user" u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
GROUP BY u.id, u.username, u.email, u.is_active
ORDER BY u.username;

-- 2. Give elebow Super Admin role (so you can access everything)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u, role r
WHERE u.username = 'elebow' 
  AND r.name = 'Super Admin'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur 
    WHERE ur.user_id = u.id AND ur.role_id = r.id
  );

-- 3. Verify elebow now has Super Admin role
SELECT 
    u.username,
    r.name as role_name,
    COUNT(p.id) as permission_count
FROM "user" u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permission p ON rp.permission_id = p.id
WHERE u.username = 'elebow'
GROUP BY u.username, r.name;

-- 4. Delete the non-working admin user (optional)
-- DELETE FROM "user" WHERE username = 'admin';

-- 5. Or update admin password to match elebow's (abc123)
-- First, get elebow's password hash
SELECT username, password_hash 
FROM "user" 
WHERE username = 'elebow';

-- Then update admin with that hash (uncomment and run with the hash from above)
-- UPDATE "user" 
-- SET password_hash = 'PASTE_ELEBOW_HASH_HERE'
-- WHERE username = 'admin';

-- 6. Final check - who has Super Admin role?
SELECT 
    '=== USERS WITH SUPER ADMIN ROLE ===' as status;
SELECT 
    u.username,
    u.email,
    u.is_active,
    'Super Admin' as role,
    '36 permissions' as access
FROM "user" u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
WHERE r.name = 'Super Admin'
ORDER BY u.username;

-- Success message
SELECT '✅ elebow should now have Super Admin access!' as message
UNION ALL
SELECT 'Logout and login again to see all menu items.';