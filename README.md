# Claude Code Config Templates

> OpenSpec + Superpowers + Multi-AI Collaboration 统一开发工作流

这是一个 Claude Code 配置模板项目，提供：
- **统一开发流程** - OpenSpec 规范骨架 + Superpowers 执行方法论
- **多 AI 协同规则** - Claude + Codex + Gemini 三位一体协作
- **Skills 系统** - 可复用的开发技能模板
- **Plugins 配置** - 推荐的插件集合
- **一键部署脚本** - 快速配置任何项目/新机器

## 快速开始

### 新机器完整配置

```bash
# 1. 克隆此仓库
git clone <repo-url> ~/.claude/config-templates

# 2. 运行全局配置脚本（安装插件、MCP、全局 CLAUDE.md）
~/.claude/config-templates/setup-global.sh

# 3. 部署到具体项目
cd your-project
~/.claude/config-templates/setup-claude-config.sh
```

### 仅部署到项目

```bash
# 进入你的项目目录
cd your-project

# 运行部署脚本
~/.claude/config-templates/setup-claude-config.sh
```

### Windows (PowerShell)

#### 新机器完整配置

```powershell
# 1. 克隆此仓库
git clone <repo-url> $env:USERPROFILE\.claude\config-templates

# 2. 运行全局配置脚本（安装插件、MCP、全局 CLAUDE.md）
& "$env:USERPROFILE\.claude\config-templates\setup-global.ps1"
下面为windows改进的命令，在这前提需要提前将github的SSH与本机绑定下：
& "$env:USERPROFILE\.claude\config-templates\setup-global_back.ps1"

本地绑定github的公钥：
1、查看是否有公钥：ls ~/.ssh  若没有类似 id_ed25519 则没有安装
2、生成新的：ssh-keygen -t ed25519 -C "你的github邮箱" 
3、然后一路回车
4、输入命令然后复制公钥：cat ~/.ssh/id_ed25519.pub
5、贴在 https://github.com/settings/keys 上即可（路径：GitHub → Settings → SSH and GPG keys → New SSH key）
6、测试：ssh -T git@github.com  输出你的github名字就正常

# 3. 部署到具体项目
cd your-project
& "$env:USERPROFILE\.claude\config-templates\setup-claude-config.ps1"
```

#### 仅部署到项目

```powershell
# 进入你的项目目录
cd your-project

# 运行部署脚本（可指定目标目录）
& "$env:USERPROFILE\.claude\config-templates\setup-claude-config.ps1" -TargetDir .
```

> **注意**: Windows 用户需要先启用 PowerShell 脚本执行：
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

## 目录结构

```
ontologyDevOS/
├── setup-global.sh            # 全局配置脚本（插件、MCP、全局规则）
├── setup-claude-config.sh     # 项目配置脚本（skills、hooks、项目规则）
├── scripts/
│   ├── setup-openclaw.sh      # OpenClaw 一键安装脚本（macOS）
│   └── migrate-openclaw.sh    # OpenClaw 环境迁移脚本（导出/导入）
├── global/
│   └── CLAUDE.md              # 全局 CLAUDE.md 模板
├── CLAUDE.md                  # 项目级 CLAUDE.md 模板
├── skills/
│   ├── openspec-workflow/     # OpenSpec 规范驱动工作流 Skill
│   ├── git-workflow/          # Git 工作流 Skill
│   ├── python-backend-guidelines/  # Python 后端规范
│   ├── python-error-tracking/      # 错误追踪规范
│   └── skill-developer/      # Skill 开发指南
├── agents/                    # 专业 Agent 模板
├── hooks/                     # Skill 激活钩子
└── settings.json              # Claude Code 设置模板
```

## 统一工作流程

```
Step 1: 项目设计文件 → Step 2: 需求设计 → Step 3: Spec 提案 → Step 4: 开发实现 → Step 5: 验证与完成
         ↓                  ↓                ↓                ↓               ↓
   生成/整理项目       brainstorming      /openspec:proposal  writing-plans   verification +
   级设计文件         + 多AI交叉验证      生成变更提案        + TDD执行       finishing-branch
```

