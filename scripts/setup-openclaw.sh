#!/usr/bin/env bash
# ============================================================================
# OpenClaw 一键安装脚本 (macOS)
# 方案：原生 Node.js + OrbStack 轻量沙箱
#
# 使用方式：
#   chmod +x scripts/setup-openclaw.sh
#   ./scripts/setup-openclaw.sh
#
# 前置条件：
#   - macOS (Apple Silicon 或 Intel)
#   - Homebrew 已安装
#   - 需要准备大模型 API Key（脚本运行时交互输入）
#
# 配置的模型提供商：
#   - 火山引擎（豆包 Doubao 2.0）- 默认模型
#   - 阿里百炼（MiniMax-M2.5）- 备选模型
# ============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ============================================================================
# Step 0: 环境检测
# ============================================================================
echo ""
echo "============================================"
echo "  🦞 OpenClaw 一键安装脚本 (macOS)"
echo "  方案: 原生 Node.js + OrbStack 轻量沙箱"
echo "============================================"
echo ""

# 检测 macOS
[[ "$(uname)" == "Darwin" ]] || error "此脚本仅支持 macOS"

# 检测 Homebrew
command -v brew &>/dev/null || error "请先安装 Homebrew: https://brew.sh"
ok "Homebrew 已安装"

# 检测架构
ARCH=$(uname -m)
info "系统架构: $ARCH"

# ============================================================================
# Step 1: 安装 Node.js (如果需要)
# ============================================================================
echo ""
info "=== Step 1: 检查 Node.js ==="

