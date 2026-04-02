# Spec Delta: log-alert

## ADDED Requirements

### Requirement: 日志批量摄取
系统 SHALL 提供 POST /api/logs 端点，接收批量日志并返回摄取结果。

#### Scenario: 正常摄取
- **WHEN** 客户端提交包含有效 LogEntry 列表的 LogBatchRequest
- **THEN** 返回 200，body 包含 accepted、alerts_triggered、alerts_failed

#### Scenario: 空批次
- **WHEN** 客户端提交 logs 为空数组
- **THEN** 返回 200，accepted=0，不报错

#### Scenario: 批量大小限制
- **WHEN** 客户端提交超过 1000 条日志
- **THEN** 返回 422，错误信息提示批量大小超限

#### Scenario: 无效输入 - 字段格式
- **WHEN** timestamp 格式不符或 level 不在 ERROR/WARN/INFO 内
- **THEN** 返回 422，Pydantic 校验错误

#### Scenario: 无效输入 - 结构异常
- **WHEN** 缺少 logs 字段、logs 不是数组、logs 为 null、任一必填字段缺失
- **THEN** 返回 422，Pydantic 校验错误

#### Scenario: Level 大小写标准化
- **WHEN** 客户端提交 level 为 "error"、"Error"、"ERROR"
- **THEN** 自动标准化为 "ERROR"，摄取成功

---

### Requirement: 日志统计查询
系统 SHALL 提供 GET /api/logs/stats 端点，返回累计统计数据。

#### Scenario: 统计结构稳定
- **WHEN** 调用 GET /api/logs/stats
- **THEN** by_level 使用 LogLevelStats 固定结构体，始终包含 ERROR、WARN、INFO 三个字段

#### Scenario: 无日志时初始状态
- **WHEN** 未提交任何日志时调用 GET /api/logs/stats
- **THEN** total=0，by_level 三个字段均为 0，by_service 为空对象

#### Scenario: 多服务计数
- **WHEN** 提交来自多个 service 的日志
- **THEN** by_service 各服务计数独立正确

#### Scenario: 累计统计
- **WHEN** 多次调用 POST /api/logs
- **THEN** GET /api/logs/stats 返回累计值（进程启动以来的总和）

---

### Requirement: ERROR 告警触发
系统 SHALL 对 ERROR 级别日志触发 webhook 告警，带窗口抑制机制。

#### Scenario: 窗口内抑制
- **WHEN** 同一 service 在 ALERT_WINDOW_MINUTES 内连续出现 ERROR（时间差严格小于窗口）
- **THEN** 只触发一次 webhook，后续在窗口内的 ERROR 被抑制，alerts_triggered=1

#### Scenario: 窗口边界行为
- **WHEN** 同一 service 两次 ERROR 时间差恰好等于 ALERT_WINDOW_MINUTES
- **THEN** 视为超出窗口，触发第二次告警（实现使用 >= 判断）

#### Scenario: 窗口过期重触发
- **WHEN** 同一 service 的 ERROR 时间间隔超过 ALERT_WINDOW_MINUTES
- **THEN** 再次触发 webhook，alerts_triggered 递增

#### Scenario: 跨服务独立
- **WHEN** 不同 service 同时出现 ERROR
- **THEN** 各自独立触发 webhook，互不影响

#### Scenario: 首次 ERROR
- **WHEN** 某 service 首次出现 ERROR
- **THEN** 立即触发 webhook

#### Scenario: 批量中多个相同 service 的 ERROR
- **WHEN** 单次请求中同一 service 出现多个 ERROR
- **THEN** 仅触发一次告警（窗口抑制生效）

#### Scenario: webhook 失败降级
- **WHEN** webhook 调用抛出异常
- **THEN** 日志摄取正常完成，统计正确写入，alerts_failed 计数加一，不返回 500

---

### Requirement: Webhook Payload 规范
系统 SHALL 在 webhook payload 中包含以下字段：
- alert_id: UUID v4，每次告警唯一
- alert_timestamp: 告警发送时间（UTC，格式 YYYY-MM-DD HH:MM:SS）
- log_timestamp: 日志原始时间（格式 YYYY-MM-DD HH:MM:SS）
- level: 日志级别（ERROR/WARN/INFO）
- service: 服务名
- message: 错误信息
- environment: 环境标识（读取 ENVIRONMENT 环境变量，默认 "dev"）

