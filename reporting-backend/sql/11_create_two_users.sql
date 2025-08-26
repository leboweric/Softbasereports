-- Create two users with abc123 password and Super Admin role

-- 1. First ensure organization exists (check first, then insert if needed)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM organization WHERE name = 'Bennett Equipment') THEN
        INSERT INTO organization (name, is_active)
        VALUES ('Bennett Equipment', true);
    END IF;
END $$;

-- 2. Create elebow@bmhmn.com user
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
    'elebow',
    'elebow@bmhmn.com',
    '$2a$10$lPUiRt3O5Hba0nAiGLPKQOtL.r30cXC8YllgbqxvpKASW0hHyq0Tu', -- abc123
    'Eric',
    'LeBow',
    'admin',
    o.id,
    true
FROM organization o
WHERE o.name = 'Bennett Equipment'
ON CONFLICT (username) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    is_active = true;

-- 3. Create jchristensen@bmhmn.com user
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
    'jchristensen',
    'jchristensen@bmhmn.com',
    '$2a$10$lPUiRt3O5Hba0nAiGLPKQOtL.r30cXC8YllgbqxvpKASW0hHyq0Tu', -- abc123
    'J',
    'Christensen',
    'admin',
    o.id,
    true
FROM organization o
WHERE o.name = 'Bennett Equipment'
ON CONFLICT (username) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    is_active = true;

-- 4. Assign Super Admin role to elebow
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u
CROSS JOIN role r
WHERE u.username = 'elebow' 
  AND r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- 5. Assign Super Admin role to jchristensen
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u
CROSS JOIN role r
WHERE u.username = 'jchristensen'
  AND r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- 6. Verify both users were created with roles
SELECT 
    u.username,
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    u.is_active,
    string_agg(r.name, ', ') as roles
FROM "user" u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
WHERE u.username IN ('elebow', 'jchristensen')
GROUP BY u.id, u.username, u.email, u.first_name, u.last_name, u.is_active
ORDER BY u.username;

-- Success message
SELECT '===========================================' as info
UNION ALL
SELECT '✅ Users Created Successfully!'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'User 1: elebow / abc123 (Super Admin)'
UNION ALL
SELECT 'User 2: jchristensen / abc123 (Super Admin)'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'Both users can now login with password: abc123'
UNION ALL
SELECT '===========================================';