# 第3章：多租户基础层设计文档

**日期**：2026-04-03
**状态**：已批准
**范围**：TenantRepository、SPARQL 查询代理、租户 CRUD API、多租户隔离集成测试

---

## 1. 背景与约束

DRP 是面向多家央企的 SaaS 化监管平台，每个租户的业务数据必须严格隔离。隔离机制选用 **GraphDB Named Graph**（应用层隔离），每个租户拥有独立的命名图空间，查询代理层自动注入租户上下文。

已有基础：
- PostgreSQL `tenant` 表（id UUID、slug、graph_iri、status）
- GraphDB 全局仓库 `drp`，当前已加载 CTIO 本体
- FastAPI 后端骨架（`/health` 端点）

**关键设计决策**：
1. Named Graph IRI 格式：`urn:tenant:{uuid}`（与现有 SQL schema `graph_iri` 字段一致）
2. 隔离强度：应用层查询代理注入，不做 GraphDB ACL（第15章安全加固时补充）
3. 元数据持久化：PostgreSQL 作为单一来源，GraphDB Named Graph 按需创建/删除
4. SPARQL 代理接口：混合模式（`ContextVar` 自动注入 + 显式 `tenant_id` 参数覆盖）

---

## 2. 目录结构

```
backend/src/drp/
├── db/
│   └── session.py          # AsyncSession 工厂（SQLAlchemy asyncpg）
├── graphdb/
│   └── client.py           # GraphDBClient — 薄 HTTP 客户端（httpx）
├── sparql/
│   └── proxy.py            # sparql_query() / sparql_update() + ContextVar
├── tenants/
│   ├── models.py           # SQLAlchemy ORM 模型（映射 tenant 表）
│   ├── repository.py       # TenantRepository — PostgreSQL CRUD
│   ├── service.py          # TenantService — 协调 PG + GraphDB
│   ├── schemas.py          # Pydantic 请求/响应模型
│   └── router.py           # FastAPI 路由（POST/GET/DELETE /tenants）
└── main.py                 # 注册 tenants router
```

**模块职责约定**：
- `graphdb/client.py`：只知道 HTTP，不知道租户业务逻辑
- `sparql/proxy.py`：只知道查询改写和上下文注入，不知道业务
- `tenants/`：唯一包含"租户"业务概念的模块

---

## 3. 核心接口

### 3.1 GraphDBClient

```python
class GraphDBClient:
    async def create_named_graph(self, graph_iri: str) -> None: ...
    async def delete_named_graph(self, graph_iri: str) -> None: ...
    async def named_graph_exists(self, graph_iri: str) -> bool: ...
```

底层使用 `httpx.AsyncClient`，操作 GraphDB REST API。不依赖 FastAPI，可在 Celery worker 中直接实例化。

### 3.2 SPARQL 代理

```python
# ContextVar：FastAPI 中间件写入，Celery task 显式设置
_tenant_ctx: ContextVar[str | None] = ContextVar("tenant_id", default=None)

async def sparql_query(sparql: str, tenant_id: str | None = None) -> list[dict]:
    """执行 SPARQL SELECT，自动注入租户 Named Graph 上下文。"""
    tid = tenant_id or _tenant_ctx.get()
    if not tid:
        raise TenantContextMissingError("未设置租户上下文")
    rewritten = _inject_graph_context(sparql, tid)
    # 调用 GraphDB HTTP API
    ...

async def sparql_update(sparql: str, tenant_id: str | None = None) -> None:
    """执行 SPARQL UPDATE，限定在租户 Named Graph 内。"""
    ...
```

`_inject_graph_context()` 将 `WHERE { ... }` 改写为 `WHERE { GRAPH <urn:tenant:{tid}> { ... } }`，支持 SELECT / CONSTRUCT / ASK / UPDATE。

### 3.3 TenantRepository

