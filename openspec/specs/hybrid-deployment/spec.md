## ADDED Requirements

### Requirement: Docker Compose 开发环境
系统 SHALL 提供 Docker Compose 配置，一键启动包含 GraphDB、PostgreSQL 和 Redis 的完整开发环境。

#### Scenario: 启动开发环境
- **WHEN** 开发者执行 `docker compose -f docker-compose.dev.yml up -d`
- **THEN** GraphDB（端口 7200）、PostgreSQL（端口 5432）、Redis（端口 6379）全部启动就绪
- **AND** GraphDB 自动加载 FIBO + CTIO 本体
- **AND** PostgreSQL 自动执行初始化 DDL 脚本

#### Scenario: 环境重置
- **WHEN** 开发者执行 `docker compose down -v`
- **THEN** 所有容器和数据卷清除
- **AND** 重新 up 后得到干净的初始状态

---

### Requirement: 混合云生产部署拓扑
系统 SHALL 支持混合云部署：GraphDB、ETL Agent 和业务数据部署在客户私有环境，LLM 映射服务和监管看板部署在云端。

#### Scenario: 私有环境组件部署
- **WHEN** 运维人员在客户私有环境执行部署
- **THEN** GraphDB、ETL Agent、PostgreSQL（从库）、Redis（从节点）成功启动
- **AND** 私有环境通过 API Gateway 向云端暴露安全接口

#### Scenario: 云端组件访问私有数据
- **WHEN** 监管看板发起 SPARQL 查询请求
- **THEN** 请求通过加密通道转发到私有环境的查询代理层
- **AND** 查询结果返回云端，不在云端持久化原始数据

---

### Requirement: 安全通信
系统 SHALL 确保云端与私有环境之间的所有通信通过 TLS 加密，API Gateway 执行认证和访问控制。

#### Scenario: API 请求认证
- **WHEN** 云端服务向私有环境发送 API 请求
- **THEN** 请求携带有效的 mTLS 证书或 API Key
- **AND** API Gateway 验证身份后转发请求
- **AND** 未认证请求直接拒绝，记录安全日志

---

### Requirement: 云端-私有链路中断降级
系统 SHALL 在云端与私有环境通信中断时，保障看板基础展示功能可用，不出现白屏或崩溃。

#### Scenario: 私有链路完全中断
- **WHEN** 云端无法访问私有环境 API Gateway（连续 3 次心跳超时）
- **THEN** 看板切换到"离线模式"，展示最后一次成功缓存的指标数据
- **AND** 页面顶部展示橙色横幅："数据连接异常，展示数据截至 [最后刷新时间]"
- **AND** 底部 Ticker 停止实时事件流，显示"实时事件暂停"
- **AND** 后端每 30 秒执行一次重连探测

#### Scenario: 私有链路恢复
- **WHEN** 云端与私有环境链路恢复后首次心跳成功
- **THEN** 看板自动触发一次全量指标刷新
- **AND** 离线模式横幅消失，恢复正常状态
- **AND** 链路恢复事件记录到系统运维日志
