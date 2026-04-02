# Change: 日志清洗告警服务（重构版）

## Why

现有日志告警服务已实现基本功能，但经过 Claude + Codex 三方交叉验证后，发现以下设计改进点：
1. 请求模型需要更明确的批量限制和校验规则
2. 并发安全需要更清晰的原子操作语义
3. 告警窗口边界行为需要明确定义
4. 存储层抽象需要更好的扩展性设计

本次重构旨在按照规范��多 AI 协同流程，重新设计并实现一个生产级的日志告警服务。

## What Changes

### 核心功能
- **POST /api/logs** - 接收批量日志数据（JSON 对象格式，包含 logs 数组）
- **GET /api/logs/stats** - 返回日志统计信息（total、by_level、by_service）
- **ERROR 自动告警** - ERROR 级别日志触发 Webhook，带窗口抑制机制

### 关键改进
1. **请求模型规范化**
   - 使用 `LogBatchRequest` 包装，格式：`{"logs": [...]}`
   - 批量限制：单次最多 1000 条
   - 严格校验：timestamp 格式、level 枚举、字段非空

2. **并发安全增强**
   - 告警检查和时间更新原子化（单锁保护）
   - 统计更新独立加锁
   - 先告警后统计，避免锁嵌套

3. **告警窗口明确化**
   - 窗口边界：时间差严格 `<` 窗口时间（等于时触发新告警）
   - 去重键：按 `service` 去重（初版）
   - Webhook 失败不阻断摄取，返回 `alerts_failed` 计数

4. **存储层抽象**
   - `StatsStore` 接口：支持内存/Redis 切换
   - `AlertWindowStore` 接口：支持内存/Redis 切换
   - 默认内存实现，预留 Redis 扩展

5. **数据模型强化**
   - `LogLevelStats` 固定三 key 结构体（ERROR/WARN/INFO）
   - `LogIngestResponse` 包含 `alerts_failed` 字段
   - Level 大小写自动标准化

## Impact

### Affected specs
- **新增**：`log-alert` capability 完整规范

### Affected code
- `app/models/log.py` - Pydantic 模型定义
- `app/services/log_service.py` - 日志处理服务
- `app/services/alert_service.py` - 告警服务
- `app/stores/stats_store.py` - 统计存储抽象
- `app/stores/alert_window_store.py` - 告警窗口存储抽象
- `app/stores/memory_*.py` - 内存实现
- `app/routers/logs.py` - FastAPI 路由
- `app/config.py` - 配置项
- `tests/test_logs.py` - 完整测试覆盖

### 破坏性变更
无（全新实现）

### 部署要求
- Python 3.11+
- FastAPI 0.100+
- Pydantic 2.0+
- 环境变量：
  - `WEBHOOK_URL`（可选，默认 mock）
  - `ALERT_WINDOW_MINUTES`（默认 5）
  - `ENVIRONMENT`（默认 dev）
  - `ALLOWED_ORIGINS`（默认 http://localhost:3000）

### 适用场景
- 单进程训练练习（内存存储）
- 扩展路径：多进程部署时切换 Redis 实现
