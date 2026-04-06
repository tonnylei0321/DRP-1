-- 003_fix_permissions.sql - 修复权限种子数据
-- 前端 NAV_ITEMS 使用的 requiredPermission 与数据库 permission.resource 不匹配
-- 补充缺失的权限记录，确保 superadmin 角色拥有所有权限

BEGIN;

-- 补充前端需要但数据库中缺失的权限
INSERT INTO permission (resource, description) VALUES
    ('drill:read',    '查看监管看板与穿透钻取'),
    ('mapping:write', '上传 DDL 与编辑映射'),
    ('etl:write',     '触发 ETL 同步任务')
ON CONFLICT (resource) DO NOTHING;

-- 确保 superadmin 角色拥有所有权限（包括新增的）
INSERT INTO role_permission (role_id, permission_id)
SELECT '217b6187-b25d-469b-9b14-5a42e3218ff7', id
FROM permission
WHERE NOT EXISTS (
    SELECT 1 FROM role_permission rp
    WHERE rp.role_id = '217b6187-b25d-469b-9b14-5a42e3218ff7' AND rp.permission_id = permission.id
);

COMMIT;
