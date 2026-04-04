#!/usr/bin/env bash
# 重启 DRP 平台所有服务（Docker Compose + 后端 FastAPI + 前端 Vite）
#
# 使用方式：
#   ./scripts/restart.sh           # 重启全部（Docker + 后端 + 前端）
#   ./scripts/restart.sh backend   # 仅重启后端
#   ./scripts/restart.sh frontend  # 仅重启前端
#   ./scripts/restart.sh graphdb   # 重启指定 Docker 服务

set -euo pipefail

# 防止被 source 时执行主逻辑
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return 0 2>/dev/null || exit 0
fi

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"
FRONTEND_LOG="$PROJECT_ROOT/.frontend_logs"
BACKEND_PID_FILE="$PROJECT_ROOT/.backend.pid"
BACKEND_LOG="$PROJECT_ROOT/log/backend.log"
UV_PYTHON="${UV_PYTHON:-$HOME/.local/share/uv/python/cpython-3.12.10-macos-aarch64-none/bin/python3.12}"
SITE_PKGS="$BACKEND_DIR/.venv/lib/python3.12/site-packages"

cd "$PROJECT_ROOT"
mkdir -p log

# ── 前端启停函数 ──
stop_frontend() {
    local _fp
    if [ -f "$FRONTEND_PID_FILE" ]; then
        _fp=$({ cat "$FRONTEND_PID_FILE"; } 2>/dev/null)
        _fp=${_fp//[[:space:]]/}
        if [[ -n "${_fp-}" ]]; then
            kill "$_fp" 2>/dev/null || true
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi
    if [ -f "$FRONTEND_PID_FILE.dashboard" ]; then
        _fp=$({ cat "$FRONTEND_PID_FILE.dashboard"; } 2>/dev/null)
        _fp=${_fp//[[:space:]]/}
        if [[ -n "${_fp-}" ]]; then
            kill "$_fp" 2>/dev/null || true
        fi
        rm -f "$FRONTEND_PID_FILE.dashboard"
    fi
    pkill -f "vite.*frontend" 2>/dev/null || true
}

start_frontend() {
    echo "[$(date '+%H:%M:%S')] 启动前端（Vite）..."
    cd "$FRONTEND_DIR"
    mkdir -p "$PROJECT_ROOT/.frontend_logs"
    # 管理后台 5173
    nohup npm run dev > "$FRONTEND_LOG/admin.log" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
    # 监管大屏 5174
    nohup npm run dev:dashboard > "$FRONTEND_LOG/dashboard.log" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE.dashboard"
    cd "$PROJECT_ROOT"
    sleep 2
    echo "[$(date '+%H:%M:%S')] 前端已启动"
    echo "  管理后台：http://localhost:5173/"
    echo "  监管大屏：http://localhost:5174/"
}

# ── 后端启停函数 ──
stop_backend() {
    if [ ! -f "$BACKEND_PID_FILE" ]; then
        pkill -f "uvicorn drp.main" 2>/dev/null || true
        return
    fi
    local _bp=$({ cat "$BACKEND_PID_FILE"; } 2>/dev/null)
    _bp=${_bp//[[:space:]]/}
    if [[ -z "${_bp-}" ]]; then
        rm -f "$BACKEND_PID_FILE"
        return
    fi
    echo "[$(date '+%H:%M:%S')] 停止后端，PID=$_bp..."
    kill "$_bp" 2>/dev/null || true
    sleep 1
    rm -f "$BACKEND_PID_FILE"
}

start_backend() {
    echo "[$(date '+%H:%M:%S')] 启动后端（FastAPI）..."
    local env_file="$PROJECT_ROOT/.env"
    [ -f "$env_file" ] || { echo "  ⚠ 缺少 .env 文件，请先执行：cp .env.example .env"; return 1; }
    set -a && source "$env_file" && set +a
    nohup env PYTHONPATH="$BACKEND_DIR/src:$SITE_PKGS" \
        "$UV_PYTHON" -m uvicorn drp.main:app \
        --host 0.0.0.0 --port 8000 \
        > "$BACKEND_LOG" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
    sleep 3
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] 后端已启动: http://localhost:8000"
        echo "  API 文档: http://localhost:8000/api/docs"
    else
        echo "[$(date '+%H:%M:%S')] ⚠ 后端启动可能失败，查看日志: log/backend.log"
        tail -5 "$BACKEND_LOG"
    fi
}

# ── 主逻辑 ──
SERVICE="${1:-}"

if [ "$SERVICE" = "frontend" ]; then
    stop_frontend
    start_frontend
elif [ "$SERVICE" = "backend" ]; then
    stop_backend
    start_backend
elif [ -n "$SERVICE" ]; then
    echo "[$(date '+%H:%M:%S')] 重启 Docker 服务: $SERVICE"
    docker compose -f "$COMPOSE_FILE" restart "$SERVICE"
    echo "[$(date '+%H:%M:%S')] $SERVICE 已重启"
else
    echo "[$(date '+%H:%M:%S')] 重启所有服务..."
    stop_frontend
    stop_backend
    docker compose -f "$COMPOSE_FILE" down
    docker compose -f "$COMPOSE_FILE" up -d
    echo "[$(date '+%H:%M:%S')] 等待 Docker 服务就绪..."
    sleep 5
    start_backend
    start_frontend
    echo "[$(date '+%H:%M:%S')] 所有服务已重启"
fi

echo ""
echo "=== Docker 服务状态 ==="
docker compose -f "$COMPOSE_FILE" ps
