-- Migrate Existing Users to RBAC System
-- Run this script AFTER creating tables and inserting default data

-- Assign Super Admin role to users with 'admin' in their legacy role field
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u, role r
WHERE u.role = 'admin' AND r.name = 'Super Admin'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur 
    WHERE ur.user_id = u.id AND ur.role_id = r.id
  );

-- Assign Leadership role to users with 'manager' in their legacy role field
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u, role r
WHERE u.role = 'manager' AND r.name = 'Leadership'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur 
    WHERE ur.user_id = u.id AND ur.role_id = r.id
  );

-- Assign Read Only role to all other users who don't have any roles yet
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u, role r
WHERE r.name = 'Read Only'
  AND u.role NOT IN ('admin', 'manager')
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur 
    WHERE ur.user_id = u.id
  );

-- For the first user in each organization, make them Super Admin if they don't have a role
WITH first_users AS (
    SELECT MIN(id) as user_id, organization_id
    FROM "user"
    GROUP BY organization_id
)
INSERT INTO user_roles (user_id, role_id)
SELECT fu.user_id, r.id
FROM first_users fu, role r
WHERE r.name = 'Super Admin'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur 
    WHERE ur.user_id = fu.user_id
  );

-- Verification query - show all users with their assigned roles
SELECT 
    u.id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.role as legacy_role,
    string_agg(r.name, ', ') as assigned_roles
FROM "user" u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
GROUP BY u.id, u.username, u.email, u.first_name, u.last_name, u.role
ORDER BY u.id;