### OpenSpec 提供规范骨架

```
提案 (Proposal) → 审批 → 实现 (Apply) → 归档 (Archive)
```

- `/openspec:proposal` — 创建变更提案
- `/openspec:apply` — 实现已批准的提案
- `/openspec:archive` — 归档已完成的变更

### Superpowers 提供执行方法论

| 工作流步骤 | Superpowers 技能 | 用途 |
|-----------|-----------------|------|
| Step 2: 需求设计 | `brainstorming` | 苏格拉底式需求探索与设计 |
| Step 4: 开发前 | `using-git-worktrees` | 创建隔离工作空间（可选） |
| Step 4: 计划细化 | `writing-plans` | 将 OpenSpec tasks 细化为 bite-sized 步骤 |
| Step 4: 执行 | `subagent-driven-development` | subagent 驱动的任务执行 + 双阶段审查 |
| Step 4: 实现 | `test-driven-development` | 强制 TDD RED-GREEN-REFACTOR |
| Step 4: 审查 | `requesting-code-review` | 每个 task 后的代码审查 |
| Step 5: 验证 | `verification-before-completion` | 完成前的证据验证 |
| Step 5: 完成 | `finishing-a-development-branch` | 分支集成与清理 |

### 多 AI 协同提供质量保障

```
Claude (主体思考者 + 决策者)
    ├── Codex (后端技术顾问) - 交叉检查、算法审查
    └── Gemini (前端开发主力) - 大文本分析、前端实现
```

每个关键环节（设计、开发、验证）进行 2-3 轮交叉验证。

## 包含的插件

| 插件 | 用途 |
|------|------|
| claude-mem | 记忆/历史插件，搜索历史会话 |
| superpowers | 核心技能库，包含 13 个 skills |
| pyright-lsp | Python LSP 支持 |
| pinecone | 向量数据库，用于 RAG |
| commit-commands | Git 提交命令增强 |
| code-review | 代码审查增强 |

### Superpowers 插件内置 Skills

| Skill | 用途 |
|-------|------|
| brainstorming | 头脑风暴，探索方案 |
| dispatching-parallel-agents | 并行任务分发 |
| executing-plans | 执行计划 |
| finishing-a-development-branch | 完成开发分支 |
| receiving-code-review | 接收代码审查 |
| requesting-code-review | 请求代码审查 |
| subagent-driven-development | 子代理驱动开发 |
| systematic-debugging | 系统化调试 |
| test-driven-development | 测试驱动开发 |
| using-git-worktrees | 使用 Git Worktrees |
| verification-before-completion | 完成前验证 |
| writing-plans | 编写计划 |
| writing-skills | 编写 Skills |

## MCP 工具

| MCP | 用途 |
|-----|------|
| codex | 代码生成、交叉检查（使用 OpenAI Codex） |
| gemini-cli | 大文本分析、前端开发（使用 Google Gemini） |

```bash
# 查看已安装的 MCP 工具
claude mcp list

# 手动安装 Codex MCP
claude mcp add codex -s user --transport stdio -- uvx --from git+https://github.com/GuDaStudio/codexmcp.git codexmcp

# 手动安装 Gemini MCP
claude mcp add gemini-cli -- npx -y gemini-mcp-tool
```

## 项目级 Skills

| Skill | 用途 |
|-------|------|
| openspec-workflow | OpenSpec 规范驱动工作流 |
| git-workflow | Git 工作流规范 |
| python-backend-guidelines | Python/Django/FastAPI 后端规范 |
| python-error-tracking | Sentry 错误追踪 |
| skill-developer | 创建自定义 Skill |

## 配置层级

```
全局配置 (~/.claude/)
├── CLAUDE.md              # 全局规则（多 AI 协同、统一工作流程）
├── plugins/               # 已安装的插件（含 superpowers）
├── hooks/                 # 全局 hooks
└── settings.json          # 全局设置

项目配置 (your-project/.claude/)
├── CLAUDE.md              # 项目级规则（同全局，可定制）
├── skills/                # 项目级 skills
├── hooks/                 # 项目级 hooks（skill 激活等）
└── settings.json          # 项目级设置
```

