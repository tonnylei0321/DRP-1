#!/usr/bin/env bash
# 停止 DRP 平台所有服务（Docker Compose + 前端 Vite）
#
# 使用方式：
#   ./scripts/killall.sh        # 停止所有服务，保留数据卷
#   ./scripts/killall.sh -v     # 停止所有服务并删除数据卷（危险：数据不可恢复）

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"
BACKEND_PID_FILE="$PROJECT_ROOT/.backend.pid"

BACKEND_PID_FILE="$PROJECT_ROOT/.backend.pid"

cd "$PROJECT_ROOT"

# ── 停止后端 ──
if [ -f "$BACKEND_PID_FILE" ]; then
    pid=$(cat "$BACKEND_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "[$(date '+%H:%M:%S')] 停止后端进程 (PID $pid)..."
        kill "$pid" 2>/dev/null || true
    fi
    rm -f "$BACKEND_PID_FILE"
else
    pkill -f "uvicorn drp.main" 2>/dev/null || true
fi
echo "[$(date '+%H:%M:%S')] 后端已停止"

# ── 停止前端 ──
if [ -f "$FRONTEND_PID_FILE" ]; then
    pid=$(cat "$FRONTEND_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "[$(date '+%H:%M:%S')] 停止前端管理后台 (PID $pid)..."
        kill "$pid" 2>/dev/null || true
    fi
    rm -f "$FRONTEND_PID_FILE"
fi
if [ -f "$FRONTEND_PID_FILE.dashboard" ]; then
    pid=$(cat "$FRONTEND_PID_FILE.dashboard")
    if kill -0 "$pid" 2>/dev/null; then
        echo "[$(date '+%H:%M:%S')] 停止前端监管大屏 (PID $pid)..."
        kill "$pid" 2>/dev/null || true
    fi
    rm -f "$FRONTEND_PID_FILE.dashboard"
fi
pkill -f "vite.*frontend\|vite.*dashboard" 2>/dev/null || true
echo "[$(date '+%H:%M:%S')] 前端已停止"

# ── 停止 Docker 服务 ──
REMOVE_VOLUMES=false
if [ "${1:-}" = "-v" ]; then
    REMOVE_VOLUMES=true
fi

if $REMOVE_VOLUMES; then
    echo "[$(date '+%H:%M:%S')] ⚠ 警告：将删除所有数据卷（GraphDB / PostgreSQL / Redis 数据将清空）"
    read -r -p "确认删除数据卷？[y/N] " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "已取消"
        exit 0
    fi
    echo "[$(date '+%H:%M:%S')] 停止并删除所有服务和数据卷..."
    docker compose -f "$COMPOSE_FILE" down -v
else
    echo "[$(date '+%H:%M:%S')] 停止并移除所有 Docker 服务（数据卷保留）..."
    docker compose -f "$COMPOSE_FILE" down
fi

echo "[$(date '+%H:%M:%S')] 完成"
