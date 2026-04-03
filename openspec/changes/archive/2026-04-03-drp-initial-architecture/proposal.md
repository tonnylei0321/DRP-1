# Change: 穿透式资金监管平台 (DRP) 初始架构

## Why

央企资金管理目前依赖人工查询和 Excel 报表，无法满足国资委���"在线监控、事前预警、事后追溯"的硬性考核要求。本项目从零构建基于知识图谱的 SaaS 化穿透式监管平台，实现 106 项监管指标的自动化采集、语义化处理与三级穿透溯源。

## What Changes

全新项目，无存量系统。引入以下核心能力：

- 新增 **LLM 驱动的 DDL 语义映射引擎**：客户提供建表语句，LLM 自动生成 MappingSpec.yaml，置信度分级审核后编译为 RML，驱动 ETL 采集
- 新增 **知识图谱存储层**：Ontotext GraphDB + FIBO 本体 + CTIO 中国监管扩展本体，Named Graph 实现多租户隔离
- 新增 **106 项指标计算引擎**：SPARQL 存储过程每 60 分钟计算一次，SHACL 校验器自动生成 RiskEvent 实例
- 新增 **穿透式监管看板**：React + D3，Palantir 风格深色主题，混合布局（层级骨架 + 力导向展开），支持指标→实体→账户三级钻取
- 新增 **接入管理后台**：DDL 上传、映射审核、ETL 监控、用户/角色/权限/审计管理，支持 SAML 2.0 / OIDC / LDAP SSO
- 新增 **混合云部署架构**：LLM 映射和看板在云端，GraphDB 和业务数据在客户私有环境

## Capabilities

### New Capabilities

- `schema-mapping`: LLM 驱动的 DDL → MappingSpec.yaml 语义映射，置信度分级（自动生效 / 审核队列 / 告警），RML 编译器
- `etl-pipeline`: Celery 调度的全量/增量 ETL，从客户业务数据库采集原始数据，清洗后写入 GraphDB Named Graph
- `ctio-ontology`: CTIO 中国监管扩展本体定义（Classes + Properties），挂载到 FIBO，覆盖银行账户、资金归集、债务融资、票据、风险推理五大域
- `indicator-engine`: 106 项 SPARQL 指标计算（7 大业务域），Redis 缓存计算结果，SHACL 风险推理自动生成 RiskEvent
- `drill-down`: 指标→法人实体→底层账户三级穿透溯源，基于图谱路径查询
- `monitoring-dashboard`: React + D3 监管看板，Palantir 深色风格，混合布局，实时风险事件流（Redis Pub/Sub → WebSocket）
- `admin-portal`: 接入管理后台，含 SSO 认证、RBAC 权限模型、DDL 上传与映射审核工作流、ETL 任务监控、审计日志
- `multi-tenant`: Named Graph 租户隔离，查询代理层自动注入租户上下文，租户配置管理
- `hybrid-deployment`: Docker Compose 开发环境（GraphDB + PostgreSQL + Redis），生产混合云拓扑

### Modified Capabilities

（无，全新项目）

## Impact

- **技术依赖**：Ontotext GraphDB 10.x、Python 3.11+、FastAPI、Celery、React 18、D3 v7、PostgreSQL 16、Redis 7
- **外部服务**：LLM API（OpenAI / Claude / 本地模型）用于 DDL 语义分析
- **部署约束**：客户私有环境需支持 Docker；云端需 API Gateway 安全通道
- **数据主权**：业务数据和 GraphDB 留在客户私有环境，DDL 结构可上云分析
