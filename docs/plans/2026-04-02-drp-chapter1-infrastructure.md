# DRP 第1章：基础设施与开发环境 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 DRP 项目的完整本地开发环境，包含 Docker 三服务编排、GraphDB 自动初始化、PostgreSQL 基础 schema、Python FastAPI 骨架、React+D3 骨架和环境变量模板。

**Architecture:** docker-compose.dev.yml 统一编排 GraphDB 10.x / PostgreSQL 16 / Redis 7 三服务；init 脚本在容器首次启动时自动创建 GraphDB 仓库并拉取 FIBO 核心 7 模块；PostgreSQL 通过 `/docker-entrypoint-initdb.d` 自动执行 DDL；Python 后端使用 uv + FastAPI + pydantic-settings，通过 `GET /health` 验证基础启动；React 前端使用 Vite + TypeScript + D3 v7，使用 `npm run dev` 验证基础启动。

**Tech Stack:** Docker Compose 3.9, Ontotext GraphDB 10.7.0, PostgreSQL 16-alpine, Redis 7-alpine, Python 3.11 + uv + FastAPI 0.111, React 18 + Vite 5 + TypeScript 5 + D3 v7

---

## 文件结构

```
DRP-1/
├── docker-compose.dev.yml          # Task 1: 三服务编排
├── .env.example                    # Task 6: 环境变量模板
├── infra/
│   ├── graphdb/
│   │   ├── init/
│   │   │   ├── 01-create-repo.sh  # Task 2: GraphDB 初始化脚本
│   │   │   └── repo-config.ttl    # Task 2: 仓库配置（Turtle格式）
│   │   └── fibo/                  # Task 2: FIBO 核心模块（脚本下载）
│   └── postgres/
│       └── init/
│           └── 001_schema.sql     # Task 3: 基础表 DDL
├── backend/
│   ├── pyproject.toml             # Task 4: Python 依赖
│   ├── src/
│   │   └── drp/
│   │       ├── __init__.py        # Task 4
│   │       ├── main.py            # Task 4: FastAPI app 工厂
│   │       └── config.py          # Task 4: pydantic-settings 配置
│   └── tests/
│       ├── conftest.py            # Task 4
│       └── test_health.py         # Task 4: /health 端点测试
└── frontend/
    ├── package.json               # Task 5: npm 依赖
    ├── vite.config.ts             # Task 5
    ├── tsconfig.json              # Task 5
    ├── index.html                 # Task 5
    └── src/
        ├── main.tsx               # Task 5
        └── App.tsx                # Task 5: 基础占位页
```

---

## Task 1: docker-compose.dev.yml

**Files:**
- Create: `docker-compose.dev.yml`

- [ ] **Step 1: 编写 docker-compose.dev.yml**

```yaml
version: '3.9'

services:
  graphdb:
    image: ontotext/graphdb:10.7.0
    container_name: drp-graphdb
    ports:
      - "7200:7200"
    volumes:
      - graphdb-data:/opt/graphdb/home
      - ./infra/graphdb/fibo:/opt/graphdb/home/fibo:ro
    environment:
      GDB_HEAP_SIZE: "2g"
      GDB_MIN_MEM: "512m"
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:7200/rest/repositories"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 60s
    networks:
      - drp-net

  graphdb-init:
    image: curlimages/curl:8.7.1
    container_name: drp-graphdb-init
    depends_on:
      graphdb:
        condition: service_healthy
    volumes:
      - ./infra/graphdb/init:/init:ro
      - ./infra/graphdb/fibo:/fibo:ro
    entrypoint: ["/bin/sh", "/init/01-create-repo.sh"]
    networks:
      - drp-net
    restart: "no"

  postgres:
    image: postgres:16-alpine
    container_name: drp-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: drp
      POSTGRES_USER: drp
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-drp_dev}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./infra/postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U drp -d drp"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - drp-net

  redis:
    image: redis:7-alpine
    container_name: drp-redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --appendfsync everysec
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - drp-net

volumes:
  graphdb-data:
  postgres-data:
  redis-data:

networks:
  drp-net:
    driver: bridge
```

