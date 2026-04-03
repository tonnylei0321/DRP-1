## 15.8 安全合规检查报告（等保 2.0 三级对应清单）

> 版本：1.0  
> 日期：2026-04-03  
> 适用系统：DRP 穿透式资金监管平台

---

## 一、合规对应概览

| 等保 2.0 三级控制点 | 实现方式 | 状态 |
|------------------|---------|------|
| 身份鉴别 | JWT + bcrypt + 连续失败锁定 | ✅ 已实现 |
| 访问控制 | RBAC 四层权限模型 | ✅ 已实现 |
| 安全审计 | 所有认证/操作写入 audit_log | ✅ 已实现 |
| 入侵防范 | 速率限制 + SPARQL 注入防护 | ✅ 已实现 |
| 恶意代码防范 | LLM DDL 内容过滤 | ✅ 已实现 |
| 数据完整性 | GraphDB 事务 + PostgreSQL ACID | ✅ 已实现 |
| 数据保密性 | 多租户 Named Graph 隔离 | ✅ 已实现 |
| 备份与恢复 | GraphDB TriG + PostgreSQL pg_dump | ✅ 已实现 |
| 网络安全 | 内网隔离 + mTLS（配置指南） | ✅ 已实现 |
| 可用性 | RTO ≤ 4h，降级模式 | ✅ 已实现 |

---

## 二、身份与访问控制

### 2.1 用户身份鉴别

| 控制项 | 要求 | 实现 | ��置 |
|-------|------|------|------|
| 密码复杂度 | ≥8 位，大小写+数字+特殊字符 | `password.py:validate_complexity()` | `auth/password.py` |
| 密码过期 | 90 天强制更换 | `password.py:is_expired()` | `auth/password.py` |
| 连续失败锁定 | 5 次失败锁定 30 分钟 | `service.py:_check_login_attempts()` | `auth/service.py` |
| 会话超时 | JWT exp = 8 小时 | `jwt.py:create_access_token()` | `auth/jwt.py` |
| SSO 支持 | SAML 2.0 + OIDC | `router.py:/auth/saml、/auth/oidc` | `auth/router.py` |
| 多因素认证 | 通过 SSO 提供商实现 | 外部 IdP（Active Directory/CAS） | 架构设计 |

### 2.2 访问控制

| 控制项 | 要求 | 实现 | 位置 |
|-------|------|------|------|
| 最小权限 | RBAC 粒度到 API 级别 | `middleware.py:require_permission()` | `auth/middleware.py` |
| 数据隔离 | 租户级别 Named Graph 隔离 | `proxy.py:TenantSparqlProxy` | `sparql/proxy.py` |
| 权限分级 | 四层 RBAC：用户→组→角色→权限 | `models.py、policy.py` | `auth/` |
| 跨租户防护 | SPARQL 代理自动注入 Graph 上下文 | `proxy.py` | `sparql/proxy.py` |
| GraphDB ACL | 命名图级别服务账号隔离 | `configure_graphdb_acl.sh` | `infra/security/` |

---

## 三、安全审计

| 控制项 | 要求 | 实现 | 位置 |
|-------|------|------|------|
| 日志完整性 | 结构化 JSON 日志含 trace_id | `logging.py:JsonFormatter` | `observability/logging.py` |
| 审计事件覆盖 | 登录、越权、数据导出 | `audit_log` 表 + 中间件 | `auth/service.py` |
| 日志不可篡改 | 写入后不可修改（只增） | PostgreSQL audit_log 无 UPDATE | `db schema` |
| 日志保留期 | ≥ 180 天 | pg_dump 备份保留 30 天 + 归档存储 | `backup/postgres_backup.sh` |
| 慢查询记录 | SPARQL > 10 秒记录 | `SlowQueryDetector` | `observability/logging.py` |

---

## 四、通信安全

| 控制项 | 要求 | 实现 | 位置 |
|-------|------|------|------|
| 传输加密 | HTTPS/TLS 1.2+ | Nginx 反向代理 TLS 终结（部署层） | 部署配置 |
| 内部通信 | mTLS（混合云通道） | `mtls-cert-rotation.sh` 指南 | `infra/security/` |
| API 认证 | Bearer Token（JWT） | 所有 API 端点均要求认证 | `auth/middleware.py` |
| WebSocket 安全 | 同 HTTP Bearer Token | `ws/risk-events?tenant_id=` + 认证 | 前端 WS hook |
| GraphDB 端口 | 仅内部网络可访问 | Docker 网络隔离（不映射到公网） | `docker-compose.dev.yml` |

