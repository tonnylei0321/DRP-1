## 1. 基础设施与开发环境

- [x] 1.1 编写 `docker-compose.dev.yml`，包含 GraphDB 10.x、PostgreSQL 16、Redis 7 服务配置
- [x] 1.2 编写 GraphDB 初始化脚本，自动创建 Repository 并加载 FIBO 核心本体
- [x] 1.3 编写 PostgreSQL 初始化 DDL，创建 tenant、user、role、permission、audit_log、etl_job、mapping_spec 等基础表
- [x] 1.4 初始化 Python 项目结构（FastAPI + uv/poetry），配置 pyproject.toml 依赖
- [x] 1.5 初始化 React 项目结构（Vite + TypeScript），配置 D3 v7 依赖
- [x] 1.6 配置开发环境变量模板 `.env.example`

## 2. CTIO 本体构建

- [x] 2.1 编写 `ctio-core.ttl`，定义 8 个核心扩展类（DirectLinkedAccount、InternalDepositAccount、ControlToken、CashPool、RepaymentMilestone、RiskEvent、RegulatoryIndicator、EndorsementChain）
- [x] 2.2 编写 CTIO 核心属性（isRestricted、isDirectLinked、6311Status、hasUKeyStatus、belongsToSegment、inCashPool）
- [x] 2.3 编写 106 项 `ctio:RegulatoryIndicator` 实例数据 TTL 文件，含指标 ID、业务域、目标值、阈值
- [x] 2.4 编写四大红线 SHACL 规则文件（直联率、集中率×2、结算率）
- [x] 2.5 将 CTIO TTL 加入 GraphDB 初始化脚本，验证本体加载和推理正确性

## 3. 多租户基础层

- [x] 3.1 实现 TenantRepository 接口（GraphDB Named Graph CRUD）
- [x] 3.2 实现 SPARQL 查询代理层，自动注入 `FROM NAMED <urn:tenant:{id}>` 上下文
- [x] 3.3 实现租户 CRUD API（POST /tenants、GET /tenants/{id}、DELETE /tenants/{id}）
- [x] 3.4 编写多租户隔离集成测试，验证跨租户查询拦截

## 4. 认证与权限系统（管理后台）

- [x] 4.1 实现本地账号认证（bcrypt + JWT，POST /auth/login）
- [x] 4.2 实现 SAML 2.0 SSO 接入（python3-saml，POST /auth/saml/callback）
- [x] 4.3 实现 OIDC 接入（authlib，GET /auth/oidc/callback）
- [x] 4.4 实现 LDAP/AD 认证（ldap3，作为降级兜底）
- [x] 4.5 实现 RBAC 数据模型（User、Group、Role、Permission 四层）
- [x] 4.6 实现权限中间件（FastAPI Depends，API 级别鉴权）
- [x] 4.7 实现密码安全策略（复杂度校验、过期提醒、连续失败锁定）
- [x] 4.8 实现审计日志写入（所有认证事件、权限变更、越权尝试）

## 5. LLM 语义映射引擎

- [x] 5.1 实现 DDL 解析器（支持 MySQL/PostgreSQL/Oracle DDL 语法，提取表/字段/类型/注释）
- [x] 5.2 实现 LLM 映射服务（调用 LLM API，输入 DDL + CTIO 本体上下文，输出字段映射建议）
- [x] 5.3 实现置信度评分算法（字段名语义、注释质量、值域推断、历史映射匹配）
- [x] 5.4 实现 MappingSpec.yaml 生成器（含 source_field、target、transform、confidence、auto_approved 字段）
- [x] 5.5 实现 MappingSpec → RML 确定性编译器
- [x] 5.6 实现历史映射存储与检索（PostgreSQL mapping_spec 表）
- [x] 5.7 实现映射 API（POST /mappings/generate、PUT /mappings/{id}/approve、PUT /mappings/{id}/reject）

## 6. ETL 管道

