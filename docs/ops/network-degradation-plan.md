# 13.6 混合云网络中断降级预案

> 适用场景：私有化 GraphDB/PostgreSQL 节点与公有云 Celery Worker 之间网络断开，��台需在只读降级模式下维持监管看板正常展示。

---

## 1. 降级触发条件

| 条件 | 判断方式 | 触发降级 |
|------|---------|---------|
| GraphDB 不可达 | `/health` 接口 `graphdb: error:*` | 是 |
| PostgreSQL 不可达 | `/health` 接口 `postgres: error:*` | 是 |
| ETL 超时 ≥ 90 分钟 | `drp_etl_last_sync_timestamp_seconds` 告警 | 是 |
| 单次 SPARQL P95 > 30s | Prometheus `SparqlHighTimeoutRate` 告警 | 否（仅限速） |

---

## 2. 降级策略

### 2.1 看板展示降级

**降级前（正常模式）**：指标值从 GraphDB 实时查询。

**降级后（缓存模式）**：
- 所有 `GET /drill/*` 和 SPARQL 请求改为从 Redis 缓存读取
- Key 格式：`kpi:{tenant_id}:{indicator_id}`，TTL 3600s
- 若 Redis 也不可用，返回上次持久化的快照（见 2.3）

**前端展示**：
- 看板顶部 Topbar 显示降级提示横幅：
  ```
  ⚠ 数据模式：缓存（数据截至 YYYY-MM-DD HH:MM UTC+8）
  ```
- 节点颜色保持最后一次已知状态，不再闪烁更新

### 2.2 写入操作限流

网络中断期间，以下操作将被暂停或排队：
- ETL 增量同步（任务保留在 Celery Beat 队列，网络恢复后自动重放）
- 指标计算写回 GraphDB（本地 Redis 缓存仍有效）
- 租户数据导出（返回 503 + Retry-After: 300）

### 2.3 降级快照持久化

**正常模式**下，每小时将当前 Redis KPI 缓存持久化为 JSON 快照：

```bash
# 快照路径：/backups/kpi-snapshot/kpi_YYYYMMDD_HH.json.gz
# 格式：{"tenant_id": {"indicator_id": {"value": 0.85, "is_compliant": true, "ts": "..."}}}
```

**降级模式**下，FastAPI 从最新快照文件读取数据：
- 自动选择 `/backups/kpi-snapshot/` 下最新的快照文件
- 在响应头注入 `X-Data-Stale: true` 和 `X-Data-As-Of: <timestamp>`

---

## 3. 降级模式切换

### 3.1 自动切换

`/health` 端点连续 3 次检测失败（45 秒内）后，自动设置 Redis key：

```
SET drp:degraded_mode "1" EX 300
```

FastAPI 在处理请求时检查此 key，决定走降级路径。

### 3.2 手动切换

```bash
# 启用降级模式
redis-cli SET drp:degraded_mode "1" EX 3600

# 禁用降级模式（网络恢复后）
redis-cli DEL drp:degraded_mode
```

---

## 4. 网络恢复后的处理流程

```
网络恢复
  ↓
/health 检查全部 OK（连续 3 次）
  ↓
自动清除 drp:degraded_mode key
  ↓
Celery Beat 触发补偿增量同步（水位线从 last_synced_at 开始）
  ↓
指标计算任务执行，更新 Redis 缓存
  ↓
看板恢复实时模式，移除降级提示
```

---

## 5. 运维检查清单

**网络中断时（5 分钟内）：**
- [ ] 确认告警来源（Prometheus / Grafana）
- [ ] 检查 `/health` 端点，定位故障组件
- [ ] 确认降级模式已自动启用（检查 Redis key `drp:degraded_mode`）
- [ ] 通知业务监管人员：数据为缓存模式，截至时间为 `X`

**恢复后（30 分钟内）：**
- [ ] 确认 `/health` 全部 OK
- [ ] 确认增量 ETL 已自动触发并成功
- [ ] 确认指标计算已完成，Redis 缓存已更新
- [ ] 确认看板已恢复实时模式
- [ ] 记录故障时间段和影响范围

---

## 6. 关键配置参数

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `DEGRADED_MODE_TTL` | 300s | 降级模式 Redis key 过期时间 |
| `HEALTH_CHECK_FAILURES` | 3 | 触发降级所需连续失败次数 |
| `CACHE_STALE_THRESHOLD_MINUTES` | 90 | 数据新鲜度告警阈值 |
| `KPI_SNAPSHOT_INTERVAL_HOURS` | 1 | KPI 快照持久化频率 |
| `ETL_REPLAY_WINDOW_HOURS` | 24 | 网络恢复后补偿同步的最大回溯窗口 |
