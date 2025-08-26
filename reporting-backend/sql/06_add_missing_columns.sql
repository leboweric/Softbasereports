-- Add missing columns to user table

-- Check if department_id column exists, if not add it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user' 
        AND column_name = 'department_id'
    ) THEN
        ALTER TABLE "user" ADD COLUMN department_id INTEGER;
        ALTER TABLE "user" ADD FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE SET NULL;
        RAISE NOTICE 'Added department_id column to user table';
    ELSE
        RAISE NOTICE 'department_id column already exists';
    END IF;
END $$;

-- Check if role column exists, if not add it (for legacy support)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user' 
        AND column_name = 'role'
    ) THEN
        ALTER TABLE "user" ADD COLUMN role VARCHAR(50) DEFAULT 'user';
        RAISE NOTICE 'Added role column to user table';
    ELSE
        RAISE NOTICE 'role column already exists';
    END IF;
END $$;

-- Verify the user table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'user'
ORDER BY ordinal_position;

-- Check that we can query the user table without errors
SELECT 
    u.username,
    u.email,
    u.role as legacy_role,
    u.department_id,
    d.name as department_name
FROM "user" u
LEFT JOIN department d ON u.department_id = d.id;

-- Success message
SELECT '✅ User table structure updated successfully!' as status;