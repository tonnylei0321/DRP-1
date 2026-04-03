# Design: 穿透式资金监管平台 (DRP) 初始架构

## Context

本项目为全新建设，无存量系统迁移包袱。目标客户为中国央企集团，数据主权要求业务数据不出私有环境。平台以 SaaS 模式服务多个央企租户，每个租户拥有异构的业务源系统（SAP/用友/金蝶/自研），需要在统一的知识图谱语义框架下完成监管指标计算和穿透溯源。

核心挑战：异构源系统语义对齐 + 多租户隔离 + 实时穿透溯源 + 企业级安全合规。

## Goals / Non-Goals

**Goals:**
- 建立端到端的知识图谱监管平台，从 DDL 接入到看板展示全流程打通
- LLM 驱动的智能接入，降低新租户上线成本
- 支持 106 项国资委监管指标的自动化计算与风险推理
- 三级穿透溯源（指标 → 法人实体 → 底层账户）
- 多租户 SaaS，数据主权满足央企合规要求

**Non-Goals:**
- 不替代客户现有业务系统（ERP/TMS）
- 不做实时交易处理（最小刷新周期 60 分钟）
- 一期不支持自然语言查询（SPARQL 路径查询已满足需求）
- 不自建 LLM 模型，调用外部 LLM API

## Decisions

### 决策 1：图数据库选型 — Ontotext GraphDB

**选择**：Ontotext GraphDB 10.x

**原因**：
- 原生 SPARQL 1.1 + SHACL 支持，L4 风险推理层的硬性依赖
- Named Graph 多租户隔离方案成熟，有生产案例
- FIBO 领域（金融/保险）最活跃的 RDF 存储
- Docker 部署契合混合云私有化需求

**备选**：Stardog（功能更强但美国公司，采购风险）、Apache Jena（开源但 SHACL 弱）

**国产化路径**：一期使用 GraphDB，预留存储抽象层（Repository 接口），未来可替换为国产方案

---

### 决策 2：LLM 映射产物格式 — MappingSpec.yaml 中间格式

**选择**：DDL → LLM → MappingSpec.yaml → 编译器 → RML

**原因**：
- RML 可读性极差，无法支撑人工审核工作流
- MappingSpec.yaml 人类可读，支持版本控制和 diff
- 编译器是确定性的（LLM 只负责语义理解，不直接生成代码）
- 审核是整个接入流程的信任锚点，产物必须可被实施人员理解

**备选**：直接生成 RML（体验差，审核困难）

---

### 决策 3：映射置信度分级 — 三档策略

**选择**：
- ≥ 80%：自动生效，直接进入 ETL
- 40–79%：进入审核队列，实施人员确认后生效
- < 40%：标记为未映射，告警实施人员，不参与指标计算

**原因**：全自动风险过高（系统性偏差），纯人工效率过低。三档平衡安全与效率，且历史审核记录可反哺置信度模型���

---

### 决策 4：多租户隔离 — Named Graph + 查询代理层

**选择**：共享 GraphDB 实例 + Named Graph 隔离 + 查询代理层自动注入租户上下文

**原因**：
- 独立实例方案运维成本随租户数线性增长
- Named Graph 隔离在 GraphDB 中有成熟的访问控制机制
- 查询代理层统一注入 `FROM NAMED <tenant-graph>` 上下文，开发者无需手写

**风险**：慢查询影响其他租户 → 缓解：GraphDB 查询超时配置 + Redis 缓存热点查询结果

---

### 决策 5：指标建模 — 进入本体（方案 P）

**选择**：106 项指标作为 `ctio:RegulatoryIndicator` 实例存储在图谱中

**原因**：
- 三级穿透的核心价值是"从指标到账户的完整图谱路径"
- 若指标定义在关系库，穿透路径需跨存储，链路断裂
- 指标本体化后，SPARQL 可直接从指标节点出发遍历到根因账户

**备选**：指标元数据存 PostgreSQL，SPARQL 只做计算（穿透链路断裂，放弃）

---

### 决策 6：CTIO 本体设计原则 — 最小化扩展

**选择**：仅扩展 FIBO 缺失的中国监管语义，通过 `rdfs:subClassOf` 挂载

