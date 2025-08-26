-- Debug and fix user login issues

-- 1. Check EXACTLY what users exist
SELECT 'Current users in database:' as info;
SELECT 
    id,
    username,
    email,
    first_name,
    last_name,
    is_active,
    substring(password_hash, 1, 20) as pass_hash_start
FROM "user"
ORDER BY id;

-- 2. Check who has roles assigned
SELECT 'Users with roles:' as info;
SELECT 
    u.username,
    u.email,
    string_agg(r.name, ', ') as roles,
    COUNT(r.id) as role_count
FROM "user" u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
GROUP BY u.id, u.username, u.email
ORDER BY u.username;

-- 3. Fix elebow - ensure it has Super Admin role
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u
CROSS JOIN role r
WHERE u.username = 'elebow'  -- Note: using username, not email
  AND r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- 4. Create/Update users with BOTH username and email correct
-- Update elebow user
UPDATE "user" 
SET 
    email = 'elebow@bmhmn.com',
    password_hash = '$2a$10$lPUiRt3O5Hba0nAiGLPKQOtL.r30cXC8YllgbqxvpKASW0hHyq0Tu',
    is_active = true
WHERE username = 'elebow';

-- Create jchristensen if doesn't exist, or update if it does
INSERT INTO "user" (
    username,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    organization_id,
    is_active
)
SELECT 
    'jchristensen',  -- Keep username simple
    'jchristensen@bmhmn.com',
    '$2a$10$lPUiRt3O5Hba0nAiGLPKQOtL.r30cXC8YllgbqxvpKASW0hHyq0Tu',
    'J',
    'Christensen',
    'admin',
    (SELECT id FROM organization LIMIT 1),
    true
ON CONFLICT (username) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    is_active = true;

-- 5. Ensure jchristensen has Super Admin role
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u
CROSS JOIN role r
WHERE u.username = 'jchristensen'
  AND r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- 6. Final verification
SELECT '=== FINAL USER STATUS ===' as info;
SELECT 
    u.username as "Login Username",
    u.email as "Email",
    CASE 
        WHEN u.password_hash = '$2a$10$lPUiRt3O5Hba0nAiGLPKQOtL.r30cXC8YllgbqxvpKASW0hHyq0Tu' 
        THEN 'abc123' 
        ELSE 'unknown' 
    END as "Password",
    string_agg(r.name, ', ') as "Roles",
    u.is_active as "Active"
FROM "user" u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
WHERE u.username IN ('elebow', 'jchristensen')
GROUP BY u.id, u.username, u.email, u.password_hash, u.is_active
ORDER BY u.username;

-- 7. Double check role permissions are linked
SELECT 
    'Super Admin role has ' || COUNT(*) || ' permissions' as check
FROM role_permissions rp
JOIN role r ON r.id = rp.role_id
WHERE r.name = 'Super Admin';

-- Instructions
SELECT '==========================================' as info
UNION ALL
SELECT 'LOGIN INSTRUCTIONS:'
UNION ALL
SELECT '------------------------------------------'
UNION ALL
SELECT 'Username: elebow'
UNION ALL
SELECT 'Password: abc123'
UNION ALL
SELECT ''
UNION ALL
SELECT 'Username: jchristensen'
UNION ALL
SELECT 'Password: abc123'
UNION ALL
SELECT '------------------------------------------'
UNION ALL
SELECT 'Both users now have Super Admin role'
UNION ALL
SELECT 'LOGOUT and LOGIN again to see menu items'
UNION ALL
SELECT '==========================================';