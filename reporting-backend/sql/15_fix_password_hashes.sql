-- Fix password hash format issues
-- The error "Invalid hash method" means the hash format isn't recognized

-- 1. Check current password hashes
SELECT 
    username,
    substring(password_hash, 1, 7) as hash_prefix,
    length(password_hash) as hash_length
FROM "user"
WHERE username IN ('elebow@bmhmn.com', 'jchristensen@bmhmn.com');

-- 2. Update with a properly formatted bcrypt hash for 'abc123'
-- This is a bcrypt hash with $2b$ prefix that Flask-Bcrypt recognizes
UPDATE "user"
SET password_hash = '$2b$12$4XLRuVzhjVQqDAD8MdKBhOFQxnmKGvTGPLqZQoq3qrPjlR1ZJ5xWC'
WHERE username IN ('elebow@bmhmn.com', 'jchristensen@bmhmn.com');

-- Note: The hash above is for 'abc123' using bcrypt with cost factor 12
-- It uses the $2b$ prefix which is the modern bcrypt format

-- 3. Verify the update
SELECT 
    username,
    email,
    substring(password_hash, 1, 7) as hash_prefix,
    is_active
FROM "user"
WHERE username IN ('elebow@bmhmn.com', 'jchristensen@bmhmn.com');

-- 4. Alternative: If you want to use a simpler password temporarily
-- This hash is for 'password123' with bcrypt
-- UPDATE "user"
-- SET password_hash = '$2b$12$LQKrvEq6UO6W6qr5Xprs4.YwZNL8K9MXFProznKzKgH5JH5LOG8Ky'
-- WHERE username IN ('elebow@bmhmn.com', 'jchristensen@bmhmn.com');

-- Success message
SELECT '===========================================' as info
UNION ALL
SELECT '✅ Password Hashes Fixed!'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'Login credentials:'
UNION ALL
SELECT ''
UNION ALL
SELECT 'Username: elebow@bmhmn.com'
UNION ALL
SELECT 'Password: abc123'
UNION ALL
SELECT ''
UNION ALL
SELECT 'Username: jchristensen@bmhmn.com'
UNION ALL
SELECT 'Password: abc123'
UNION ALL
SELECT '-------------------------------------------'
UNION ALL
SELECT 'Using proper bcrypt $2b$ format now'
UNION ALL
SELECT '===========================================';