-- Create the missing association tables
-- Run this if user_roles and role_permissions tables don't exist

-- Create User-Roles association table (many-to-many)
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES "user"(id)
);

-- Create Role-Permissions association table (many-to-many)
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permission(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);

-- Verify tables were created
SELECT 
    table_name,
    CASE 
        WHEN table_name IS NOT NULL THEN '✓ CREATED'
        ELSE '✗ FAILED'
    END as status
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('user_roles', 'role_permissions')
ORDER BY table_name;