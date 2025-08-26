-- Fix elebow access - detailed debugging

-- 1. First, check if elebow exists
SELECT 'Checking if elebow user exists:' as step;
SELECT id, username, email, is_active 
FROM "user" 
WHERE username = 'elebow';

-- 2. Check if Super Admin role exists
SELECT 'Checking if Super Admin role exists:' as step;
SELECT id, name, level 
FROM role 
WHERE name = 'Super Admin';

-- 3. Get the exact IDs we need
SELECT 'Getting IDs for insert:' as step;
SELECT 
    u.id as user_id,
    u.username,
    r.id as role_id,
    r.name as role_name
FROM "user" u
CROSS JOIN role r
WHERE u.username = 'elebow' 
  AND r.name = 'Super Admin';

-- 4. Force insert with explicit IDs (modify these IDs based on results above)
-- First, check what the IDs are from query above, then uncomment and run:
-- INSERT INTO user_roles (user_id, role_id) VALUES (USER_ID_HERE, ROLE_ID_HERE);

-- 5. Alternative: Insert using a more direct approach
DO $$ 
DECLARE
    v_user_id INTEGER;
    v_role_id INTEGER;
BEGIN
    -- Get user ID
    SELECT id INTO v_user_id FROM "user" WHERE username = 'elebow';
    -- Get role ID
    SELECT id INTO v_role_id FROM role WHERE name = 'Super Admin';
    
    IF v_user_id IS NOT NULL AND v_role_id IS NOT NULL THEN
        -- Insert the relationship
        INSERT INTO user_roles (user_id, role_id) 
        VALUES (v_user_id, v_role_id)
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Successfully assigned Super Admin role to elebow (user_id: %, role_id: %)', v_user_id, v_role_id;
    ELSE
        RAISE NOTICE 'Could not find user or role. User ID: %, Role ID: %', v_user_id, v_role_id;
    END IF;
END $$;

-- 6. Verify the assignment worked
SELECT 'Final verification:' as step;
SELECT 
    u.username,
    u.email,
    r.name as role_name,
    ur.assigned_at
FROM "user" u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
WHERE u.username = 'elebow';

-- 7. Double-check permissions count
SELECT 
    u.username,
    COUNT(DISTINCT p.id) as total_permissions
FROM "user" u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permission p ON rp.permission_id = p.id
WHERE u.username = 'elebow'
GROUP BY u.username;

-- 8. If still no results, check user_roles table directly
SELECT 'Checking user_roles table:' as step;
SELECT * FROM user_roles;

-- Message
SELECT '===========================================' as info
UNION ALL
SELECT 'After running this script:'
UNION ALL
SELECT '1. Logout from the application'
UNION ALL
SELECT '2. Login again with elebow/abc123'
UNION ALL
SELECT '3. You should see all menu items now'
UNION ALL
SELECT '===========================================';