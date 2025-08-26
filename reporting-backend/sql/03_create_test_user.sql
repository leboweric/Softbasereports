-- Create a test organization and admin user
-- Only run this if you need to create your first user

-- Create organization
INSERT INTO organization (name, is_active)
VALUES ('Bennett Equipment', true)
ON CONFLICT DO NOTHING;

-- Create admin user (password: admin123)
-- Note: This uses a simple hash for testing. In production, use proper password hashing
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
    'admin',
    'admin@bennettequipment.com',
    -- This is a bcrypt hash of 'admin123' - CHANGE THIS PASSWORD AFTER FIRST LOGIN
    '$2b$12$YH6R5VryKw6P3zr9h2UN2ukohFLSAYDf9H.rG7F1qY2hPjM5qB3Vy',
    'Admin',
    'User',
    'admin',
    o.id,
    true
FROM organization o
WHERE o.name = 'Bennett Equipment'
ON CONFLICT (username) DO NOTHING;

-- Assign Super Admin role to the admin user
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u, role r
WHERE u.username = 'admin' 
  AND r.name = 'Super Admin'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur 
    WHERE ur.user_id = u.id AND ur.role_id = r.id
  );

-- Verify user was created with role
SELECT 
    u.username,
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    o.name as organization,
    r.name as role_name
FROM "user" u
JOIN organization o ON u.organization_id = o.id
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
WHERE u.username = 'admin';

-- Show login credentials
SELECT 
    '===========================================' as info
UNION ALL
SELECT 'Test User Created Successfully!'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'Username: admin'
UNION ALL
SELECT 'Password: admin123'
UNION ALL
SELECT 'Role: Super Admin'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'IMPORTANT: Change this password after first login!'
UNION ALL
SELECT '===========================================';