- [ ] **Step 2: 验证 YAML 语法**

```bash
docker compose -f docker-compose.dev.yml config --quiet
```

期望输出：无错误，退出码 0

- [ ] **Step 3: 启动服务（不含 graphdb-init，先验证三主服务）**

```bash
docker compose -f docker-compose.dev.yml up -d graphdb postgres redis
```

期望：三个容器启动，graphdb 健康检查约 60s 后变为 healthy

```bash
docker compose -f docker-compose.dev.yml ps
```

期望：
```
drp-graphdb    ... healthy
drp-postgres   ... healthy
drp-redis      ... healthy
```

- [ ] **Step 4: 验证服务端口**

```bash
curl -sf http://localhost:7200/rest/repositories | head -c 100
curl -sf http://localhost:6379 || redis-cli -p 6379 ping
docker exec drp-postgres psql -U drp -c "\l"
```

期望：GraphDB 返回 JSON，Redis 返回 PONG，PostgreSQL 列出数据库

- [ ] **Step 5: 停止服务（不删除数据卷）**

```bash
docker compose -f docker-compose.dev.yml stop
```

---

## Task 2: GraphDB 初始化脚本

**Files:**
- Create: `infra/graphdb/init/01-create-repo.sh`
- Create: `infra/graphdb/init/repo-config.ttl`
- Create: `infra/graphdb/fibo/.gitkeep`（占位，FIBO 文件由脚本下载）

- [ ] **Step 1: 创建 infra 目录结构**

```bash
mkdir -p infra/graphdb/init infra/graphdb/fibo infra/postgres/init
```

- [ ] **Step 2: 编写仓库配置文件 `infra/graphdb/init/repo-config.ttl`**

```turtle
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rep:  <http://www.openrdf.org/config/repository#> .
@prefix sr:   <http://www.openrdf.org/config/repository/sail#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix owlim: <http://www.ontotext.com/trree/owlim#> .

[] a rep:Repository ;
   rep:repositoryID "drp" ;
   rdfs:label "DRP 穿透式资金监管平台" ;
   rep:repositoryImpl [
      rep:repositoryType "graphdb:FreeSailRepository" ;
      sr:sailImpl [
         sail:sailType "graphdb:FreeSail" ;
         owlim:base-URL <http://drp.example.com/> ;
         owlim:defaultNS "" ;
         owlim:entity-index-size "10000000" ;
         owlim:entity-id-size "32" ;
         owlim:ruleset "rdfsplus-optimized" ;
         owlim:storage-folder "storage" ;
         owlim:enable-context-index "true" ;
         owlim:cache-memory "200m" ;
         owlim:tuple-index-memory "200m" ;
         owlim:enable-full-text-search "false" ;
         owlim:check-for-inconsistencies "false"
      ]
   ] .
```

- [ ] **Step 3: 编写初始化脚本 `infra/graphdb/init/01-create-repo.sh`**

