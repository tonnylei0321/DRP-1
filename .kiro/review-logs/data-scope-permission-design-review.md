# 评审日志：data-scope-permission 设计文档

## 评审信息
- 阶段：系统设计
- 评审方式：设计评审（架构 + 安全）
- 评审结论：有条件通过（12 条接受，5 条推迟）

## 评审结论

- 接受：12 条（P0×2, P1×4, P2×4, P3×2）
- 推迟：5 条（D-07 ~ D-11）
- 最终结论：全部接受项已纳入 design.md，推迟项已记录

## 接受项处理结果

| 编号 | 优先级 | 处理 | 影响组件 | 说明 |
|------|--------|------|----------|------|
| 001 | P0 | 接受 | Expression Parser、data_scope_rule 表 | custom_condition 最大 500 字符；严格白名单 AST（仅 column OP value + AND/OR/NOT）；Unicode NFC 规范化预处理；Property 2 fuzzing ≥10000 次迭代 |
| 002 | P0 | 接受 | Scope_Circuit_Breaker、前端 | 二次密码验证（请求体需提供当前用户密码）；5 分钟操作冷却期（同一租户）；触发时向所有 circuit_breaker 权限用户发送审计通知 |
| 003 | P1 | 接受 | Data_Scope_Interceptor | SQLAlchemy 拦截器改用 `@event.listens_for(Session, "do_orm_execute")` 替代 `before_compile`，兼容 SQLAlchemy 2.x AsyncSession |
| 004 | P1 | 接受 | Column_Mask_Serializer | 改用 FastAPI `APIRoute` 子类（`MaskedAPIRoute`）替代 BaseHTTPMiddleware，在 Pydantic 序列化阶段执行脱敏 |
| 005 | P1 | 接受 | Column_Mask_Serializer | 明确脱敏覆盖范围：JSON API（APIRoute 子类）、文件导出（独立 export_mask 函数）、WebSocket/SSE 不在 MVP |
| 006 | P1 | 接受 | 缓存失效策略 | Redis Pipeline（MULTI/EXEC）确保原子性；审计日志记录缓存失效是否成功 |
| 009 | P2 | 接受 | 部门管理 API、权限种子数据 | 新增独立权限 `department:read` / `department:write`，不再复用 `data_scope:write` |
| 010 | P2 | 接受 | Data_Scope_Interceptor | `@data_scope` 装饰器改为 FastAPI 依赖 `Depends(require_data_scope("table_name"))`，自动从依赖注入获取 TokenPayload |
| 011 | P2 | 接受 | ContextVar 设计 | table_name 通过 ContextVar `_current_table` 在 `require_data_scope` 依赖中设置，Column_Mask_Serializer 从 ContextVar 读取 |
| 012 | P2 | 接受 | Route Guard（新增组件） | 应用启动时扫描所有路由，检查查询了已注册业务表但未使用 `require_data_scope` 依赖的路由，输出警告日志 |
| 014 | P3 | 接受 | Celery beat | 熔断"每 5 分钟审计提醒"使用 Celery beat 定时任务实现 |
| 015 | P3 | 接受 | 前端路由 | Page 类型新增 'data-scope-rules' / 'data-scope-masks'，PageContent switch-case 新增对应分支，NAV_ITEMS 新增数据权限菜单项 |

## 推迟项

| 编号 | 功能 | 推迟理由 |
|------|------|----------|
| D-07 | 多角色脱敏策略可配置（最宽松/最严格） | MVP 先用最宽松，当前用户量少角色冲突概率低 |
| D-08 | PostgreSQL RLS 租户隔离 | 应用层已有 tenant_id 过滤 + Property 1 测试覆盖，RLS 是深度防御增强项 |
| D-09 | 单父部门最大子部门数量限制 | 当前部门数量极少 |
| D-10 | Redis Hash 结构优化缓存键 | 当前缓存键数量少 |
| D-11 | 审计日志防篡改机制 | 后续迭代增加 append-only 或外部日志同步 |

## design.md 变更清单

以下为本次评审后 design.md 的具体修改点：

### 概述
- 行级过滤：`before_compile` → `do_orm_execute`（003）
- 列级脱敏：`BaseHTTPMiddleware` → `APIRoute` 子类（004）
- 新增表达式安全描述：500 字符限制 + 白名单 AST + NFC（001）
- 缓存失效：新增 Pipeline 原子性描述（006）
- 熔断：新增二次密码验证 + 冷却期 + Celery beat（002, 014）
- 设计目标：`@data_scope` 装饰器 → `Depends(require_data_scope())`（010）
- 新增启动时路由扫描描述（012）

### 架构图
- Data_Scope_Interceptor 标注改为 `do_orm_execute`（003）
- Column_Mask_Serializer 标注改为 `APIRoute 子类`（004）
- Expression Parser 标注改为 `严格白名单 AST + NFC`（001）
- 新增 Celery Workers 子图和 Celery Beat 节点（014）
- 新增 Route Guard 节点（012）

### 组件与接口
- 组件 1：改用 `do_orm_execute` + `require_data_scope` 依赖（003, 010, 011）
- 组件 2：改用 `MaskedAPIRoute` + `export_mask` + ContextVar 读取（004, 005, 011）
- 组件 3：新增 500 字符限制 + NFC + 严格白名单 AST 描述（001）
- 组件 6：新增密码验证 + 冷却期 + 审计通知（002）
- 组件 7：权限改为 `department:read` / `department:write`（009）
- 新增组件 8：Route Guard 路由安全扫描（012）

### 数据模型
- data_scope_rule 表新增 CHECK 约束 `length(custom_condition) <= 500`（001）
- 权限种子数据新增 `department:read` / `department:write`（009）
- Redis 缓存键新增 `ds:cb_cooldown:{tenant_id}`（002）
- 缓存失效策略改为 Pipeline 原子操作 + 审计日志记录（006）

### 实现方案
- Data_Scope_Interceptor：`before_compile` → `do_orm_execute`，装饰器 → 依赖（003, 010, 011）
- Column_Mask_Serializer：`BaseHTTPMiddleware` → `MaskedAPIRoute`，新增 `export_mask`（004, 005）

### 正确性属性
- Property 2：增强为含 500 字符限制 + AST 白名单 + NFC，迭代数 ≥10000（001）
- 新增 Property 11：熔断操作安全性（密码验证 + 冷却期 + 审计通知）（002）

### 错误处理
- 新增：custom_condition 超长（400）、熔断密码失败（401）、冷却期（429）、缓存失效失败、路由未保护警告

### 测试策略
- Property 2 迭代数改为 ≥10000（001）
- 新增 Property 11 测试模块（002）
- 单元测试新增 9 个测试用例
- 集成测试更新为新架构
- 前端测试新增路由集成测试

### 前端
- Page 类型新增 `data-scope-rules` / `data-scope-masks`（015）
- NAV_ITEMS 新增两个菜单项（015）
- PageContent 新增 switch-case 分支（015）
- CircuitBreakerPanel 新增密码输入和冷却期 UI（002）
