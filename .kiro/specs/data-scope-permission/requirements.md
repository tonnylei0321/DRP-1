# 需求文档：细粒度数据权限（Data Scope Permission）

## 简介

在现有 RBAC（User → Role → Permission）模型基础上，增加**数据范围权限**层，实现同一角色下不同用户看到不同数据行和列的能力。核心场景：同为"销售经理"角色，张三只能看北京区域数据，李四只能看自己创建的数据；敏感字段（手机号、身份证）对特定角色进行脱敏或隐藏。

## 术语表

- **Data_Scope_Rule**：数据范围规则，定义某个用户在某张业务表上的行级过滤条件（如 `region = 'Beijing'`）
- **Column_Mask_Rule**：列级脱敏规则，定义某个角色对某张业务表中敏感列的处理策略（脱敏或隐藏）
- **Scope_Type**：数据范围类型枚举，包括 `all`（全部数据）、`dept`（本部门及下级）、`self`（仅本人创建）、`custom`（自定义条件）
- **Mask_Strategy**：脱敏策略枚举，包括 `mask`（部分遮蔽，如手机号中间四位替换为 `****`）、`hide`（完全隐藏该列，API 响应中不返回）、`none`（不脱敏）
- **Mask_Pattern**：脱敏模式标识枚举，包括 `phone`（手机号）、`id_card`（身份证号）、`email`（邮箱）、`custom_regex`（自定义正则表达式）
- **Data_Scope_Interceptor**：数据范围拦截器，在 SQLAlchemy 查询执行前自动注入行级过滤条件的组件
- **Column_Mask_Serializer**：列级脱敏序列化器，在 API 响应序列化阶段对敏感字段执行脱敏或隐藏的组件
- **Scope_Admin_API**：数据范围管理接口，供管理员配置数据范围规则和列级脱敏规则的 REST API
- **Current_User**：当前已认证用户，通过 JWT 令牌解析获得的 TokenPayload 对象
- **Business_Table_Registry**：业务表注册表，维护可配置数据权限的业务表白名单及其列定义元数据
- **Scope_Circuit_Breaker**：数据权限熔断开关，紧急情况下一键禁用所有数据范围规则的全局开关

## 需求

### 需求 1：数据范围规则存储

**用户故事：** 作为系统管理员，我希望能为每个用户配置独立的数据范围规则，以便同一角色下不同用户看到不同范围的业务数据。

#### 验收标准

1. THE Data_Scope_Rule 表 SHALL 存储以下字段：规则 ID、租户 ID（tenant_id）、用户 ID、业务表名、scope_type（枚举：all / dept / self / custom）、自定义过滤条件表达式、创建时间、更新时间
2. THE Data_Scope_Rule 表 SHALL 包含 tenant_id 外键约束（引用 tenant 表），所有查询 SHALL 自动带租户过滤条件，防止跨租户数据泄露
3. WHEN scope_type 为 `custom` 时，THE Data_Scope_Rule SHALL 要求 custom_condition 字段非空，且 custom_condition 仅允许包含列名、比较运算符（=, !=, >, <, >=, <=, IN, BETWEEN, LIKE）、逻辑运算符（AND, OR, NOT）和字面量值，禁止子查询和函数调用
4. WHEN 创建或更新 custom_condition 时，THE Scope_Admin_API SHALL 解析条件表达式并校验其中引用的列名是否存在于目标业务表的列定义中
5. WHEN scope_type 为 `self` 时，THE Data_Scope_Interceptor SHALL 将过滤条件解析为 `created_by = :current_user_id`
6. WHEN scope_type 为 `dept` 时，THE Data_Scope_Interceptor SHALL 查询当前用户所属部门及其所有下级部门 ID，将过滤条件解析为 `dept_id IN (:current_user_dept_ids)`
7. WHEN scope_type 为 `all` 时，THE Data_Scope_Interceptor SHALL 不追加任何行级过滤条件
8. IF 同一用户对同一业务表存在多条 Data_Scope_Rule，THEN THE Data_Scope_Interceptor SHALL 使用 OR 逻辑合并所有规则的过滤条件
9. THE Data_Scope_Rule 表 SHALL 通过 (tenant_id, user_id, table_name, scope_type) 的联合唯一约束防止完全重复的规则
10. WHEN 创建规则时检测到与已有规则存在逻辑冲突（如已有 `all` 规则时新增 `self` 规则），THE Scope_Admin_API SHALL 返回警告信息说明 OR 合并后的实际效果
11. WHEN scope_type 为 `all` 的规则被创建时，THE Scope_Admin_API SHALL 要求前端二次确认，确认提示说明"此操作将授予该用户对该表的全部数据访问权限"

