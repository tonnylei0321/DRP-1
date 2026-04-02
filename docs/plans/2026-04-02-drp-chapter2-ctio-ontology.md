# DRP 第2章：CTIO 本体构建 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 CTIO（China Treasury Intelligence Ontology）本体，包括 8 个核心扩展类、6 个核心属性、106 项监管指标实例和四大红线 SHACL 规则，并加载到 GraphDB，验证本体推理与 SHACL 校验正确性。

**Architecture:** 所有 TTL 文件放在 `infra/graphdb/ontology/` 目录；CTIO 通过 `rdfs:subClassOf` 挂载到 FIBO（不修改 FIBO 文件）；106 项指标分 7 个业务域 TTL 文件存储；SHACL 规则独立文件；GraphDB 初始化脚本追加加载逻辑；Python 测试通过 GraphDB REST API 验证 SPARQL 查询结果。

**Tech Stack:** Turtle (TTL) 1.1, SPARQL 1.1, SHACL (W3C), Ontotext GraphDB 10.7.0, Python 3.11 + httpx (测试)

---

## 文件结构

```
infra/graphdb/ontology/
├── ctio-core.ttl               # Task 1: 8个核心类 + 6个核心属性
├── ctio-indicators.ttl         # Task 2: 106项指标实例（全部合并一个文件）
├── ctio-shacl.ttl              # Task 3: 四大红线 SHACL 规则
                                # （每个 TTL 文件含独立前缀声明，无需单独命名空间文件）

infra/graphdb/init/
└── 01-create-repo.sh           # Task 4: 追加 CTIO 加载逻辑（修改现有文件）

backend/tests/
└── test_ctio_ontology.py       # Task 4+5: GraphDB 集成测试
```

---

## Task 1: CTIO 核心类与属性 (ctio-core.ttl)

**Files:**
- Create: `infra/graphdb/ontology/ctio-core.ttl`

- [ ] **Step 1: 创建 ontology 目录**

```bash
mkdir -p /Users/leitao/Documents/Cursor-workspace/Demo8/DRP-1/infra/graphdb/ontology
```

- [ ] **Step 2: 编写 `infra/graphdb/ontology/ctio-core.ttl`**

