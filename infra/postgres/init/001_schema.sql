-- DRP 穿透式资金监管平台 - 基础数据库 Schema
-- 版本: 1.0.0  创建时间: 2026-04-02

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================
-- 租户表
-- ==============================
CREATE TABLE tenant (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name         VARCHAR(255) NOT NULL,
    slug         VARCHAR(100) UNIQUE NOT NULL,
    status       VARCHAR(50)  NOT NULL DEFAULT 'active'
                              CHECK (status IN ('active', 'suspended', 'deleted')),
    graph_iri    VARCHAR(500) NOT NULL,  -- urn:tenant:{id}
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenant_status ON tenant(status);
CREATE INDEX idx_tenant_slug   ON tenant(slug);

-- ==============================
-- 用户表
-- ==============================
CREATE TABLE "user" (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            UUID         REFERENCES tenant(id) ON DELETE CASCADE,
    email                VARCHAR(255) NOT NULL,
    username             VARCHAR(100),
    password_hash        VARCHAR(255),               -- SSO-only 用户为 NULL
    full_name            VARCHAR(255),
    status               VARCHAR(50)  NOT NULL DEFAULT 'active'
                                      CHECK (status IN ('active', 'inactive', 'locked')),
    sso_provider         VARCHAR(50),                -- saml | oidc | ldap | null
    sso_subject          VARCHAR(500),               -- IdP 侧的外部身份标识
    failed_login_count   INTEGER      NOT NULL DEFAULT 0,
    locked_until         TIMESTAMPTZ,
    last_login_at        TIMESTAMPTZ,
    password_changed_at  TIMESTAMPTZ,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, email)
);

CREATE INDEX idx_user_tenant ON "user"(tenant_id);
CREATE INDEX idx_user_email  ON "user"(email);
CREATE INDEX idx_user_sso    ON "user"(sso_provider, sso_subject)
    WHERE sso_provider IS NOT NULL;

-- ==============================
-- 用户组表
-- ==============================
CREATE TABLE "group" (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID         NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

CREATE TABLE user_group (
    user_id  UUID REFERENCES "user"(id)  ON DELETE CASCADE,
    group_id UUID REFERENCES "group"(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, group_id)
);

-- ==============================
-- 角色与权限表
-- ==============================
CREATE TABLE role (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID         REFERENCES tenant(id) ON DELETE CASCADE,
    name           VARCHAR(100) NOT NULL,
    description    TEXT,
    is_system_role BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

CREATE TABLE permission (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    resource    VARCHAR(200) UNIQUE NOT NULL,  -- 如 'mapping:approve', 'tenant:read'
    description TEXT
);

CREATE TABLE role_permission (
    role_id       UUID REFERENCES role(id)       ON DELETE CASCADE,
    permission_id UUID REFERENCES permission(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_role (
    user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
    role_id UUID REFERENCES role(id)   ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- ==============================
-- 审计日志表（不可篡改，仅 INSERT）
-- ==============================
CREATE TABLE audit_log (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID         REFERENCES tenant(id),
    user_id       UUID         REFERENCES "user"(id),
    action        VARCHAR(100) NOT NULL,      -- 如 'user.login', 'mapping.approve'
    resource_type VARCHAR(100),
    resource_id   VARCHAR(500),
    ip_address    INET,
    user_agent    TEXT,
    detail        JSONB,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_user   ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_log(action, created_at DESC);

-- ==============================
-- ETL 任务记录表（含 run_id 幂等设计，见 design.md 决策14）
-- ==============================
CREATE TABLE etl_job (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID        UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    job_type        VARCHAR(50) NOT NULL
                                CHECK (job_type IN ('full_sync', 'incremental_sync')),
    status          VARCHAR(50) NOT NULL DEFAULT 'running'
                                CHECK (status IN ('running', 'success', 'failed',
                                                  'timeout', 'retrying', 'skipped')),
    last_synced_at  TIMESTAMPTZ,            -- 增量水位线
    triples_written INTEGER     NOT NULL DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX idx_etl_tenant ON etl_job(tenant_id, started_at DESC);
CREATE INDEX idx_etl_status ON etl_job(status, started_at DESC);
CREATE INDEX idx_etl_run_id ON etl_job(run_id);

-- ==============================
-- 映射规范表
-- ==============================
CREATE TABLE mapping_spec (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID         NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    ddl_hash        CHAR(64)     NOT NULL,       -- SHA-256(DDL 内容)
    source_table    VARCHAR(255) NOT NULL,
    source_field    VARCHAR(255) NOT NULL,
    target_property VARCHAR(500),               -- CTIO/FIBO 属性 IRI
    transform_rule  TEXT,                       -- 值转换规则（YAML 片段）
    confidence      NUMERIC(5,2),               -- 0.00~100.00
    status          VARCHAR(50)  NOT NULL DEFAULT 'pending'
                                 CHECK (status IN ('pending', 'approved',
                                                   'rejected', 'unmapped')),
    auto_approved   BOOLEAN      NOT NULL DEFAULT FALSE,
    approved_by     UUID         REFERENCES "user"(id),
    approved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, ddl_hash, source_table, source_field)
);

CREATE INDEX idx_mapping_tenant ON mapping_spec(tenant_id, status);
CREATE INDEX idx_mapping_ddl    ON mapping_spec(ddl_hash);

-- ==============================
-- 内置权限种子数据
-- ==============================
INSERT INTO permission (resource, description) VALUES
    ('tenant:read',     '查看租户信息'),
    ('tenant:write',    '创建/修改租户'),
    ('tenant:delete',   '删除租户'),
    ('user:read',       '查看用户列表'),
    ('user:write',      '创建/修改用户'),
    ('user:delete',     '删除用户'),
    ('role:read',       '查看角色'),
    ('role:write',      '创建/修改角色'),
    ('mapping:read',    '查看映射规范'),
    ('mapping:approve', '审核映射'),
    ('etl:read',        '查看 ETL 任务'),
    ('etl:trigger',     '手动触发 ETL'),
    ('dashboard:view',  '访问监管看板'),
    ('drill:execute',   '执行穿透溯源'),
    ('audit:read',      '查看审计日志');