### 需求 1.1：部门组织架构模型

**用户故事：** 作为系统管理员，我希望系统维护部门层级结构，以便 `dept` 类型的数据范围规则能正确解析为部门及下级部门的过滤条件。

#### 验收标准

1. THE department 表 SHALL 存储以下字段：部门 ID、租户 ID、部门名称、上级部门 ID（parent_id，自引用外键，根部门为 NULL）、排序号、状态、创建时间
2. THE user 表 SHALL 新增 dept_id 字段（外键引用 department 表），表示用户所属部门
3. THE Data_Scope_Interceptor SHALL 在解析 `dept` 类型规则时，通过递归查询（WITH RECURSIVE CTE）获取当前用户所属部门及其所有下级部门的 ID 列表，递归 CTE SHALL 设置最大递归深度为 10 层
4. THE department 表 SHALL 通过 (tenant_id, name, parent_id) 的联合唯一约束防止同级重名
5. WHEN 创建或更新 department 记录时，THE Scope_Admin_API SHALL 校验 parent_id 链路不产生循环引用（即不允许 A→B→…→A 的闭环），检测到循环时 SHALL 拒绝操作并返回错误信息
6. THE user 表的 dept_id 字段 SHALL 为 nullable（允许未分配部门的用户），存量用户 dept_id 默认值为 NULL
7. WHEN 删除 department 记录时，THE Scope_Admin_API SHALL 校验是否有用户关联该部门，有关联用户时 SHALL 拒绝删除并返回错误信息"该部门下仍有关联用户，请先迁移用户后再删除"

### 需求 2：列级脱敏规则存储

**用户故事：** 作为系统管理员，我希望能按角色配置敏感字段的脱敏策略，以便不同角色看到不同程度的敏感信息。

#### 验收标准

1. THE Column_Mask_Rule 表 SHALL 存储以下字段：规则 ID、租户 ID（tenant_id）、角色 ID、业务表名、列名、mask_strategy（枚举：mask / hide / none）、mask_pattern（脱敏模式标识，仅 mask 策略时使用）、创建时间、更新时间
2. THE Column_Mask_Rule 表 SHALL 包含 tenant_id 外键约束（引用 tenant 表），所有查询 SHALL 自动带租户过滤条件
3. WHEN mask_strategy 为 `mask` 时，THE Column_Mask_Rule SHALL 要求 mask_pattern 字段非空，mask_pattern SHALL 限制为预定义枚举值（phone / id_card / email / custom_regex）；WHEN mask_pattern 为 `custom_regex` 时，THE Column_Mask_Rule SHALL 要求额外提供 regex_expression 字段且 Scope_Admin_API SHALL 校验该正则表达式的合法性
4. WHEN mask_strategy 为 `hide` 时，THE Column_Mask_Serializer SHALL 从 API 响应中完全移除该列
5. WHEN mask_strategy 为 `mask` 时，THE Column_Mask_Serializer SHALL 按 mask_pattern 对该列的值进行部分遮蔽处理
6. WHEN mask_strategy 为 `none` 时，THE Column_Mask_Serializer SHALL 返回该列的原始值
7. IF 同一用户拥有多个角色且各角色对同一列配置了不同的 mask_strategy，THEN THE Column_Mask_Serializer SHALL 采用最宽松策略（优先级：none > mask > hide）
8. THE Column_Mask_Rule 表 SHALL 通过 (tenant_id, role_id, table_name, column_name) 的联合唯一约束防止重复规则

### 需求 3：行级数据过滤拦截器

**用户故事：** 作为开发者，我希望行级数据过滤能自动注入到 SQL 查询中，以便业务代码无需手动添加过滤条件。

#### 验收标准

