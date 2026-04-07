# 实施计划：细粒度数据权限（Data Scope Permission）

## 概述

按组件依赖顺序实施：数据库迁移 → ORM 模型 → 核心组件（表达式解析器、注册表、拦截器、脱敏器、熔断器）→ 管理 API → 前端界面 → 集成测试。每个任务引用具体需求编号，属性测试标记为可选。

## 任务

- [x] 1. 数据库迁移与 ORM 模型
  - [x] 1.1 创建数据库迁移脚本 `infra/postgres/init/002_data_scope.sql`
    - 创建 `department` 表（含自引用外键、联合唯一约束 `(tenant_id, name, parent_id)`）
    - `ALTER TABLE "user" ADD COLUMN dept_id` 外键引用 department
    - 创建 `data_scope_rule` 表（含联合唯一约束、CHECK 约束、长度限制 500 字符）
    - 创建 `column_mask_rule` 表（含联合唯一约束、CHECK 约束）
    - 插入权限种子数据：`data_scope:read`、`data_scope:write`、`data_scope:circuit_breaker`、`department:read`、`department:write`
    - _需求: 1.1, 1.2, 1.9, 1.1.1, 1.1.4, 1.1.6, 2.1, 2.2, 2.8, 7.1_

  - [x] 1.2 创建 ORM 模型 `backend/src/drp/scope/models.py`
    - 实现 `Department`、`DataScopeRule`、`ColumnMaskRule` 三个 SQLAlchemy 模型
    - 在 `User` 模型中新增 `dept_id` 字段和 `department` relationship
    - 确保所有外键、约束与迁移脚本一致
    - _需求: 1.1, 1.1.1, 1.1.2, 2.1_

- [x] 2. Business_Table_Registry（业务表注册表）
  - [x] 2.1 实现注册表模块 `backend/src/drp/scope/registry.py`
    - 实现 `TableMeta` TypedDict、`get_registry()`、`is_table_registered()`、`is_column_valid()` 接口
    - 支持通过 SQLAlchemy 模型 `__data_scope__ = True` 标记自动发现
    - 支持 `supports_self` 字段校验（检查 `created_by` 列是否存在）
    - 应用启动时加载到内存
    - _需求: 5.1.1, 5.1.2, 5.1.3, 5.1.4, 5.1.5_

  - [ ]* 2.2 属性测试：业务表注册校验（Property 10）
    - **Property 10: 业务表注册校验**
    - 验证未注册表名被拒绝、self 类型无 created_by 列被拒绝、无效列名被拒绝
    - **验证需求: 5.1.3, 5.1.5, 5.4**

- [x] 3. Expression Parser（表达式解析器）
  - [x] 3.1 实现表达式解析器 `backend/src/drp/scope/expr_parser.py`
    - 实现 `parse_condition(expr, allowed_columns) -> ParseResult` 接口
    - 长度校验（≤ 500 字符）、Unicode NFC 规范化预处理
    - 词法分析 → 严格白名单 AST 构建（仅允许 ColumnRef/Literal/CompareExpr/LogicalExpr）
    - 列名白名单校验、生成参数化 SQL 片段（绑定变量 `:pN`）
    - 禁止子查询、函数调用、SQL 关键字注入
    - _需求: 1.3, 1.4, 3.5_

  - [ ]* 3.2 属性测试：表达式解析器安全性（Property 2）
    - **Property 2: 表达式解析器安全性**
    - 使用 Hypothesis fuzzing ≥ 10000 次迭代
    - 验证超长输入拒绝、非白名单 AST 节点拒绝、非白名单列名拒绝、输出仅含绑定参数占位符
    - **验证需求: 1.3, 1.4, 3.5**

- [x] 4. 检查点 — 基础组件验证
  - 确保注册表和表达式解析器的所有测试通过，有问题请询问用户。

