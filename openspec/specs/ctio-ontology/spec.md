## ADDED Requirements

### Requirement: CTIO 核心类定义
系统 SHALL 提供 CTIO 本体的核心扩展类，通过 `rdfs:subClassOf` 挂载到 FIBO，覆盖中国监管所需的实体语义。

#### Scenario: 加载 CTIO 本体
- **WHEN** GraphDB 初始化时加载 CTIO TTL 文件
- **THEN** 所有 CTIO 类和属性在 SPARQL 查询中可用
- **AND** CTIO 类与 FIBO 类的继承关系正确推理

#### Scenario: 账户直联属性推理
- **WHEN** 查询 `ctio:DirectLinkedAccount` 的所有实例
- **THEN** 返回所有 `ctio:isDirectLinked = true` 的银行账户
- **AND** 这些账户同时满足 `fibo-fbc-fas-fca:BankAccount` 的类约束

---

### Requirement: CTIO 核心属性定义
系统 SHALL 提供 CTIO 扩展属性，覆盖中国特有监管语义，与 FIBO 标准属性无冲突。

#### Scenario: isRestricted 参与集中率计算
- **WHEN** SPARQL 计算可归集集中率
- **THEN** 分母自动排除 `ctio:isRestricted = true` 的账户余额
- **AND** 计算结果与人工 Excel 计算结果一致

#### Scenario: 6311 状态机约束
- **WHEN** SHACL 校验器检测到 `ctio:6311Status` 值不在合法枚举集合内
- **THEN** 生成 SHACL 违规报告
- **AND** 触发 RiskEvent 实例

---

### Requirement: CTIO 监管指标实例化
系统 SHALL 将 106 项监管指标作为 `ctio:RegulatoryIndicator` 实例存储在图谱中，每项指标包含 ID、目标值、阈值、业务域和计算逻辑引用。

#### Scenario: 指标实例加载
- **WHEN** GraphDB 初始化时加载指标实例数据
- **THEN** 106 项指标均可通过 SPARQL 查询获取
- **AND** 每项指标的目标值和告警阈值可配置

#### Scenario: 指标关联根因路径
- **WHEN** 从指标节点出发执行图谱路径查询
- **THEN** 可遍历到该指标关联的法人实体
- **AND** 进一步遍历到底层账户实例

---

### Requirement: SHACL 风险规则定义
系统 SHALL 提供覆盖四大监管红线的 SHACL 约束规则，当指标偏离目标时自动生成 RiskEvent 实例。

#### Scenario: 账户直联率红线触发
- **WHEN** 某租户账户直联率 < 95%
- **THEN** SHACL 校验器生成 `ctio:RiskEvent` 实例
- **AND** RiskEvent 包含触发时间、严重等级、关联指标和违规描述

#### Scenario: 全口径集中率预警
- **WHEN** 全口径集中率 < 85%（预警阈值）
- **THEN** 生成 WARN 级别的 RiskEvent
- **AND** 推送到看板实时事件流

---

### Requirement: 票据背书链环路检测
系统 SHALL 检测票据背书链中的循环引用，防止 EndorsementChain 图形成环路导致 SPARQL 路径查询无限递归。

#### Scenario: 票据背书环路检测
- **WHEN** ETL 写入新的背书关系三元组
- **THEN** 系统执行 SPARQL 路径长度检测（最大路径深度 50）
- **AND** 若检测到环路，拒绝写入该三元组
- **AND** 生成 `ctio:RiskEvent`（riskLevel: CRITICAL，描述"背书链环路"）
- **AND** 记录冲突的背书关系到错误日志

#### Scenario: 背书链深度超限
- **WHEN** 票据背书链长度超过 20 层
- **THEN** 生成 WARN 级别 RiskEvent（描述"背书链异常深度"）
- **AND** 穿透溯源 API 在展示该链路时截断到 20 层并提示"链路过长"

---

### Requirement: 图谱一致性检查
系统 SHALL 在 ETL 完成后执行图谱完整性检查，确保 CTIO 实例满足 SHACL 约束。

#### Scenario: 每轮 ETL 后完整性校验
- **WHEN** 全量或增量 ETL 写入完成
- **THEN** 触发轻量级 SHACL 校验（仅校验本次写入的实例子集）
- **AND** 校验违规的三元组标记为 `ctio:dataQualityIssue: true`
- **AND** 违规统计写入数据质量评分，不阻塞 ETL 任务完成状态

#### Scenario: 孤立节点检测
- **WHEN** SPARQL 检测到无法通过图路径到达任何 `ctio:RegulatoryIndicator` 的账户节点
- **THEN** 标记为孤立账户，加入数据质量告警列表
- **AND** 不参与指标计算，避免污染集中率等分母数据