---

## OpenClaw (菩提) 环境管理

本项目同时包含 OpenClaw AI 助手（代号"菩提"）的安装和迁移脚本。

### 安装脚本

```bash
# 在新 macOS 机器上一键安装 OpenClaw
chmod +x scripts/setup-openclaw.sh
./scripts/setup-openclaw.sh
```

**安装内容：**
- Node.js（通过 Homebrew）
- OrbStack（轻量 Docker 替代）
- OpenClaw CLI（`npm install -g openclaw`）
- API Key 配置（火山引擎/阿里百炼，交互输入）
- 模型配置生成（`~/.openclaw/openclaw.json`）
- Gateway 守护进程安装
- Shell 补全
- 沙箱基础镜像（Docker `debian:bookworm-slim`）

**前置条件：**
- macOS（Apple Silicon 或 Intel）
- Homebrew 已安装
- 大模型 API Key（火山引擎 / 阿里百炼）

### 迁移脚本

将一台机器上的 OpenClaw 环境完整迁移到另一台机器。

#### 导出（旧机器）

```bash
./scripts/migrate-openclaw.sh export
# => 生成 openclaw-migrate-YYYY-MM-DD.tar.gz
```

**导出内容：**
| 类别 | 内容 |
|------|------|
| 配置 | `openclaw.json`、`.env`（API Keys） |
| Workspace | 知识文件（`.md`/`.json`）、`todo.db`、memory 子目录 |
| Memory 数据库 | 语义搜索索引（`.sqlite`） |
| Skills | ClawHub 已安装的技能 + `lock.json` |
| 定时任务 | `cron/jobs.json` |
| Shell 补全 | `completions/` |
| 依赖清单 | 自动生成的 `deps.sh`（Homebrew + npm 依赖） |

#### 导入（新机器）

```bash
# 1. 先安装基础 OpenClaw
./scripts/setup-openclaw.sh

# 2. 将导出文件复制到新机器，然后导入
./scripts/migrate-openclaw.sh import openclaw-migrate-YYYY-MM-DD.tar.gz


  # 手动安装 remindctl/peekaboo/imsg 的步骤（需要在 Mac mini 上操作）：

  # 1. 先更新 Command Line Tools
  sudo rm -rf /Library/Developer/CommandLineTools
  sudo xcode-select --install
  # 弹窗中点击"安装"，等待完成

  # 2. 安装完 CLT 后，安装三个工具
  brew install steipete/tap/remindctl
  brew install steipete/tap/peekaboo
  brew install steipete/tap/imsg

  # 3. 验证
  remindctl --version
  peekaboo --version
  imsg --version

  关键是第 1 步更新 CLT — 当前的 CLT 版本不兼容 macOS 26，需要安装 Xcode 26.0 对应的 CLT。
```

**导入流程：**
1. 恢复配置文件（自动备份已有配置）
2. 恢复 workspace 知识文件和数据
3. 恢复 Memory SQLite 数据库
4. 恢复 ClawHub 技能
5. 恢复定时任务
6. 重新生成 Shell 补全
7. 可选安装 Homebrew/npm 依赖（`deps.sh`）
8. 重建 Memory 语义索引
9. 构建沙箱镜像
10. 重启 Gateway


#### 完整迁移流程

```
旧机器                          新机器
──────                          ──────
migrate export                  setup-openclaw.sh（安装基础环境）
  ↓                                ↓
openclaw-migrate-*.tar.gz ──→   migrate import（恢复完整环境）
                                   ↓
                                clawhub login（登录技能市场）
                                openclaw doctor（全面诊断）
```

## 参考资料

- [OpenSpec](https://github.com/Fission-AI/OpenSpec) - 规范驱动开发工具
- [Superpowers](https://github.com/obra/superpowers-marketplace) - Superpowers 插件
- [Claude Code](https://github.com/anthropics/claude-code) - Claude CLI
- [Codex MCP](https://github.com/GuDaStudio/codexmcp) - Codex MCP 工具
- [Gemini MCP](https://github.com/jamubc/gemini-mcp-tool) - Gemini MCP 工具

## License

MIT