1. THE Data_Scope_Interceptor SHALL 以 SQLAlchemy 事件监听器或查询拦截器的形式实现，在 SELECT 语句执行前自动追加 WHERE 条件
2. WHEN Current_User 对目标业务表存在 Data_Scope_Rule 时，THE Data_Scope_Interceptor SHALL 将对应的过滤条件以参数化查询（绑定变量）的方式追加到 SQL WHERE 子句
3. WHEN Current_User 对目标业务表不存在任何 Data_Scope_Rule 时，THE Data_Scope_Interceptor SHALL 返回 HTTP 403 错误，响应体包含明确错误信息"未配置数据范围规则，请联系管理员"，并写入审计日志
4. THE Data_Scope_Interceptor SHALL 仅对标记了 `@data_scope` 装饰器的路由或查询生效，未标记的查询不受影响
5. THE Data_Scope_Interceptor SHALL 使用参数化查询防止 SQL 注入，custom_condition 中的值 SHALL 作为绑定参数传递
6. IF Data_Scope_Interceptor 在解析 custom_condition 时遇到不合法的表达式，THEN THE Data_Scope_Interceptor SHALL 拒绝该查询并返回 HTTP 403 错误，同时写入审计日志
7. WHEN Current_User 的 dept_id 为 NULL 且目标业务表存在 `dept` 类型的 Data_Scope_Rule 时，THE Data_Scope_Interceptor SHALL 返回空结果集，并写入警告日志记录"用户未分配部门，dept 类型规则返回空结果"

### 需求 4：列级脱敏序列化器

**用户故事：** 作为开发者，我希望列级脱敏能在 API 响应阶段自动执行，以便业务代码无需关心脱敏逻辑。

#### 验收标准

1. THE Column_Mask_Serializer SHALL 在 FastAPI 响应序列化阶段（response_model 处理后）对匹配的字段执行脱敏
2. WHEN 目标字段匹配 Column_Mask_Rule 且策略为 `mask` 时，THE Column_Mask_Serializer SHALL 按 mask_pattern 替换字段值中的敏感部分
3. WHEN 目标字段匹配 Column_Mask_Rule 且策略为 `hide` 时，THE Column_Mask_Serializer SHALL 从响应 JSON 中移除该字段
4. THE Column_Mask_Serializer SHALL 提供内置脱敏模式：手机号（保留前3后4位）、身份证号（保留前3后4位）、邮箱（用户名部分遮蔽）
5. THE Column_Mask_Serializer SHALL 以 FastAPI 中间件或响应钩子的形式实现，业务路由代码无需修改
6. IF Column_Mask_Serializer 处理过程中发生异常，THEN THE Column_Mask_Serializer SHALL 对该字段执行最严格策略（hide），并写入错误日志

### 需求 5：数据权限管理 API

**用户故事：** 作为系统管理员，我希望通过管理界面配置数据范围规则和列级脱敏规则，以便灵活调整不同用户和角色的数据可见性。

#### 验收标准

1. THE Scope_Admin_API SHALL 提供 Data_Scope_Rule 的 CRUD 接口：创建、查询列表（按用户筛选）、更新、删除
2. THE Scope_Admin_API SHALL 提供 Column_Mask_Rule 的 CRUD 接口：创建、查询列表（按角色筛选）、更新、删除
3. WHEN 创建或更新 Data_Scope_Rule 时，THE Scope_Admin_API SHALL 验证 table_name 是否存在于 Business_Table_Registry 中
4. WHEN 创建或更新 Column_Mask_Rule 时，THE Scope_Admin_API SHALL 验证 column_name 是否存在于 Business_Table_Registry 中指定 table_name 的列定义中
5. THE Scope_Admin_API SHALL 要求调用者拥有 `data_scope:write` 权限才能执行创建、更新、删除操作
6. THE Scope_Admin_API SHALL 要求调用者拥有 `data_scope:read` 权限才能执行查询操作
7. WHEN Data_Scope_Rule 或 Column_Mask_Rule 被创建、更新或删除时，THE Scope_Admin_API SHALL 写入审计日志，记录操作者、操作类型和规则内容
8. WHEN 删除 Data_Scope_Rule 时，IF 该规则是用户对该业务表的最后一条规则，THEN THE Scope_Admin_API SHALL 返回警告信息"删除后该用户将无法访问此表数据"，并要求前端二次确认
9. THE Scope_Admin_API SHALL 提供 `GET /data-scope/tables` 端点，返回 Business_Table_Registry 中所有已注册的业务表名及其列定义，供前端下拉选择器使用


