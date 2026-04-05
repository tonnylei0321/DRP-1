#!/usr/bin/env bash
# 查看 DRP 平台进程和服务状态
#
# 使用方式：
#   ./scripts/pstat.sh

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"
FRONTEND_LOG_DIR="$PROJECT_ROOT/.frontend_logs"
BACKEND_PID_FILE="$PROJECT_ROOT/.backend.pid"
BACKEND_LOG="$PROJECT_ROOT/log/backend.log"

cd "$PROJECT_ROOT"

echo "=== Docker 服务状态 ==="
docker compose -f "$COMPOSE_FILE" ps 2>/dev/null || echo "（Docker Compose 服务未运行）"

echo ""
echo "=== 资源占用 ==="
docker compose -f "$COMPOSE_FILE" ps -q 2>/dev/null \
    | xargs -r docker stats --no-stream --format \
      "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}" \
    2>/dev/null || echo "（无运行中的容器）"

echo ""
echo "=== 后端状态 ==="
if [ -f "$BACKEND_PID_FILE" ]; then
    pid=$(cat "$BACKEND_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        health=$(curl -sf http://localhost:8000/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "无响应")
        echo "  运行中 (PID $pid)  health: $health"
        echo "  API: http://localhost:8000"
        echo "  API 文档: http://localhost:8000/api/docs"
    else
        echo "  已停止（PID 文件残留，执行 restart.sh backend 重启）"
    fi
else
    echo "  未运行"
fi

echo ""
echo "=== 前端状态 ==="
# 管理后台
if [ -f "$FRONTEND_PID_FILE" ]; then
    pid=$(cat "$FRONTEND_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "  管理后台 运行中 (PID $pid)"
        echo "  地址: http://localhost:5173/"
    else
        echo "  管理后台 已停止（PID 文件残留）"
    fi
else
    echo "  管理后台 未运行"
fi
# 监管大屏
if [ -f "$FRONTEND_PID_FILE.dashboard" ]; then
    pid=$(cat "$FRONTEND_PID_FILE.dashboard")
    if kill -0 "$pid" 2>/dev/null; then
        echo "  监管大屏 运行中 (PID $pid)"
        echo "  地址: http://localhost:5174/"
    else
        echo "  监管大屏 已停止（PID 文件残留）"
    fi
else
    echo "  监管大屏 未运行"
fi

echo ""
echo "=== 端口监听 ==="
for port in 7201 5433 6380 8000 5173 5174; do
    info=$(lsof -iTCP:$port -sTCP:LISTEN -n -P 2>/dev/null | tail -1)
    if [ -n "$info" ]; then
        echo "  :$port  $info"
    else
        echo "  :$port  （未监听）"
    fi
done

echo ""
echo "=== FastAPI 后端进程 ==="
pgrep -fl "uvicorn|drp" 2>/dev/null || echo "（未运行）"

echo ""
echo "=== Celery Worker 进程 ==="
pgrep -fl "celery" 2>/dev/null || echo "（未运行）"
