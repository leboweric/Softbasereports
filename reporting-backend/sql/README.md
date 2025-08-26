# RBAC Database Setup Instructions

## Overview
These SQL scripts set up the Role-Based Access Control (RBAC) system for the Softbase Reports application.

## Prerequisites
- PostgreSQL database (already setup on Railway)
- pgAdmin or similar PostgreSQL client
- Admin access to the database

## Installation Steps

### Step 1: Create Tables
Run the following script to create all necessary RBAC tables:
```sql
-- File: create_rbac_tables.sql
```
This creates:
- `department` table
- `role` table  
- `permission` table
- `user_roles` association table (many-to-many)
- `role_permissions` association table (many-to-many)
- Adds `department_id` column to user table if needed

### Step 2: Insert Default Data
Run the following script to populate default roles and permissions:
```sql
-- File: insert_default_rbac_data.sql
```
This inserts:
- 5 departments (Parts, Service, Rental, Accounting, Sales)
- 42 granular permissions
- 10 default roles (Super Admin, Leadership, Managers, Staff, etc.)
- Permission assignments for each role

### Step 3: Migrate Existing Users
Run the following script to assign roles to existing users:
```sql
-- File: migrate_existing_users.sql
```
This will:
- Assign Super Admin role to users with 'admin' in legacy role field
- Assign Leadership role to users with 'manager' in legacy role field
- Assign Read Only role to all other users
- Make the first user in each organization a Super Admin

### Step 4: Verify Setup
Check the results by running queries from:
```sql
-- File: useful_rbac_queries.sql
```

## Default Roles Created

| Role | Level | Department | Description |
|------|-------|------------|-------------|
| Super Admin | 10 | - | Full system access, all permissions |
| Leadership | 9 | - | View all departments, export data |
| Accounting Manager | 5 | Accounting | Full accounting access |
| Parts Manager | 5 | Parts | Full parts department access |
| Service Manager | 5 | Service | Full service department access |
| Rental Manager | 5 | Rental | Full rental department access |
| Parts Staff | 1 | Parts | View parts data only |
| Service Tech | 1 | Service | View service, edit own work orders |
| Sales Rep | 1 | Sales | View own commission data |
| Read Only | 0 | - | Dashboard only |

## Managing Users After Setup

### Assign a role to a user:
```sql
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM "user" u, role r
WHERE u.username = 'john.doe' AND r.name = 'Parts Manager';
```

### Remove a role from a user:
```sql
DELETE FROM user_roles
WHERE user_id = (SELECT id FROM "user" WHERE username = 'john.doe')
  AND role_id = (SELECT id FROM role WHERE name = 'Parts Manager');
```

### Check user permissions:
```sql
SELECT DISTINCT p.name, p.description
FROM "user" u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permission p ON rp.permission_id = p.id
WHERE u.username = 'john.doe'
ORDER BY p.name;
```

## Troubleshooting

### If tables already exist:
The scripts use `IF NOT EXISTS` and `ON CONFLICT DO NOTHING` clauses, so they're safe to run multiple times.

### If you need to reset:
```sql
-- CAUTION: This will delete all RBAC data!
DROP TABLE IF EXISTS user_roles CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS permission CASCADE;
DROP TABLE IF EXISTS role CASCADE;
DROP TABLE IF EXISTS department CASCADE;
-- Then run the setup scripts again
```

### Check current state:
```sql
-- Count records in each table
SELECT 'departments' as table_name, COUNT(*) as count FROM department
UNION ALL
SELECT 'roles', COUNT(*) FROM role
UNION ALL
SELECT 'permissions', COUNT(*) FROM permission
UNION ALL
SELECT 'user_roles', COUNT(*) FROM user_roles
UNION ALL
SELECT 'role_permissions', COUNT(*) FROM role_permissions;
```

## Notes
- The system uses PostgreSQL for user management (separate from Azure SQL Softbase data)
- All scripts are idempotent (safe to run multiple times)
- The frontend will automatically filter menu items based on permissions
- Users can have multiple roles (permissions are cumulative)