### 需求 5.1：业务表注册机制

**用户故事：** 作为开发者，我希望系统维护一份可配置数据权限的业务表白名单，以便管理员只能对已注册的表和列配置规则，防止配置错误。

#### 验收标准

1. THE Business_Table_Registry SHALL 以配置文件（YAML 或 Python 模块）的形式维护，包含业务表名、列名列表、列数据类型
2. THE Business_Table_Registry SHALL 在应用启动时加载到内存中，供 Scope_Admin_API 和 Data_Scope_Interceptor 使用
3. WHEN Business_Table_Registry 中未注册某张表时，THE Scope_Admin_API SHALL 拒绝为该表创建任何数据权限规则
4. THE Business_Table_Registry SHALL 支持通过 SQLAlchemy 模型元数据自动发现已注册的 ORM 模型及其列定义
5. WHEN Business_Table_Registry 中某张业务表配置为支持 `self` 类型规则时，THE Business_Table_Registry SHALL 要求该表包含 `created_by` 列；不包含 `created_by` 列的表 SHALL 不允许配置 `self` 类型的 Data_Scope_Rule

### 需求 5.2：紧急熔断开关

**用户故事：** 作为系统运维人员，我希望在发现数据泄露或规则配置错误时，能一键禁用所有数据范围规则，快速回退到无过滤状态。

#### 验收标准

1. THE Scope_Circuit_Breaker SHALL 提供 `POST /data-scope/circuit-breaker` 端点，接受 `enabled: bool` 参数，控制全局数据范围规则的启用/禁用状态
2. WHEN Scope_Circuit_Breaker 设置为禁用时，THE Data_Scope_Interceptor SHALL 跳过所有行级过滤，等同于所有用户拥有 `all` 权限
3. WHEN Scope_Circuit_Breaker 设置为禁用时，THE Column_Mask_Serializer SHALL 跳过所有列级脱敏，返回原始数据
4. THE Scope_Circuit_Breaker 状态变更 SHALL 写入审计日志，记录操作者和变更前后状态
5. THE Scope_Circuit_Breaker SHALL 要求调用者拥有独立权限 `data_scope:circuit_breaker`
6. THE Scope_Circuit_Breaker SHALL 支持可选的 `auto_recover_minutes` 参数（如 30 分钟），设置后 SHALL 在指定时长后自动重新启用数据范围规则；未设置时 SHALL 保持手动恢复模式
7. WHILE Scope_Circuit_Breaker 处于禁用状态时，THE Scope_Circuit_Breaker SHALL 每 5 分钟写入一条审计日志提醒，记录"数据权限熔断开关仍处于禁用状态，已持续 N 分钟"
8. WHILE Scope_Circuit_Breaker 处于禁用状态时，THE Data_Scope_Interceptor SHALL 在 API 响应的 HTTP Header 中添加 `X-Data-Scope: bypassed` 标记

### 需求 6：数据权限缓存与失效

**用户故事：** 作为系统运维人员，我希望数据权限规则能被高效缓存，以便不会因为每次查询都读取规则表而影响系统性能。

#### 验收标准

1. THE Data_Scope_Interceptor 和 Column_Mask_Serializer SHALL 使用 Redis 作为集中缓存存储，确保多 worker 部署下缓存一致性
2. THE Data_Scope_Interceptor SHALL 在首次加载用户的 Data_Scope_Rule 后将规则缓存到 Redis，后续查询从 Redis 读取
3. THE Column_Mask_Serializer SHALL 在首次加载用户角色的 Column_Mask_Rule 后将规则缓存到 Redis，后续查询从 Redis 读取
4. WHEN Data_Scope_Rule 通过 Scope_Admin_API 被修改时，THE Scope_Admin_API SHALL 清除 Redis 中受影响用户的数据范围规则缓存键；WHEN Column_Mask_Rule 通过 Scope_Admin_API 被修改时，THE Scope_Admin_API SHALL 清除该角色关联的所有用户的脱敏规则缓存键
5. THE Data_Scope_Interceptor 和 Column_Mask_Serializer SHALL 支持通过配置项设置缓存 TTL（生存时间），默认值为 300 秒
6. IF Redis 缓存不可用，THEN THE Data_Scope_Interceptor SHALL 回退到直接查询数据库获取规则，并写入警告日志