**核心扩展类**：
```
ctio:DirectLinkedAccount  → 银企直联账户
ctio:InternalDepositAccount → 内部存款账户
ctio:ControlToken           → 结算安全介质(U-Key/印鉴)
ctio:CashPool               → 资金池
ctio:RepaymentMilestone     → 6311还款里程碑
ctio:RiskEvent              → SHACL生成的风险事件
ctio:RegulatoryIndicator    → 监管指标实例
ctio:EndorsementChain       → 票据背书链
```

**核心扩展属性**：
```
ctio:isRestricted    xsd:boolean  → 冻结/质押/共管标志
ctio:isDirectLinked  xsd:boolean  → 直联实时取数标志
ctio:6311Status      xsd:string   → 还款状态机(Enum)
ctio:hasUKeyStatus   → ctio:ControlToken
ctio:belongsToSegment → fibo-be-le-lp:LegalEntity
ctio:inCashPool       → ctio:CashPool
```

---

### 决策 7：前端布局 — 混合布局 C

**选择**：固定层级骨架（集团→大区→子公司）+ 点击展开力导向子图（子公司→账户网络）

**原因**：
- 纯层级树：结构清晰但缺乏空间张力，无法表达资金流关系
- 纯力导向：大规模节点布局不稳定
- 混合布局：管理层用层级视角，分析师用图谱视角，两者兼顾

**技术实现**：D3 hierarchy（骨架） + D3 forceSimulation（展开子图），React 管理状态

---

### 决策 8：DDL 上云分析（方案 X）

**选择**：DDL 结构上传云端 LLM 分析，业务数据留在私有环境

**原因**：DDL 只含字段名/类型/注释，不含业务数据，不涉及数据主权问题。上云分析体验最优，无需本地部署 LLM。

**合规边界**：客户签署数据处理协议，明确 DDL 结构数据的处理范围

---

### 决策 9：ETL 刷新周期 — 60 分钟

**选择**：增量 ETL 每 60 分钟执行一次

**原因**：监管指标本质是管理驾驶舱，T+1小时满足"在线监控"要求。5分钟刷新对原始数据库压力过大，且采集→映射→写入→计算的端到端链路在60分钟内才能可靠完成。

---

### 决策 10：认证架构 — 多协议 SSO + JWT

**选择**：支持 SAML 2.0 / OIDC / LDAP，统一颁发 JWT Token

**原因**：央企 IT 环境异构，SAML 2.0 是主流企业 SSO 协议，OIDC 用于现代云平台，LDAP 作为降级兜底。平台内部统一用 JWT，隔离外部协议差异。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| GraphDB 国产化合规压力 | 预留 Repository 抽象层，存储层可替换 |
| LLM 映射准确率不稳定 | 置信度三档分级 + 人工审核队列 + 历史映射学习 |
| SPARQL 慢查询影响多租户 | 查询超时限制 + Redis 缓存热点结果 |
| DDL 上云的合规顾虑 | 与客户签数据处理协议；预留本地 LLM 选项（方案 Z 备用） |
| 106 项指标 SPARQL 计算性能 | 分批计算 + GraphDB 集群化 + 关键指标优先级排序 |
| Named Graph 隔离被绕过 | 查询代理层强制注入，禁止直接访问 GraphDB 端口 |
| 混合云网络延迟 | 私有环境部署 API Gateway，减少云端往返 |

---

### 决策 11：GraphDB 安全边界 — 仓库级 ACL + 网络隔离

**选择**：GraphDB 仓库绑定租户专属服务账号 + 7200 端口仅内部可达 + 查询代理层拦截所有写操作

**原因**：
- Named Graph 逻辑隔离不能替代物理访问控制；若 GraphDB 端口公开，攻击者可绕过代理层直接跨租户查询
- 每个租户服务账号仅有对应 Named Graph 的读写权限，GraphDB ACL 作为纵深防御第二层
- 查询代理层强制拦截 `UPDATE / DROP / CLEAR / LOAD` 操作，防止 SPARQL 注入写入或删除三元组