```turtle
# CTIO — China Treasury Intelligence Ontology
# 版本: 1.0.0  基于 FIBO 最小裁剪集扩展（见 design.md 决策6、决策12）
# IRI 约定: https://drp.example.com/ontology/ctio/

@prefix ctio:      <https://drp.example.com/ontology/ctio/> .
@prefix owl:       <http://www.w3.org/2002/07/owl#> .
@prefix rdf:       <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:      <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:       <http://www.w3.org/2001/XMLSchema#> .
@prefix skos:      <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms:   <http://purl.org/dc/terms/> .

# ── FIBO 最小裁剪集前缀（FIBO 未加载时，类仍可作为 IRI 引用）──
@prefix fibo-fbc-fas-fca: <https://spec.edmcouncil.org/fibo/ontology/FBC/FunctionalEntities/FinancialServicesEntities/> .
@prefix fibo-be-le-lp:    <https://spec.edmcouncil.org/fibo/ontology/BE/LegalEntities/LegalPersons/> .
@prefix fibo-fnd-acc-cur: <https://spec.edmcouncil.org/fibo/ontology/FND/Accounting/CurrencyAmount/> .

# ══════════════════════════════════════════════
# 本体元数据
# ══════════════════════════════════════════════

ctio: a owl:Ontology ;
    dcterms:title "China Treasury Intelligence Ontology" ;
    dcterms:description "面向中国央企资金监管的 FIBO 扩展本体，覆盖银企直联、资金池、6311还款、SHACL风险推理等中国特色监管语义。" ;
    owl:versionInfo "1.0.0" ;
    dcterms:created "2026-04-02"^^xsd:date .

# ══════════════════════════════════════════════
# 核心扩展类（共8个，全部通过 rdfs:subClassOf 挂载到 FIBO）
# ══════════════════════════════════════════════

# 1. 银企直联账户（可通过 API 实时取数的账户）
ctio:DirectLinkedAccount a owl:Class ;
    rdfs:subClassOf fibo-fbc-fas-fca:DepositAccount ;
    rdfs:label "银企直联账户"@zh , "Direct Linked Account"@en ;
    skos:definition "通过银企直联系统与企业 ERP/TMS 实时对接的银行账户，可获取实时余额和交易流水。" ;
    rdfs:comment "指标计算中：直联账户数/总账户数 = 账户直联率，目标 ≥95%。" .

# 2. 内部存款账户（集团内部资金归集账户）
ctio:InternalDepositAccount a owl:Class ;
    rdfs:subClassOf fibo-fbc-fas-fca:DepositAccount ;
    rdfs:label "内部存款账户"@zh , "Internal Deposit Account"@en ;
    skos:definition "用于集团内部资金归集和调拨的银行存款账户，通常为资金池的成员账户。" .

# 3. 结算安全介质（U-Key 或印鉴管理��
ctio:ControlToken a owl:Class ;
    rdfs:subClassOf owl:Thing ;
    rdfs:label "结算安全介质"@zh , "Control Token"@en ;
    skos:definition "用于授权银行账户结算操作的安全介质，包括 U-Key（USB密钥）和印鉴（印章/签章）。" ;
    rdfs:comment "SHACL 规则：结算直联率 = 持有 U-Key 且直联的账户数/总结算账户数，目标 ≥95%。" .

# 4. 资金池（集团资金归集结构）
ctio:CashPool a owl:Class ;
    rdfs:subClassOf owl:Thing ;
    rdfs:label "资金池"@zh , "Cash Pool"@en ;
    skos:definition "集团资金归集管理结构，包含一个主账户（归集账户）和多个成员账户，支持实体资金池和虚拟资金池两种模式。" .

# 5. 6311还款里程碑（债务偿还状态机）
ctio:RepaymentMilestone a owl:Class ;
    rdfs:subClassOf owl:Thing ;
    rdfs:label "6311还款里程碑"@zh , "6311 Repayment Milestone"@en ;
    skos:definition "国资委6311政策要求的债务偿还里程碑节点，定义了从还款计划制定到账户清零的四个状态阶段。" ;
    rdfs:comment "状态机: PlanDefined → FundingSourced → CashReserved → AccountCleared" .

# 6. 风险事件（SHACL推理产物）
ctio:RiskEvent a owl:Class ;
    rdfs:subClassOf owl:Thing ;
    rdfs:label "风险事件"@zh , "Risk Event"@en ;
    skos:definition "由 SHACL 校验器在监管指标违规时自动生成的风险事件实例，包含严重等级、触发原因和关联实体信息。" .

# 7. 监管指标（国资委106项指标本体实例）
ctio:RegulatoryIndicator a owl:Class ;
    rdfs:subClassOf owl:Thing ;
    rdfs:label "监管指标"@zh , "Regulatory Indicator"@en ;
    skos:definition "国资委发布的资金监管指标，以本体实例形式存储在图谱中，支持从指标节点出发的三级穿透溯源。" ;
    rdfs:comment "存储在图谱而非关系库（见 design.md 决策5），确保穿透路径不断裂。" .

# 8. 票据背书链
ctio:EndorsementChain a owl:Class ;
    rdfs:subClassOf owl:Thing ;
    rdfs:label "票据背书链"@zh , "Endorsement Chain"@en ;
    skos:definition "记录票据从出票到到期全生命周期背书转让路径的有序链式结构。" ;
    rdfs:comment "SHACL 校验：背书链最大深度50，超过20层触发 WARN 级别 RiskEvent。" .

# ══════════════════════════════════════════════
# 核心扩展属性（共6个）
# ══════════════════════════════════════════════

# 1. 账户受限标志（冻结/质押/共管）
ctio:isRestricted a owl:DatatypeProperty ;
    rdfs:domain fibo-fbc-fas-fca:DepositAccount ;
    rdfs:range  xsd:boolean ;
    rdfs:label  "受限标志"@zh , "Is Restricted"@en ;
    skos:definition "标识账户是否处于冻结、质押或共管等受限状态。受限账户余额不计入可归集集中率分母。" .

# 2. 银企直联标志
ctio:isDirectLinked a owl:DatatypeProperty ;
    rdfs:domain fibo-fbc-fas-fca:DepositAccount ;
    rdfs:range  xsd:boolean ;
    rdfs:label  "直联标志"@zh , "Is Direct Linked"@en ;
    skos:definition "标识账户是否已接入银企直联系统，可实时获取余额和流水。" .

# 3. 6311还款状态（枚举）
# 注意: 属性名以 repaymentStatus6311 命名，避免 Turtle PN_LOCAL 不允许数字开头的限制
ctio:repaymentStatus6311 a owl:DatatypeProperty ;
    rdfs:domain ctio:RepaymentMilestone ;
    rdfs:range  xsd:string ;
    rdfs:label  "6311还款状态"@zh , "6311 Repayment Status"@en ;
    skos:definition "6311还款里程碑的当前状态。合法值：PlanDefined | FundingSourced | CashReserved | AccountCleared" ;
    rdfs:comment "SHACL 约束：值必须在上述四个合法枚举中，否则生成违规报告。" .

# 4. U-Key 状态
ctio:hasUKeyStatus a owl:ObjectProperty ;
    rdfs:domain fibo-fbc-fas-fca:DepositAccount ;
    rdfs:range  ctio:ControlToken ;
    rdfs:label  "U-Key状态"@zh , "Has UKey Status"@en ;
    skos:definition "账户关联的 U-Key（USB密钥）安全介质状态，用于结算直联率计算。" .

# 5. 归属细分（法人分部归属）
ctio:belongsToSegment a owl:ObjectProperty ;
    rdfs:domain fibo-fbc-fas-fca:DepositAccount ;
    rdfs:range  fibo-be-le-lp:LegalPerson ;
    rdfs:label  "归属细分"@zh , "Belongs To Segment"@en ;
    skos:definition "账户所属的法人实体或业务细分单元，用于集团穿透监管中的归属定位。" .

# 6. 资金池归属
ctio:inCashPool a owl:ObjectProperty ;
    rdfs:domain ctio:InternalDepositAccount ;
    rdfs:range  ctio:CashPool ;
    rdfs:label  "资金池归属"@zh , "In Cash Pool"@en ;
    skos:definition "标识内部存款账户所属的资金池归集结构。" .

# ══════════════════════════════════════════════
# RiskEvent 属性（用于 SHACL 生成事件实例）
# ══════════════════════════════════════════════

ctio:riskLevel a owl:DatatypeProperty ;
    rdfs:domain ctio:RiskEvent ;
    rdfs:range  xsd:string ;
    rdfs:label  "风险等级"@zh ;
    rdfs:comment "合法值：CRITICAL | WARN | INFO" .

ctio:riskDescription a owl:DatatypeProperty ;
    rdfs:domain ctio:RiskEvent ;
    rdfs:range  xsd:string ;
    rdfs:label  "风险描述"@zh .

ctio:triggeredAt a owl:DatatypeProperty ;
    rdfs:domain ctio:RiskEvent ;
    rdfs:range  xsd:dateTime ;
    rdfs:label  "触发时间"@zh .

ctio:triggeredByRun a owl:DatatypeProperty ;
    rdfs:domain ctio:RiskEvent ;
    rdfs:range  xsd:string ;
    rdfs:label  "触发批次"@zh ;
    rdfs:comment "关联到 etl_job.run_id，见 design.md 决策13" .

ctio:asOfTime a owl:DatatypeProperty ;
    rdfs:domain ctio:RiskEvent ;
    rdfs:range  xsd:dateTime ;
    rdfs:label  "数据快照时间"@zh .

ctio:evidenceValue a owl:DatatypeProperty ;
    rdfs:domain ctio:RiskEvent ;
    rdfs:range  xsd:decimal ;
    rdfs:label  "违规时指标值"@zh .

ctio:thresholdValue a owl:DatatypeProperty ;
    rdfs:domain ctio:RiskEvent ;
    rdfs:range  xsd:decimal ;
    rdfs:label  "对应阈值"@zh .

ctio:affectedIndicator a owl:ObjectProperty ;
    rdfs:domain ctio:RiskEvent ;
    rdfs:range  ctio:RegulatoryIndicator ;
    rdfs:label  "关联指标"@zh .

# ══════════════════════════════════════════════
# RegulatoryIndicator 属性
# ══════════════════════════════════════════════

ctio:indicatorId a owl:DatatypeProperty ;
    rdfs:domain ctio:RegulatoryIndicator ;
    rdfs:range  xsd:string ;
    rdfs:label  "指标编号"@zh .

ctio:indicatorName a owl:DatatypeProperty ;
    rdfs:domain ctio:RegulatoryIndicator ;
    rdfs:range  xsd:string ;
    rdfs:label  "指标名称"@zh .

ctio:businessDomain a owl:DatatypeProperty ;
    rdfs:domain ctio:RegulatoryIndicator ;
    rdfs:range  xsd:string ;
    rdfs:label  "业务域"@zh ;
    rdfs:comment "合法值：银行账户监管域|资金集中监管域|结算监管域|票据监管域|债务融资监管域|决策风险域|国资委考核域" .

ctio:targetValue a owl:DatatypeProperty ;
    rdfs:domain ctio:RegulatoryIndicator ;
    rdfs:range  xsd:decimal ;
    rdfs:label  "目标值"@zh .

ctio:warnThreshold a owl:DatatypeProperty ;
    rdfs:domain ctio:RegulatoryIndicator ;
    rdfs:range  xsd:decimal ;
    rdfs:label  "预警阈值"@zh .

ctio:currentValue a owl:DatatypeProperty ;
    rdfs:domain ctio:RegulatoryIndicator ;
    rdfs:range  xsd:decimal ;
    rdfs:label  "当前计算值"@zh .

ctio:lastCalculatedAt a owl:DatatypeProperty ;
    rdfs:domain ctio:RegulatoryIndicator ;
    rdfs:range  xsd:dateTime ;
    rdfs:label  "最近计算时间"@zh .

ctio:calculationStatus a owl:DatatypeProperty ;
    rdfs:domain ctio:RegulatoryIndicator ;
    rdfs:range  xsd:string ;
    rdfs:label  "计算状态"@zh ;
    rdfs:comment "合法值：OK | COMPUTATION_ERROR | DATA_INCOMPLETE | PARTIAL_REFRESH" .

ctio:sparqlRef a owl:DatatypeProperty ;
    rdfs:domain ctio:RegulatoryIndicator ;
    rdfs:range  xsd:string ;
    rdfs:label  "SPARQL查询引用"@zh ;
    rdfs:comment "关联到指标计算引擎中对应的 SPARQL 语句 ID" .

ctio:dataQualityIssue a owl:DatatypeProperty ;
    rdfs:domain owl:Thing ;
    rdfs:range  xsd:boolean ;
    rdfs:label  "数据质量问题"@zh ;
    rdfs:comment "ETL 写入后 SHACL 完整性校验失败时标记为 true" .

```