- [x] 5. 部门服务与递归查询
  - [x] 5.1 实现部门服务 `backend/src/drp/scope/dept_service.py`
    - 递归 CTE 查询获取部门及所有下级部门 ID（最大递归深度 10 层）
    - 循环引用检测（parent_id 链路闭环校验）
    - 部门树缓存（Redis 键 `ds:dept_tree:{tenant_id}:{dept_id}`，TTL 300s）
    - _需求: 1.1.3, 1.1.5, 1.6, 6.1_

  - [ ]* 5.2 属性测试：部门树递归查询正确性（Property 3）
    - **Property 3: 部门树递归查询正确性**
    - 随机生成部门树（深度 ≤ 10），验证递归 CTE 返回的 ID 集合等于传递闭包
    - **验证需求: 1.6, 1.1.3**

  - [ ]* 5.3 属性测试：部门循环引用检测（Property 5）
    - **Property 5: 部门循环引用检测**
    - 随机生成部门树和 parent_id 更新操作，验证闭环被正确检测
    - **验证需求: 1.1.5**

- [x] 6. Data_Scope_Interceptor（行级过滤拦截器）
  - [x] 6.1 实现拦截器 `backend/src/drp/scope/interceptor.py`
    - 基于 SQLAlchemy `do_orm_execute` 事件监听器（兼容 AsyncSession）
    - 实现 `require_data_scope(table_name)` FastAPI 依赖工厂，设置/清除 ContextVar
    - 从 Redis 缓存加载规则（缓存键 `ds:scope:{tenant_id}:{user_id}:{table_name}`，TTL 300s）
    - Redis 不可用时回退到数据库直查，写入警告日志
    - scope_type 解析：`all` 不追加条件、`self` → `created_by = :current_user_id`、`dept` → `dept_id IN (:dept_ids)`、`custom` → 调用表达式解析器
    - 无规则时返回 HTTP 403 + 审计日志
    - 多规则 OR 合并
    - dept_id 为 NULL 时 dept 规则返回空结果集 + 警告日志
    - 熔断状态检查（bypass 时跳过过滤，添加 `X-Data-Scope: bypassed` Header）
    - _需求: 1.5, 1.6, 1.7, 1.8, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 5.2.2, 5.2.8, 6.1, 6.2, 6.5, 6.6, 7.2, 7.5_

  - [ ]* 6.2 属性测试：多规则 OR 合并（Property 4）
    - **Property 4: 多规则 OR 合并**
    - 验证 N 条规则生成的 WHERE 子句等价于各规则条件的 OR 组合
    - **验证需求: 1.8**

  - [ ]* 6.3 属性测试：熔断旁路正确性（Property 9）
    - **Property 9: 熔断旁路正确性**
    - 验证熔断禁用时不追加 WHERE 条件、不修改字段值
    - **验证需求: 5.2.2, 5.2.3**

- [x] 7. Column_Mask_Serializer（列级脱敏序列化器）
  - [x] 7.1 实现脱敏序列化器 `backend/src/drp/scope/mask_serializer.py`
    - 实现 `MaskedAPIRoute(APIRoute)` 子类，在序列化阶段执行脱敏
    - 从 ContextVar `_current_table` 获取 table_name
    - 从 Redis 缓存加载脱敏规则（缓存键 `ds:mask:{tenant_id}:{user_id}:{table_name}`，TTL 300s）
    - 内置脱敏函数：`phone`（保留前3后4）、`id_card`（保留前3后4）、`email`（用户名遮蔽）、`custom_regex`
    - `mask` 策略部分遮蔽、`hide` 策略移除字段、`none` 策略返回原值
    - 多角色取最宽松策略（优先级：none > mask > hide）
    - 异常时 fallback 到 hide + 错误日志
    - 实现 `export_mask()` 文件导出专用脱敏函数
    - 熔断状态检查（bypass 时跳过脱敏）
    - _需求: 2.4, 2.5, 2.6, 2.7, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.2.3_

  - [ ]* 7.2 属性测试：脱敏策略应用正确性（Property 6）
    - **Property 6: 脱敏策略应用正确性**
    - 验证 mask/hide/none 三种策略的输出符合预期
    - **验证需求: 2.4, 2.5, 2.6, 4.2, 4.3, 4.4**

  - [ ]* 7.3 属性测试：多角色脱敏策略合并取最宽松（Property 7）
    - **Property 7: 多角色脱敏策略合并取最宽松**
    - 验证合并后的有效策略等于集合中优先级最高的策略
    - **验证需求: 2.7**