**实现要点**：
- 网络层：docker-compose / K8s NetworkPolicy 限制 7200 端口访问来源
- GraphDB Security：开启 GraphDB Free/Enterprise 安全模块，每租户一个角色
- 代理层：解析 SPARQL AST，白名单只允许 SELECT / CONSTRUCT / ASK / DESCRIBE

---

### 决策 12：FIBO 加载策略 — 最小裁剪集

**选择**：只加载 FIBO 中 Banking / Corporations / LegalPersons 三个模块，不加载完整 FIBO（约 600+ 文件）

**原因**：
- 完整 FIBO 加载到 GraphDB 后推理图超过 300 万三元组，大幅影响 SPARQL 查询性能
- DRP 实际使用的 FIBO 类集中在 `fibo-fbc-fas-fca:BankAccount`、`fibo-be-le-lp:LegalEntity`、`fibo-fnd-acc-cur:MonetaryAmount` 等核心类
- 裁剪后保留约 15 个必要模块，推理基数降低 90%

**FIBO 裁剪清单**（模块前缀）：
```
fibo-fbc-fas-fca (银行账户)
fibo-be-le-lp    (法人实体)
fibo-be-le-cb    (商业银行)
fibo-fnd-acc-cur (货币金额)
fibo-fnd-rel-rel (关系属性)
fibo-fnd-dt-fd   (日期时间)
fibo-fnd-arr-cls (分类)
```

---

### 决策 13：RiskEvent 溯源模型 — 带 run_id 的事件实例

**选择**：每个 SHACL 生成的 `ctio:RiskEvent` 携带 `ctio:triggeredByRun`（关联计算批次 run_id）、`ctio:asOfTime`（计算快照时间）和 `ctio:evidencePath`（触发路径三元组列表）

**原因**：
- 监管穿透报告需要可重现性：事后审计时需要知道"在哪个计算批次、基于什么数据触发了该风险"
- run_id 关联 `etl_job` 表，可追溯到具体 ETL 批次的源数据版本
- asOfTime 使 RiskEvent 具有明确的时态语义，避免混淆"当前状态"与"历史风险"

**RiskEvent 关键属性**：
```turtle
ctio:RiskEvent
  ctio:riskLevel        xsd:string    # CRITICAL / WARN / INFO
  ctio:triggeredByRun   xsd:string    # run_id（ETL 批次）
  ctio:asOfTime         xsd:dateTime  # 计算快照时间
  ctio:affectedIndicator → ctio:RegulatoryIndicator
  ctio:affectedEntity    → fibo-be-le-lp:LegalEntity
  ctio:evidenceValue    xsd:decimal   # 违规时的指标值
  ctio:thresholdValue   xsd:decimal   # 对应阈值
```

---

### 决策 14：ETL 幂等性 — run_id + 水位线持久化

**选择**：每次 ETL 任务生成唯一 `run_id`，水位线（last_synced_at）和 run_id 写入 PostgreSQL `etl_job` 表，ETL 任务基于 run_id 幂等

**原因**：
- 增量 ETL 失败重试时，若水位线未持久化会导致数据重复写入或漏写
- run_id 关联 RiskEvent 可实现计算可重现性（给定 run_id 可重跑该批次的 SPARQL 计算）
- 幂等设计：相同 run_id 重复触发不会产生重复三元组（基于 `SPARQL UPDATE INSERT WHERE` 的 upsert 语义）

**etl_job 表关键字段**：
```sql
run_id          UUID PRIMARY KEY
tenant_id       UUID
status          ENUM(running, success, failed, retrying)
last_synced_at  TIMESTAMPTZ  -- 增量水位线
triples_written INTEGER
error_message   TEXT
started_at      TIMESTAMPTZ
finished_at     TIMESTAMPTZ
```

## Open Questions

1. **LLM 供应商**：使用 OpenAI / Claude API，还是支持客户自带本地模型（Qwen/DeepSeek）？影响映射服务的架构设计。
2. **GraphDB 集群**：一期单节点还是主从复制？取决于租户规模和 SLA 要求。
3. **CTIO 本体版本管理**：随监管政策变化，本体需要演进，版本策略待定。
4. **历史数据回溯**：ETL 是否需要支持历史数据补录？影响数据模型的时态设计。