```bash
#!/bin/sh
set -e

GRAPHDB_URL="${GRAPHDB_URL:-http://graphdb:7200}"
REPO_ID="drp"

echo "[init] 等待 GraphDB 就绪..."
until curl -sf "${GRAPHDB_URL}/rest/repositories" > /dev/null 2>&1; do
  echo "[init] GraphDB 尚未就绪，等待 5 秒..."
  sleep 5
done
echo "[init] GraphDB 已就绪"

# 检查仓库是否已存在
if curl -sf "${GRAPHDB_URL}/rest/repositories/${REPO_ID}" > /dev/null 2>&1; then
  echo "[init] 仓库 '${REPO_ID}' 已存在，跳过创建"
else
  echo "[init] 创建仓库 '${REPO_ID}'..."
  curl -sf -X POST "${GRAPHDB_URL}/rest/repositories" \
    -H "Content-Type: multipart/form-data" \
    -F "config=@/init/repo-config.ttl;type=text/turtle" \
    || { echo "[init] 仓库创建失败"; exit 1; }
  echo "[init] 仓库创建成功"
fi

# 加载 FIBO 核心模块
FIBO_BASE="https://spec.edmcouncil.org/fibo/ontology/master/2024Q3"
FIBO_MODULES="
  FBC/FunctionalEntities/FinancialServicesEntities.rdf
  BE/LegalEntities/LegalPersons.rdf
  BE/LegalEntities/CorporateBodies.rdf
  FND/Accounting/CurrencyAmount.rdf
  FND/Relations/Relations.rdf
  FND/DatesAndTimes/FinancialDates.rdf
  FND/Arrangements/ClassificationSchemes.rdf
"

for MODULE in $FIBO_MODULES; do
  FILE_NAME=$(basename "$MODULE" .rdf)
  LOCAL_PATH="/fibo/${FILE_NAME}.rdf"

  if [ -f "$LOCAL_PATH" ]; then
    echo "[init] 加载 FIBO 模块: ${FILE_NAME}（本地缓存）"
    curl -sf -X POST \
      "${GRAPHDB_URL}/repositories/${REPO_ID}/statements" \
      -H "Content-Type: application/rdf+xml" \
      --data-binary "@${LOCAL_PATH}" \
      && echo "[init]   加载成功: ${FILE_NAME}" \
      || echo "[init]   加载失败（跳过）: ${FILE_NAME}"
  else
    echo "[init] 下载 FIBO 模块: ${FILE_NAME}..."
    curl -sf "${FIBO_BASE}/${MODULE}" -o "$LOCAL_PATH" \
      && echo "[init]   下载成功: ${FILE_NAME}" \
      || { echo "[init]   下载失败（跳过）: ${FILE_NAME}"; continue; }

    curl -sf -X POST \
      "${GRAPHDB_URL}/repositories/${REPO_ID}/statements" \
      -H "Content-Type: application/rdf+xml" \
      --data-binary "@${LOCAL_PATH}" \
      && echo "[init]   加载成功: ${FILE_NAME}" \
      || echo "[init]   加载失败（跳过）: ${FILE_NAME}"
  fi
done

echo "[init] GraphDB 初始化完成"
```

- [ ] **Step 4: 创建 fibo 占位文件**

```bash
touch infra/graphdb/fibo/.gitkeep
```

在 `.gitignore` 中排除 FIBO rdf 文件（体积大）：

```bash
echo "infra/graphdb/fibo/*.rdf" >> .gitignore
```

- [ ] **Step 5: 启动完整服务（含 graphdb-init）**

```bash
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml logs -f graphdb-init
```

期望：看到 `[init] GraphDB 初始化完成` 日志

- [ ] **Step 6: 验证仓库创建成功**

```bash
curl -sf http://localhost:7200/rest/repositories/drp | python3 -m json.tool | grep '"id"'
```

期望：
```json
"id": "drp"
```

- [ ] **Step 7: 验证 FIBO 三元组已加载**

```bash
curl -sf -X POST "http://localhost:7200/repositories/drp" \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  -d 'SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }' \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('三元组数量:', r['results']['bindings'][0]['count']['value'])"
```

期望：三元组数量 > 1000

- [ ] **Step 8: 提交**

```bash
git add docker-compose.dev.yml infra/graphdb/ .gitignore
git commit -m "feat: 新增 docker-compose 开发环境和 GraphDB 初始化脚本"
```

---

## Task 3: PostgreSQL 基础 DDL

**Files:**
- Create: `infra/postgres/init/001_schema.sql`

- [ ] **Step 1: 编写 `infra/postgres/init/001_schema.sql`**