### 需求 7：数据权限与现有 RBAC 集成

**用户故事：** 作为系统管理员，我希望数据权限功能与现有的角色权限体系无缝集成，以便在同一管理界面中统一管理功能权限和数据权限。

#### 验收标准

1. THE Permission 表 SHALL 新增 `data_scope:read`、`data_scope:write` 和 `data_scope:circuit_breaker` 三条权限种子数据
2. THE Data_Scope_Interceptor SHALL 在 `require_permission` 中间件之后执行，确保用户已通过功能权限校验
3. WHEN 用户的角色被修改时，THE Column_Mask_Serializer SHALL 在下一次请求时使用更新后的角色对应的脱敏规则
4. THE TokenPayload SHALL 保持现有结构不变，数据范围规则通过数据库查询获取而非存储在 JWT 中
5. WHILE 用户同时拥有功能权限和数据范围规则时，THE Data_Scope_Interceptor SHALL 先验证功能权限（HTTP 403），再应用数据范围过滤（缩小结果集）

### 需求 8：前端数据权限管理界面

**用户故事：** 作为系统管理员，我希望在管理后台中有专门的页面来配置数据范围规则和列级脱敏规则，以便直观地管理数据权限。

#### 验收标准

1. THE 前端管理界面 SHALL 提供"数据权限"导航菜单项，包含"行级规则"和"列级规则"两个子页面
2. WHEN 管理员进入"行级规则"页面时，THE 前端管理界面 SHALL 展示 Data_Scope_Rule 列表，支持按用户筛选
3. WHEN 管理员进入"列级规则"页面时，THE 前端管理界面 SHALL 展示 Column_Mask_Rule 列表，支持按角色筛选
4. THE 前端管理界面 SHALL 提供表单用于创建和编辑 Data_Scope_Rule，table_name 和 column_name 通过下拉选择器从 Business_Table_Registry 获取，scope_type 为 `custom` 时显示自定义条件输入框
5. THE 前端管理界面 SHALL 提供表单用于创建和编辑 Column_Mask_Rule，table_name 和 column_name 通过下拉选择器获取，mask_strategy 为 `mask` 时显示脱敏模式选择器（手机号、身份证、邮箱、自定义）
6. THE 前端管理界面 SHALL 仅对拥有 `data_scope:read` 权限的用户显示"数据权限"菜单项
7. THE 前端管理界面 SHALL 仅对拥有 `data_scope:write` 权限的用户启用创建、编辑、删除按钮
8. WHEN 管理员删除一条行级规则且该规则是用户对该表的最后一条规则时，THE 前端管理界面 SHALL 显示二次确认弹窗，提示"删除后该用户将无法访问此表数据"
9. WHEN 管理员创建行级规则时检测到逻辑冲突，THE 前端管理界面 SHALL 显示警告提示说明 OR 合并后的实际效果
10. THE 前端管理界面 SHALL 提供熔断开关操作入口（仅 `data_scope:circuit_breaker` 权限可见），显示当前开关状态并支持一键切换

## 推迟项（后续迭代）

以下需求已评审确认，推迟到后续版本实现：

| 编号 | 功能 | 推迟理由 |
|------|------|----------|
| D-01 | 规则预览/模拟功能 | 需构建沙箱查询机制，开发量 2-3 天；MVP 阶段可通过审计日志间接验证 |
| D-02 | 权限审计报告导出 | 合规增强项，需设计报告模板和导出格式；短期可通过 SQL 手动出报告 |
| D-03 | 可视化条件构建器 | 前端条件编辑器组件工作量 3-5 天；MVP 用下拉选择+文本输入+运算符白名单兜底 |
| D-04 | 规则版本历史和回滚 | 需增加版本号和历史表；当前审计日志已记录变更内容，可手动恢复 |
| D-05 | 批量配置和模板机制 | 当前用户量小不需要批量操作；等用户规模增长后再投入 |
| D-06 | custom_condition 前端语法提示 | 与 D-03 可视化构建器合并到后续迭代，统一前端条件编辑体验 |
