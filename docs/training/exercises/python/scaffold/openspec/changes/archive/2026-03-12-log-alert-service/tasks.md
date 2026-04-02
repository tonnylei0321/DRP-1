# Tasks: 日志清洗告警服务

## 1. 模型层
- [x] 1.1 实现 LogEntry（timestamp datetime 严格解析、level Literal 枚举、field_validator 大小写标准化）
- [x] 1.2 实现 LogBatchRequest、LogStats（by_level 固定三 key）、LogIngestResponse（含 alerts_failed）
- [x] 1.3 新增 LogLevelStats 强类型结构体，替换 by_level: Dict[str, int]，OpenAPI schema 自动声明枚举

## 2. 服务层
- [x] 2.1 实现 LogService.process_logs()（先告警后原子提交统计，Lock 保护，移除无界 _logs 列表）
- [x] 2.2 实现 LogService.get_stats()（加锁读取，返回 LogLevelStats）
- [x] 2.3 实现 AlertService.check_and_alert()（ERROR 触发、ALERT_WINDOW_MINUTES 窗口抑制，严格 < 边界）
- [x] 2.4 实现 AlertService._send_webhook()（mock print，payload 含 alert_id / alert_timestamp / environment）
- [x] 2.5 两个 Service 均实现 reset() 供测试隔离

## 3. 路由层
- [x] 3.1 实现 POST /api/logs（Depends 注入服务，返回 LogIngestResponse，声明 422 响应描述）
- [x] 3.2 实现 GET /api/logs/stats（返回 LogStats，声明 200 状态码）

## 4. 配置与基础设施
- [x] 4.1 config.py 补充 ENVIRONMENT、ALLOWED_ORIGINS 配置项
- [x] 4.2 main.py CORS 收紧（allow_origins 读环境变量，methods/headers 限定）

## 5. 测试
- [x] 5.1 conftest.py 添加 autouse reset fixture（同时重置 LogService 和 AlertService）
- [x] 5.2 补充 23 个测试场景：
  - 输入验证（无效时间、级别、缺字段、结构异常）
  - 统计正确性（by_level 固定 key、by_service 多服务、空日志）
  - 窗口聚合（抑制、跨服务独立、过期重触发、边界行为固化）
  - 告警 payload 验证（alert_id UUID 格式、字段完整性）
  - 降级容错（webhook 失败不阻断摄取，统计正确写入）
