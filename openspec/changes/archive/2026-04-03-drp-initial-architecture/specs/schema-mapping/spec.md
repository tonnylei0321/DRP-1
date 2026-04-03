## ADDED Requirements

### Requirement: DDL 上传与解析
系统 SHALL 接受客户上传的 SQL DDL 建表语句，解析出表名、字段名、字段类型、约束和注释，作为 LLM 语义分析的输入。

#### Scenario: 成功上传并解析 DDL
- **WHEN** 实施人员通过管理后台上传 DDL 文件
- **THEN** 系统解析 DDL 并提取所有表结构信息
- **AND** 展示解析结果供实施人员确认字段列表

#### Scenario: DDL 格式不合法
- **WHEN** 上传的 DDL 包含语法错误
- **THEN** 系统返回具体错误位置和错误描述
- **AND** 不触发 LLM 映射流程

---

### Requirement: LLM 语义映射生成 MappingSpec
系统 SHALL 调用 LLM API 分析 DDL 字段语义，生成 MappingSpec.yaml 中间格式文件，每个字段映射包含目标本体属性和置信度分值。

#### Scenario: 高置信度字段自动映射
- **WHEN** LLM 分析字段语义，置信度 ≥ 80%
- **THEN** 该字段映射标记为 `auto_approved: true`
- **AND** 无需人工审核，直接进入 ETL 配置

#### Scenario: 中置信度字段进入审核队列
- **WHEN** LLM 分析字段语义，置信度在 40%–79% 之间
- **THEN** 该字段映射标记为 `auto_approved: false`
- **AND** 进入映射审核队列，等待实施人员确认

#### Scenario: 低置信度字段告警
- **WHEN** LLM 分析字段语义，置信度 < 40%
- **THEN** 该字段标记为 `unmapped`
- **AND** 系统告警实施人员，该字段不参与指标计算

---

### Requirement: MappingSpec 人工审核工作流
系统 SHALL 提供映射审核界面，实施人员可对待确认映射执行确认、修改或忽略操作。

#### Scenario: 实施人员确认映射
- **WHEN** 实施人员在审核队列中点击"确认"
- **THEN** 映射状态更新为已批准
- **AND** 该映射加入 ETL 配置生效

#### Scenario: 实施人员修改映射
- **WHEN** 实施人员修改目标本体属性或值转换规则
- **THEN** 系统保存修改后的映射，置信度标记为"人工确认"
- **AND** 修改记录写入审计日志

---

### Requirement: MappingSpec 编译为 RML
系统 SHALL 提供确定性编译器，将审核通过的 MappingSpec.yaml 编译为标准 RML 映射规则文件，供 ETL 模块使用。

#### Scenario: 编译成功
- **WHEN** 所有必要字段映射已审核通过
- **THEN** 编译器生成合法的 RML 文件
- **AND** ETL 可基于该 RML 执行数据转换

#### Scenario: 编译发现缺失映射
- **WHEN** 关键指标依赖的字段尚未完成映射
- **THEN** 编译器列出缺失映射清单
- **AND** 受影响的指标标记为"数据不完整"

---

### Requirement: 历史映射学习
系统 SHALL 记录所有人工审核决策，用于提升后续相似字段的映射置信度。

#### Scenario: 相似字段置信度提升
- **WHEN** 新租户上传的 DDL 包含与历史审核记录相似的字段
- **THEN** LLM 基于历史决策提升置信度评分
- **AND** 历史来源标注在置信度依据中

---

### Requirement: LLM 服务不可用降级
系统 SHALL 在 LLM API 不可用时提供降级机制，保障接入流程不完全中断。

#### Scenario: LLM API 超时或返回错误
- **WHEN** LLM 映射请求超时���>30 秒）或返回 5xx 错误
- **THEN** 系统自动重试最多 3 次，重试间隔指数退避
- **AND** 3 次重试均失败后，将该 DDL 任务标记为"待人工映射"
- **AND** 系统通知实施人员，提供手动输入映射的界面入口

#### Scenario: LLM 返回结构不合法
- **WHEN** LLM 返回的 MappingSpec 无法通过 JSON Schema 校验
- **THEN** 系统拒绝该映射结果，记录原始 LLM 输出到错误日志
- **AND** 该字段映射标记为置信度 0%，进入人工映射流程
- **AND** 不影响其他字段的映射处理