**验证命令:**
```bash
rapper -i turtle infra/graphdb/ontology/ctio-core.ttl 2>&1 | tail -3
# 预期: N-Triples 输出中有 50+ 三元组，无解析错误
```

---

## Task 2: 106项监管指标实例 (ctio-indicators.ttl)

**Files:**
- Create: `infra/graphdb/ontology/ctio-indicators.ttl`

- [ ] **Step 3: 编写 `infra/graphdb/ontology/ctio-indicators.ttl`**

106项指标按7个业务域分组，每个实例包含指标编号、名称、业务域、目标值和预警阈值。四大红线指标标注 `rdfs:comment "红线指标"@zh`。

```turtle
# CTIO — 106项监管指标实例
# 版本: 1.0.0  指标编号规则: IND-{域代码}-{序号3位}
# 域代码: BA=银行账户 CC=资金集中 ST=结算 BL=票据 DF=债务融资 DR=决策风险 SA=国资委考核

@prefix ctio:  <https://drp.example.com/ontology/ctio/> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .

# ══════════════════════════════════════════════
# 域1: 银行账户监管域（15项）
# ══════════════════════════════════════════════

ctio:IND-BA-001 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-001" ;
    ctio:indicatorName "账户开立合规率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-001" .

ctio:IND-BA-002 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-002" ;
    ctio:indicatorName "账户直联率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "0.95"^^xsd:decimal ;
    ctio:warnThreshold "0.90"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-002" ;
    rdfs:comment "红线指标：直联账户数/总账户数 ≥ 95%"@zh .

ctio:IND-BA-003 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-003" ;
    ctio:indicatorName "账户注销及时率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.95"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-003" .

ctio:IND-BA-004 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-004" ;
    ctio:indicatorName "账户余额异常检测率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-004" .

ctio:IND-BA-005 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-005" ;
    ctio:indicatorName "账户信息完整率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.99"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-005" .

ctio:IND-BA-006 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-006" ;
    ctio:indicatorName "专户专用合规率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-006" .

ctio:IND-BA-007 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-007" ;
    ctio:indicatorName "境外账户合规率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-007" .

ctio:IND-BA-008 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-008" ;
    ctio:indicatorName "账户印鉴管理合规率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-008" .

ctio:IND-BA-009 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-009" ;
    ctio:indicatorName "账户U-Key配置率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.95"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-009" .

ctio:IND-BA-010 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-010" ;
    ctio:indicatorName "账户授权层级合规率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-010" .

ctio:IND-BA-011 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-011" ;
    ctio:indicatorName "账户余额月度盘点率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-011" .

ctio:IND-BA-012 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-012" ;
    ctio:indicatorName "账户重复开立风险率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "0.00"^^xsd:decimal ;
    ctio:warnThreshold "0.01"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-012" .

ctio:IND-BA-013 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-013" ;
    ctio:indicatorName "账户开立审批合规率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-013" .

ctio:IND-BA-014 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-014" ;
    ctio:indicatorName "银行关系集中度"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "0.60"^^xsd:decimal ;
    ctio:warnThreshold "0.70"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-014" .

ctio:IND-BA-015 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-BA-015" ;
    ctio:indicatorName "账户有效使用率"@zh ;
    ctio:businessDomain "银行账户监管域" ;
    ctio:targetValue "0.95"^^xsd:decimal ;
    ctio:warnThreshold "0.90"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-BA-015" .

# ══════════════════════════════════════════════
# 域2: 资金集中监管域（15项）
# ══════════════════════════════════════════════

ctio:IND-CC-001 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-001" ;
    ctio:indicatorName "全口径资金集中率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.95"^^xsd:decimal ;
    ctio:warnThreshold "0.90"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-001" ;
    rdfs:comment "红线指标：归集账户余额/集团全部账户余额 ≥ 95%"@zh .

ctio:IND-CC-002 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-002" ;
    ctio:indicatorName "可归集资金集中率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.85"^^xsd:decimal ;
    ctio:warnThreshold "0.80"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-002" ;
    rdfs:comment "红线指标：归集账户余额/（全部账户余额−受限账户余额） ≥ 85%"@zh .

ctio:IND-CC-003 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-003" ;
    ctio:indicatorName "资金池归集效率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.90"^^xsd:decimal ;
    ctio:warnThreshold "0.85"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-003" .

ctio:IND-CC-004 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-004" ;
    ctio:indicatorName "集团内部借贷合规率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-004" .

ctio:IND-CC-005 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-005" ;
    ctio:indicatorName "资金归集计划完成率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.95"^^xsd:decimal ;
    ctio:warnThreshold "0.90"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-005" .

ctio:IND-CC-006 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-006" ;
    ctio:indicatorName "日间资金归集及时率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.95"^^xsd:decimal ;
    ctio:warnThreshold "0.90"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-006" .

ctio:IND-CC-007 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-007" ;
    ctio:indicatorName "成员单位归集率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.95"^^xsd:decimal ;
    ctio:warnThreshold "0.88"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-007" .

ctio:IND-CC-008 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-008" ;
    ctio:indicatorName "资金池利率合理性指数"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.95"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-008" .

ctio:IND-CC-009 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-009" ;
    ctio:indicatorName "跨境资金归集合规率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-009" .

ctio:IND-CC-010 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-010" ;
    ctio:indicatorName "闲置资金投资转化率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.80"^^xsd:decimal ;
    ctio:warnThreshold "0.70"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-010" .

ctio:IND-CC-011 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-011" ;
    ctio:indicatorName "资金集中度环比变化率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.00"^^xsd:decimal ;
    ctio:warnThreshold "-0.05"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-011" .

ctio:IND-CC-012 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-012" ;
    ctio:indicatorName "资金池容量利用率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.80"^^xsd:decimal ;
    ctio:warnThreshold "0.95"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-012" .

ctio:IND-CC-013 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-013" ;
    ctio:indicatorName "内部存款账户余额稳定性"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.90"^^xsd:decimal ;
    ctio:warnThreshold "0.80"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-013" .

ctio:IND-CC-014 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-014" ;
    ctio:indicatorName "资金归集覆盖率"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.95"^^xsd:decimal ;
    ctio:warnThreshold "0.90"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-014" .

ctio:IND-CC-015 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-CC-015" ;
    ctio:indicatorName "集团资金使用效率指数"@zh ;
    ctio:businessDomain "资金集中监管域" ;
    ctio:targetValue "0.85"^^xsd:decimal ;
    ctio:warnThreshold "0.75"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-CC-015" .

# ══════════════════════════════════════════════
# 域3: 结算监管域（15项）
# ══════════════════════════════════════════════

ctio:IND-ST-001 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-001" ;
    ctio:indicatorName "结算直联率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "0.95"^^xsd:decimal ;
    ctio:warnThreshold "0.90"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-001" ;
    rdfs:comment "红线指标：持有U-Key且直联的结算账户数/总结算账户数 ≥ 95%"@zh .

ctio:IND-ST-002 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-002" ;
    ctio:indicatorName "大额支付合规率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.99"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-002" .

ctio:IND-ST-003 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-003" ;
    ctio:indicatorName "支付授权及时率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "0.98"^^xsd:decimal ;
    ctio:warnThreshold "0.95"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-003" .

ctio:IND-ST-004 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-004" ;
    ctio:indicatorName "结算差错率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "0.00"^^xsd:decimal ;
    ctio:warnThreshold "0.001"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-004" .

ctio:IND-ST-005 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-005" ;
    ctio:indicatorName "跨行结算及时率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "0.99"^^xsd:decimal ;
    ctio:warnThreshold "0.95"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-005" .

ctio:IND-ST-006 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-006" ;
    ctio:indicatorName "银企直联系统在线率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "0.999"^^xsd:decimal ;
    ctio:warnThreshold "0.995"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-006" .

ctio:IND-ST-007 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-007" ;
    ctio:indicatorName "支付业务集中度"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "0.80"^^xsd:decimal ;
    ctio:warnThreshold "0.70"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-007" .

ctio:IND-ST-008 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-008" ;
    ctio:indicatorName "银企对账及时率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-008" .

ctio:IND-ST-009 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-009" ;
    ctio:indicatorName "异常交易检测率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.99"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-009" .

ctio:IND-ST-010 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-010" ;
    ctio:indicatorName "结算单据合规率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-010" .

ctio:IND-ST-011 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-011" ;
    ctio:indicatorName "电子支付比率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "0.98"^^xsd:decimal ;
    ctio:warnThreshold "0.95"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-011" .

ctio:IND-ST-012 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-012" ;
    ctio:indicatorName "支付授权链合规率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.99"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-012" .

ctio:IND-ST-013 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-013" ;
    ctio:indicatorName "结算系统可用性"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "0.999"^^xsd:decimal ;
    ctio:warnThreshold "0.995"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-013" .

ctio:IND-ST-014 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-014" ;
    ctio:indicatorName "支付风险管控率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.99"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-014" .

ctio:IND-ST-015 a ctio:RegulatoryIndicator ;
    ctio:indicatorId "IND-ST-015" ;
    ctio:indicatorName "结算业务合规审查率"@zh ;
    ctio:businessDomain "结算监管域" ;
    ctio:targetValue "1.00"^^xsd:decimal ;
    ctio:warnThreshold "0.98"^^xsd:decimal ;
    ctio:sparqlRef "SPARQL-ST-015" .

# ══════════════════════════════════════════════
# 域4: 票据监管域（15项）
# ══════════════════════════════════════════════

ctio:IND-BL-001 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-001" ; ctio:indicatorName "票据背书链深度合规率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-001" ; rdfs:comment "背书链超过20层触发WARN，超过50层为CRITICAL"@zh .
ctio:IND-BL-002 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-002" ; ctio:indicatorName "票据真实性验证率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.99"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-002" .
ctio:IND-BL-003 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-003" ; ctio:indicatorName "票据逾期率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "0.00"^^xsd:decimal ; ctio:warnThreshold "0.005"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-003" .
ctio:IND-BL-004 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-004" ; ctio:indicatorName "商票贴现合规率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-004" .
ctio:IND-BL-005 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-005" ; ctio:indicatorName "票据托管合规率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-005" .
ctio:IND-BL-006 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-006" ; ctio:indicatorName "电子票据比率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "0.95"^^xsd:decimal ; ctio:warnThreshold "0.90"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-006" .
ctio:IND-BL-007 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-007" ; ctio:indicatorName "票据信息完整率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.99"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-007" .
ctio:IND-BL-008 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-008" ; ctio:indicatorName "票据风险分散度指数"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "0.70"^^xsd:decimal ; ctio:warnThreshold "0.60"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-008" .
ctio:IND-BL-009 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-009" ; ctio:indicatorName "票据池管理效率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "0.90"^^xsd:decimal ; ctio:warnThreshold "0.80"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-009" .
ctio:IND-BL-010 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-010" ; ctio:indicatorName "关联方票据合规率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-010" .
ctio:IND-BL-011 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-011" ; ctio:indicatorName "票据保管合规率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-011" .
ctio:IND-BL-012 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-012" ; ctio:indicatorName "票据到期预警及时率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-012" .
ctio:IND-BL-013 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-013" ; ctio:indicatorName "票据背书链断裂率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "0.00"^^xsd:decimal ; ctio:warnThreshold "0.005"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-013" .
ctio:IND-BL-014 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-014" ; ctio:indicatorName "融资性票据识别率"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-014" .
ctio:IND-BL-015 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-BL-015" ; ctio:indicatorName "票据业务集中度指数"@zh ; ctio:businessDomain "票据监管域" ; ctio:targetValue "0.60"^^xsd:decimal ; ctio:warnThreshold "0.70"^^xsd:decimal ; ctio:sparqlRef "SPARQL-BL-015" .

# ══════════════════════════════════════════════
# 域5: 债务融资监管域（15项）
# ══════════════════════════════════════════════

ctio:IND-DF-001 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-001" ; ctio:indicatorName "6311还款完成率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.95"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-001" .
ctio:IND-DF-002 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-002" ; ctio:indicatorName "债务到期预警及时率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-002" .
ctio:IND-DF-003 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-003" ; ctio:indicatorName "债务融资成本合规率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-003" .
ctio:IND-DF-004 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-004" ; ctio:indicatorName "带息负债增长控制达标率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.95"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-004" .
ctio:IND-DF-005 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-005" ; ctio:indicatorName "融资计划执行率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "0.95"^^xsd:decimal ; ctio:warnThreshold "0.88"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-005" .
ctio:IND-DF-006 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-006" ; ctio:indicatorName "债务集中度指数"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "0.50"^^xsd:decimal ; ctio:warnThreshold "0.60"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-006" .
ctio:IND-DF-007 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-007" ; ctio:indicatorName "短期债务占比"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "0.30"^^xsd:decimal ; ctio:warnThreshold "0.40"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-007" .
ctio:IND-DF-008 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-008" ; ctio:indicatorName "隐性债务识别率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-008" .
ctio:IND-DF-009 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-009" ; ctio:indicatorName "担保合规率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-009" .
ctio:IND-DF-010 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-010" ; ctio:indicatorName "债务信息披露合规率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.99"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-010" .
ctio:IND-DF-011 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-011" ; ctio:indicatorName "债务对冲覆盖率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "0.80"^^xsd:decimal ; ctio:warnThreshold "0.70"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-011" .
ctio:IND-DF-012 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-012" ; ctio:indicatorName "融资渠道多元化指数"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "0.60"^^xsd:decimal ; ctio:warnThreshold "0.50"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-012" .
ctio:IND-DF-013 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-013" ; ctio:indicatorName "债务延期处置合规率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-013" .
ctio:IND-DF-014 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-014" ; ctio:indicatorName "债券发行合规率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "1.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-014" .
ctio:IND-DF-015 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DF-015" ; ctio:indicatorName "利息支付及时率"@zh ; ctio:businessDomain "债务融资监管域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "1.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DF-015" .

# ══════════════════════════════════════════════
# 域6: 决策风险域（16项）
# ══════════════════════════════════════════════

ctio:IND-DR-001 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-001" ; ctio:indicatorName "资金决策合规率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.99"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-001" .
ctio:IND-DR-002 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-002" ; ctio:indicatorName "大额资金决策审批率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "1.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-002" .
ctio:IND-DR-003 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-003" ; ctio:indicatorName "关联交易资金合规率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "1.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-003" .
ctio:IND-DR-004 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-004" ; ctio:indicatorName "对外投资资金合规率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "1.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-004" .
ctio:IND-DR-005 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-005" ; ctio:indicatorName "资金预算执行偏差率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "0.05"^^xsd:decimal ; ctio:warnThreshold "0.10"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-005" .
ctio:IND-DR-006 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-006" ; ctio:indicatorName "流动性风险指标达标率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-006" .
ctio:IND-DR-007 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-007" ; ctio:indicatorName "汇率风险对冲率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "0.80"^^xsd:decimal ; ctio:warnThreshold "0.70"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-007" .
ctio:IND-DR-008 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-008" ; ctio:indicatorName "利率风险敞口控制率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "0.80"^^xsd:decimal ; ctio:warnThreshold "0.70"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-008" .
ctio:IND-DR-009 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-009" ; ctio:indicatorName "操作风险事件发生率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "0.00"^^xsd:decimal ; ctio:warnThreshold "0.001"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-009" .
ctio:IND-DR-010 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-010" ; ctio:indicatorName "资金决策信息完整率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.99"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-010" .
ctio:IND-DR-011 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-011" ; ctio:indicatorName "投资决策合规率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "1.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-011" .
ctio:IND-DR-012 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-012" ; ctio:indicatorName "资金风险压力测试覆盖率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.95"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-012" .
ctio:IND-DR-013 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-013" ; ctio:indicatorName "紧急资金调配响应达标率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-013" .
ctio:IND-DR-014 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-014" ; ctio:indicatorName "资金风险预警响应率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-014" .
ctio:IND-DR-015 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-015" ; ctio:indicatorName "资金监管数据准确率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.99"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-015" .
ctio:IND-DR-016 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-DR-016" ; ctio:indicatorName "内部审计发现整改率"@zh ; ctio:businessDomain "决策风险域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.95"^^xsd:decimal ; ctio:sparqlRef "SPARQL-DR-016" .

# ══════════════════════════════════════════════
# 域7: 国资委考核域（15项）
# ══════════════════════════════════════════════

ctio:IND-SA-001 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-001" ; ctio:indicatorName "国资委报表提交及时率"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "1.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-001" .
ctio:IND-SA-002 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-002" ; ctio:indicatorName "资金管理评级分数"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "90.00"^^xsd:decimal ; ctio:warnThreshold "80.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-002" .
ctio:IND-SA-003 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-003" ; ctio:indicatorName "年度资金监管目标完成率"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.95"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-003" .
ctio:IND-SA-004 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-004" ; ctio:indicatorName "资金集中度年度提升幅度"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "0.02"^^xsd:decimal ; ctio:warnThreshold "0.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-004" .
ctio:IND-SA-005 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-005" ; ctio:indicatorName "监管整改落实率"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.98"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-005" .
ctio:IND-SA-006 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-006" ; ctio:indicatorName "资金管理体系建设完成率"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.90"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-006" .
ctio:IND-SA-007 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-007" ; ctio:indicatorName "信息化水平指数"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "0.90"^^xsd:decimal ; ctio:warnThreshold "0.80"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-007" .
ctio:IND-SA-008 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-008" ; ctio:indicatorName "资金风险案例发生数"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "0.00"^^xsd:decimal ; ctio:warnThreshold "1.00"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-008" .
ctio:IND-SA-009 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-009" ; ctio:indicatorName "合规培训覆盖率"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.95"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-009" .
ctio:IND-SA-010 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-010" ; ctio:indicatorName "资金管理制度更新及时率"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.95"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-010" .
ctio:IND-SA-011 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-011" ; ctio:indicatorName "子企业资金管理督导覆盖率"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "1.00"^^xsd:decimal ; ctio:warnThreshold "0.95"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-011" .
ctio:IND-SA-012 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-012" ; ctio:indicatorName "数字化转型进度指数"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "0.80"^^xsd:decimal ; ctio:warnThreshold "0.70"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-012" .
ctio:IND-SA-013 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-013" ; ctio:indicatorName "资金管理创新指数"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "0.80"^^xsd:decimal ; ctio:warnThreshold "0.60"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-013" .
ctio:IND-SA-014 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-014" ; ctio:indicatorName "ESG资金合规指数"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "0.90"^^xsd:decimal ; ctio:warnThreshold "0.80"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-014" .
ctio:IND-SA-015 a ctio:RegulatoryIndicator ; ctio:indicatorId "IND-SA-015" ; ctio:indicatorName "综合资金管理效能指数"@zh ; ctio:businessDomain "国资委考核域" ; ctio:targetValue "0.90"^^xsd:decimal ; ctio:warnThreshold "0.80"^^xsd:decimal ; ctio:sparqlRef "SPARQL-SA-015" .
```

