-- Check what data was actually inserted and fix missing data

-- 1. Check what we have
SELECT 'Departments' as category, COUNT(*) as count FROM department
UNION ALL
SELECT 'Roles', COUNT(*) FROM role
UNION ALL
SELECT 'Permissions', COUNT(*) FROM permission
UNION ALL
SELECT 'Role-Permission Links', COUNT(*) FROM role_permissions
UNION ALL
SELECT 'User-Role Links', COUNT(*) FROM user_roles;

-- 2. Check specific records
SELECT '--- Existing Departments ---' as info;
SELECT name FROM department;

SELECT '--- Existing Roles ---' as info;
SELECT name, level FROM role ORDER BY level DESC;

SELECT '--- Existing Permissions (first 10) ---' as info;
SELECT name FROM permission LIMIT 10;

-- 3. Clear and re-insert if needed (uncomment if you want to start fresh)
-- TRUNCATE TABLE role_permissions CASCADE;
-- TRUNCATE TABLE user_roles CASCADE;
-- TRUNCATE TABLE permission CASCADE;
-- TRUNCATE TABLE role CASCADE;
-- TRUNCATE TABLE department CASCADE;

-- 4. Re-run the inserts with better error handling
DO $$ 
BEGIN
    -- Insert Departments (should be 5)
    INSERT INTO department (name, code, description) VALUES
        ('Parts', 'PRT', 'Parts department'),
        ('Service', 'SVC', 'Service department'),
        ('Rental', 'RNT', 'Rental department'),
        ('Accounting', 'ACC', 'Accounting department'),
        ('Sales', 'SLS', 'Sales department')
    ON CONFLICT (code) DO NOTHING;
    
    RAISE NOTICE 'Departments inserted: %', (SELECT COUNT(*) FROM department);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error inserting departments: %', SQLERRM;
END $$;

DO $$ 
BEGIN
    -- Insert Roles (should be 10)
    INSERT INTO role (name, description, department, level) VALUES
        ('Super Admin', 'Full system access', NULL, 10),
        ('Leadership', 'Executive level access to all departments', NULL, 9),
        ('Accounting Manager', 'Full access to accounting and financial data', 'Accounting', 5),
        ('Parts Manager', 'Full access to parts department', 'Parts', 5),
        ('Service Manager', 'Full access to service department', 'Service', 5),
        ('Rental Manager', 'Full access to rental department', 'Rental', 5),
        ('Parts Staff', 'View-only access to parts data', 'Parts', 1),
        ('Service Tech', 'View service work orders and update status', 'Service', 1),
        ('Sales Rep', 'View own commission data', 'Sales', 1),
        ('Read Only', 'View-only access to authorized areas', NULL, 0)
    ON CONFLICT (name) DO NOTHING;
    
    RAISE NOTICE 'Roles inserted: %', (SELECT COUNT(*) FROM role);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error inserting roles: %', SQLERRM;
END $$;

