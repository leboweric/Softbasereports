-- Debug database connection and schema

-- 1. Check current database
SELECT current_database() as current_db;

-- 2. Check current schema
SELECT current_schema() as current_schema;

-- 3. List all schemas
SELECT schema_name FROM information_schema.schemata;

-- 4. Check if user table exists in different schemas
SELECT 
    table_schema,
    table_name,
    column_name
FROM information_schema.columns
WHERE table_name = 'user'
  AND column_name IN ('id', 'username', 'department_id')
ORDER BY table_schema, ordinal_position;

-- 5. Check specifically in public schema
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'user'
  AND table_schema = 'public'
ORDER BY ordinal_position;

-- 6. Try to query the user table with explicit schema
SELECT 
    username,
    email,
    department_id
FROM public."user"
LIMIT 5;