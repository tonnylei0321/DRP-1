# 技术设计：日志清洗告警服务

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI 路由层                         │
│  POST /api/logs          GET /api/logs/stats                │
│  (依赖注入 LogService + AlertService)                        │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                         服务层                               │
│  ┌─────────────────┐         ┌──────────────────┐          │
│  │  LogService     │         │  AlertService    │          │
│  │  - process_logs │         │  - check_and_alert│         │
│  │  - get_stats    │         │  - _send_webhook │          │
│  └────────┬────────┘         └────────┬─────────┘          │
└───────────┼──────────────────────────┼────────────────────┘
            │                          │
┌───────────▼──────────────────────────▼────────────────────┐
│                        存储层（抽象接口）                     │
│  ┌─────────────────┐         ┌──────────────────┐          │
│  │  StatsStore     │         │ AlertWindowStore │          │
│  │  (ABC)          │         │ (ABC)            │          │
│  └────────┬────────┘         └────────┬─────────┘          │
│           │                           │                     │
│  ┌────────▼────────┐         ┌────────▼─────────┐          │
│  │ MemoryStatsStore│         │ MemoryAlertWindow│          │
│  │                 │         │ Store            │          │
│  └─────────────────┘         └──────────────────┘          │
│                                                              │
│  (预留 Redis 实现)                                           │
└─────────────────────────────────────────────────────────────┘
```

## 核心设计决策

### 1. 分层架构

**模型层（Pydantic）**
- `LogEntry`：单条日志，严格校验 timestamp、level、service、message
- `LogBatchRequest`：批量请求包装，限制最多 1000 条
- `LogStats`：统计响应，`by_level` 使用固定结构体
- `LogIngestResponse`：摄取响应，包含 accepted、alerts_triggered、alerts_failed

**服务层**
- `LogService`：负责日志处理和统计
  - `process_logs()`：先触发告警，后原子更新统计
  - `get_stats()`：加锁读取统计快照
- `AlertService`：负责告警判定和发送
  - `check_and_alert()`：原子操作（检查窗口 + 更新时间）
  - `_send_webhook()`：Mock 实现（print 输出）

**存储层**
- 抽象接口：`StatsStore`、`AlertWindowStore`
- 内存实现：`MemoryStatsStore`、`MemoryAlertWindowStore`
- 扩展路径：`RedisStatsStore`、`RedisAlertWindowStore`（未实现）

**路由层**
- FastAPI 依赖注入
- 模块级单例（`_log_service`、`_alert_service`）
- 异常转换为 HTTP 状态码

### 2. 并发安全策略

**锁粒度设计**
```python
# LogService：统计锁
with self._lock:
    self._store.increment_stats(logs)

# AlertService：告警窗口锁
with self._lock:
    last_time = self._store.get_last_alert_time(service)
    if should_alert:
        self._send_webhook(log)
        self._store.set_last_alert_time(service, now)
```

**关键原则**
1. **两把独立锁**：统计锁和告警锁分离，避免嵌套
2. **原子操作**：检查窗口和更新时间在同一锁内
3. **锁外 I/O**：Webhook 调用在锁内（因为是 mock print，无网络延迟）
4. **快照复制**：`get_stats()` 返回副本，避免外部修改

**并发场景**
- ✅ 多线程并发摄取：Lock 保护统计和窗口
- ✅ 同时读写统计：读操作加锁
- ❌ 多进程部署：需要切换 Redis 实现

### 3. 告警窗口机制

**窗口判定逻辑**
```python
if last_alert_time is None or (now - last_alert_time).total_seconds() >= window_minutes * 60:
    # 触发告警
```

**边界行为**
- 时间差 `< 窗口`：抑制
- 时间差 `>= 窗口`：触发
- 首次 ERROR：触发（`last_alert_time is None`）

**去重键**
- 初版：按 `service` 去重
- 扩展：支持 `service + error_signature`

**失败处理**
- Webhook 异常捕获，不阻断摄取
- `alerts_failed` 计数返回给客户端
- 失败时仍更新 `last_alert_time`（避免风暴）

### 4. 数据校验规则

**LogEntry 校验**
```python
class LogEntry(BaseModel):
    timestamp: datetime  # 自动解析 ISO 8601 或 "YYYY-MM-DD HH:MM:SS"
    level: Literal["ERROR", "WARN", "INFO"]  # 枚举
    service: str  # 非空
    message: str

    @field_validator('level')
    def normalize_level(cls, v):
        return v.upper()  # 大小写标准化