- [x] 8. 检查点 — 核心组件验证
  - 确保拦截器和脱敏序列化器的所有测试通过，有问题请询问用户。

- [x] 9. Scope_Circuit_Breaker（熔断开关）
  - [x] 9.1 实现熔断开关 `backend/src/drp/scope/circuit_breaker.py`
    - Redis 键值存储（`ds:circuit_breaker:{tenant_id}`）
    - `is_circuit_open()` 检查熔断状态
    - `set_circuit_breaker()` 设置状态（含二次密码验证、5 分钟冷却期 `ds:cb_cooldown:{tenant_id}`）
    - 可选 `auto_recover_minutes` 参数（TTL 自动恢复）
    - 状态变更写入审计日志
    - _需求: 5.2.1, 5.2.2, 5.2.3, 5.2.4, 5.2.5, 5.2.6_

  - [x] 9.2 实现 Celery beat 熔断审计定时任务 `backend/src/drp/scope/tasks.py`
    - 每 5 分钟检查熔断状态，禁用时写入审计日志提醒
    - 注册到 `celery_app.conf.beat_schedule`
    - _需求: 5.2.7_

  - [ ]* 9.3 属性测试：熔断开关操作安全性（Property 11）
    - **Property 11: 熔断开关操作安全性**
    - 验证密码错误被拒绝、冷却期内重复操作被拒绝
    - **验证需求: 5.2.1, 5.2.4, 5.2.5**

- [x] 10. 规则冲突检测
  - [x] 10.1 实现冲突检测模块 `backend/src/drp/scope/conflict_detector.py`
    - 检测已有 `all` 规则时新增其他类型规则的冲突
    - 检测新增 `all` 规则时已有其他类型规则的冲突
    - 返回警告信息说明 OR 合并后的实际效果
    - _需求: 1.10, 1.11_

  - [ ]* 10.2 属性测试：规则冲突检测（Property 8）
    - **Property 8: 规则冲突检测**
    - 验证包含 `all` 类型时正确返回警告
    - **验证需求: 1.10**

- [x] 11. 缓存服务
  - [x] 11.1 实现缓存服务 `backend/src/drp/scope/cache.py`
    - 封装 Redis 缓存读写（scope 规则、mask 规则、部门树）
    - 使用 Redis Pipeline（MULTI/EXEC）原子失效缓存键
    - 缓存失效结果写入审计日志
    - 可配置 TTL（默认 300s）
    - Redis 不可用时回退到数据库直查 + 警告日志
    - _需求: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 12. Scope_Admin_API（管理接口）与部门管理 API
  - [x] 12.1 实现部门管理路由 `backend/src/drp/scope/dept_router.py`
    - CRUD 接口：GET/POST/PUT/DELETE `/departments`
    - 权限校验：`department:read` / `department:write`
    - 创建/更新时校验循环引用
    - 删除时校验用户关联（有关联用户拒绝删除）
    - _需求: 1.1.1, 1.1.4, 1.1.5, 1.1.7_

  - [x] 12.2 实现数据权限管理路由 `backend/src/drp/scope/router.py`
    - Data_Scope_Rule CRUD：GET/POST/PUT/DELETE `/data-scope/rules`
    - Column_Mask_Rule CRUD：GET/POST/PUT/DELETE `/data-scope/mask-rules`
    - `GET /data-scope/tables` 返回注册表元数据
    - `POST /data-scope/circuit-breaker` 和 `GET /data-scope/circuit-breaker`
    - 权限校验：`data_scope:read` / `data_scope:write` / `data_scope:circuit_breaker`
    - 创建/更新时校验 table_name 和 column_name 在注册表中
    - 创建/更新 custom_condition 时调用表达式解析器校验
    - custom_regex 时校验正则表达式合法性
    - 规则变更时清除 Redis 缓存（Pipeline 原子失效）
    - 规则变更写入审计日志
    - 删除最后一条规则时返回警告
    - all 类型创建时要求确认
    - 冲突检测返回警告
    - _需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 1.3, 1.4, 1.10, 1.11, 2.3, 6.4_

  - [x] 12.3 注册路由到 FastAPI 应用 `backend/src/drp/main.py`
    - 引入并注册 `scope_router` 和 `dept_router`
    - 注册 `do_orm_execute` 事件监听器
    - 添加启动事件加载 Business_Table_Registry
    - _需求: 7.2_

