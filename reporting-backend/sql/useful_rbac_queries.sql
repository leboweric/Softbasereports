-- Useful RBAC Queries for Administration

-- 1. View all users with their roles
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

-- 2. View all permissions for a specific user (replace 'username_here')
SELECT DISTINCT
    u.username,
    r.name as role_name,
    p.name as permission_name,
    p.description
FROM "user" u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permission p ON rp.permission_id = p.id
WHERE u.username = 'username_here'
ORDER BY r.name, p.name;

-- 3. View all roles and their permission counts
SELECT 
    r.name as role_name,
    r.description,
    r.department,
    r.level,
    COUNT(rp.permission_id) as permission_count
FROM role r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
GROUP BY r.id, r.name, r.description, r.department, r.level
ORDER BY r.level DESC, r.name;

-- 4. View which users have access to specific departments
SELECT 
    u.username,
    u.email,
    r.name as role_name,
    CASE 
        WHEN r.name IN ('Super Admin', 'Leadership') THEN 'All Departments'
        WHEN r.department IS NOT NULL THEN r.department
        ELSE 'Dashboard Only'
    END as department_access
FROM "user" u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
WHERE u.is_active = true
ORDER BY department_access, u.username;

-- 5. Find users without any roles (need assignment)
SELECT 
    u.id,
    u.username,
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    u.created_at
FROM "user" u
LEFT JOIN user_roles ur ON u.id = ur.user_id
WHERE ur.user_id IS NULL
ORDER BY u.created_at DESC;

-- 6. Audit trail - see who assigned roles
SELECT 
    u1.username as user_name,
    r.name as role_name,
    ur.assigned_at,
    u2.username as assigned_by_username
FROM user_roles ur
JOIN "user" u1 ON ur.user_id = u1.id
JOIN role r ON ur.role_id = r.id
LEFT JOIN "user" u2 ON ur.assigned_by = u2.id
ORDER BY ur.assigned_at DESC;

-- 7. Check if a specific user has a specific permission (replace values)
SELECT EXISTS (
    SELECT 1
    FROM "user" u
    JOIN user_roles ur ON u.id = ur.user_id
    JOIN role r ON ur.role_id = r.id
    JOIN role_permissions rp ON r.id = rp.role_id
    JOIN permission p ON rp.permission_id = p.id
    WHERE u.username = 'username_here'
      AND p.name = 'view_parts'
) as has_permission;

-- 8. Count users by role
SELECT 
    r.name as role_name,
    COUNT(ur.user_id) as user_count
FROM role r
LEFT JOIN user_roles ur ON r.id = ur.role_id
GROUP BY r.id, r.name
ORDER BY user_count DESC;

-- 9. View all permissions grouped by resource
SELECT 
    resource,
    COUNT(*) as permission_count,
    string_agg(name || ' (' || action || ')', ', ') as permissions
FROM permission
GROUP BY resource
ORDER BY resource;

-- 10. Quick role assignment (replace user_id and role_name)
-- INSERT INTO user_roles (user_id, role_id, assigned_by)
-- SELECT 1, r.id, 1  -- user_id=1, assigned_by=1 (admin)
-- FROM role r
-- WHERE r.name = 'Parts Manager';

-- 11. Quick role removal (replace user_id and role_name)
-- DELETE FROM user_roles
-- WHERE user_id = 1
--   AND role_id = (SELECT id FROM role WHERE name = 'Parts Manager');