-- 004_data_scope.sql - 细粒度数据权限（Data Scope Permission）数据库迁移
-- 新增 department、data_scope_rule、column_mask_rule 表
-- 为 user 表新增 dept_id 字段
-- 插入数据权限相关权限种子数据

BEGIN;

-- ==============================
-- 部门表（自引用树形结构）
-- ==============================
CREATE TABLE department (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID         NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    parent_id   UUID         REFERENCES department(id) ON DELETE RESTRICT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    status      VARCHAR(50)  NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active', 'inactive')),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name, parent_id)
);

CREATE INDEX idx_dept_tenant ON department(tenant_id);
CREATE INDEX idx_dept_parent ON department(parent_id);

-- ==============================
-- user 表新增 dept_id 字段
-- ==============================
ALTER TABLE "user" ADD COLUMN dept_id UUID REFERENCES department(id) ON DELETE SET NULL;
CREATE INDEX idx_user_dept ON "user"(dept_id);

-- ==============================
-- 数据范围规则表（行级过滤）
-- ==============================
CREATE TABLE data_scope_rule (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID         NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    user_id          UUID         NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    table_name       VARCHAR(255) NOT NULL,
    scope_type       VARCHAR(50)  NOT NULL
                                  CHECK (scope_type IN ('all', 'dept', 'self', 'custom')),
    custom_condition TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, user_id, table_name, scope_type),
    CHECK (scope_type != 'custom' OR custom_condition IS NOT NULL),
    CHECK (custom_condition IS NULL OR length(custom_condition) <= 500)
);

CREATE INDEX idx_dsr_tenant_user ON data_scope_rule(tenant_id, user_id);
CREATE INDEX idx_dsr_table ON data_scope_rule(table_name);

-- ==============================
-- 列级脱敏规则表
-- ==============================
CREATE TABLE column_mask_rule (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID         NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    role_id          UUID         NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    table_name       VARCHAR(255) NOT NULL,
    column_name      VARCHAR(255) NOT NULL,
    mask_strategy    VARCHAR(50)  NOT NULL
                                  CHECK (mask_strategy IN ('mask', 'hide', 'none')),
    mask_pattern     VARCHAR(50)  CHECK (mask_pattern IN ('phone', 'id_card', 'email', 'custom_regex')),
    regex_expression TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, role_id, table_name, column_name),
    CHECK (mask_strategy != 'mask' OR mask_pattern IS NOT NULL),
    CHECK (mask_pattern != 'custom_regex' OR regex_expression IS NOT NULL)
);

CREATE INDEX idx_cmr_tenant_role ON column_mask_rule(tenant_id, role_id);
CREATE INDEX idx_cmr_table ON column_mask_rule(table_name);

-- ==============================
-- 权限种子数据
-- ==============================
INSERT INTO permission (resource, description) VALUES
    ('data_scope:read',            '查看数据权限规则'),
    ('data_scope:write',           '创建/修改/删除数据权限规则'),
    ('data_scope:circuit_breaker', '操作数据权限熔断开关'),
    ('department:read',            '查看部门组织架构'),
    ('department:write',           '创建/修改/删除部门')
ON CONFLICT (resource) DO NOTHING;

-- 为 superadmin 角色授予所有新权限
INSERT INTO role_permission (role_id, permission_id)
SELECT '217b6187-b25d-469b-9b14-5a42e3218ff7', id
FROM permission
WHERE NOT EXISTS (
    SELECT 1 FROM role_permission rp
    WHERE rp.role_id = '217b6187-b25d-469b-9b14-5a42e3218ff7' AND rp.permission_id = permission.id
);

COMMIT;