```sql
-- DRP 穿透式资金监管平台 - 基础数据库 Schema
-- 版本: 1.0.0  创建时间: 2026-04-02

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================
-- 租户表
-- ==============================
CREATE TABLE tenant (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            UUID        REFERENCES tenant(id) ON DELETE CASCADE,
    email                VARCHAR(255) NOT NULL,
    username             VARCHAR(100),
    password_hash        VARCHAR(255),               -- SSO-only 用户为 NULL
    full_name            VARCHAR(255),
    status               VARCHAR(50)  NOT NULL DEFAULT 'active'
                                      CHECK (status IN ('active', 'inactive', 'locked')),
    sso_provider         VARCHAR(50),                -- saml | oidc | ldap | null
    sso_subject          VARCHAR(500),               -- IdP ��的外部身份标识
    failed_login_count   INTEGER      NOT NULL DEFAULT 0,
    locked_until         TIMESTAMPTZ,
    last_login_at        TIMESTAMPTZ,
    password_changed_at  TIMESTAMPTZ,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, email)
);

CREATE INDEX idx_user_tenant    ON "user"(tenant_id);
CREATE INDEX idx_user_email     ON "user"(email);
CREATE INDEX idx_user_sso       ON "user"(sso_provider, sso_subject) WHERE sso_provider IS NOT NULL;

-- ==============================
-- 用户组表
-- ==============================
CREATE TABLE "group" (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
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
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID        REFERENCES tenant(id) ON DELETE CASCADE,
    name           VARCHAR(100) NOT NULL,
    description    TEXT,
    is_system_role BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

CREATE TABLE permission (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID        REFERENCES tenant(id),
    user_id       UUID        REFERENCES "user"(id),
    action        VARCHAR(100) NOT NULL,      -- 如 'user.login', 'mapping.approve'
    resource_type VARCHAR(100),
    resource_id   VARCHAR(500),
    ip_address    INET,
    user_agent    TEXT,
    detail        JSONB,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant     ON audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_user       ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_action     ON audit_log(action, created_at DESC);

-- ==============================
-- ETL 任务记录表
-- ==============================
CREATE TABLE etl_job (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID        UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    job_type        VARCHAR(50)  NOT NULL CHECK (job_type IN ('full_sync', 'incremental_sync')),
    status          VARCHAR(50)  NOT NULL DEFAULT 'running'
                                 CHECK (status IN ('running', 'success', 'failed', 'timeout', 'retrying', 'skipped')),
    last_synced_at  TIMESTAMPTZ,            -- 增量水位线
    triples_written INTEGER      NOT NULL DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX idx_etl_tenant  ON etl_job(tenant_id, started_at DESC);
CREATE INDEX idx_etl_status  ON etl_job(status, started_at DESC);
CREATE INDEX idx_etl_run_id  ON etl_job(run_id);

-- ==============================
-- 映射规范表
-- ==============================
CREATE TABLE mapping_spec (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID        NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    ddl_hash        CHAR(64)    NOT NULL,       -- SHA-256(DDL 内容)
    source_table    VARCHAR(255) NOT NULL,
    source_field    VARCHAR(255) NOT NULL,
    target_property VARCHAR(500),               -- CTIO/FIBO 属性 IRI
    transform_rule  TEXT,                       -- 值转换规则（YAML 片段）
    confidence      NUMERIC(5,2),               -- 0.00~100.00
    status          VARCHAR(50)  NOT NULL DEFAULT 'pending'
                                 CHECK (status IN ('pending', 'approved', 'rejected', 'unmapped')),
    auto_approved   BOOLEAN      NOT NULL DEFAULT FALSE,
    approved_by     UUID        REFERENCES "user"(id),
    approved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, ddl_hash, source_table, source_field)
);

CREATE INDEX idx_mapping_tenant  ON mapping_spec(tenant_id, status);
CREATE INDEX idx_mapping_ddl     ON mapping_spec(ddl_hash);

-- ==============================
-- 内置权限种子数据
-- ==============================
INSERT INTO permission (resource, description) VALUES
    ('tenant:read',         '查看租户信息'),
    ('tenant:write',        '创建/修改租户'),
    ('tenant:delete',       '删除租户'),
    ('user:read',           '查看用户列表'),
    ('user:write',          '创建/修改用户'),
    ('user:delete',         '删除用户'),
    ('role:read',           '查看角色'),
    ('role:write',          '创建/修改角色'),
    ('mapping:read',        '查看映射规范'),
    ('mapping:approve',     '审核映射'),
    ('etl:read',            '查看 ETL 任务'),
    ('etl:trigger',         '手动触发 ETL'),
    ('dashboard:view',      '访问监管看板'),
    ('drill:execute',       '执行穿透溯源'),
    ('audit:read',          '查看审计日志');
```

