## ADDED Requirements

### Requirement: 106 项指标 SPARQL 计算
系统 SHALL 通过 SPARQL 存储过程计算覆盖 7 大业务域的 106 项监管指标，每 60 分钟执行一次，结果写入 GraphDB 并缓存至 Redis。

#### Scenario: 定时触发指标计算
- **WHEN** Celery 定时任务每 60 分钟触发
- **THEN** 按业务域顺序执行 106 条 SPARQL 计算语句
- **AND** 每项指标计算结果更新到对应 `ctio:RegulatoryIndicator` 实例的 `ctio:currentValue` 属性
- **AND** 计算结果同时写入 Redis（TTL 60 分钟）

#### Scenario: 单项指标计算超时
- **WHEN** 某条 SPARQL 计算语句执行超过 30 秒
- **THEN** 记录超时告警，该指标标记为"计算异常"
- **AND** 不影响其他指标的计算

---

### Requirement: 四大监管红线实时监控
系统 SHALL 持续监控账户直联率（>95%）、全口径集中率（>95%）、可归集集中率（>85%）、结算直联率（>95%）四大红线，违规时立即触发告警。

#### Scenario: 红线指标达标
- **WHEN** 四大红线指标均满足目标值
- **THEN** 看板展示绿色状态，无预警

#### Scenario: 红线指标违规
- **WHEN** 任一红线指标低于目标值
- **THEN** 指标状态变为红色，触发 SHACL RiskEvent
- **AND** 风险事件推送到看板实时事件流
- **AND** 事件记录写入 PostgreSQL 审计表

---

### Requirement: 业务域指标分组计算
系统 SHALL 按 7 大业务域组织指标计算，支持按域过滤查询。

#### Scenario: 按域查询指标
- **WHEN** 看板用户选择"银行账户监管域"
- **THEN** 展示该域下 001–031 号指标的当前值和状态
- **AND** 支持从指标钻取到相关账户实体

---

### Requirement: 数据质量三维评分
系统 SHALL 计算每个租户的数据质量评分，包含空值率、数据延迟和格式合规率三个维度。

#### Scenario: 数据质量评分计算
- **WHEN** 每次 ETL 同步完成后
- **THEN** 系统计算空值率（NULL 字段占比）、延迟（距上次同步时间）、格式合规率
- **AND** 综合评分展示在管理后台数据质量面板

---

### Requirement: 计算轮次超时与熔断
系统 SHALL 在单轮指标计算超出时间窗口时触发熔断，保障下一轮 ETL 数据写入不被阻塞。

#### Scenario: 单轮计算总时长超出窗口
- **WHEN** 一个租户的 106 项指标计算总耗时超过 45 分钟（留 15 分钟余量）
- **THEN** 熔断器触发，停止本轮剩余指标的计算
- **AND** 已完成的指标结果写入 Redis（含部分刷新标志 `partial_refresh: true`）
- **AND** 看板展示"部分指标数据截至上一轮"的提示
- **AND** 触发性能告警，记录哪些指标未完成计算

#### Scenario: GraphDB 单次 SPARQL 超时
- **WHEN** 某条 SPARQL 计算语句执行超过 30 秒
- **THEN** GraphDB 返回查询超时异常
- **AND** 该指标标记为 `COMPUTATION_ERROR`，currentValue 保留上一次成功值
- **AND** 记录超时的 SPARQL 语句和 run_id 到慢查询日志
- **AND** 继续执行下一条指标的计算，不中断整轮

#### Scenario: 计算结果与历史值异常偏差
- **WHEN** 某指标新计算值与上次值偏差超过 30%
- **THEN** 系统标记该指标为"异常波动"，不直接覆盖历史值
- **AND** 生成 WARN ��� RiskEvent，包含新旧值和计算 run_id
- **AND** 待管理员确认后正式发布新值，或标记为数据异常
