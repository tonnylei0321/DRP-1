# Tasks: 日志清洗告警服务（重构版）

## 1. 模型层实现
- [x] 1.1 创建 `app/models/log.py`，实现 `LogEntry`
- [x] 1.2 实现 `LogBatchRequest` 和批量限制
- [x] 1.3 实现 `LogLevelStats` 固定结构体
- [x] 1.4 实现 `LogStats` 和 `LogIngestResponse`

## 2. 存储层抽象
- [x] 2.1 创建 `app/stores/stats_store.py`，定义 `StatsStore` 抽象接口
- [x] 2.2 创建 `app/stores/alert_window_store.py`，定义 `AlertWindowStore` 抽象接口
- [x] 2.3 实现 `MemoryStatsStore`
- [x] 2.4 实现 `MemoryAlertWindowStore`

## 3. 服务层实现
- [x] 3.1 创建 `app/services/log_service.py`，实现 `LogService`
- [x] 3.2 实现 `LogService.get_stats()`
- [x] 3.3 实现 `LogService.reset()` 供测试使用
- [x] 3.4 创建 `app/services/alert_service.py`，实现 `AlertService`
- [x] 3.5 实现 `AlertService._send_webhook()` Mock 版本
- [x] 3.6 实现 `AlertService.reset()` 供测试使用

## 4. 路由层实现
- [x] 4.1 创建 `app/routers/logs.py`，实现依赖注入
- [x] 4.2 实现 `POST /api/logs` 端点
- [x] 4.3 实现 `GET /api/logs/stats` 端点
- [x] 4.4 在 `app/main.py` 中注册路由

## 5. 配置层实现
- [x] 5.1 更新 `app/config.py`，添加配置项
- [x] 5.2 更新 `app/main.py` CORS 配置

## 6. 测试实现
- [x] 6.1 创建 `tests/conftest.py`，添加 reset fixture
- [x] 6.2 实现输入验证测试（8 个场景）
- [x] 6.3 实现统计正确性测试（5 个场景）
- [x] 6.4 实现告警窗口测试（6 个场景）
- [x] 6.5 实现 Webhook payload 测试（3 个场景）
- [x] 6.6 实现降级容错测试（2 个场景）

## 7. 文档和部署
- [x] 7.1 创建 `README.md`
- [x] 7.2 创建 `requirements.txt`
- [x] 7.3 验证完整功能
- [x] 7.4 运行完整测试套件