- [x] 13. Route Guard（路由安全扫描）
  - [x] 13.1 实现路由扫描 `backend/src/drp/scope/route_guard.py`
    - 应用启动时扫描所有路由
    - 检查查询了已注册业务表但未使用 `require_data_scope` 依赖的路由
    - 未保护路由输出 WARNING 日志
    - 在 `main.py` 启动事件中调用
    - _需求: 3.4_

- [x] 14. 检查点 — 后端 API 验证
  - 确保所有后端 API 端点可正常调用，所有测试通过，有问题请询问用户。

- [x] 15. 冒烟测试
  - [x] 15.1 编写冒烟测试 `backend/tests/test_data_scope_smoke.py`
    - **用例 1：行级规则 Happy Path**
      - 前置条件：已有用户 A（tenant_1）、业务表 `item` 已注册
      - 操作步骤：管理员为用户 A 创建 scope_type=self 的行级规则 → 用户 A 查询 /items
      - 预期结果：仅返回 created_by = 用户 A 的记录
    - **用例 2：列级脱敏 Happy Path**
      - 前置条件：已有角色 R1、Column_Mask_Rule（table=item, column=phone, strategy=mask, pattern=phone）
      - 操作步骤：拥有角色 R1 的用户查询 /items
      - 预期结果：phone 字段返回 `138****5678` 格式
    - **用例 3：熔断开关 Happy Path**
      - 前置条件：已有行级规则和列级脱敏规则
      - 操作步骤：管理员通过 POST /data-scope/circuit-breaker 禁用过滤（含密码验证）→ 用户查询 /items
      - 预期结果：返回全部数据且无脱敏，响应 Header 包含 `X-Data-Scope: bypassed`
    - **用例 4：管理 API CRUD Happy Path**
      - 前置条件：管理员拥有 `data_scope:write` 权限
      - 操作步骤：创建行级规则 → 查询列表 → 更新规则 → 删除规则
      - 预期结果：各步骤返回正确状态码和数据，审计日志已记录
    - **用例 5：部门层级过滤 Happy Path**
      - 前置条件：部门树 A→B→C，用户属于部门 B，scope_type=dept
      - 操作步骤：用户查询 /items
      - 预期结果：返回 dept_id IN (B, C) 的记录
    - _需求: 1.5, 1.6, 2.5, 3.1, 3.2, 5.1, 5.2.2, 5.2.8_

- [ ] 16. 单元测试
  - [ ]* 16.1 编写单元测试 `backend/tests/test_data_scope_unit.py`
    - self 类型生成 `created_by = :current_user_id`
    - all 类型不追加条件
    - 无规则时返回 403
    - dept_id 为 NULL 时 dept 规则返回空结果集
    - 脱敏异常时 fallback 到 hide
    - Redis 不可用时降级到数据库
    - 删除最后一条规则时返回警告
    - all 类型创建时要求确认
    - 删除部门有关联用户时拒绝
    - custom_condition 超过 500 字符时拒绝
    - Unicode 混淆字符经 NFC 规范化后正确处理
    - 熔断开关密码验证失败时拒绝
    - 熔断开关 5 分钟冷却期内重复操作时拒绝（429）
    - 缓存失效 Pipeline 原子性验证
    - `require_data_scope` 依赖正确设置/清除 ContextVar
    - `export_mask` 函数与 API 脱敏结果一致
    - 启动时路由扫描检测未保护路由
    - _需求: 1.3, 1.5, 1.7, 1.8, 1.10, 1.11, 1.1.5, 1.1.7, 3.3, 3.6, 3.7, 4.6, 5.2.4, 5.2.5, 6.6_