- [x] 6.1 配置 Celery + Redis Broker，实现任务调度基础设施
- [x] 6.2 实现全量同步任务（读源库全量 → RML 转换 → 写 Named Graph）
- [x] 6.3 实现增量同步任务（基于 updated_at 水位线，每 60 分钟触发）
- [x] 6.4 实现无时间戳表的主键哈希比对模式
- [x] 6.5 实现数据清洗模块（NULL 处理、枚举归一化、编码转换）
- [x] 6.6 实现 ETL 任务状态持久化（PostgreSQL etl_job 表）
- [x] 6.7 实现 ETL 失败重试（指数退避，最多 3 次）
- [x] 6.8 实现数据质量三维评分（空值率、延迟、格式合规率）

## 7. 指标计算引擎

- [x] 7.1 编写 7 大业务域 106 条 SPARQL 计算语句（银行账户域 001-031、资金集中域 032-041、结算域 042-068、票据域 069-078、债务融资域 079-085、决策风险域 086-097、国资委考核域 098-106）
- [x] 7.2 实现指标计算调度任务（Celery，每 60 分钟，按业务域分批执行）
- [x] 7.3 实现计算结果写回 GraphDB（更新 RegulatoryIndicator.currentValue）
- [x] 7.4 实现 Redis 缓存写入（TTL 60 分钟，Key: `kpi:{tenant_id}:{indicator_id}`）
- [x] 7.5 实现 SHACL ���险推理触发（计算完成后执行 SHACL 校验，生成 RiskEvent）
- [x] 7.6 实现 RiskEvent → Redis Pub/Sub 发布（供 WebSocket 推送）

## 8. 穿透溯源 API

- [x] 8.1 实现第一级穿透 API（GET /drill/{indicator_id}/entities，返回拉低指标的法人列表）
- [x] 8.2 实现第二级穿透 API（GET /drill/{entity_id}/accounts，返回法人下账户网络）
- [x] 8.3 实现第三级穿透 API（GET /drill/{account_id}/properties，返回账户完整 FIBO+CTIO 属性）
- [x] 8.4 实现图谱路径查询（SPARQL 属性路径，从指标到根因账户的完整链路）
- [x] 8.5 实现溯源报告生成（PDF 导出，含路径、属性和时间戳）

## 9. 管理后台前端（React）

- [x] 9.1 实现登录页（支持本地账号 + SSO 跳转）
- [x] 9.2 实现用户管理页（增删改查、角色分配）
- [x] 9.3 实现用户组管理页
- [x] 9.4 实现角色管理页（权限树配置）
- [x] 9.5 实现审计日志页（时间/用户/操作类型过滤、导出）
- [x] 9.6 实现 DDL 上传页（文件上传 + 解析结果预览）
- [x] 9.7 实现映射审核队列页（置信度展示、确认/修改/忽略操作）
- [x] 9.8 实现 ETL 任务监控页（同步历史、耗时、数据量、错误日志）
- [x] 9.9 实现租户管理页（仅平台管理员可见）
- [x] 9.10 实现数据质量面板（三维评分可视化）

## 10. 监管看板前端（React + D3）

- [x] 10.1 实现看板整体布局（Topbar + 左侧树 + 中央图谱 + 右侧检查器 + 底部 Ticker）
- [x] 10.2 实现深色主题设计系统（CSS 变量：bg/accent/warn/danger/gold）
- [x] 10.3 实现 D3 层级骨架图（集团 → 大区 → 子公司，节点按风险着色）
- [x] 10.4 实现 D3 力导向子图（点击法人节点展开账户网络）
- [x] 10.5 实现战术节点组件（圆形节点 + 呼吸光晕 + 风险状态动画）
- [x] 10.6 实现 HUD 浮窗组件（节点详情卡 + 连接线 + 角框装饰���
- [x] 10.7 实现 WebSocket 客户端（订阅风险事件流，驱动节点状态更新）
- [x] 10.8 实现底部 Ticker 组件（风险事件滚动播报）
- [x] 10.9 实现右侧检查器面板（三级穿透路径展示 + 属性详情）
- [x] 10.10 实现图层过滤器（全部 / 资金流 / 账户 / 违规节点）
- [x] 10.11 实现中英文切换

## 11. 集成测试与验证

- [x] 11.1 端到端测试：DDL 上传 → 映射生成 → ETL 同步 → 指标计算 → 看板展示
- [x] 11.2 多租户隔离测试：验证租户 A 数据不可被租户 B 查询
- [x] 11.3 穿透溯源测试：验证三级穿透路径完整性
- [x] 11.4 SHACL 风险推理测试：触发四大红线，验证 RiskEvent 生成和推送
- [x] 11.5 性能测试���106 项指标计算在 60 分钟窗口内完成
- [x] 11.6 SSO 集成测试（SAML 2.0 + OIDC）

