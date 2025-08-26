-- Simple script to add department_id column

-- Add the column
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS department_id INTEGER;

-- Verify it was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'user' 
  AND column_name = 'department_id';

-- Test query
SELECT username, email, department_id FROM "user" LIMIT 5;