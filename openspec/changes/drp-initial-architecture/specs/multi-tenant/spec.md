## ADDED Requirements

### Requirement: Named Graph 租户隔离
系统 SHALL 为每个租户分配独立的 Named Graph，所有三元组写入和查询均限定在租户命名空间内，租户间数据严格隔离。

#### Scenario: 三元组写入租户 Named Graph
- **WHEN** ETL 向 GraphDB 写入数据
- **THEN** 所有三元组写入格式为 `<urn:tenant:{tenant_id}>` 的 Named Graph
- **AND** 不同租户的三元组不混合存储

#### Scenario: 跨租户查询拦截
- **WHEN** SPARQL 查询未包含租户上下文
- **THEN** 查询代理层自动注入 `FROM NAMED <urn:tenant:{tenant_id}>` 子句
- **AND** 查询结果只返回当前租户数据

---

### Requirement: 查询代理层
系统 SHALL 提供 SPARQL 查询代理层，自动注入租户上下文，防止开发者遗漏租户过滤条件。

#### Scenario: 自动注入租户上下文
- **WHEN** 业务层通过代理层发送 SPARQL 查询
- **THEN** 代理层解析查询，注入当前租户的 Named Graph 限定
- **AND** 转发到 GraphDB 执行
- **AND** 结果返回前剥除内部租户标识

---

### Requirement: 租户配置管理
系统 SHALL 支持租户的创建、配置、暂停和删除，租户元数据存储在 PostgreSQL。

#### Scenario: 创建新租户
- **WHEN** 平台管理员创建新租户
- **THEN** 系统在 GraphDB 中创建对应 Named Graph
- **AND** 在 PostgreSQL 创建租户记录和默认管理员账号
- **AND** 返回租户接入凭据

#### Scenario: 删除租户数据
- **WHEN** 平台管理员执行租户数据清除
- **THEN** 删除对应 Named Graph 内所有三元组
- **AND** 清除 PostgreSQL 中租户相关记录
- **AND** 操作记录到审计日志，需二次确认

---

### Requirement: 租户暂停与恢复
系统 SHALL 支持在不删除数据的情况下暂停租户服务，暂停期间拒绝该租户的所有 API 请求。

#### Scenario: 暂停租户服务
- **WHEN** 平台管理员将租户状态设为"暂停"
- **THEN** 该租户的所有 API 请求返回 403（含提示"租户已暂停"）
- **AND** ETL 定时任务跳过该租户
- **AND** GraphDB Named Graph 数据和 PostgreSQL 数据保留不删除

#### Scenario: 恢复租户服务
- **WHEN** 平台管理员将租户状态恢复为"活跃"
- **THEN** 该租户 API 请求恢复正常
- **AND** ETL 定时任务在下一个 60 分钟窗口自动触发增量同步
- **AND** 恢复操作记录到审计日志

---

### Requirement: 租户数据迁移
系统 SHALL 支持将租户数据从一个 GraphDB 实例迁移到另一个实例，不丢失历史数据。

#### Scenario: 租户 Named Graph 导出
- **WHEN** 平台管理员触发租户数据导出
- **THEN** 系统将该租户 Named Graph 全量导出为 TriG 格式文件
- **AND** 同步导出 PostgreSQL 中该租户的元数据（etl_job、mapping_spec 等）
- **AND** 导出文件加密压缩，提供下载链接

#### Scenario: 租户数据导入目标实例
- **WHEN** 管理员在目标 GraphDB 实例执行导入
- **THEN** Named Graph 数据完整恢复，三元组数量与源导出一致
- **AND** PostgreSQL 元数据恢复，ETL 水位线从最后一次成功同步时间继续

---

### Requirement: 周期性租户隔离验证
系统 SHALL 定期执行���动化测试，验证多租户隔离机制未被配置变更破坏。

#### Scenario: 跨租户查询拦截验证
- **WHEN** 系统执行每日隔离验证任务
- **THEN** 使用租户 A 的凭据尝试查询租户 B 的 Named Graph
- **AND** 验证系统返回空结果（而非 403，以防止信息泄露）
- **AND** 验证通过记录到安全审计日志；验证失败立即触发告警