**验证命令:**
```bash
rapper -i turtle infra/graphdb/ontology/ctio-indicators.ttl 2>&1 | grep "Triple"
# 预期: 约 630 个三元组（106 × ~6属性）
```

---

## Task 3: 四大红线 SHACL 规则 (ctio-shacl.ttl)

**Files:**
- Create: `infra/graphdb/ontology/ctio-shacl.ttl`

- [ ] **Step 4: 编写 `infra/graphdb/ontology/ctio-shacl.ttl`**

四大红线通过 `sh:sparql` 约束实现，因为比率计算需要跨多节点聚合。违规时对 `ctio:RegulatoryIndicator` 实例进行约束（`sh:targetClass`）。

```turtle
# CTIO — 四大红线 SHACL 规则
# 规则说明：
#   红线1: 账户直联率 IND-BA-002 currentValue < 0.95 → CRITICAL
#   红线2: 全口径资金集中率 IND-CC-001 currentValue < 0.95 → CRITICAL
#   红线3: 可归集资金集中率 IND-CC-002 currentValue < 0.85 → CRITICAL
#   红线4: 结算直联率 IND-ST-001 currentValue < 0.95 → CRITICAL

@prefix ctio:  <https://drp.example.com/ontology/ctio/> .
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .

# ══════════════════════════════════════════════
# 红线1: 账户直联率 ≥ 95%（IND-BA-002）
# ══════════════════════════════════════════════

ctio:AccountDirectLinkageRateShape a sh:NodeShape ;
    sh:targetClass ctio:RegulatoryIndicator ;
    sh:name "账户直联率红线校验"@zh ;
    rdfs:comment "IND-BA-002: 直联账户数/总账户数 必须 ≥ 0.95，否则生成CRITICAL风险事件。"@zh ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "红线违规：账户直联率（IND-BA-002）低于阈值 0.95，请立即提升银企直联覆盖率。"@zh ;
        sh:severity sh:Violation ;
        sh:prefixes ctio: ;
        sh:select """
            PREFIX ctio: <https://drp.example.com/ontology/ctio/>
            SELECT $this
            WHERE {
                $this ctio:indicatorId "IND-BA-002" ;
                      ctio:currentValue ?currentValue .
                FILTER (?currentValue < 0.95)
            }
        """ ;
    ] .

# ══════════════════════════════════════════════
# 红线2: 全口径资金集中率 ≥ 95%（IND-CC-001）
# ══════════════════════════════════════════════

ctio:FullScopeConcentrationRateShape a sh:NodeShape ;
    sh:targetClass ctio:RegulatoryIndicator ;
    sh:name "全口径资金集中率红线校验"@zh ;
    rdfs:comment "IND-CC-001: 归集账户余额/集团全部账户余额 必须 ≥ 0.95"@zh ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "红线违规：全口径资金集中率（IND-CC-001）低于阈值 0.95。"@zh ;
        sh:severity sh:Violation ;
        sh:prefixes ctio: ;
        sh:select """
            PREFIX ctio: <https://drp.example.com/ontology/ctio/>
            SELECT $this
            WHERE {
                $this ctio:indicatorId "IND-CC-001" ;
                      ctio:currentValue ?currentValue .
                FILTER (?currentValue < 0.95)
            }
        """ ;
    ] .

# ══════════════════════════════════════════════
# 红线3: 可归集资金集中率 ≥ 85%（IND-CC-002）
# ══════════════════════════════════════════════

ctio:PoolableConcentrationRateShape a sh:NodeShape ;
    sh:targetClass ctio:RegulatoryIndicator ;
    sh:name "可归集资金集中率红线校验"@zh ;
    rdfs:comment "IND-CC-002: 归集余额/（全部余额−受限余额） 必须 ≥ 0.85"@zh ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "红线违规：可归集资金集中率（IND-CC-002）低于阈值 0.85。"@zh ;
        sh:severity sh:Violation ;
        sh:prefixes ctio: ;
        sh:select """
            PREFIX ctio: <https://drp.example.com/ontology/ctio/>
            SELECT $this
            WHERE {
                $this ctio:indicatorId "IND-CC-002" ;
                      ctio:currentValue ?currentValue .
                FILTER (?currentValue < 0.85)
            }
        """ ;
    ] .

# ══════════════════════════════════════════════
# 红线4: 结算直联率 ≥ 95%（IND-ST-001）
# ══════════════════════════════════════════════

ctio:SettlementDirectLinkageRateShape a sh:NodeShape ;
    sh:targetClass ctio:RegulatoryIndicator ;
    sh:name "结算直联率红线校验"@zh ;
    rdfs:comment "IND-ST-001: 持U-Key且直联的结算账户数/总结算账户数 必须 ≥ 0.95"@zh ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "红线违规：结算直联率（IND-ST-001）低于阈值 0.95。"@zh ;
        sh:severity sh:Violation ;
        sh:prefixes ctio: ;
        sh:select """
            PREFIX ctio: <https://drp.example.com/ontology/ctio/>
            SELECT $this
            WHERE {
                $this ctio:indicatorId "IND-ST-001" ;
                      ctio:currentValue ?currentValue .
                FILTER (?currentValue < 0.95)
            }
        """ ;
    ] .

# ══════════════════════════════════════════════
# 6311还款状态枚举校验
# ══════════════════════════════════════════════

ctio:RepaymentStatusShape a sh:NodeShape ;
    sh:targetClass ctio:RepaymentMilestone ;
    sh:name "6311还款状态枚举校验"@zh ;
    sh:property [
        sh:path ctio:repaymentStatus6311 ;
        sh:in ("PlanDefined"^^xsd:string "FundingSourced"^^xsd:string "CashReserved"^^xsd:string "AccountCleared"^^xsd:string) ;
        sh:message "6311还款状态值非法，必须为: PlanDefined | FundingSourced | CashReserved | AccountCleared"@zh ;
        sh:severity sh:Violation ;
    ] .

# ══════════════════════════════════════════════
# 票据背书链深度警告（深度 > 20 触发 WARN）
# ══════════════════════════════════════════════

ctio:EndorsementChainDepthShape a sh:NodeShape ;
    sh:targetClass ctio:EndorsementChain ;
    sh:name "票据背书链深度校验"@zh ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "票据背书链深度超过20层，触发风险预警，请检查该链的背书节点数。"@zh ;
        sh:severity sh:Warning ;
        sh:prefixes ctio: ;
        sh:select """
            PREFIX ctio: <https://drp.example.com/ontology/ctio/>
            PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT $this (COUNT(?step) AS ?depth)
            WHERE {
                $this rdf:rest*/rdf:first ?step .
            }
            GROUP BY $this
            HAVING (COUNT(?step) > 20)
        """ ;
    ] .
```

