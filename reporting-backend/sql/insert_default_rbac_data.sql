-- Insert Default RBAC Data
-- Run this script AFTER creating the tables to populate with default roles, permissions, and departments

-- Insert Default Departments
INSERT INTO department (name, code, description) VALUES
    ('Parts', 'PRT', 'Parts department'),
    ('Service', 'SVC', 'Service department'),
    ('Rental', 'RNT', 'Rental department'),
    ('Accounting', 'ACC', 'Accounting department'),
    ('Sales', 'SLS', 'Sales department')
ON CONFLICT (code) DO NOTHING;

-- Insert Default Permissions
INSERT INTO permission (name, resource, action, description) VALUES
    -- Dashboard
    ('view_dashboard', 'dashboard', 'view', 'View main dashboard'),
    
    -- Parts Department
    ('view_parts', 'parts', 'view', 'View parts reports and data'),
    ('edit_parts', 'parts', 'edit', 'Edit parts data'),
    ('view_inventory', 'inventory', 'view', 'View inventory levels'),
    ('edit_inventory', 'inventory', 'edit', 'Adjust inventory levels'),
    ('export_parts', 'parts', 'export', 'Export parts data'),
    
    -- Service Department
    ('view_service', 'service', 'view', 'View service reports and work orders'),
    ('edit_service', 'service', 'edit', 'Edit service data'),
    ('view_technicians', 'technicians', 'view', 'View technician performance'),
    ('edit_work_orders', 'work_orders', 'edit', 'Edit work orders'),
    ('edit_own_work_orders', 'work_orders', 'edit_own', 'Edit only own work orders'),
    ('export_service', 'service', 'export', 'Export service data'),
    
    -- Rental Department
    ('view_rental', 'rental', 'view', 'View rental reports'),
    ('edit_rental', 'rental', 'edit', 'Edit rental data'),
    ('view_equipment', 'equipment', 'view', 'View equipment status'),
    ('edit_equipment', 'equipment', 'edit', 'Edit equipment data'),
    ('export_rental', 'rental', 'export', 'Export rental data'),
    
    -- Accounting Department
    ('view_accounting', 'accounting', 'view', 'View accounting reports'),
    ('edit_accounting', 'accounting', 'edit', 'Edit accounting data'),
    ('view_commissions', 'commissions', 'view', 'View all commission data'),
    ('edit_commissions', 'commissions', 'edit', 'Edit commission calculations'),
    ('view_own_commissions', 'commissions', 'view_own', 'View only own commission data'),
    ('view_ar', 'accounts_receivable', 'view', 'View AR aging reports'),
    ('export_accounting', 'accounting', 'export', 'Export accounting data'),
    
    -- Customer Management
    ('view_customers', 'customers', 'view', 'View all customers'),
    ('view_own_customers', 'customers', 'view_own', 'View only assigned customers'),
    ('edit_customers', 'customers', 'edit', 'Edit customer data'),
    
    -- System Administration
    ('view_users', 'users', 'view', 'View user list'),
    ('edit_users', 'users', 'edit', 'Edit user accounts'),
    ('manage_roles', 'roles', 'manage', 'Manage user roles and permissions'),
    
    -- Database Access
    ('view_database_explorer', 'database', 'view', 'Access database explorer'),
    ('execute_queries', 'database', 'execute', 'Execute custom SQL queries'),
    
    -- AI Features
    ('use_ai_query', 'ai', 'query', 'Use AI query assistant'),
    ('use_report_creator', 'reports', 'create', 'Create custom reports'),
    
    -- Minitrac
    ('view_minitrac', 'minitrac', 'view', 'View Minitrac equipment data'),
    ('export_minitrac', 'minitrac', 'export', 'Export Minitrac data')
ON CONFLICT (name) DO NOTHING;

-- Insert Default Roles
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

-- Assign Permissions to Roles
-- Note: This is more complex because we need to get the IDs first

-- Super Admin gets all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- Leadership gets all view and export permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Leadership' 
  AND (p.name LIKE 'view_%' OR p.name LIKE 'export_%')
ON CONFLICT DO NOTHING;

-- Accounting Manager permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Accounting Manager' 
  AND p.name IN ('view_dashboard', 'view_accounting', 'edit_accounting', 
                 'view_commissions', 'edit_commissions', 'view_ar', 
                 'export_accounting')
ON CONFLICT DO NOTHING;

-- Parts Manager permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Parts Manager' 
  AND p.name IN ('view_dashboard', 'view_parts', 'edit_parts', 
                 'view_inventory', 'edit_inventory', 'export_parts')
ON CONFLICT DO NOTHING;

-- Service Manager permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Service Manager' 
  AND p.name IN ('view_dashboard', 'view_service', 'edit_service', 
                 'view_technicians', 'edit_work_orders', 'export_service')
ON CONFLICT DO NOTHING;

-- Rental Manager permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Rental Manager' 
  AND p.name IN ('view_dashboard', 'view_rental', 'edit_rental', 
                 'view_equipment', 'edit_equipment', 'export_rental')
ON CONFLICT DO NOTHING;

-- Parts Staff permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Parts Staff' 
  AND p.name IN ('view_parts', 'view_inventory')
ON CONFLICT DO NOTHING;

-- Service Tech permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Service Tech' 
  AND p.name IN ('view_service', 'edit_own_work_orders')
ON CONFLICT DO NOTHING;

-- Sales Rep permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Sales Rep' 
  AND p.name IN ('view_own_commissions', 'view_own_customers')
ON CONFLICT DO NOTHING;

-- Read Only permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM role r, permission p
WHERE r.name = 'Read Only' 
  AND p.name = 'view_dashboard'
ON CONFLICT DO NOTHING;