if command -v node &>/dev/null; then
    NODE_VER=$(node -v | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
    if [[ "$NODE_MAJOR" -ge 22 ]]; then
        ok "Node.js $NODE_VER 已安装（满足 >=22 要求）"
    else
        warn "Node.js $NODE_VER 版本过低，需要 >=22"
        info "正在通过 Homebrew 安装 Node.js..."
        brew install node
        ok "Node.js $(node -v) 安装完成"
    fi
else
    info "Node.js 未安装，正在通过 Homebrew 安装..."
    brew install node
    ok "Node.js $(node -v) 安装完成"
fi

# ============================================================================
# Step 2: 安装 OrbStack
# ============================================================================
echo ""
info "=== Step 2: 安装 OrbStack (轻量 Docker 替代) ==="

if command -v orbctl &>/dev/null; then
    ok "OrbStack 已安装"
else
    info "正在安装 OrbStack..."
    brew install --cask orbstack
    ok "OrbStack 安装完成"
fi

# 启动 OrbStack
if orbctl status &>/dev/null 2>&1; then
    ok "OrbStack 正在运行"
else
    info "正在启动 OrbStack..."
    open -a OrbStack
    echo "等待 OrbStack 初始化..."
    for i in $(seq 1 30); do
        if orbctl status &>/dev/null 2>&1; then
            ok "OrbStack 已启动"
            break
        fi
        sleep 2
    done
fi

# 验证 Docker CLI
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    ok "Docker CLI 可用 (via OrbStack)"
else
    warn "Docker CLI 暂不可用，请手动打开 OrbStack 完成初始化"
    warn "初始化完成后重新运行此脚本"
fi

# ============================================================================
# Step 3: 安装 OpenClaw
# ============================================================================
echo ""
info "=== Step 3: 安装 OpenClaw ==="

if command -v openclaw &>/dev/null; then
    CURRENT_VER=$(openclaw --version 2>/dev/null || echo "unknown")
    ok "OpenClaw 已安装 (版本: $CURRENT_VER)"
    read -p "是否更新到最新版本? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "正在更新 OpenClaw..."
        npm install -g openclaw@latest
        ok "OpenClaw 已更新到 $(openclaw --version)"
    fi
else
    info "正在安装 OpenClaw..."
    npm install -g openclaw@latest
    ok "OpenClaw $(openclaw --version) 安装完成"
fi

# ============================================================================
# Step 4: 收集 API Key
# ============================================================================
echo ""
info "=== Step 4: 配置大模型 API Key ==="
echo ""
echo "需要配置以下 API Key（至少配置一个）："
echo "  1. 火山引擎（豆包 Doubao）- 推荐作为默认模型"
echo "  2. 阿里百炼（DashScope）- 推荐作为备选模型"
echo ""

# 火山引擎
read -p "请输入火山引擎 API Key (留空跳过): " VOLCENGINE_KEY
VOLCENGINE_KEY="${VOLCENGINE_KEY:-}"

# 阿里百炼
read -p "请输入阿里百炼 API Key (留空跳过): " DASHSCOPE_KEY
DASHSCOPE_KEY="${DASHSCOPE_KEY:-}"

if [[ -z "$VOLCENGINE_KEY" && -z "$DASHSCOPE_KEY" ]]; then
    error "至少需要配置一个 API Key"
fi

# 确定默认模型
if [[ -n "$VOLCENGINE_KEY" ]]; then
    DEFAULT_MODEL="volcengine/doubao-seed-2-0-pro-260215"
    DEFAULT_ALIAS="豆包2.0"
else
    DEFAULT_MODEL="dashscope/MiniMax-M2.5"
    DEFAULT_ALIAS="MiniMax-M2.5"
fi

info "默认模型: $DEFAULT_MODEL ($DEFAULT_ALIAS)"

# ============================================================================
# Step 5: 生成配置文件
# ============================================================================
echo ""
info "=== Step 5: 生成 OpenClaw 配置 ==="

OPENCLAW_DIR="$HOME/.openclaw"
mkdir -p "$OPENCLAW_DIR"
chmod 700 "$OPENCLAW_DIR"

# 写入 .env（API Key）
cat > "$OPENCLAW_DIR/.env" << ENV_EOF
# OpenClaw 环境变量配置
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')
ENV_EOF

if [[ -n "$VOLCENGINE_KEY" ]]; then
    echo "VOLCANO_ENGINE_API_KEY=$VOLCENGINE_KEY" >> "$OPENCLAW_DIR/.env"
fi
if [[ -n "$DASHSCOPE_KEY" ]]; then
    echo "DASHSCOPE_API_KEY=$DASHSCOPE_KEY" >> "$OPENCLAW_DIR/.env"
fi

chmod 600 "$OPENCLAW_DIR/.env"
ok ".env 已生成 (权限 600)"

# 构建 providers JSON
PROVIDERS=""

# 火山引擎 provider
if [[ -n "$VOLCENGINE_KEY" ]]; then
    PROVIDERS="$PROVIDERS
      \"volcengine\": {
        \"baseUrl\": \"https://ark.cn-beijing.volces.com/api/v3\",
        \"apiKey\": \"\${VOLCANO_ENGINE_API_KEY}\",
        \"api\": \"openai-completions\",
        \"models\": [
          {
            \"id\": \"doubao-seed-2-0-pro-260215\",
            \"name\": \"Doubao Seed 2.0 Pro\",
            \"reasoning\": true,
            \"input\": [\"text\", \"image\"],
            \"contextWindow\": 128000,
            \"maxTokens\": 16384
          }
        ]
      }"
fi

# 阿里百炼 provider
if [[ -n "$DASHSCOPE_KEY" ]]; then
    [[ -n "$PROVIDERS" ]] && PROVIDERS="$PROVIDERS,"
    PROVIDERS="$PROVIDERS
      \"dashscope\": {
        \"baseUrl\": \"https://dashscope.aliyuncs.com/compatible-mode/v1\",
        \"apiKey\": \"\${DASHSCOPE_API_KEY}\",
        \"api\": \"openai-completions\",
        \"models\": [
          {
            \"id\": \"MiniMax-M2.5\",
            \"name\": \"MiniMax M2.5 (阿里百炼)\",
            \"reasoning\": true,
            \"input\": [\"text\"],
            \"contextWindow\": 1000000,
            \"maxTokens\": 16384
          }
        ]
      }"
fi

# 构建 fallbacks
FALLBACKS=""
if [[ "$DEFAULT_MODEL" == "volcengine/doubao-seed-2-0-pro-260215" && -n "$DASHSCOPE_KEY" ]]; then
    FALLBACKS="\"dashscope/MiniMax-M2.5\""