**验证命令:**
```bash
rapper -i turtle infra/graphdb/ontology/ctio-shacl.ttl 2>&1 | tail -3
# 预期: 无解析错误，有 SHACL 三元组输出
```

---

## Task 4: 更新初始化脚本加载 CTIO 文件

**Files:**
- Modify: `infra/graphdb/init/01-create-repo.sh`

- [ ] **Step 5: 在 `01-create-repo.sh` 末尾追加 CTIO 加载逻辑**

在现有脚本的 FIBO 加载段之后，追加以下内容：

```bash
# ── 加载 CTIO 本体（核心类 + 指标实例 + SHACL 规则）──
echo "加载 CTIO 本体文件..."
CTIO_DIR="${SCRIPT_DIR}/../ontology"

for TTL_FILE in \
    "${CTIO_DIR}/ctio-core.ttl" \
    "${CTIO_DIR}/ctio-indicators.ttl" \
    "${CTIO_DIR}/ctio-shacl.ttl"
do
    if [ -f "${TTL_FILE}" ]; then
        FILENAME=$(basename "${TTL_FILE}")
        GRAPH_IRI="https://drp.example.com/graph/${FILENAME%.ttl}"
        echo "  加载 ${FILENAME} → Named Graph: ${GRAPH_IRI}"
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST \
            -H "Content-Type: application/x-turtle" \
            -H "Accept: application/json" \
            --data-binary "@${TTL_FILE}" \
            "${GRAPHDB_URL}/repositories/${REPO_ID}/statements?context=<${GRAPH_IRI}>")
        if [ "${HTTP_STATUS}" = "204" ]; then
            echo "    ✓ ${FILENAME} 加载成功"
        else
            echo "    ✗ ${FILENAME} 加载失败，HTTP ${HTTP_STATUS}"
            exit 1
        fi
    else
        echo "  警告: 文件不存在，跳过: ${TTL_FILE}"
    fi
done

echo "CTIO 本体加载完成。"
```

