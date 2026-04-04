-- 002_seed.sql - 开发环境默认管理员种子数据
-- 密码: DrpAdmin123! (bcrypt hash from pgcrypto: gen_salt('bf'))
-- 使用: docker exec drp-postgres psql -U drp -d drp -f /docker-entrypoint-initdb.d/002_seed.sql

BEGIN;

-- 确保系统管理员角色存在（is_system_role=true 的超级管理员）
INSERT INTO role (id, name, description, is_system_role, tenant_id)
VALUES (
    '217b6187-b25d-469b-9b14-5a42e3218ff7',
    'superadmin',
    '系统超级管理员（拥有全部权限）',
    true,
    NULL
) ON CONFLICT (id) DO NOTHING;

-- 确保默认管理员用户存在（密码: DrpAdmin123!）
INSERT INTO "user" (id, email, full_name, password_hash, status, tenant_id, created_at, updated_at)
VALUES (
    '102116d0-f947-43c6-b703-66f3c3b4aa3a',
    'admin@drp.local',
    '系统管理员',
    '$2a$06$DLdIbx/JSRwQk/rJW6Nb7eVTIxvlR3Ny6//cpPye3/3rzoACuej2C',
    'active',
    NULL,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    status = 'active',
    updated_at = NOW();

-- 将管理员绑定到超级管理员角色
INSERT INTO user_role (user_id, role_id)
VALUES (
    '102116d0-f947-43c6-b703-66f3c3b4aa3a',
    '217b6187-b25d-469b-9b14-5a42e3218ff7'
) ON CONFLICT DO NOTHING;

-- 为超级管理员角色授予所有权限
INSERT INTO role_permission (role_id, permission_id)
SELECT '217b6187-b25d-469b-9b14-5a42e3218ff7', id
FROM permission
WHERE NOT EXISTS (
    SELECT 1 FROM role_permission rp
    WHERE rp.role_id = '217b6187-b25d-469b-9b14-5a42e3218ff7' AND rp.permission_id = permission.id
);

COMMIT;