- [ ] **Step 2: 重建 PostgreSQL 容器加载 DDL**

```bash
docker compose -f docker-compose.dev.yml stop postgres
docker compose -f docker-compose.dev.yml rm -f postgres
docker volume rm drp-1_postgres-data 2>/dev/null || true
docker compose -f docker-compose.dev.yml up -d postgres
sleep 5
```

- [ ] **Step 3: 验证表结构创建**

```bash
docker exec drp-postgres psql -U drp -d drp -c "\dt"
```

期望输出（9 张表）：
```
 Schema |     Name      | Type  | Owner
--------+---------------+-------+-------
 public | audit_log     | table | drp
 public | etl_job       | table | drp
 public | group         | table | drp
 public | mapping_spec  | table | drp
 public | permission    | table | drp
 public | role          | table | drp
 public | role_permission| table | drp
 public | tenant        | table | drp
 public | user          | table | drp
 public | user_group    | table | drp
 public | user_role     | table | drp
```

- [ ] **Step 4: 验证权限种子数据**

```bash
docker exec drp-postgres psql -U drp -d drp -c "SELECT COUNT(*) FROM permission;"
```

期望：`count = 15`

- [ ] **Step 5: 提交**

```bash
git add infra/postgres/
git commit -m "feat: 新增 PostgreSQL 基础 schema（租户/用户/RBAC/ETL/映射规范）"
```

---

## Task 4: Python 后端骨架

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/src/drp/__init__.py`
- Create: `backend/src/drp/config.py`
- Create: `backend/src/drp/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

**前置要求：** 安装 uv（`curl -LsSf https://astral.sh/uv/install.sh | sh`）

- [ ] **Step 1: 初始化 Python 项目**

```bash
mkdir -p backend/src/drp backend/tests
cd backend
uv init --no-workspace
```

生成的 `pyproject.toml` 将在下一步替换。

- [ ] **Step 2: 编写 `backend/pyproject.toml`**

```toml
[project]
name = "drp-backend"
version = "0.1.0"
description = "穿透式资金监管平台 — FastAPI 后端"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "celery[redis]>=5.4.0",
    "redis>=5.0.0",
    "asyncpg>=0.29.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "alembic>=1.13.0",
    "httpx>=0.27.0",
    "tenacity>=8.3.0",
    "python-multipart>=0.0.9",
    "pyyaml>=6.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "anyio>=4.4.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "anyio>=4.4.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/drp"]
```

- [ ] **Step 3: 安装依赖**

```bash
cd backend
uv sync
```

期望：依赖解析完成，生成 `uv.lock`

- [ ] **Step 4: 编写 `backend/src/drp/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从环境变量或 .env 文件加载。"""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # GraphDB
    graphdb_url: str = "http://localhost:7200"
    graphdb_repository: str = "drp"
    graphdb_username: str = "admin"
    graphdb_password: str = "root"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "drp"
    postgres_user: str = "drp"
    postgres_password: str = "drp_dev"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    @property
    def postgres_dsn(self) -> str:
        """异步 PostgreSQL 连接字符串。"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
```

