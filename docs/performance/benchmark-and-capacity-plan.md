# 14. 性能基准与容量规划

> 测试环境：5 租户 × 1000 法人 × 10000 账户 × 106 指标  
> 测试日期：待执行

---

## 14.1 性能基准测试环境配置

### 基准测试数据规格

| 维度 | 规模 | 三元组估算 |
|------|------|----------|
| 租户数 | 5 | - |
| 法人实体数 | 1000 / 租户 | ~20 三元组/实体 × 5000 = 100K |
| 账户数 | 10000 / 租户 | ~15 三元组/账户 × 50000 = 750K |
| 指标实例 | 106 × 5 租户 | ~10 三元组/指标 = 5.3K |
| CTIO 本体 | 固定 | ~5K |
| **总计** | | **~860K 三元组** |

### 数据生成脚本

```bash
# 安装测试依赖
pip install faker rdflib

# 生成测试数据
python scripts/benchmark/generate_test_data.py \
  --tenants 5 \
  --entities-per-tenant 1000 \
  --accounts-per-entity 10 \
  --output /tmp/benchmark_data.trig

# 导入 GraphDB
curl -s -X POST -u admin:root \
  -H "Content-Type: application/x-trig" \
  --data-binary @/tmp/benchmark_data.trig \
  "http://localhost:7200/repositories/drp/statements"
```

---

## 14.2 106 项指标 SPARQL 计算耗时

**目标**：全部 106 项指标在 45 分钟内完成（含 15 分钟裕量）

### 测试方法

```bash
# 测量单租户指标计算总耗时
python scripts/benchmark/measure_indicator_calc.py \
  --tenant-id <uuid> \
  --output benchmark_results/kpi_calc_$(date +%Y%m%d).json
```

### 基准测试结果（待填写）

| 业务域 | 指标数 | 单域耗时（秒） | 备注 |
|------|------|------------|------|
| 银行账户域 (001-031) | 31 | - | - |
| 资金集中域 (032-041) | 10 | - | - |
| 结算域 (042-068) | 27 | - | - |
| 票据域 (069-078) | 10 | - | - |
| 债务融资域 (079-085) | 7 | - | - |
| 决策风险域 (086-097) | 12 | - | - |
| 国资委考核域 (098-106) | 9 | - | - |
| **合计** | **106** | **-** | **目标 < 2700s** |

---

## 14.3 三级穿透 API 响应时间（P95 < 3 秒）

### 测试方法

```bash
# 使用 wrk 或 k6 进行负载测试
k6 run --vus 10 --duration 60s scripts/benchmark/drill_load_test.js

# 测试脚本 drill_load_test.js 包含：
# - GET /drill/{indicator_id}/entities
# - GET /drill/{entity_id}/accounts
# - GET /drill/{account_id}/properties
```

### 基准测试结果（待填写）

| 接口 | P50 (ms) | P95 (ms) | P99 (ms) | 目标 P95 |
|------|---------|---------|---------|---------|
| 一级：指标→法人 | - | - | - | < 3000ms |
| 二级：法人→账户 | - | - | - | < 3000ms |
| 三级：账户→属性 | - | - | - | < 3000ms |
| 路径查询 | - | - | - | < 3000ms |

---

## 14.4 GraphDB 写入吞吐（100 万三元组全量初始化）

### 测试方法

```bash
# 生成 100 万三元组测试文件
python scripts/benchmark/generate_large_trig.py \
  --triples 1000000 \
  --output /tmp/bulk_load_test.trig

# 测量批量导入耗时
time curl -s -X POST -u admin:root \
  -H "Content-Type: application/x-trig" \
  --data-binary @/tmp/bulk_load_test.trig \
  "http://localhost:7200/repositories/drp/statements"
```

### 基准测试结果（待填写）

| 测试规模 | 耗时（秒） | 吞吐率（三元组/秒） |
|---------|---------|---------------|
| 10 万三元组 | - | - |
| 50 万三元组 | - | - |
| 100 万三元组 | - | - |

---

## 14.5 SPARQL 查询优化方案

### 本体索引配置

GraphDB 需配置以下索引以加速常用 SPARQL 模式：

```sparql
# 在 GraphDB Workbench 中执行（或通过 REST API）

# 1. 账户类型索引
CREATE INDEX ON :Account(rdf:type);

# 2. 租户图谱覆盖属性索引
CREATE INDEX ON :DirectLinkedAccount(ctio:isDirectLinked);
CREATE INDEX ON :RegulatoryIndicator(ctio:currentValue);
```

### SPARQL 慢查询分析

超过 10 秒的查询会被 `SlowQueryDetector`（`observability/logging.py`）自动记录。  
分析方式：

```bash
# 查看慢查询日志
grep "SLOW_QUERY" /var/log/drp/app.log | jq .

# 在 GraphDB Workbench 中使用 EXPLAIN 分析查询计划
EXPLAIN SELECT ?s ?p ?o WHERE { GRAPH <urn:tenant:xxx> { ?s ?p ?o } }
```

---

## 14.6 WebSocket 并发推送能力（100 并发连接，延迟 < 500ms）

### 测试方法

```bash
# 使用 websocket-bench 或自定义脚本
python scripts/benchmark/ws_load_test.py \
  --connections 100 \
  --duration 60 \
  --url ws://localhost:8000/ws/risk-events
```

### 基准测试结果（待填写）

| 并发连接数 | P50 推送延迟 (ms) | P95 推送延迟 (ms) | CPU 占用 | 目标 P95 |
|---------|--------------|--------------|---------|---------|
| 10 | - | - | - | < 500ms |
| 50 | - | - | - | < 500ms |
| 100 | - | - | - | < 500ms |
| 200 | - | - | - | 参考值 |

---

## 14.7 LLM 映射生成耗时（100 字段 DDL）

### 测试方法

```bash
python scripts/benchmark/llm_mapping_bench.py \
  --fields 100 \
  --iterations 5 \
  --output benchmark_results/llm_mapping_$(date +%Y%m%d).json
```

### 基准测试结果（待填写）

| 字段数 | 平均耗时（秒） | P95 耗时（秒） | Token 消耗 |
|------|------------|------------|---------|
| 10 | - | - | - |
| 50 | - | - | - |
| 100 | - | - | - |

---

## 14.8 容量规划（单节点 GraphDB 租户上限估算）

### 资源消耗模型

**单租户三元组估算**（1000 法人 × 10000 账户）：

| 数据类型 | 数量 | 三元组/条 | 小计 |
|---------|------|---------|------|
| 法人实体 | 1000 | 20 | 20K |
| 银行账户 | 10000 | 15 | 150K |
| 账户关系 | ~30000 | 3 | 90K |
| 指标实例 | 106 | 10 | 1.06K |
| **单租户合计** | | | **~261K 三元组** |

### 单节点容量上限

GraphDB 10.x 在 8 核 32GB RAM 规格下：
- 内存可容纳约 2 亿三元组（推理关系）
- 单租户约 261K 三元组 × 安全系数 5 = ~1.3M 三元组/租户
- **理论租户上限**：2 亿 ÷ 1.3M ≈ **150 租户**
- **推荐生产上限**：**50 租户**（保留 66% 裕量用于查询执行和推理）

### 扩容策略

| 租户规模 | 推荐架构 |
|---------|---------|
| ≤ 20 租户 | 单节点 GraphDB + 主从备份 |
| 21-100 租户 | GraphDB 集群（3 节点），按业务域分片 |
| > 100 租户 | 按租户组水平分片，每组独立 GraphDB 实例 |