---

## Task 5: Python 集成测试

**Files:**
- Create: `backend/tests/test_ctio_ontology.py`

- [ ] **Step 6: 编写集成测试（需 GraphDB 运行）**

```python
"""CTIO 本体集成测试

测试策略：
- 通过 GraphDB REST API 执行 SPARQL 查询
- 验证本体类和属性可访问
- 验证106项指标全部加载
- 验证四大红线指标存在
- 跳过条件：GraphDB 未运行（标记 @pytest.mark.integration）

运行方式：
    pytest backend/tests/test_ctio_ontology.py -v -m integration
"""

import os
import pytest
import httpx

GRAPHDB_URL = os.getenv("GRAPHDB_URL", "http://localhost:7200")
REPO = os.getenv("GRAPHDB_REPOSITORY", "drp")
SPARQL_ENDPOINT = f"{GRAPHDB_URL}/repositories/{REPO}"

CTIO_PREFIX = "PREFIX ctio: <https://drp.example.com/ontology/ctio/>"


def sparql_select(query: str) -> list[dict]:
    """执行 SPARQL SELECT 查询，返回绑定列表。"""
    resp = httpx.get(
        SPARQL_ENDPOINT,
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["results"]["bindings"]


def graphdb_available() -> bool:
    """检查 GraphDB 是否可用。"""
    try:
        r = httpx.get(f"{GRAPHDB_URL}/rest/repositories", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False


skip_if_no_graphdb = pytest.mark.skipif(
    not graphdb_available(),
    reason="GraphDB 未运行，跳过集成测试"
)


@skip_if_no_graphdb
@pytest.mark.integration
def test_ctio_core_classes_exist():
    """验证8个核心 CTIO 类已加载到图谱。"""
    query = f"""
    {CTIO_PREFIX}
    SELECT (COUNT(DISTINCT ?class) AS ?count)
    WHERE {{
        VALUES ?class {{
            ctio:DirectLinkedAccount
            ctio:InternalDepositAccount
            ctio:ControlToken
            ctio:CashPool
            ctio:RepaymentMilestone
            ctio:RiskEvent
            ctio:RegulatoryIndicator
            ctio:EndorsementChain
        }}
        ?class a <http://www.w3.org/2002/07/owl#Class> .
    }}
    """
    results = sparql_select(query)
    count = int(results[0]["count"]["value"])
    assert count == 8, f"期望8个核心类，实际找到 {count} 个"


@skip_if_no_graphdb
@pytest.mark.integration
def test_indicator_total_count():
    """验证106项监管指标全部加载。"""
    query = f"""
    {CTIO_PREFIX}
    SELECT (COUNT(?ind) AS ?count)
    WHERE {{
        ?ind a ctio:RegulatoryIndicator .
    }}
    """
    results = sparql_select(query)
    count = int(results[0]["count"]["value"])
    assert count == 106, f"期望106项指标，实际找到 {count} 项"


@skip_if_no_graphdb
@pytest.mark.integration
def test_four_redline_indicators_exist():
    """验证四大红线指标存在并有目标值。"""
    redlines = ["IND-BA-002", "IND-CC-001", "IND-CC-002", "IND-ST-001"]
    for ind_id in redlines:
        query = f"""
        {CTIO_PREFIX}
        SELECT ?name ?targetValue
        WHERE {{
            ?ind ctio:indicatorId "{ind_id}" ;
                 ctio:indicatorName ?name ;
                 ctio:targetValue ?targetValue .
        }}
        """
        results = sparql_select(query)
        assert len(results) == 1, f"红线指标 {ind_id} 未找到"
        target = float(results[0]["targetValue"]["value"])
        assert target > 0, f"{ind_id} 目标值应 > 0，实际 {target}"


@skip_if_no_graphdb
@pytest.mark.integration
def test_indicators_cover_all_seven_domains():
    """验证7个业务域全部有指标。"""
    expected_domains = {
        "银行账户监管域", "资金集中监管域", "结算监管域",
        "票据监管域", "债务融资监管域", "决策风险域", "国资委考核域"
    }
    query = f"""
    {CTIO_PREFIX}
    SELECT DISTINCT ?domain
    WHERE {{
        ?ind a ctio:RegulatoryIndicator ;
             ctio:businessDomain ?domain .
    }}
    """
    results = sparql_select(query)
    found_domains = {r["domain"]["value"] for r in results}
    missing = expected_domains - found_domains
    assert not missing, f"以下业务域缺少指标: {missing}"


@skip_if_no_graphdb
@pytest.mark.integration
def test_shacl_graph_loaded():
    """验证 SHACL 图已加载（存在 SHACL NodeShape）。"""
    query = """
    PREFIX sh: <http://www.w3.org/ns/shacl#>
    SELECT (COUNT(?shape) AS ?count)
    WHERE {
        ?shape a sh:NodeShape .
    }
    """
    results = sparql_select(query)
    count = int(results[0]["count"]["value"])
    assert count >= 4, f"期望至少4个 SHACL NodeShape（四大红线），实际 {count} 个"


@skip_if_no_graphdb
@pytest.mark.integration
def test_named_graphs_exist():
    """验证 CTIO Named Graph 已创建。"""
    query = """
    SELECT DISTINCT ?graph
    WHERE {
        GRAPH ?graph { ?s ?p ?o }
        FILTER(CONTAINS(STR(?graph), "drp.example.com"))
    }
    """
    results = sparql_select(query)
    graph_iris = {r["graph"]["value"] for r in results}
    expected_graphs = {
        "https://drp.example.com/graph/ctio-core",
        "https://drp.example.com/graph/ctio-indicators",
        "https://drp.example.com/graph/ctio-shacl",
    }
    missing = expected_graphs - graph_iris
    assert not missing, f"以下 Named Graph 未找到: {missing}"
```

