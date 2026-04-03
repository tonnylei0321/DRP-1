#!/bin/bash
# 13.1 GraphDB 定时备份脚本 — 每日全量导出 TriG，保留 7 天
# 在 crontab 中配置：0 2 * * * /infra/backup/graphdb_backup.sh

set -euo pipefail

GRAPHDB_URL="${GRAPHDB_URL:-http://graphdb:7200}"
GRAPHDB_REPO="${GRAPHDB_REPO:-drp}"
GRAPHDB_USER="${GRAPHDB_USER:-admin}"
GRAPHDB_PASS="${GRAPHDB_PASS:-root}"
BACKUP_DIR="${BACKUP_DIR:-/backups/graphdb}"
RETAIN_DAYS="${RETAIN_DAYS:-7}"

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/graphdb_${GRAPHDB_REPO}_${TIMESTAMP}.trig"

echo "[$(date)] 开始 GraphDB 备份: ${GRAPHDB_REPO} → ${BACKUP_FILE}"

# 导出所有命名图
curl -s -f \
  -u "${GRAPHDB_USER}:${GRAPHDB_PASS}" \
  -H "Accept: application/x-trig" \
  "${GRAPHDB_URL}/repositories/${GRAPHDB_REPO}/statements" \
  -o "${BACKUP_FILE}"

# 压缩
gzip "${BACKUP_FILE}"
echo "[$(date)] 备份完成: ${BACKUP_FILE}.gz ($(du -sh "${BACKUP_FILE}.gz" | cut -f1))"

# 删除超过 RETAIN_DAYS 天的旧备份
find "${BACKUP_DIR}" -name "graphdb_*.trig.gz" -mtime "+${RETAIN_DAYS}" -delete
echo "[$(date)] 已清理 ${RETAIN_DAYS} 天前的旧备份"
