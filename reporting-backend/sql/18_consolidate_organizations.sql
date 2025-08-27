-- Consolidate all users into one organization and remove duplicate

-- 1. First, check current state
SELECT 'Current Users and Organizations' as info;
SELECT u.id, u.username, u.email, u.organization_id, o.name as org_name
FROM "user" u
LEFT JOIN organization o ON u.organization_id = o.id
ORDER BY u.id;

-- 2. Move all users to Bennett Material Handling (id=4)
UPDATE "user" 
SET organization_id = 4 
WHERE organization_id = 5;

-- 3. Delete the duplicate Bennett Equipment organization
DELETE FROM organization 
WHERE id = 5;

-- 4. Verify the consolidation
SELECT '===========================================' as info
UNION ALL
SELECT 'After Consolidation:' as info
UNION ALL
SELECT '-------------------------------------------';

SELECT u.id, u.username, u.email, u.organization_id, o.name as org_name
FROM "user" u
LEFT JOIN organization o ON u.organization_id = o.id
ORDER BY u.id;

SELECT '===========================================' as info
UNION ALL
SELECT 'All users are now in the same organization!' as info
UNION ALL
SELECT 'You should now see all users in User Management' as info
UNION ALL
SELECT '===========================================';