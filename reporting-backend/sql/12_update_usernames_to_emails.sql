-- Update usernames to use full email addresses

-- 1. Update elebow to elebow@bmhmn.com
UPDATE "user" 
SET username = 'elebow@bmhmn.com'
WHERE username = 'elebow';

-- 2. Update jchristensen to jchristensen@bmhmn.com
UPDATE "user" 
SET username = 'jchristensen@bmhmn.com'
WHERE username = 'jchristensen';

-- 3. Update admin if it exists
UPDATE "user" 
SET username = 'admin@bennettequipment.com'
WHERE username = 'admin';

-- 4. Verify the updates
SELECT 
    u.id,
    u.username,
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    u.is_active,
    string_agg(r.name, ', ') as roles
FROM "user" u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
GROUP BY u.id, u.username, u.email, u.first_name, u.last_name, u.is_active
ORDER BY u.username;

-- Success message
SELECT '===========================================' as info
UNION ALL
SELECT '✅ Usernames Updated Successfully!'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'User 1: elebow@bmhmn.com / abc123'
UNION ALL
SELECT 'User 2: jchristensen@bmhmn.com / abc123'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'Login with full email address as username'
UNION ALL
SELECT '===========================================';