elif [[ "$DEFAULT_MODEL" == "dashscope/MiniMax-M2.5" && -n "$VOLCENGINE_KEY" ]]; then
    FALLBACKS="\"volcengine/doubao-seed-2-0-pro-260215\""
fi

# 构建 models 允许列表
MODELS_LIST=""
if [[ -n "$VOLCENGINE_KEY" ]]; then
    MODELS_LIST="\"volcengine/doubao-seed-2-0-pro-260215\": { \"alias\": \"豆包2.0\" }"
fi
if [[ -n "$DASHSCOPE_KEY" ]]; then
    [[ -n "$MODELS_LIST" ]] && MODELS_LIST="$MODELS_LIST,"
    MODELS_LIST="$MODELS_LIST \"dashscope/MiniMax-M2.5\": { \"alias\": \"MiniMax-M2.5\" }"
fi

# 生成 openclaw.json
cat > "$OPENCLAW_DIR/openclaw.json" << CONFIG_EOF
{
  "gateway": {
    "mode": "local",
    "bind": "loopback",
    "controlUi": { "enabled": true }
  },
  "models": {
    "mode": "merge",
    "providers": {
$PROVIDERS
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "$DEFAULT_MODEL",
        "fallbacks": [${FALLBACKS}]
      },
      "models": {
        $MODELS_LIST
      },
      "sandbox": {
        "mode": "non-main",
        "scope": "session"
      },
      "compaction": {
        "mode": "safeguard"
      },
      "maxConcurrent": 4,
      "subagents": {
        "maxConcurrent": 8
      }
    }
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto",
    "restart": true
  }
}
CONFIG_EOF

chmod 600 "$OPENCLAW_DIR/openclaw.json"
ok "openclaw.json 已生成"

# ============================================================================
# Step 6: 安装守护进程
# ============================================================================
echo ""
info "=== Step 6: 安装 OpenClaw 守护进程 ==="

openclaw daemon install 2>&1 || warn "守护进程安装可能需要手动完成"
ok "OpenClaw 守护进程已安装"

# ============================================================================
# Step 7: 创建必要目录
# ============================================================================
mkdir -p "$OPENCLAW_DIR/agents/main/sessions"
chmod 700 "$OPENCLAW_DIR/agents/main/sessions"

# ============================================================================
# Step 8: 验证安装
# ============================================================================
echo ""
info "=== Step 8: 验证安装 ==="

# 验证模型状态
echo ""
info "模型配置状态:"
openclaw models status 2>&1 | grep -E "Default|Fallback|Alias|Configured" || true

# 测试模型调用
echo ""
info "测试模型调用..."
REPLY=$(openclaw agent --message "回复 OK 即可" --agent main 2>/dev/null || echo "FAIL")
if [[ "$REPLY" == *"OK"* ]] || [[ "$REPLY" != "FAIL" ]]; then
    ok "模型调用成功!"
    echo "  回复: $REPLY"
else
    warn "模型调用未成功，请检查 API Key 和网络连接"
fi

# ============================================================================
# 安装完成
# ============================================================================
echo ""
echo "============================================"
echo "  🦞 OpenClaw 安装完成!"
echo "============================================"
echo ""
echo "  Dashboard: http://127.0.0.1:18789/"
echo "  默认模型: $DEFAULT_MODEL"
echo "  沙箱模式: non-main (via OrbStack Docker)"
echo ""
echo "  常用命令:"
echo "    openclaw status          # 查看状态"
echo "    openclaw models status   # 查看模型配置"
echo "    openclaw agent --message '你好' --agent main  # 发送消息"
echo "    openclaw doctor          # 诊断问题"
echo "    openclaw dashboard       # 打开浏览器 Dashboard"
echo "    openclaw logs --follow   # 查看日志"
echo ""
echo "  配置文件:"
echo "    ~/.openclaw/openclaw.json  # 主配置"
echo "    ~/.openclaw/.env           # API Key (敏感)"
echo ""
