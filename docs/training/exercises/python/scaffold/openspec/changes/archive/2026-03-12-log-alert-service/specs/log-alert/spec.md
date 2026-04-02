# Spec Delta: log-alert

## ADDED Requirements

### Requirement: 日志批量摄取
系统 SHALL 提供 POST /api/logs 端点，接收批量日志并返回摄取结果。

#### Scenario: 正常摄取
- **WHEN** 客户端提交包含有效 LogEntry 列表的请求
- **THEN** 返回 200，body 包含 accepted、alerts_triggered、alerts_failed

#### Scenario: 空批次
- **WHEN** 客户端提交 logs 为空数组
- **THEN** 返回 200，accepted=0，不报错

#### Scenario: 无效输入 - 字段格式
- **WHEN** timestamp 格式不符或 level 不在 ERROR/WARN/INFO 内
- **THEN** 返回 422

#### Scenario: 无效输入 - 结构异常
- **WHEN** 缺少 logs 字段、logs 不是数组、logs 为 null、任一必填字段缺失
- **THEN** 返回 422

---

### Requirement: 日志统计查询
系统 SHALL 提供 GET /api/logs/stats 端点，返回累计统计数据。

#### Scenario: 统计结构稳定
- **WHEN** 调用 GET /api/logs/stats
- **THEN** by_level 始终包含 ERROR、WARN、INFO 三个 key，值为 0 或正整数

#### Scenario: 无日志��初始状态
- **WHEN** 未提交任何日志时调用 GET /api/logs/stats
- **THEN** total=0，by_level 三个 key 均为 0，by_service 为空对象

#### Scenario: 多服务计数
- **WHEN** 提交来自多个 service 的日志
- **THEN** by_service 各服务计数独立正确

---

### Requirement: ERROR 告警触发
系统 SHALL 对 ERROR 级别日志触发 webhook 告警。

#### Scenario: 窗口内抑制
- **WHEN** 同一 service 在 ALERT_WINDOW_MINUTES 内连续出现 ERROR（时间差严格小于窗口）
- **THEN** 只触发一次 webhook，后续在窗口内的 ERROR 被抑制

#### Scenario: 窗口边界行为
- **WHEN** 同一 service 两次 ERROR 时间差恰好等于 ALERT_WINDOW_MINUTES
- **THEN** 视为超出窗口，触发第二次告警（实现使用严格 <）

#### Scenario: 窗口过期重触发
- **WHEN** 同一 service 的 ERROR 时间间隔超过 ALERT_WINDOW_MINUTES
- **THEN** 再次触发 webhook

#### Scenario: 跨服务独立
- **WHEN** 不同 service 同时出现 ERROR
- **THEN** 各自独立触发 webhook

#### Scenario: webhook 失败降级
- **WHEN** webhook 调用抛出异常
- **THEN** 日志摄取正常完成，统计正确写入，alerts_failed 计数加一，不返回 500

---

### Requirement: Webhook Payload 规范
系统 SHALL 在 webhook payload 中包含以下字段：
- alert_id: UUID v4，每次告警唯一
- alert_timestamp: 告警发送时间（UTC，格式 YYYY-MM-DD HH:MM:SS）
- log_timestamp: 日志原始时间
- level: 日志级别
- service: 服务名
- message: 错误信息
- environment: 环境标识（prod/staging/dev，读取 ENVIRONMENT 环境变量）

---

### Requirement: API 响应模型规范
系统 SHALL 在 OpenAPI schema 中声明：
- LogLevelStats 强类型结构体（ERROR/WARN/INFO 三个固定字段）替代 Dict[str, int]
- POST /api/logs 端点显式声明 422 响应描述

---

### Requirement: CORS 安全配置
系统 SHALL 通过 ALLOWED_ORIGINS 环境变量控制跨域来源，默认仅允许 http://localhost:3000。
allow_methods 限定为 GET、POST，allow_headers 限定为 Content-Type。