- [ ] **Step 5: 编写 `backend/src/drp/__init__.py`**

```python
# DRP 后端包初始化
```

- [ ] **Step 6: 先写测试（RED 阶段）**

编写 `backend/tests/test_health.py`：

```python
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health_returns_200():
    """健康检查端点应返回 200 和服务状态。"""
    from drp.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_schema():
    """健康检查响应体应包含 status 字段。"""
    from drp.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    body = response.json()
    assert "status" in body
    assert body["status"] == "ok"
    assert "version" in body
```

编写 `backend/tests/conftest.py`：

```python
import sys
from pathlib import Path

# 将 src/ 加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

- [ ] **Step 7: 运行测试（期望 FAIL）**

```bash
cd backend
uv run pytest tests/test_health.py -v
```

期望：`ImportError: No module named 'drp.main'` 或类似错误

- [ ] **Step 8: 编写 `backend/src/drp/main.py`（GREEN 阶段）**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from drp.config import settings

app = FastAPI(
    title="DRP — 穿透式资金监管平台",
    version="0.1.0",
    docs_url="/api/docs" if settings.app_env == "development" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["基础设施"])
async def health_check() -> dict:
    """服务健康检查端点。"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "env": settings.app_env,
    }
```

- [ ] **Step 9: 运行测试（期望 PASS）**

```bash
cd backend
uv run pytest tests/test_health.py -v
```

期望：
```
tests/test_health.py::test_health_returns_200 PASSED
tests/test_health.py::test_health_response_schema PASSED
2 passed in 0.XXs
```

- [ ] **Step 10: 验证服务可启动**

```bash
cd backend
uv run uvicorn drp.main:app --host 0.0.0.0 --port 8000 &
sleep 2
curl -sf http://localhost:8000/health | python3 -m json.tool
kill %1
```

期望：
```json
{
    "status": "ok",
    "version": "0.1.0",
    "env": "development"
}
```

- [ ] **Step 11: 提交**

```bash
cd ..
git add backend/
git commit -m "feat: 初始化 Python FastAPI 后端骨架（含 /health 端点和 TDD 测试）"
```

---

## Task 5: React 前端骨架

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

**前置要求：** Node.js >= 20

- [ ] **Step 1: 初始化 React+Vite+TypeScript 项目**

```bash
cd /Users/leitao/Documents/Cursor-workspace/Demo8/DRP-1
npm create vite@latest frontend -- --template react-ts
cd frontend
```

- [ ] **Step 2: 安装 D3 v7 和类型定义**

```bash
npm install d3@7
npm install --save-dev @types/d3@7
```

- [ ] **Step 3: 验证 package.json 包含正确依赖**

```bash
cat package.json | grep -E '"d3"|"react"'
```

期望：
```json
"d3": "^7.x.x",
"react": "^18.x.x",
```

- [ ] **Step 4: 编写 `frontend/src/App.tsx`（基础占位页）**

```tsx
function App() {
  return (
    <div style={{ fontFamily: 'monospace', padding: '2rem', background: '#020810', color: '#00d8ff', minHeight: '100vh' }}>
      <h1>DRP — 穿透式资金监管平台</h1>
      <p style={{ color: '#666' }}>监管看板（开发中）</p>
    </div>
  )
}

export default App
```

- [ ] **Step 5: 验证开发服务器启动**

```bash
cd frontend
npm run dev &
sleep 3
curl -sf http://localhost:5173 | grep -o 'DRP\|vite' | head -3
kill %1
```

期望：输出包含 `vite` 或页面内容

- [ ] **Step 6: 验证 TypeScript 编译无错误**

```bash
cd frontend
npm run build 2>&1 | tail -5
```

期望：`built in` 字样，无 TypeScript 错误

- [ ] **Step 7: 提交**

```bash
cd ..
git add frontend/
git commit -m "feat: 初始化 React+Vite+TypeScript+D3 v7 前端骨架"
```