**运行验证:**
```bash
# 单元模式（无需 GraphDB）
cd backend && python -m pytest tests/test_ctio_ontology.py -v --collect-only

# 集成模式（需 GraphDB 运行）
cd backend && python -m pytest tests/test_ctio_ontology.py -v -m integration
```

---

## Task 6: 自检清单

- [ ] **Step 7: 对照 spec 自检**

| 检查项 | 来源 | 状态 |
|--------|------|------|
| 8个核心扩展类均有 `rdfs:subClassOf` 挂载 | design.md 决策6 | ctio-core.ttl ✓ |
| FIBO IRI 以 `@prefix` 引用，不修改 FIBO 文件 | architecture 约定 | ctio-core.ttl ✓ |
| 106项指标分7域，IND-BA/CC/ST/BL/DF/DR/SA | spec.md 指标需求 | ctio-indicators.ttl ✓ |
| 四大红线指标 IND-BA-002/CC-001/CC-002/ST-001 | spec.md 红线需求 | ctio-indicators.ttl ✓ |
| SHACL 规则使用 `sh:sparql` 约束（非简单 sh:minInclusive） | spec.md 场景3 | ctio-shacl.ttl ✓ |
| 6311状态枚举约束 4个合法值 | spec.md 指标需求 | ctio-shacl.ttl ✓ |
| TTL 文件放置在 `infra/graphdb/ontology/` | architecture 约定 | 目录结构 ✓ |
| 初始化脚本加载3个 CTIO TTL 文件 | Task 4 | 01-create-repo.sh ✓ |
| 集成测试覆盖类/指标数/域/SHACL/Named Graph | spec.md 验收标准 | test_ctio_ontology.py ✓ |
| `ctio:repaymentStatus6311` 属性名不以数字开头 | TTL 1.1 语法 | ctio-core.ttl ✓ |
| `sh:in` 枚举值带 `^^xsd:string` 类型标注 | SHACL W3C 规范 | ctio-shacl.ttl ✓ |
| `sh:message` 为静态字符串（无变量插值） | SHACL W3C 规范 | ctio-shacl.ttl ✓ |

> **已修正的已知问题（审查后修复）**：
> 1. `ctio:6311Status` → `ctio:repaymentStatus6311`（Turtle PN_LOCAL 不允许数字开头）
> 2. `sh:in` 枚举值加 `^^xsd:string` 类型（确保 GraphDB SHACL 引擎正确匹配）
> 3. `sh:message` 移除 `{$currentValue}`/`{$depth}` 占位符（SHACL 规范不支持消息插值）
> 4. 文件结构删除不存在的 `ctio-namespaces.ttl` 引用