DO $$ 
BEGIN
    -- Insert all 42 permissions
    INSERT INTO permission (name, resource, action, description) VALUES
        ('view_dashboard', 'dashboard', 'view', 'View main dashboard'),
        ('view_parts', 'parts', 'view', 'View parts reports and data'),
        ('edit_parts', 'parts', 'edit', 'Edit parts data'),
        ('view_inventory', 'inventory', 'view', 'View inventory levels'),
        ('edit_inventory', 'inventory', 'edit', 'Adjust inventory levels'),
        ('export_parts', 'parts', 'export', 'Export parts data'),
        ('view_service', 'service', 'view', 'View service reports and work orders'),
        ('edit_service', 'service', 'edit', 'Edit service data'),
        ('view_technicians', 'technicians', 'view', 'View technician performance'),
        ('edit_work_orders', 'work_orders', 'edit', 'Edit work orders'),
        ('edit_own_work_orders', 'work_orders', 'edit_own', 'Edit only own work orders'),
        ('export_service', 'service', 'export', 'Export service data'),
        ('view_rental', 'rental', 'view', 'View rental reports'),
        ('edit_rental', 'rental', 'edit', 'Edit rental data'),
        ('view_equipment', 'equipment', 'view', 'View equipment status'),
        ('edit_equipment', 'equipment', 'edit', 'Edit equipment data'),
        ('export_rental', 'rental', 'export', 'Export rental data'),
        ('view_accounting', 'accounting', 'view', 'View accounting reports'),
        ('edit_accounting', 'accounting', 'edit', 'Edit accounting data'),
        ('view_commissions', 'commissions', 'view', 'View all commission data'),
        ('edit_commissions', 'commissions', 'edit', 'Edit commission calculations'),
        ('view_own_commissions', 'commissions', 'view_own', 'View only own commission data'),
        ('view_ar', 'accounts_receivable', 'view', 'View AR aging reports'),
        ('export_accounting', 'accounting', 'export', 'Export accounting data'),
        ('view_customers', 'customers', 'view', 'View all customers'),
        ('view_own_customers', 'customers', 'view_own', 'View only assigned customers'),
        ('edit_customers', 'customers', 'edit', 'Edit customer data'),
        ('view_users', 'users', 'view', 'View user list'),
        ('edit_users', 'users', 'edit', 'Edit user accounts'),
        ('manage_roles', 'roles', 'manage', 'Manage user roles and permissions'),
        ('view_database_explorer', 'database', 'view', 'Access database explorer'),
        ('execute_queries', 'database', 'execute', 'Execute custom SQL queries'),
        ('use_ai_query', 'ai', 'query', 'Use AI query assistant'),
        ('use_report_creator', 'reports', 'create', 'Create custom reports'),
        ('view_minitrac', 'minitrac', 'view', 'View Minitrac equipment data'),
        ('export_minitrac', 'minitrac', 'export', 'Export Minitrac data')
    ON CONFLICT (name) DO NOTHING;
    
    RAISE NOTICE 'Permissions inserted: %', (SELECT COUNT(*) FROM permission);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error inserting permissions: %', SQLERRM;
END $$;

-- 5. Link Super Admin role with ALL permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r
CROSS JOIN permission p
WHERE r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- 6. Link other roles with their permissions
-- Leadership gets all view and export permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r
CROSS JOIN permission p
WHERE r.name = 'Leadership' 
  AND (p.name LIKE 'view_%' OR p.name LIKE 'export_%')
ON CONFLICT DO NOTHING;

-- Parts Manager
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r
CROSS JOIN permission p
WHERE r.name = 'Parts Manager' 
  AND p.name IN ('view_dashboard', 'view_parts', 'edit_parts', 
                 'view_inventory', 'edit_inventory', 'export_parts')
ON CONFLICT DO NOTHING;

-- Service Manager
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r
CROSS JOIN permission p
WHERE r.name = 'Service Manager' 
  AND p.name IN ('view_dashboard', 'view_service', 'edit_service', 
                 'view_technicians', 'edit_work_orders', 'export_service')
ON CONFLICT DO NOTHING;

-- Accounting Manager
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r
CROSS JOIN permission p
WHERE r.name = 'Accounting Manager' 
  AND p.name IN ('view_dashboard', 'view_accounting', 'edit_accounting', 
                 'view_commissions', 'edit_commissions', 'view_ar', 
                 'export_accounting')
ON CONFLICT DO NOTHING;

-- Read Only
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r
CROSS JOIN permission p
WHERE r.name = 'Read Only' 
  AND p.name = 'view_dashboard'
ON CONFLICT DO NOTHING;

-- 7. Final check
SELECT 'Final Counts After Fix:' as status;
SELECT 'Departments' as category, COUNT(*) as count FROM department
UNION ALL
SELECT 'Roles', COUNT(*) FROM role
UNION ALL
SELECT 'Permissions', COUNT(*) FROM permission
UNION ALL
SELECT 'Role-Permission Links', COUNT(*) FROM role_permissions
UNION ALL
SELECT 'User-Role Links', COUNT(*) FROM user_roles
ORDER BY category;

-- 8. Verify Super Admin has all permissions
SELECT 
    r.name as role,
    COUNT(rp.permission_id) as permission_count
FROM role r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
WHERE r.name = 'Super Admin'
GROUP BY r.name;