#### Scenario: Payload 字段完整性
- **WHEN** 触发告警
- **THEN** webhook payload 包含所有必需字段

#### Scenario: alert_id 格式
- **WHEN** 触发告警
- **THEN** alert_id 符合 UUID v4 格式

#### Scenario: environment 读取
- **WHEN** 设置 ENVIRONMENT=prod 后触发告警
- **THEN** webhook payload 中 environment="prod"

---

### Requirement: API 响应模型规范
系统 SHALL 在 OpenAPI schema 中声明：
- LogLevelStats 强类型结构体（ERROR/WARN/INFO 三个固定字段）替代 Dict[str, int]
- LogIngestResponse 包含 alerts_failed 字段
- POST /api/logs 端点显式声明 422 响应描述

#### Scenario: OpenAPI 文档生成
- **WHEN** 访问 /docs
- **THEN** LogLevelStats 显示为固定结构体，LogIngestResponse 包含 alerts_failed

---

### Requirement: CORS 安全配置
系统 SHALL 通过 ALLOWED_ORIGINS 环境变量控制跨域来源，默认仅允许 http://localhost:3000。
allow_methods 限定为 GET、POST，allow_headers 限定为 Content-Type。

#### Scenario: 默认 CORS 配置
- **WHEN** 未设置 ALLOWED_ORIGINS 环境变量
- **THEN** 仅允许 http://localhost:3000 跨域访问

#### Scenario: 自定义 CORS 配置
- **WHEN** 设置 ALLOWED_ORIGINS=["https://example.com"]
- **THEN** 仅允许 https://example.com 跨域访问

---

### Requirement: 并发安全
系统 SHALL 保证多线程并发摄取时的数据一致性。

#### Scenario: 并发统计正确性
- **WHEN** 多个线程同时调用 POST /api/logs
- **THEN** GET /api/logs/stats 返回的 total 等于所有线程提交的日志总数

#### Scenario: 并发告警窗口正确性
- **WHEN** 多个线程同时提交同一 service 的 ERROR
- **THEN** 仅触发一次告警（窗口抑制生效）

---

### Requirement: 存储层抽象
系统 SHALL 提供 StatsStore 和 AlertWindowStore 抽象接口，支持内存和 Redis 实现切换。

#### Scenario: 内存存储模式
- **WHEN** 未设置 USE_REDIS 或 USE_REDIS=false
- **THEN** 使用 MemoryStatsStore 和 MemoryAlertWindowStore

#### Scenario: Redis 存储模式（预留）
- **WHEN** 设置 USE_REDIS=true 和 REDIS_URL
- **THEN** 使用 RedisStatsStore 和 RedisAlertWindowStore（未实现，预留接口）

---

### Requirement: 测试隔离
系统 SHALL 提供服务重置机制，确保测试间隔离。

#### Scenario: 测试前自动重置
- **WHEN** 运行测试套件
- **THEN** 每个测试前自动调用 reset()，状态清零

---

### Requirement: 配置项
系统 SHALL 支持以下环境变量配置：

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| WEBHOOK_URL | None | Webhook 地址（可选，默认 mock） |
| ALERT_WINDOW_MINUTES | 5 | 告警窗口时间（分钟） |
| ENVIRONMENT | dev | 环境标识（dev/staging/prod） |
| ALLOWED_ORIGINS | ["http://localhost:3000"] | CORS 允许的来源列表 |
| USE_REDIS | false | 是否使用 Redis 存储 |
| REDIS_URL | redis://localhost:6379/0 | Redis 连接地址 |

#### Scenario: 默认配置
- **WHEN** 未设置任何环境变量
- **THEN** 使用默认值启动服务

#### Scenario: 自定义告警窗口
- **WHEN** 设置 ALERT_WINDOW_MINUTES=10
- **THEN** 告警窗口为 10 分钟
