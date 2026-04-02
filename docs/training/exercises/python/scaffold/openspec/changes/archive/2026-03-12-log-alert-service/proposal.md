# Change: 日志清洗告警服务实现

## Why
脚手架仅提供空壳结构，缺少完整的业务逻辑实现。需要实现日志摄取、统计聚合、窗口告警等核心能力，并补充完整测试覆盖。

## What Changes
- 新增 Pydantic 模型：LogEntry（含严格验证）、LogBatchRequest、LogStats、LogIngestResponse
- 实现 LogService：批量日志摄取、统计聚合、线程安全写入
- 实现 AlertService：ERROR 级别触发、ALERT_WINDOW_MINUTES 窗口抑制、webhook 降级容错
- 实现 API 路由：POST /api/logs、GET /api/logs/stats
- 收紧 CORS：从 `*` 改为环境变量控制
- 补充 webhook payload 字段：alert_id、alert_timestamp、environment

## Impact
- Affected specs: log-alert
- Affected code: app/models/log.py, app/services/log_service.py, app/services/alert_service.py, app/routers/logs.py, app/main.py, app/config.py
