#!/usr/bin/env bash
# ============================================================================
# OpenClaw 环境迁移脚本 (macOS)
# 功能：将当前机器的 OpenClaw 环境完整迁移到另一台机器
#
# 两种模式：
#   export  — 在当前机器打包导出
#   import  — 在新机器导入并恢复
#
# 使用方式：
#   # 当前机器：导出
#   ./scripts/migrate-openclaw.sh export
#   # => 生成 openclaw-migrate-YYYY-MM-DD.tar.gz
#
#   # 新机器：先运行 setup-openclaw.sh 安装基础环境，然后导入
#   ./scripts/migrate-openclaw.sh import openclaw-migrate-YYYY-MM-DD.tar.gz
#
# 迁移内容：
#   - openclaw.json（主配置，含模型/插件/频道等）
#   - .env（API Keys）
#   - workspace/（知识文件 + todo.db + memory）
#   - skills/（ClawHub 安装的技能）
#   - cron/（定时任务）
#   - completions/（shell 补全）
#   - Homebrew/npm 依赖清单（自动重装）
# ============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

OPENCLAW_DIR="$HOME/.openclaw"
DATE=$(date '+%Y-%m-%d')
EXPORT_NAME="openclaw-migrate-${DATE}"

# ============================================================================
# export 模式：打包当前环境
# ============================================================================
do_export() {
    echo ""
    echo "============================================"
    echo "  🦞 OpenClaw 环境导出"
    echo "============================================"
    echo ""

    [[ -d "$OPENCLAW_DIR" ]] || error "未找到 OpenClaw 目录: $OPENCLAW_DIR"

    TMPDIR_EXPORT=$(mktemp -d)
    EXPORT_DIR="$TMPDIR_EXPORT/$EXPORT_NAME"
    mkdir -p "$EXPORT_DIR"

    # --- 1. 配置文件 ---
    info "打包配置文件..."
    mkdir -p "$EXPORT_DIR/config"
    cp "$OPENCLAW_DIR/openclaw.json" "$EXPORT_DIR/config/"
    [[ -f "$OPENCLAW_DIR/.env" ]] && cp "$OPENCLAW_DIR/.env" "$EXPORT_DIR/config/"
    ok "配置文件"

    # --- 2. Workspace（知识文件 + 数据） ---
    info "打包 workspace..."
    mkdir -p "$EXPORT_DIR/workspace"
    # 只复制知识文件和数据，跳过 venv/node_modules
    find "$OPENCLAW_DIR/workspace" -maxdepth 1 \( -name "*.md" -o -name "*.json" -o -name "*.db" \) \
        -exec cp {} "$EXPORT_DIR/workspace/" \;
    # memory 子目录（知识文件）
    if [[ -d "$OPENCLAW_DIR/workspace/memory" ]]; then
        mkdir -p "$EXPORT_DIR/workspace/memory"
        find "$OPENCLAW_DIR/workspace/memory" -maxdepth 1 \( -name "*.md" -o -name "*.json" \) \
            -exec cp {} "$EXPORT_DIR/workspace/memory/" \;
    fi
    # memory SQLite 数据库（语义搜索索引 + embedding 缓存）
    if [[ -d "$OPENCLAW_DIR/memory" ]]; then
        mkdir -p "$EXPORT_DIR/memory-db"
        cp "$OPENCLAW_DIR/memory/"*.sqlite "$EXPORT_DIR/memory-db/" 2>/dev/null || true
    fi
    # skills 模板
    if [[ -d "$OPENCLAW_DIR/workspace/skills/_template" ]]; then
        mkdir -p "$EXPORT_DIR/workspace/skills/_template"
        cp -r "$OPENCLAW_DIR/workspace/skills/_template/" "$EXPORT_DIR/workspace/skills/_template/"
    fi
    # tools 目录结构
    mkdir -p "$EXPORT_DIR/workspace/tools/scripts" "$EXPORT_DIR/workspace/tools/lib"
    ok "workspace（$(find "$EXPORT_DIR/workspace" -type f | wc -l | tr -d ' ') 个文件）"

    # --- 3. ClawHub 安装的 Skills ---
    info "打包 ClawHub skills..."
    if [[ -d "$OPENCLAW_DIR/skills" ]]; then
        mkdir -p "$EXPORT_DIR/skills"
        # 复制已安装的 skills（排除 bundled）
        for skill_dir in "$OPENCLAW_DIR/skills"/*/; do
            [[ -d "$skill_dir" ]] || continue
            skill_name=$(basename "$skill_dir")
            cp -r "$skill_dir" "$EXPORT_DIR/skills/$skill_name"
        done
        # 复制锁文件
        [[ -f "$OPENCLAW_DIR/.clawhub/lock.json" ]] && {
            mkdir -p "$EXPORT_DIR/.clawhub"
            cp "$OPENCLAW_DIR/.clawhub/lock.json" "$EXPORT_DIR/.clawhub/"
        }
    fi
    ok "skills（$(ls -1 "$EXPORT_DIR/skills" 2>/dev/null | wc -l | tr -d ' ') 个）"

    # --- 4. Cron 定时任务 ---
    info "打包定时任务..."
    if [[ -f "$OPENCLAW_DIR/cron/jobs.json" ]]; then
        mkdir -p "$EXPORT_DIR/cron"
        cp "$OPENCLAW_DIR/cron/jobs.json" "$EXPORT_DIR/cron/"
    fi
    ok "定时任务"

    # --- 5. Shell 补全 ---
    if [[ -d "$OPENCLAW_DIR/completions" ]]; then
        mkdir -p "$EXPORT_DIR/completions"
        cp "$OPENCLAW_DIR/completions"/* "$EXPORT_DIR/completions/" 2>/dev/null || true
    fi

    # --- 6. 生成依赖清单 ---
    info "生成依赖清单..."
    cat > "$EXPORT_DIR/deps.sh" << 'DEPS_HEADER'
#!/usr/bin/env bash
# OpenClaw 依赖安装脚本（由 migrate-openclaw.sh export 自动生成）
set -euo pipefail
info()  { echo -e "\033[0;34m[INFO]\033[0m $*"; }
ok()    { echo -e "\033[0;32m[OK]\033[0m $*"; }
warn()  { echo -e "\033[1;33m[WARN]\033[0m $*"; }
DEPS_HEADER

    # Homebrew formulae
    echo "" >> "$EXPORT_DIR/deps.sh"
    echo "# --- Homebrew formulae ---" >> "$EXPORT_DIR/deps.sh"
    echo "BREW_FORMULAE=()" >> "$EXPORT_DIR/deps.sh"
    for pkg in gh tmux ffmpeg ripgrep himalaya; do
        if brew list --formula "$pkg" &>/dev/null 2>&1; then
            echo "BREW_FORMULAE+=($pkg)" >> "$EXPORT_DIR/deps.sh"
        fi
    done
    # steipete tap 包
    echo "BREW_TAP_FORMULAE=()" >> "$EXPORT_DIR/deps.sh"
    for pkg in remindctl peekaboo imsg; do
        if command -v "$pkg" &>/dev/null; then
            echo "BREW_TAP_FORMULAE+=($pkg)" >> "$EXPORT_DIR/deps.sh"
        fi
    done
    # Homebrew cask
    echo "BREW_CASKS=()" >> "$EXPORT_DIR/deps.sh"
    if brew list --cask codexbar &>/dev/null 2>&1; then
        echo "BREW_CASKS+=(codexbar)" >> "$EXPORT_DIR/deps.sh"
    fi

    # npm 全局包
    echo "" >> "$EXPORT_DIR/deps.sh"
    echo "# --- npm 全局包 ---" >> "$EXPORT_DIR/deps.sh"
    echo "NPM_PACKAGES=()" >> "$EXPORT_DIR/deps.sh"
    for pkg in clawhub mcporter summarize @steipete/oracle; do
        if npm list -g "$pkg" &>/dev/null 2>&1; then
            ver=$(npm list -g "$pkg" --json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(list(d.get('dependencies',{}).values())[0]['version'])" 2>/dev/null || echo "latest")
            echo "NPM_PACKAGES+=(\"${pkg}@${ver}\")" >> "$EXPORT_DIR/deps.sh"
        fi
    done

    # 安装逻辑
    cat >> "$EXPORT_DIR/deps.sh" << 'DEPS_INSTALL'

info "安装 Homebrew 依赖..."
for pkg in "${BREW_FORMULAE[@]}"; do
    if brew list --formula "$pkg" &>/dev/null 2>&1; then
        ok "$pkg 已安装"
    else
        info "安装 $pkg..."
        brew install "$pkg"
    fi
done

if [[ ${#BREW_TAP_FORMULAE[@]} -gt 0 ]]; then
    brew tap steipete/tap 2>/dev/null || true
    for pkg in "${BREW_TAP_FORMULAE[@]}"; do
        if command -v "$pkg" &>/dev/null; then
            ok "$pkg 已安装"
        else
            info "安装 steipete/tap/$pkg..."
            brew install "steipete/tap/$pkg" || warn "$pkg 安装失败（可能需要更新 CLT）"
        fi
    done
fi

for cask in "${BREW_CASKS[@]}"; do
    if brew list --cask "$cask" &>/dev/null 2>&1; then
        ok "$cask 已安装"
    else
        info "安装 $cask..."
        brew install --cask "$cask"
    fi
done

info "安装 npm 全局依赖..."
for pkg in "${NPM_PACKAGES[@]}"; do
    info "安装 $pkg..."
    npm install -g "$pkg" || warn "$pkg 安装失败"
done

ok "依赖安装完成"
DEPS_INSTALL

    chmod +x "$EXPORT_DIR/deps.sh"
    ok "依赖清单（deps.sh）"

    # --- 7. 生成元数据 ---
    cat > "$EXPORT_DIR/manifest.json" << MANIFEST_EOF
{
  "exportDate": "$DATE",
  "exportTime": "$(date '+%H:%M:%S')",
  "sourceHost": "$(hostname)",
  "openclawVersion": "$(openclaw --version 2>/dev/null || echo 'unknown')",
  "nodeVersion": "$(node -v 2>/dev/null || echo 'unknown')",
  "platform": "$(uname -m)",
  "skills": $(cat "$OPENCLAW_DIR/.clawhub/lock.json" 2>/dev/null || echo '{}')
}
MANIFEST_EOF

    # --- 打包 ---
    info "创建压缩包..."
    ARCHIVE="${EXPORT_NAME}.tar.gz"
    (cd "$TMPDIR_EXPORT" && tar czf "$ARCHIVE" "$EXPORT_NAME")
    mv "$TMPDIR_EXPORT/$ARCHIVE" "./$ARCHIVE"
    rm -rf "$TMPDIR_EXPORT"

    SIZE=$(du -h "./$ARCHIVE" | cut -f1)

    echo ""
    echo "============================================"
    echo "  🦞 导出完成!"
    echo "============================================"
    echo ""
    echo "  文件: ./$ARCHIVE ($SIZE)"
    echo "  内容:"
    echo "    - 配置文件 (openclaw.json, .env)"
    echo "    - workspace 知识文件 + todo.db"
    echo "    - ClawHub 技能 ($(ls -1 "$OPENCLAW_DIR/skills" 2>/dev/null | wc -l | tr -d ' ') 个)"
    echo "    - 定时任务 (cron jobs)"
    echo "    - 依赖清单 (deps.sh)"
    echo ""
    echo "  迁移到新机器："
    echo "    1. 先运行 setup-openclaw.sh 安装基础环境"
    echo "    2. 将 $ARCHIVE 复制到新机器"
    echo "    3. 运行: ./scripts/migrate-openclaw.sh import $ARCHIVE"
    echo ""
}

# ============================================================================
# import 模式：在新机器恢复环境
# ============================================================================
do_import() {
    local ARCHIVE="$1"

    echo ""
    echo "============================================"
    echo "  🦞 OpenClaw 环境导入"
    echo "============================================"
    echo ""

    [[ -f "$ARCHIVE" ]] || error "文件不存在: $ARCHIVE"

    # 检查 OpenClaw 是否已安装
    command -v openclaw &>/dev/null || error "请先运行 setup-openclaw.sh 安装基础 OpenClaw"

    # 解压
    TMPDIR_IMPORT=$(mktemp -d)
    info "解压 $ARCHIVE..."
    tar xzf "$ARCHIVE" -C "$TMPDIR_IMPORT"

    # 找到导出目录
    IMPORT_DIR=$(find "$TMPDIR_IMPORT" -maxdepth 1 -name "openclaw-migrate-*" -type d | head -1)
    [[ -d "$IMPORT_DIR" ]] || error "压缩包格式不正确"

    # 显示元数据
    if [[ -f "$IMPORT_DIR/manifest.json" ]]; then
        info "导出信息:"
        python3 -c "
import json
with open('$IMPORT_DIR/manifest.json') as f:
    m = json.load(f)
print(f'  来源: {m.get(\"sourceHost\", \"unknown\")}')
print(f'  日期: {m.get(\"exportDate\", \"unknown\")} {m.get(\"exportTime\", \"\")}')
print(f'  版本: {m.get(\"openclawVersion\", \"unknown\")}')
print(f'  平台: {m.get(\"platform\", \"unknown\")}')
" 2>/dev/null || true
    fi

    echo ""
    read -p "确认导入？这会覆盖当前 OpenClaw 配置。[y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || { info "已取消"; rm -rf "$TMPDIR_IMPORT"; exit 0; }

    mkdir -p "$OPENCLAW_DIR"

    # --- 1. 配置文件 ---
    info "恢复配置文件..."
    if [[ -f "$OPENCLAW_DIR/openclaw.json" ]]; then
        cp "$OPENCLAW_DIR/openclaw.json" "$OPENCLAW_DIR/openclaw.json.pre-import"
        ok "已备份现有配置到 openclaw.json.pre-import"
    fi
    cp "$IMPORT_DIR/config/openclaw.json" "$OPENCLAW_DIR/openclaw.json"
    chmod 600 "$OPENCLAW_DIR/openclaw.json"

    if [[ -f "$IMPORT_DIR/config/.env" ]]; then
        cp "$IMPORT_DIR/config/.env" "$OPENCLAW_DIR/.env"
        chmod 600 "$OPENCLAW_DIR/.env"
        ok "配置 + .env"
    else
        warn ".env 未包含在导出中，需要手动配置 API Keys"
        ok "配置文件"
    fi

    # --- 2. Workspace ---
    info "恢复 workspace..."
    mkdir -p "$OPENCLAW_DIR/workspace/memory" \
             "$OPENCLAW_DIR/workspace/skills/_template" \
             "$OPENCLAW_DIR/workspace/tools/scripts" \
             "$OPENCLAW_DIR/workspace/tools/lib"

    # 复制知识文件（不覆盖已有的 todo.db，合并策略）
    for f in "$IMPORT_DIR/workspace/"*.md "$IMPORT_DIR/workspace/"*.json; do
        [[ -f "$f" ]] && cp "$f" "$OPENCLAW_DIR/workspace/"
    done
    # todo.db 特殊处理：如果目标已有，询问
    if [[ -f "$IMPORT_DIR/workspace/todo.db" ]]; then
        if [[ -f "$OPENCLAW_DIR/workspace/todo.db" ]]; then
            read -p "  todo.db 已存在，覆盖？[y/N] " -n 1 -r
            echo
            [[ $REPLY =~ ^[Yy]$ ]] && cp "$IMPORT_DIR/workspace/todo.db" "$OPENCLAW_DIR/workspace/todo.db"
        else
            cp "$IMPORT_DIR/workspace/todo.db" "$OPENCLAW_DIR/workspace/todo.db"
        fi
    fi
    # memory 子目录（知识文件）
    for f in "$IMPORT_DIR/workspace/memory/"*.md "$IMPORT_DIR/workspace/memory/"*.json; do
        [[ -f "$f" ]] && cp "$f" "$OPENCLAW_DIR/workspace/memory/"
    done
    # memory SQLite 数据库
    if [[ -d "$IMPORT_DIR/memory-db" ]]; then
        mkdir -p "$OPENCLAW_DIR/memory"
        cp "$IMPORT_DIR/memory-db/"*.sqlite "$OPENCLAW_DIR/memory/" 2>/dev/null || true
        ok "memory 数据库已恢复"
    fi
    # skills 模板
    if [[ -d "$IMPORT_DIR/workspace/skills/_template" ]]; then
        cp -r "$IMPORT_DIR/workspace/skills/_template/" "$OPENCLAW_DIR/workspace/skills/_template/"
    fi
    ok "workspace"

    # --- 3. Skills ---
    info "恢复 ClawHub skills..."
    if [[ -d "$IMPORT_DIR/skills" ]]; then
        mkdir -p "$OPENCLAW_DIR/skills"
        for skill_dir in "$IMPORT_DIR/skills"/*/; do
            [[ -d "$skill_dir" ]] || continue
            skill_name=$(basename "$skill_dir")
            cp -r "$skill_dir" "$OPENCLAW_DIR/skills/$skill_name"
            ok "  $skill_name"
        done
    fi
    if [[ -f "$IMPORT_DIR/.clawhub/lock.json" ]]; then
        mkdir -p "$OPENCLAW_DIR/.clawhub"
        cp "$IMPORT_DIR/.clawhub/lock.json" "$OPENCLAW_DIR/.clawhub/"
    fi
    ok "skills 恢复完成"

    # --- 4. Cron ---
    info "恢复定时任务..."
    if [[ -f "$IMPORT_DIR/cron/jobs.json" ]]; then
        mkdir -p "$OPENCLAW_DIR/cron"
        cp "$IMPORT_DIR/cron/jobs.json" "$OPENCLAW_DIR/cron/"
        ok "定时任务"
    else
        info "无定时任务需恢复"
    fi

    # --- 5. Shell 补全 ---
    info "恢复 shell 补全..."
    openclaw completion --write-state 2>/dev/null || true
    openclaw completion --install --shell zsh --yes 2>/dev/null || true
    ok "shell 补全"

    # --- 6. 安装依赖 ---
    if [[ -f "$IMPORT_DIR/deps.sh" ]]; then
        echo ""
        read -p "是否安装 Homebrew/npm 依赖？[Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            info "运行依赖安装..."
            bash "$IMPORT_DIR/deps.sh"
        else
            info "跳过依赖安装。后续可手动运行 deps.sh"
        fi
    fi

    # --- 7. 重建 Memory 索引 ---
    info "重建 Memory 索引..."
    openclaw memory index 2>/dev/null || warn "Memory 索引失败，稍后运行 openclaw memory index"

    # --- 8. 构建沙箱镜像 ---
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "openclaw-sandbox:bookworm-slim"; then
            info "构建沙箱基础镜像..."
            docker pull debian:bookworm-slim 2>/dev/null && \
            docker tag debian:bookworm-slim openclaw-sandbox:bookworm-slim && \
            ok "沙箱镜像" || warn "沙箱镜像构建失败"
        fi
    fi

    # --- 9. 重启 Gateway ---
    info "重启 Gateway..."
    openclaw daemon install 2>/dev/null || true
    ok "Gateway"

    # --- 10. ClawHub 登录提示 ---
    echo ""
    warn "请手动登录 ClawHub（如需从市场安装/更新技能）:"
    echo "  clawhub login --token <your-token> --no-browser"

    # 清理
    rm -rf "$TMPDIR_IMPORT"

    # --- 验证 ---
    echo ""
    info "=== 验证安装 ==="
    openclaw skills check 2>&1 | grep -E "^(Total|✓|✗)" || true
    echo ""
    openclaw memory status 2>&1 | grep -E "^(Indexed|Vector|FTS)" || true

    echo ""
    echo "============================================"
    echo "  🦞 导入完成!"
    echo "============================================"
    echo ""
    echo "  后续操作："
    echo "    1. clawhub login --token <token> --no-browser  # 登录技能市场"
    echo "    2. openclaw doctor                             # 全面诊断"
    echo "    3. openclaw cron list                          # 确认定时任务"
    echo "    4. openclaw status                             # 确认运行状态"
    echo ""
}

# ============================================================================
# 入口
# ============================================================================
case "${1:-}" in
    export)
        do_export
        ;;
    import)
        [[ -n "${2:-}" ]] || error "用法: $0 import <archive.tar.gz>"
        do_import "$2"
        ;;
    *)
        echo "OpenClaw 环境迁移脚本"
        echo ""
        echo "用法:"
        echo "  $0 export              # 导出当前环境"
        echo "  $0 import <file.tar.gz> # 导入到新机器"
        echo ""
        echo "迁移流程:"
        echo "  旧机器: $0 export"
        echo "  新机器: setup-openclaw.sh → $0 import xxx.tar.gz"
        ;;
esac
