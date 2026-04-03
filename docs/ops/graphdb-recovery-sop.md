# 13.3 GraphDB 命名图恢复 SOP

> 适用场景：单租户 Named Graph 数据损坏或误删，需从 TriG 备份文件中恢复。

---

## 1. 前置条件

| 项目 | 要求 |
|------|------|
| GraphDB 服务 | 运行正常，`GET http://graphdb:7200/rest/repositories` 返回 200 |
| 备份文件 | `/backups/graphdb/graphdb_drp_YYYYMMDD_HHMMSS.trig.gz` 可访问 |
| 操作人员 | 具备 GraphDB admin 权限 |
| 工具 | `curl`, `gzip`, `jq` |

---

## 2. 确认需要恢复的租户

```bash
# 查询受损租户 ID（通过监控告警或业务反馈确认）
export TENANT_ID="<uuid>"
export GRAPH_IRI="urn:tenant:${TENANT_ID}"

# 确认当前 Named Graph 状态（三元组数量异常或为空）
curl -s -u admin:root \
  -H "Accept: application/json" \
  "http://graphdb:7200/repositories/drp/size?context=<${GRAPH_IRI}>"
```

---

## 3. 选择恢复基准备份

```bash
# 列出可用备份（按时间排序）
ls -lht /backups/graphdb/graphdb_drp_*.trig.gz | head -20

# 选择最近一次完好的备份
export BACKUP_FILE="/backups/graphdb/graphdb_drp_YYYYMMDD_HHMMSS.trig.gz"
```

**选择原则：**
- 优先选择最近一次备份（RPO ≤ 1 天）
- 若最近备份本身已损坏，依次向前选择

---

## 4. 备份验证

```bash
# 解压验证（不实际写入磁盘）
gzip -t "${BACKUP_FILE}" && echo "备份文件完整性校验通过"

# 预览备份内容（检查 Graph IRI 是否存在）
gzip -dc "${BACKUP_FILE}" | grep "GRAPH <${GRAPH_IRI}>" | head -5
```

---

## 5. 清空受损命名图

> ⚠️ **警告**：此步骤会删除指定 Named Graph 下的全部数据。执行前务必确认 TENANT_ID 正确。

```bash
curl -s -f -X DELETE \
  -u admin:root \
  "http://graphdb:7200/repositories/drp/statements?context=<${GRAPH_IRI}>"

echo "已清空��名图: ${GRAPH_IRI}"
```

---

## 6. 从 TriG 备份恢复数据

```bash
# 解压并上传 TriG 文件（命名图由 TriG 文件中的 GRAPH 声明自动匹配）
TEMP_FILE=$(mktemp /tmp/graphdb_restore_XXXXXX.trig)
gzip -dc "${BACKUP_FILE}" > "${TEMP_FILE}"

# 仅上传目标租户的三元组（过滤其他租户数据）
grep -A 999999 "GRAPH <${GRAPH_IRI}>" "${TEMP_FILE}" \
  | head -n $(grep -n "^}" "${TEMP_FILE}" | head -1 | cut -d: -f1) \
  > /tmp/tenant_restore.trig

# 上传到 GraphDB
curl -s -f -X POST \
  -u admin:root \
  -H "Content-Type: application/x-trig" \
  --data-binary @/tmp/tenant_restore.trig \
  "http://graphdb:7200/repositories/drp/statements"

echo "数据恢复完成"
rm -f "${TEMP_FILE}" /tmp/tenant_restore.trig
```

---

## 7. 验证恢复结果

```bash
# 确认三元组数量恢复正常
TRIPLE_COUNT=$(curl -s -u admin:root \
  -H "Accept: application/json" \
  "http://graphdb:7200/repositories/drp/size?context=<${GRAPH_IRI}>")

echo "恢复后三元组数量: ${TRIPLE_COUNT}"

# 运行 SPARQL 验证查询（抽检几条核心数据）
curl -s -u admin:root \
  -H "Accept: application/json" \
  -G "http://graphdb:7200/repositories/drp" \
  --data-urlencode "query=SELECT * WHERE { GRAPH <${GRAPH_IRI}> { ?s ?p ?o } } LIMIT 5"
```

---

## 8. 通知与记录

1. 在运维日志中记录：
   - 恢复时间戳
   - 受影响租户 ID
   - 使用的备份文件名和时间点
   - 恢复前后三元组数量
   - 操作人员

2. 通知租户数据管理员，告知数据截至时间点

3. 触发增量 ETL 同步，补齐备份点到当前时间的增量数据：
   ```bash
   # 通过 API 手动触发增量同步
   curl -s -X POST \
     -H "Authorization: Bearer <admin_token>" \
     "http://drp-backend:8000/etl/trigger?tenant_id=${TENANT_ID}&mode=incremental"
   ```

---

## 9. 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 上传返回 413 | TriG 文件过大 | 分批上传：`split -l 100000 restore.trig part_` |
| 上传返回 400 | TriG 语法错误 | 用 `rapper -i trig -o nquads restore.trig` 验证语法 |
| 查询返回空 | Graph IRI 不���配 | 确认 IRI 格式：`urn:tenant:${TENANT_ID}`（小写 uuid） |
| 恢复后指标异常 | 缺少本体数据 | 检查是否包含 CTIO 本体命名图，必要时重新加载本体 |

---

*目标 RTO：≤ 4 小时（从发现故障到数据服务恢复正常）*