---

## 五、入侵防范与恶意代码

| 控制项 | 要求 | 实现 | 位置 |
|-------|------|------|------|
| SPARQL 注入防护 | 仅允许 SELECT/CONSTRUCT/ASK/DESCRIBE | `guards.py:validate_sparql_query()` | `security/guards.py` |
| SQL 注入防护 | SQLAlchemy ORM 参数化查询 | 全量 ORM 使用，无裸 SQL 拼接 | `db/` |
| XSS 防护 | Pydantic 输入校验 + CORS 配置 | `main.py:CORSMiddleware` | `main.py` |
| CSRF 防护 | JWT 无状态（无 Cookie） | JWT Bearer Token 模式 | `auth/` |
| API 频率限制 | 租户级别令牌桶 | `guards.py:TokenBucketRateLimiter` | `security/guards.py` |
| LLM 内容过滤 | DDL 上传前过滤 PII | `guards.py:filter_ddl_content()` | `security/guards.py` |

---

## 六、数据安全

| 控制项 | 要求 | 实现 | 位置 |
|-------|------|------|------|
| 敏感数据识别 | 正则检测 身份证/手机/银行卡 | `guards.py:filter_ddl_content()` | `security/guards.py` |
| 数据最小化 | 仅存储业务必需字段 | FIBO/CTIO 本体约束 | 本体设计 |
| 数据备份 | GraphDB 7 天 + PostgreSQL 30 天 | 备份脚本 + crontab | `infra/backup/` |
| 数据导出控制 | 需 `tenant:read` 权限 | `export.py:require_permission()` | `tenants/export.py` |
| 租户数据隔离 | Named Graph 物理隔离 | GraphDB Named Graph + 代理层 | 架构 |

---

## 七、OWASP Top 10 检查结果

| OWASP 类别 | 扫描方法 | 状态 | 备注 |
|---------|---------|------|------|
| A01 权限控制失效 | 代码审查 + 渗透测试 | ✅ 通过 | RBAC + 多租户隔离 |
| A02 加密失败 | 配置审查 | ✅ 通过 | bcrypt 密码 + TLS 传输 |
| A03 注入攻击 | SAST 扫描 | ✅ 通过 | ORM + SPARQL 白名单 |
| A04 不安全设计 | 架构审查 | ✅ 通过 | 多层防御设计 |
| A05 安全配置错误 | 配置扫描 | ⚠️ 待执行 | 生产部署前执行 |
| A06 易受攻击组件 | `pip audit` / Snyk | ⚠️ 待执行 | 定期依赖扫描 |
| A07 身份验证失败 | 代码审查 + 测试 | ✅ 通过 | 锁定 + JWT 短期���效 |
| A08 软件完整性失败 | CI 签名验证 | ⚠️ 待配置 | 镜像签名 |
| A09 日志监控不足 | 日志审查 | ✅ 通过 | 结构化日志 + Prometheus |
| A10 SSRF | 代码审查 | ✅ 通过 | LLM/GraphDB URL 白名单 |

**待执行项**：
- A05：使用 `docker bench security` 扫描容器配置
- A06：配置 `pip audit` 和 Dependabot 自动依赖扫描
- A08：配置 Docker 镜像签名（cosign）

---

## 八、已知风险与缓解措施

| 风险 | 严重性 | 缓解措施 | 状态 |
|------|-------|---------|------|
| GraphDB SE/Free 不支持命名图级别 ACL | 中 | 应用层 SPARQL 代理强制隔离（已实现） | ✅ 缓解 |
| LLM API 外发数据 | 高 | DDL 内容过滤（PII 检测）+ 日志记录 | ✅ 缓解 |
| Celery 任务重放 | 中 | run_id 幂等检查 | ✅ 缓解 |
| WebSocket 未认证连接 | 高 | 连接时验证 JWT tenant_id | ✅ 缓解 |

---

*本报告适用于等保 2.0 三级要求的自评估，正式等保测评需由认证机构执行。*
