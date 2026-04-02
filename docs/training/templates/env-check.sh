#!/bin/bash
# =============================================================================
# AI 驱动开发培训 - 环境自检脚本
#
# 用法：bash env-check.sh
# 培训前一天运行，确保所有工具就绪。
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 无颜色
BOLD='\033[1m'

PASS=0
FAIL=0
WARN=0

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    PASS=$((PASS + 1))
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    echo -e "    ${YELLOW}修复方法：$2${NC}"
    FAIL=$((FAIL + 1))
}

check_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    WARN=$((WARN + 1))
}

echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  AI 驱动开发培训 - 环境自检${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""

# --- 1. 基础工具 ---
echo -e "${BOLD}[1/8] 基础工具${NC}"

if command -v git &>/dev/null; then
    check_pass "Git $(git --version | head -1)"
else
    check_fail "Git 未安装" "brew install git 或 apt install git"
fi

if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    check_pass "Node.js $NODE_VER"
else
    check_warn "Node.js 未安装（前端组需要）"
fi

if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version)
    check_pass "Python3 $PY_VER"
else
    check_warn "Python3 未安装（Python/算法组需要）"
fi

if command -v java &>/dev/null; then
    JAVA_VER=$(java --version 2>&1 | head -1)
    check_pass "Java $JAVA_VER"
else
    check_warn "Java 未安装（Java 组需要）"
fi

if command -v mvn &>/dev/null; then
    check_pass "Maven $(mvn --version 2>&1 | head -1)"
else
    check_warn "Maven 未安装（Java 组需要）"
fi

echo ""

# --- 2. Claude Code ---
echo -e "${BOLD}[2/8] Claude Code${NC}"

if command -v claude &>/dev/null; then
    CLAUDE_VER=$(claude --version 2>&1 || echo "版本获取失败")
    check_pass "Claude Code 已安装: $CLAUDE_VER"
else
    check_fail "Claude Code 未安装" "npm install -g @anthropic-ai/claude-code"
fi

echo ""

# --- 3. Codex CLI ---
echo -e "${BOLD}[3/8] Codex CLI${NC}"

if command -v codex &>/dev/null; then
    CODEX_VER=$(codex --version 2>&1 || echo "版本获取失败")
    check_pass "Codex CLI 已安装: $CODEX_VER"
else
    check_warn "Codex CLI 未安装（npm install -g @openai/codex）"
fi

echo ""

# --- 4. OpenSpec ---
echo -e "${BOLD}[4/8] OpenSpec${NC}"

if command -v openspec &>/dev/null; then
    OPENSPEC_VER=$(openspec --version 2>&1 || echo "版本获取失败")
    check_pass "OpenSpec 已安装: $OPENSPEC_VER"
else
    check_warn "OpenSpec 未安装（npm install -g openspec-dev）"
fi

echo ""

# --- 5. API 连通性 ---
echo -e "${BOLD}[5/8] API 连通性${NC}"

if [ -n "$ANTHROPIC_API_KEY" ]; then
    check_pass "ANTHROPIC_API_KEY 已设置"
else
    check_warn "ANTHROPIC_API_KEY 未设置（可能在 Claude Code 配置中）"
fi

# 检查网络连通性
if curl -s --connect-timeout 5 https://api.anthropic.com > /dev/null 2>&1; then
    check_pass "Anthropic API 网络可达"
else
    check_fail "Anthropic API 网络不可达" "检查网络代理设置"
fi

echo ""

# --- 6. MCP 工具 ---
echo -e "${BOLD}[6/8] MCP 工具配置${NC}"

CLAUDE_CONFIG="$HOME/.claude.json"
if [ -f "$CLAUDE_CONFIG" ]; then
    check_pass "Claude 配置文件存在"
else
    check_warn "Claude 配置文件不存在（首次启动 Claude Code 会自动创建）"
fi

# 检查 MCP 配置目录
CLAUDE_DIR="$HOME/.claude"
if [ -d "$CLAUDE_DIR" ]; then
    check_pass "Claude 配置目录存在: $CLAUDE_DIR"
else
    check_warn "Claude 配置目录不存在"
fi

echo ""

# --- 7. 技术栈专项检查 ---
echo -e "${BOLD}[7/8] 技术栈专项检查${NC}"

# Python 组
if command -v pip3 &>/dev/null || command -v pip &>/dev/null; then
    check_pass "pip 可用"
    # 检查关键包
    if python3 -c "import fastapi" 2>/dev/null; then
        check_pass "FastAPI 已安装"
    else
        check_warn "FastAPI 未安装（Python 组需要: pip install fastapi）"
    fi
    if python3 -c "import pytest" 2>/dev/null; then
        check_pass "pytest 已安装"
    else
        check_warn "pytest 未安装（pip install pytest）"
    fi
fi

# 前端组
if command -v npm &>/dev/null; then
    check_pass "npm $(npm --version)"
fi

echo ""

# --- 8. 磁盘空间 ---
echo -e "${BOLD}[8/8] 系统资源${NC}"

if [ "$(uname)" = "Darwin" ]; then
    DISK_FREE=$(df -h / | tail -1 | awk '{print $4}')
else
    DISK_FREE=$(df -h / | tail -1 | awk '{print $4}')
fi
check_pass "可用磁盘空间: $DISK_FREE"

echo ""

# --- 汇总 ---
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  检查结果汇总${NC}"
echo -e "${BOLD}============================================${NC}"
echo -e "  ${GREEN}通过：${PASS}${NC}"
echo -e "  ${RED}失败：${FAIL}${NC}"
echo -e "  ${YELLOW}警告：${WARN}${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}${BOLD}环境就绪！请在群里发送"环境检查通过"。${NC}"
else
    echo -e "${RED}${BOLD}有 ${FAIL} 项检查失败，请按提示修复后重新运行此脚本。${NC}"
    echo -e "${YELLOW}如需帮助，请联系培训助教。${NC}"
fi
