# 13.8 RTO/RPO 测试方案与验证报告

> **目标**：RTO ≤ 4 小时，RPO ≤ 1 天

---

## 1. 测试范围

| 故障场景 | 受影响组件 | RTO 目标 | RPO 目标 |
|---------|---------|---------|---------|
| GraphDB 节点故障 | 指标查询、穿透溯源 | ≤ 4h | ≤ 1 天 |
| PostgreSQL 节点故障 | 认证、ETL 状态、租户数据 | ≤ 4h | ≤ 1 天 |
| Redis 节点故障 | 缓存、会话、Pub/Sub | ≤ 30m | ≤ 1h（AOF 保护） |
| Celery Worker 全量故障 | ETL 同步、指标计算 | ≤ 1h | 基于水位线 |
| 混合云网络中断 | 所有外部请求 | ≤ 30m（降级模式） | ≤ 1 天 |

---

## 2. 测试环境准备

```bash
# 2.1 部署测试环境（与生产同规格）
docker compose -f docker-compose.dev.yml up -d

# 2.2 加载基准数据（2 租户 × 100 法人 × 1000 账户）
python scripts/seed_test_data.py --tenants 2 --entities 100 --accounts 1000

# 2.3 验证基准状态
curl -s http://localhost:8000/health | jq .
# 期望：{"status": "ok", "components": {"graphdb": "ok", "redis": "ok", "postgres": "ok"}}

# 2.4 记录基准数据量（用于 RPO 验证）
export BASELINE_TRIPLES=$(curl -s -u admin:root \
  "http://localhost:7201/repositories/drp/size" | jq .)
echo "基准三元组数: ${BASELINE_TRIPLES}"
```

---

## 3. 故障场景测试

### 3.1 场景一：GraphDB 节点故障

```bash
# ── 故障注入 ──
FAULT_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
docker stop drp-graphdb

# ── 验证降级生效 ──
sleep 60
curl -s http://localhost:8000/health | jq .components.graphdb
# 期望：返回 "error:..." 并触发降级模式

# ── 恢复步骤 ──
docker start drp-graphdb
# 等待 GraphDB 启动（约 60s）

# ── 验证 RTO ──
RECOVERY_START=$(date +%s)
until curl -sf http://localhost:7201/rest/repositories > /dev/null; do sleep 5; done
RECOVERY_END=$(date +%s)
echo "GraphDB 服务恢复耗时: $((RECOVERY_END - RECOVERY_START)) 秒"

# 触发增量 ETL 补齐数据
# [手动操作] 等待 ETL Beat 触发（最长 60 分钟）或手动触发

# ── 验证 RPO ──
RESTORED_TRIPLES=$(curl -s -u admin:root \
  "http://localhost:7201/repositories/drp/size" | jq .)
echo "恢复后三元组数: ${RESTORED_TRIPLES}（基准: ${BASELINE_TRIPLES}）"
```

**通过标准**：
- [ ] 降级模式在 45 秒内自动启用（`drp:degraded_mode` key 存在）
- [ ] 看板展示"数据截至"时间戳
- [ ] GraphDB 重启后服务自动恢复（`/health` 返回 ok）
- [ ] 增量 ETL 完成后数据量与基准一致（RPO 验证）
- [ ] 全程耗时 ≤ 4 小时

---

### 3.2 场景二：PostgreSQL 节点故障

```bash
# ── 故障注入 ──
docker stop drp-postgres

# ── 验证影响范围 ──
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "test"}' | jq .
# 期望：返回 500（PG 不可用）

# GraphDB 查询应仍可用（降级模式下）
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/health" | jq .

# ── 恢复步骤 ──
docker start drp-postgres
sleep 30

# ── 验证 RPO（pg_dump 备份恢复场景）──
# 模拟最坏情况：从 pg_dump 备份恢复
docker exec drp-postgres pg_dump -U drp drp | gzip > /tmp/drp_test_dump.sql.gz
docker exec drp-postgres psql -U drp -c "DROP DATABASE drp"
docker exec drp-postgres psql -U drp -c "CREATE DATABASE drp"
gzip -dc /tmp/drp_test_dump.sql.gz | docker exec -i drp-postgres psql -U drp drp

echo "PostgreSQL 从 pg_dump 备份恢复完成"
```

**通过标准**：
- [ ] PG 故障期间，缓存中的指标数据仍可查询
- [ ] PG 恢复后，认证和 ETL 功能自动恢复（无需重启 FastAPI）
- [ ] pg_dump 恢复后，所有历史数据完整（RPO ≤ 1 天）

---

### 3.3 场景三：Redis 故障（AOF 持久化��证）

```bash
# ── 写入测试数据 ──
redis-cli SET "kpi:test-tenant:KPI_001" '{"value": 0.85}' EX 3600

# ── 故障注入 ──
docker stop drp-redis

# ── 等待 Redis 重启（模拟 AOF 恢复）──
docker start drp-redis
sleep 10

# ── 验证 AOF 数据恢复 ──
redis-cli GET "kpi:test-tenant:KPI_001"
# 期望：返回之前写入的值（AOF 保护下数据不丢失）
```

**通过标准**：
- [ ] Redis 重启后，KPI 缓存数据通过 AOF 自动恢复
- [ ] WebSocket Pub/Sub 在 Redis 恢复后自动重连
- [ ] 会话 Token 在 Redis 恢复后仍有效

---

### 3.4 场景四：全量备份恢复演练（年度）

```bash
# 模拟生产灾难：完全丢失 GraphDB 数据
LATEST_BACKUP=$(ls -t /backups/graphdb/graphdb_drp_*.trig.gz | head -1)

# 清空所有数据
curl -s -X DELETE -u admin:root \
  "http://localhost:7201/repositories/drp/statements"

# 从备份恢复
gzip -dc "${LATEST_BACKUP}" | curl -s -X POST \
  -u admin:root \
  -H "Content-Type: application/x-trig" \
  --data-binary @- \
  "http://localhost:7201/repositories/drp/statements"

# 记录恢复耗时
echo "全量恢复耗时: $(date -u)"
```

---

## 4. 测试结果记录模板

| 场景 | 测试日期 | 故障注入时间 | 服务恢复时间 | 实际 RTO | 数据丢失量 | 实际 RPO | 通过/失败 |
|------|---------|------------|------------|---------|----------|---------|---------|
| GraphDB 节点故障 | - | - | - | - | - | - | - |
| PostgreSQL 节点故障 | - | - | - | - | - | - | - |
| Redis AOF 验证 | - | - | - | - | - | - | - |
| 全量备份恢复 | - | - | - | - | - | - | - |

---

## 5. 改进措施跟踪

| 问题 | 优先级 | 负责人 | 计划完成日期 |
|------|-------|-------|------------|
| （测试后填写） | - | - | - |

---

*测试频率：全量恢复演练每年至少 1 次；部分场景测试每季度执行。*
*测试结果归档至 `/docs/ops/rto-rpo-test-results/YYYY-QN.md`*