## 12. 可观测性与监控基础设施

- [x] 12.1 集成 Prometheus + Grafana，采集 FastAPI / Celery / GraphDB / Redis / PostgreSQL 指标
- [x] 12.2 定义告警规则：ETL 失败率、SPARQL 超时率、GraphDB 堆内存、Redis 内存占用
- [x] 12.3 实现结构化日志（JSON 格式，含 tenant_id / trace_id / run_id 字段），对接 ELK 或 Loki
- [x] 12.4 实现��布式链路追踪（OpenTelemetry），覆盖 API → Celery → GraphDB 调用链
- [x] 12.5 实现健康检查端点（GET /health，含依赖组件状态）
- [x] 12.6 实现 GraphDB 查询慢日志采集（超过 10 秒的 SPARQL 记录 query plan）
- [x] 12.7 配置 WebSocket 连接数和消息延迟监控
- [x] 12.8 实现数据新鲜度告警（超过 90 分钟未完成增量同步则告警）

## 13. 灾难恢复与备份策略

- [x] 13.1 配置 GraphDB 定时备份（每日全量导出 TriG，保留 7 天）
- [x] 13.2 配置 PostgreSQL WAL 归档 + 定时 pg_dump（每日，保留 30 天）
- [x] 13.3 编写 GraphDB 命名图恢复 SOP（从备份 TriG 恢复单租户数据）
- [x] 13.4 实现 ETL 水位线持久化（run_id + last_synced_at 写入 PostgreSQL etl_job 表，支持幂等重放）
- [x] 13.5 配置 Redis 持久化（AOF 模式，防止缓存全量丢失后雪崩）
- [x] 13.6 编写混合云网络中断降级预案（私有环境缓存最后一次指标结果，看板展示"数据截至"时间戳）
- [x] 13.7 实现租户数据导出接口（支持将单租户 Named Graph 导出为 TriG 文件）
- [x] 13.8 编写 RTO/RPO 测试方案并执行验证（目标 RTO ≤ 4h，RPO ≤ 1 天）

## 14. 性能基准与容量规划

- [x] 14.1 建立性能基准测试环境（模拟 5 租户 × 1000 法人 × 10000 账户 × 106 指标）
- [x] 14.2 测量 106 项指标 SPARQL 计算总耗时，目标 < 45 分钟（含 15 分钟裕量）
- [x] 14.3 测量三级穿透 API 响应时间（P95 < 3 秒）
- [x] 14.4 测量 GraphDB 写入吞吐（全量初始化场景，100 万三元组的写入耗时）
- [x] 14.5 实施 SPARQL 查询优化（添加必��的本体索引，分析慢查询计划）
- [x] 14.6 测量 WebSocket 并发推送能力（目标 100 并发连接下延迟 < 500ms）
- [x] 14.7 测量 LLM 映射生成耗时（100 字段 DDL 的端到端映射时间）
- [x] 14.8 输出容量规划文档（单节点 GraphDB 支撑租户上限估算）

## 15. 安全加固与合规检查

- [x] 15.1 配置 GraphDB 仓库级 ACL（每个租户 Named Graph 绑定独立服务账号，禁止跨图读写）
- [x] 15.2 限制 GraphDB 端口（7200）仅在内部网络可访问，禁止公网暴露
- [x] 15.3 实现 SPARQL 注入防护（查询代理层对 SPARQL 语句做结构化解析，拒绝 UPDATE/DROP/CLEAR 操作）
- [x] 15.4 配置 API 请求频率限制（Redis 令牌桶，租户级别）
- [x] 15.5 实现 LLM API 调用内容过滤（确保 DDL 中不含业务数据后再上传）
- [x] 15.6 配置 mTLS 证书轮换机制（混合云网络通道的证书有效期 ≤ 90 天）
- [x] 15.7 执行 OWASP Top 10 安全扫描（含 SQL 注入、XSS、CSRF、越权访问）
- [x] 15.8 输出安全合规检查报告（满足等保 2.0 三级要求的对应清单）