---

## Task 6: 环境变量模板

**Files:**
- Create: `.env.example`
- Create: `.gitignore`（新增 .env 规则）

- [ ] **Step 1: 编写 `.env.example`**

```bash
cat > .env.example << 'EOF'
# ==============================
# DRP 开发环境变量模板
# 使用方法：cp .env.example .env
# ==============================

# ------ GraphDB ------
GRAPHDB_URL=http://localhost:7200
GRAPHDB_REPOSITORY=drp
GRAPHDB_USERNAME=admin
GRAPHDB_PASSWORD=root

# ------ PostgreSQL ------
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=drp
POSTGRES_USER=drp
POSTGRES_PASSWORD=drp_dev

# ------ Redis ------
REDIS_URL=redis://localhost:6379/0

# ------ JWT ------
# 生产环境必须替换为���机强密钥: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=change-this-in-production-use-secrets-token-hex-32
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# ------ LLM 映射服务 ------
# 支持 openai / anthropic / 自定义兼容 API
LLM_API_KEY=your-api-key-here
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# ------ 应用 ------
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

# ------ 混合云（可选，生产环境配置）------
# CLOUD_API_GATEWAY_URL=https://your-gateway.example.com
# MTLS_CERT_PATH=/certs/client.crt
# MTLS_KEY_PATH=/certs/client.key
EOF
```

- [ ] **Step 2: 确保 .env 不进入版本控制**

```bash
grep -q "^\.env$" .gitignore 2>/dev/null || echo ".env" >> .gitignore
grep -q "^\.env\.local$" .gitignore 2>/dev/null || echo ".env.local" >> .gitignore
```

- [ ] **Step 3: 验证 .env.example 可被正确复制使用**

```bash
cp .env.example .env
python3 -c "
with open('.env') as f:
    lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
print(f'环境变量条目数: {len(lines)}')
assert len(lines) >= 12, '变量数量不足'
print('验证通过')
"
```

期望：`环境变量条目数: >= 12` + `验证通过`

- [ ] **Step 4: 提交**

```bash
git add .env.example .gitignore
git commit -m "feat: 新增环境变量模板和 .gitignore 规则"
```

---

## Task 7: 完整环境联调验证

- [ ] **Step 1: 重置并全量启动**

```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
```

- [ ] **Step 2: 等待所有服务 healthy**

```bash
docker compose -f docker-compose.dev.yml ps
```

期望：graphdb / postgres / redis 均为 `healthy`，graphdb-init 为 `exited (0)`

- [ ] **Step 3: 运行后端测试套件**

```bash
cd backend && uv run pytest tests/ -v --cov=drp --cov-report=term-missing
```

期望：所有测试通过，覆盖率 > 80%

- [ ] **Step 4: 验证前端构建**

```bash
cd frontend && npm run build
```

期望：无错误，生成 `dist/` 目录

- [ ] **Step 5: 完成提交**

```bash
cd ..
git add .
git commit -m "chore: 第1章基础设施联调验证完成，全部测试通过"
```

---

## 自检清单（spec 对照）

| 需求 | 对应任务 | 状态 |
|------|---------|------|
| `docker compose up -d` 启动 GraphDB/PostgreSQL/Redis | Task 1 | ✅ |
| GraphDB 自动加载 FIBO 核心本体 | Task 2 | ✅ |
| PostgreSQL 创建基础表（含 etl_job.run_id） | Task 3 | ✅ |
| Python FastAPI 项目初始化 | Task 4 | ✅ |
| React + D3 v7 前端初始化 | Task 5 | ✅ |
| .env.example 环境变量模板 | Task 6 | ✅ |
| `docker compose down -v` 重置后��重现 | Task 7 | ✅ |
| etl_job 表含 run_id 字段（决策14） | Task 3 | ✅ |
| FIBO 仅加载7个核心模块（决策12） | Task 2 | ✅ |