- [ ] 17. 租户隔离属性测试
  - [ ]* 17.1 属性测试：租户数据隔离（Property 1）
    - **Property 1: 租户数据隔离**
    - 验证查询返回的规则集合中所有 tenant_id 都等于当前租户 ID
    - **验证需求: 1.2, 2.2**

- [x] 18. 检查点 — 后端测试全量验证
  - 确保所有后端测试（冒烟测试、单元测试、属性测试）通过，有问题请询问用户。

- [x] 19. 前端数据权限管理界面
  - [x] 19.1 扩展前端 API 客户端 `frontend/src/api/client.ts`
    - 新增 `dataScopeApi` 对象，封装所有数据权限相关 API 调用
    - 包含行级规则 CRUD、列级规则 CRUD、熔断开关、业务表列表接口
    - 新增 TypeScript 类型定义（DataScopeRule、ColumnMaskRule、TableMeta、CircuitBreakerStatus 等）
    - _需求: 8.1_

  - [x] 19.2 实现数据权限管理页面 `frontend/src/pages/DataScopePages.tsx`
    - `DataScopeRulesPage`：行级规则列表 + 用户筛选 + 创建/编辑 Modal + 删除确认
    - `ColumnMaskRulesPage`：列级规则列表 + 角色筛选 + 创建/编辑 Modal + 删除确认
    - `CircuitBreakerPanel`：熔断开关状态显示 + 切换按钮 + 密码验证 + 冷却期倒计时
    - 表名/列名下拉选择器从 `/data-scope/tables` 获取
    - scope_type=custom 时显示条件输入框
    - mask_strategy=mask 时显示脱敏模式选择器
    - 删除最后一条规则时二次确认弹窗
    - 创建规则冲突时显示警告提示
    - all 类型创建时二次确认
    - 权限控制：`data_scope:read` 显示菜单、`data_scope:write` 启用编辑、`data_scope:circuit_breaker` 显示熔断入口
    - _需求: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10_

  - [x] 19.3 集成到主应用 `frontend/src/App.tsx`
    - Page 类型新增 `data-scope-rules` 和 `data-scope-masks`
    - NAV_ITEMS 新增"行级规则"和"列级规则"菜单项（requiredPermission: `data_scope:read`）
    - PageContent switch-case 新增对应分支
    - _需求: 8.1, 8.6_

- [ ] 20. 集成测试
  - [ ]* 20.1 编写集成测试 `backend/tests/test_data_scope_integration.py`
    - Scope_Admin_API 完整 CRUD 流程
    - 拦截器（do_orm_execute）+ APIRoute 子类联合工作流
    - 缓存写入/读取/Pipeline 原子失效
    - 熔断开关切换（含密码验证和冷却期）
    - 审计日志写入（含缓存失效结果记录）
    - 依赖执行顺序（require_permission → require_data_scope → MaskedAPIRoute）
    - Celery beat 熔断审计定时任务
    - 文件导出脱敏（export_mask）
    - 启动时路由安全扫描
    - _需求: 3.1, 3.2, 5.1, 5.7, 5.2.4, 5.2.7, 6.4, 7.2, 7.5_

- [x] 21. 最终检查点 — 全量验证
  - 确保所有测试通过（冒烟测试、单元测试、属性测试、集成测试），有问题请询问用户。

## 备注

- 标记 `*` 的任务为可选，可跳过以加速 MVP 交付
- 每个任务引用具体需求编号，确保需求全覆盖
- 检查点任务用于阶段性验证，确保增量正确性
- 属性测试验证设计文档中定义的正确性属性
- 冒烟测试在集成测试之前完成，验证核心功能最小可用路径
