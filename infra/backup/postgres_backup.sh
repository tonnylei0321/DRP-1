#!/bin/bash
# 13.2 PostgreSQL 定时备份脚本 — pg_dump 每日，保留 30 天
# 在 crontab 中配置：30 2 * * * /infra/backup/postgres_backup.sh

set -euo pipefail

PG_HOST="${POSTGRES_HOST:-postgres}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_DB="${POSTGRES_DB:-drp}"
PG_USER="${POSTGRES_USER:-drp}"
PGPASSWORD="${POSTGRES_PASSWORD:-drp_dev}"
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
RETAIN_DAYS="${RETAIN_DAYS:-30}"

export PGPASSWORD

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/postgres_${PG_DB}_${TIMESTAMP}.sql.gz"

echo "[$(date)] 开始 PostgreSQL 备份: ${PG_DB} → ${BACKUP_FILE}"

pg_dump \
  -h "${PG_HOST}" \
  -p "${PG_PORT}" \
  -U "${PG_USER}" \
  --format=plain \
  --no-password \
  "${PG_DB}" \
  | gzip > "${BACKUP_FILE}"

echo "[$(date)] 备份完成: ${BACKUP_FILE} ($(du -sh "${BACKUP_FILE}" | cut -f1))"

# 删除超过 RETAIN_DAYS 天的旧备份
find "${BACKUP_DIR}" -name "postgres_*.sql.gz" -mtime "+${RETAIN_DAYS}" -delete
echo "[$(date)] 已清理 ${RETAIN_DAYS} 天前的旧备份"