```python
class TenantRepository:
    async def create(self, session, data: TenantCreate) -> Tenant: ...
    async def get_by_id(self, session, tenant_id: UUID) -> Tenant | None: ...
    async def get_by_slug(self, session, slug: str) -> Tenant | None: ...
    async def delete(self, session, tenant_id: UUID) -> None: ...
    async def list_active(self, session) -> list[Tenant]: ...
```

### 3.4 TenantService

```python
class TenantService:
    async def create_tenant(self, data: TenantCreate) -> TenantResponse: ...
    async def get_tenant(self, tenant_id: UUID) -> TenantResponse: ...
    async def delete_tenant(self, tenant_id: UUID) -> None: ...
```

---

## 4. 数据流

### 创建租户

```
POST /tenants
  → TenantService.create_tenant()
      1. 生成 UUID，构造 graph_iri = "urn:tenant:{uuid}"
      2. TenantRepository.create() → INSERT INTO tenant
      3. GraphDBClient.create_named_graph(graph_iri)
      4. 若步骤3失败 → TenantRepository.delete() 回滚 → 抛 502
      5. 返回 TenantResponse
```

### 删除租户

```
DELETE /tenants/{id}
  → TenantService.delete_tenant()
      1. 查询租户（不存在则 404）
      2. GraphDBClient.delete_named_graph(graph_iri)（不存在则 warning，继续）
      3. TenantRepository.delete() → DELETE FROM tenant
```

### SPARQL 查询（FastAPI 请求上下文）

```
GET /some-endpoint  (携带 X-Tenant-ID 请求头)
  → 中间件读取请求头，写入 _tenant_ctx
  → 业务代码调用 sparql_query("SELECT ...")
  → proxy 自动注入 GRAPH <urn:tenant:{id}>
```

### SPARQL 查询（Celery 任务上下文）

```
@celery_app.task
def calculate_indicators(tenant_id: str):
    results = await sparql_query("SELECT ...", tenant_id=tenant_id)
```

---

## 5. API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tenants` | 创建租户 |
| GET | `/tenants/{tenant_id}` | 查询租户详情 |
| DELETE | `/tenants/{tenant_id}` | 删除租户及其 Named Graph |

**请求体（POST /tenants）**：
```json
{ "name": "中国航天科工集团", "slug": "casic" }
```

**响应体**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "中国航天科工集团",
  "slug": "casic",
  "status": "active",
  "graph_iri": "urn:tenant:550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-04-03T10:00:00Z"
}
```

---

## 6. 错误处理

| 场景 | HTTP 状态 | 处理方式 |
|------|----------|---------|
| PostgreSQL 写入失败 | 500 | 直接抛出，GraphDB 未动，无需回滚 |
| GraphDB 创建 Named Graph 失败 | 502 | 回滚 PostgreSQL 记录 |
| 删除时 Named Graph 不存在 | - | 记录 warning，继续删 PG（幂等） |
| SPARQL 无租户上下文 | 500 | 抛 `TenantContextMissingError`，禁止无租户查询 |
| slug 重复 | 409 | PostgreSQL unique 约束，返回 Conflict |
| 租户不存在 | 404 | GET/DELETE 时返回 Not Found |

---

## 7. 测试策略

| 层级 | 工具 | 策略 |
|------|------|------|
| `TenantRepository` | `pytest-asyncio` + 真实 PostgreSQL 测试库 | 不 mock DB |
| `GraphDBClient` | `respx`（httpx mock） | 拦截 HTTP，不依赖真实 GraphDB |
| `sparql/proxy.py` | 纯单元测试 | 测试 `_inject_graph_context()` 改写逻辑，覆盖 SELECT/CONSTRUCT/ASK |
| `TenantService` | unittest.mock | mock Repository + GraphDBClient，测试协调逻辑和回滚场景 |
| Router | `httpx.AsyncClient` + FastAPI TestClient | 端到端 CRUD 集成测试 |

**隔离验证测试**（tasks.md 3.4）：
- 创建租户 A、租户 B，各自写入不同三元组
- 用租户 A 的上下文查询租户 B 的数据，断言返回空结果