```

**批量限制**
```python
class LogBatchRequest(BaseModel):
    logs: list[LogEntry]

    @field_validator('logs')
    def check_batch_size(cls, v):
        if len(v) > 1000:
            raise ValueError("批量大小不能超过 1000")
        return v
```

**统计结构固定化**
```python
class LogLevelStats(BaseModel):
    ERROR: int = 0
    WARN: int = 0
    INFO: int = 0
```

### 5. 扩展性设计

**存储层抽象**
```python
class StatsStore(ABC):
    @abstractmethod
    def increment_stats(self, logs: list[LogEntry]): pass

    @abstractmethod
    def get_stats(self) -> LogStats: pass
```

**切换 Redis 实现**
```python
# 在 app/routers/logs.py 初始化时
if settings.USE_REDIS:
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
    _stats_store = RedisStatsStore(redis_client)
    _window_store = RedisAlertWindowStore(redis_client)
else:
    _stats_store = MemoryStatsStore()
    _window_store = MemoryAlertWindowStore()
```

**Redis 实现要点**
- 统计：使用 Hash 存储 `by_level` 和 `by_service`
- 窗口：使用 String + TTL 存储最后告警时间
- 原子性：使用 Lua 脚本或 WATCH/MULTI

### 6. 测试策略

**测试覆盖**
1. **输入验证**：无效 timestamp、level、缺字段、超大批量
2. **统计正确性**：by_level 固定 key、by_service 多服务、空日志初始状态
3. **告警窗口**：抑制、过期重触发、跨服务独立、边界行为
4. **并发安全**：多线程并发摄取（pytest-xdist）
5. **降级容错**：Webhook 失败不阻断摄取

**测试隔离**
```python
@pytest.fixture(autouse=True)
def reset_services():
    """每个测试前重置服务状态"""
    _log_service.reset()
    _alert_service.reset()
```

## 技术栈

- **Web 框架**：FastAPI 0.100+
- **数据校验**：Pydantic 2.0+
- **并发控制**：threading.Lock
- **测试框架**：pytest + pytest-asyncio
- **可选依赖**：redis-py（Redis 实现）

## 性能考虑

**单进程性能**
- 批量摄取：~1000 条/请求
- 统计查询：O(1) 内存读取
- 告警判定：O(1) 时间比较

**瓶颈分析**
- ✅ 统计更新：Lock 竞争可控（批量原子更新）
- ✅ 告警判定：Lock 竞争可控（仅 ERROR 触发）
- ⚠️ Webhook 调用：同步调用会拖慢摄取（生产环境需异步化）

**扩展路径**
1. 多进程：切换 Redis 存储
2. 高吞吐：Webhook 异步化（Celery/RQ）
3. 持久化：日志落盘（PostgreSQL/ClickHouse）

## 安全考虑

**输入安全**
- 批量大小限制：1000 条
- 字段长度限制：message 最大 10KB（可配置）
- 枚举校验：level 仅允许三个值

**CORS 配置**
- `ALLOWED_ORIGINS` 环境变量控制
- 默认仅允许 `http://localhost:3000`
- `allow_methods` 限定为 GET、POST
- `allow_headers` 限定为 Content-Type

**生产部署建议**
- 添加 API 鉴权（JWT/API Key）
- 添加限流（slowapi/redis-based）
- 添加请求体大小限制（FastAPI middleware）
- 添加监控和告警（Prometheus/Grafana）

## 配置项

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `WEBHOOK_URL` | - | Webhook 地址（可选，默认 mock） |
| `ALERT_WINDOW_MINUTES` | 5 | 告警窗口时间（分钟） |
| `ENVIRONMENT` | dev | 环境标识（prod/staging/dev） |
| `ALLOWED_ORIGINS` | http://localhost:3000 | CORS 允许来源 |
| `USE_REDIS` | false | 是否使用 Redis 存储 |
| `REDIS_URL` | redis://localhost:6379/0 | Redis 连接地址 |

## 未来改进

1. **告警去重键升级**：支持 `service + error_signature`
2. **Webhook 异步化**：使用 Celery/RQ 后台任务
3. **日志持久化**：支持 PostgreSQL/ClickHouse
4. **查询 API**：支持按时间范围、服务、级别过滤
5. **告警规则配置**：支持自定义告警条件（不只是 ERROR）
6. **指标暴露**：Prometheus metrics 端点
7. **分布式追踪**：OpenTelemetry 集成
