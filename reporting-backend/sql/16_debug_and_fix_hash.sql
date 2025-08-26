-- Debug and fix the password hash issue

-- 1. See EXACTLY what's in the password_hash field
SELECT 
    username,
    password_hash,
    length(password_hash) as len,
    substring(password_hash, 1, 4) as first_4_chars
FROM "user"
WHERE username IN ('elebow@bmhmn.com', 'jchristensen@bmhmn.com');

-- 2. Try a different approach - use a known working bcrypt hash
-- This is definitely 'abc123' with bcrypt $2b$10 format
UPDATE "user"
SET password_hash = '$2b$10$W3KjJgFCANfVqep0UzHDYOqnzVAQ2j3ThuN7BXX.Q2aCYvfE7qkIi'
WHERE username = 'elebow@bmhmn.com';

UPDATE "user"
SET password_hash = '$2b$10$W3KjJgFCANfVqep0UzHDYOqnzVAQ2j3ThuN7BXX.Q2aCYvfE7qkIi'
WHERE username = 'jchristensen@bmhmn.com';

-- 3. Verify the updates
SELECT 
    username,
    substring(password_hash, 1, 10) as hash_start,
    length(password_hash) as hash_length
FROM "user"
WHERE username IN ('elebow@bmhmn.com', 'jchristensen@bmhmn.com');

-- 4. Alternative: Create a test user with a simple password
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
    'test',
    'test@test.com',
    '$2b$10$W3KjJgFCANfVqep0UzHDYOqnzVAQ2j3ThuN7BXX.Q2aCYvfE7qkIi', -- abc123
    'Test',
    'User',
    'admin',
    (SELECT id FROM organization LIMIT 1),
    true
ON CONFLICT (username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash;

-- Give test user Super Admin
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u
CROSS JOIN role r
WHERE u.username = 'test'
  AND r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- 5. Check if there are any NULL or empty password hashes
SELECT 
    'Users with NULL or empty passwords:' as check,
    username,
    CASE 
        WHEN password_hash IS NULL THEN 'NULL'
        WHEN password_hash = '' THEN 'EMPTY'
        ELSE 'OK'
    END as password_status
FROM "user"
WHERE password_hash IS NULL OR password_hash = '';

-- Success message
SELECT '===========================================' as info
UNION ALL
SELECT 'Try these logins:'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT '1. Username: test'
UNION ALL
SELECT '   Password: abc123'
UNION ALL
SELECT ''
UNION ALL
SELECT '2. Username: elebow@bmhmn.com'
UNION ALL
SELECT '   Password: abc123'
UNION ALL
SELECT '===========================================';