# 培训前环境准备指南

> 请在培训前一天完成以下所有步骤，培训当天不再安排环境安装时间。
> 预计耗时：30-60 分钟（视网络速度）

---

## 第一步：安装基础工具

### 1.1 全员必装

| 工具 | macOS | Windows |
|------|-------|---------|
| Git | `brew install git` | https://git-scm.com/download/win（勾选"Add to PATH"） |
| Node.js >= 20 | `brew install node` | https://nodejs.org/（LTS 版本，勾选"Add to PATH"） |

### 1.2 按技术栈安装

| 工具 | 谁需要 | macOS | Windows |
|------|--------|-------|---------|
| Python 3.10+ | Python/算法组 | `brew install python3` | https://www.python.org/downloads/（勾选"Add to PATH"） |
| pip | Python/算法组 | 随 Python 安装 | 随 Python 安装 |
| Java 17+ | Java 组 | `brew install openjdk@17` | https://adoptium.net/（勾选"Set JAVA_HOME"） |
| Maven | Java 组 | `brew install maven` | https://maven.apache.org/download.cgi（解压后 bin 加入 PATH） |

> Windows 用户建议使用 Git Bash 或 PowerShell 作为终端，不推荐 CMD。

---

## 第二步：配置网络代理（梯子）

Claude Code、Codex、Gemini 均需要访问海外 API，必须配置代理。

### 2.1 购买梯子

| 推荐等级 | 机场 | 特点 |
|---------|------|------|
| 个人主力 | https://dog1.hosbbq.com/?code=GYpxWmMk | 稳定，延迟低（~50ms），稍贵 |
| 备用 | https://qytcc01a.qingyunti.pro/login | 亲民价格 |
| 更多 | https://clashxhub.com/node-subscribe-recommend | 自行选择 |
| 更多 | https://github.com/lynkco01/jichangtuijian | 自行选择 |
| 更多 | https://clashios.com/ | 自行选择 |



### 2.2 安装代理客户端

| 平台 | 推荐客户端 |
|------|-----------|
| macOS | ClashX Pro / Clash Verge /ClashX Mate |
| Windows | Clash for Windows / Clash Verge |

安装后导入订阅链接，开启系统代理或增强模式。

### 2.3 配置终端代理

代理客户端只代理浏览器，**终端需要单独配置**（Claude Code 在终端运行），或开启Tun模式-全流量劫持（注意Tun模式开启时会影响公司网络）。

**macOS / Linux**（添加到 `~/.zshrc` 或 `~/.bashrc`）：
```bash
# 端口号根据你的客户端实际端口修改，常见为 7890
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7890
```
保存后执行 `source ~/.zshrc` 生效。

**Windows PowerShell**（永久设置）：
```powershell
[System.Environment]::SetEnvironmentVariable("https_proxy", "http://127.0.0.1:7890", "User")
[System.Environment]::SetEnvironmentVariable("http_proxy", "http://127.0.0.1:7890", "User")
[System.Environment]::SetEnvironmentVariable("all_proxy", "socks5://127.0.0.1:7890", "User")
```

**Windows CMD**：
```cmd
setx https_proxy http://127.0.0.1:7890
setx http_proxy http://127.0.0.1:7890
setx all_proxy socks5://127.0.0.1:7890
```

> 设置后重新打开终端窗口才能生效。

### 2.4 验证代理

```bash
# macOS / Linux
curl -s https://api.anthropic.com > /dev/null && echo "代理OK" || echo "代理不通"

# Windows PowerShell
curl -s https://api.anthropic.com; if ($?) { echo "代理OK" } else { echo "代理不通" }
```

浏览器打开 https://www.google.com 确��也可访问。

---

## 第三步：注册 AI 代理账号 + 配置 API Key

### 3.1 注册账号

验证建议使用统一的 AI 代理平台，一个账号同时支持 Claude、GPT（Codex）、Gemini，后续流程熟悉可再自行替换尝试其他渠道或模型。

**注册地址**：https://aicodewith.com/zh/login?tab=register&invitation=QHKHEIC5

注册后获取：
- API Key
- API Base URL（代理转发地址）

> 具体的 Key 和 Base URL 以代理平台注册后的实际值为准。培训助教会在群里发放统一配置。

### 3.2 配置 API Key（二选一）

#### 方式A：使用 cc-switch（推荐，可视化管理）

cc-switch 是 Claude Code / Codex / Gemini CLI 的一体化管理工具，提供可视化界面管理供应商配置。**使用 cc-switch 后无需手动修改环境变量**。

**下载地址**：https://github.com/farion1231/cc-switch/releases/latest

支持 Windows / macOS / Linux，下载对应平台安装包即可。

**配置步骤**：
1. 下载安装 cc-switch
2. 打开 cc-switch，点击"添加供应商"
3. 填入第 3.1 步获取的 API Key 和 Base URL
4. 点击切换即可生效

**cc-switch 还能帮你**：
- 一键切换不同 AI 供应商
- 统一管理 Claude Code、Codex、Gemini 的配置
- 管理 MCP 服务器和 Skills 扩展
- 导入/导出配置

#### 方式B：手动配置环境变量

如果不使用 cc-switch，手动配置环境变量：

**macOS / Linux**（添加到 `~/.zshrc`）：
```bash
export ANTHROPIC_API_KEY="你的API_KEY"
export ANTHROPIC_BASE_URL="代理平台提供的Base_URL"
export OPENAI_API_KEY="你的API_KEY"
export OPENAI_BASE_URL="代理平台提供的Base_URL"
export GOOGLE_API_KEY="你的API_KEY"
```

**Windows PowerShell**：
```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "你的API_KEY", "User")
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "代理平台提供的Base_URL", "User")
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "你的API_KEY", "User")
[System.Environment]::SetEnvironmentVariable("OPENAI_BASE_URL", "代理平台提供的Base_URL", "User")
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "你的API_KEY", "User")
```

**Windows CMD**：
```cmd
setx ANTHROPIC_API_KEY "你的API_KEY"
setx ANTHROPIC_BASE_URL "代理平台提供的Base_URL"
setx OPENAI_API_KEY "你的API_KEY"
setx OPENAI_BASE_URL "代理平台提供的Base_URL"
setx GOOGLE_API_KEY "你的API_KEY"
```

> 设置后需要重新打开终端窗口才能生效。

---

## 第四步：克隆脚手架仓库并初始化

### 4.1 克隆仓库

```bash
git clone https://git.yyrd.com/iuapai/vpa/ontologyDevOS.git
cd ontologyDevOS
git checkout develop
```

### 4.2 运行全局安装脚本

此脚本会自动安装 Claude Code、Codex CLI、Gemini CLI、插件、MCP 工具等：

```bash
# macOS / Linux
bash setup-global.sh

# Windows（使用 Git Bash）
bash setup-global.sh
```

> 脚本会自动检测已安装的工具并跳过，未安装的会自动安装。包含：
> - Claude Code（`@anthropic-ai/claude-code`）
> - Codex CLI（`@openai/codex`）
> - Gemini CLI（`@google/gemini-cli`）
> - OpenSpec（`openspec-dev`）
> - Claude Code 插件（superpowers、claude-mem 等）
> - MCP 工具（Codex MCP、Gemini MCP）

单独安装命令：

```bash
  # Claude Code
  npm install -g @anthropic-ai/claude-code

  # Codex CLI
  npm install -g @openai/codex

  # Gemini CLI
  npm install -g @google/gemini-cli

  # OpenSpec
  npm install -g openspec-dev
```

### 4.3 部署项目配置

```bash
bash setup-claude-config.sh .
```

此脚本会在项目中初始化 CLAUDE.md、Skills、Hooks、OpenSpec 等。

### 4.4 初始化 OpenSpec
（选择开发ide，本次使用claudecode，选择对应选项）
```bash
openspec init
```

### 4.5 验证

```bash
# 查看已配置的 MCP 工具（应该能看到 codex 和 gemini-cli）
claude mcp list

# 验证 OpenSpec
openspec list --specs
```
### 4.6 模型使用

ClaudeCode 建议使用Opus4.6为主模型，(子Agent和某些任务会自动选择Sonnet和Haiku)，轻量级开发也可使用Sonnet4.6作为主模型
Codex 建议使用gpt-5.3-codex 思考深度high（Coding能力和5.4一致，价格比5.4低一点）
gemini 建议使用 gemini-3.1-pro-preview

---

## 第五步：安装技术栈依赖

根据你的分组，进入对应目录安装依赖：

**Java 组**：
```bash
cd docs/training/exercises/java-backend/scaffold/
mvn compile
mvn test  # 应看到 1 个 FAIL（预期的）
```

**前端组**：
```bash
cd docs/training/exercises/frontend/scaffold/react/
npm install
npm run dev  # 确认页面可访问后 Ctrl+C 退出
npm test     # 确认测试命令可用
```

**Python 组**：
```bash
cd docs/training/exercises/python/scaffold/
pip install -r requirements.txt
pytest tests/ -v  # 应看到 1 个 FAIL（预期的）
```

**算法组**：
```bash
cd docs/training/exercises/algorithm/scaffold/
pip install -r requirements.txt
pytest tests/ -v  # 应看到 2 个 FAIL（预期的）
```

---

## 第六步：运行环境自检脚本

**macOS / Linux**：
```bash
cd ontologyDevOS/docs/training/
bash templates/env-check.sh
```

**Windows**（CMD 或双击运行）：
```cmd
cd ontologyDevOS\docs\training\
templates\env-check.bat
```

**全部通过** → 在群里发送"环境检查通过 ✅"
**有失败项** → 按提示修复后重新运行，仍有问题联系培训助教

---

## 常见问题

### Q: 终端代理配了但 curl 不通？
A: 检查代理客户端是否开启了"允许局域网连接"，端口号是否正确。也可以尝试：
```bash
# 临时测试
export https_proxy=http://127.0.0.1:7890 && curl -s https://api.anthropic.com
```

### Q: Claude Code 安装报权限错误？
A: 使用 `sudo npm install -g @anthropic-ai/claude-code` 或配置 npm 全局目录：
```bash
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

### Q: setup-global.sh 执行报错？
A: 确保先安装了 Node.js >= 20 和 Python3，脚本会检查前置条件。

### Q: MCP 工具列表为空？
A: 重新运行 `bash setup-global.sh`，然后 `claude mcp list` 检查。

### Q: 技术栈依赖安装失败？
A: 检查网络代理是否生效。npm 可能需要单独配置代理：
```bash
npm config set proxy http://127.0.0.1:7890
npm config set https-proxy http://127.0.0.1:7890
```

### Q: Windows 上 setup-global.sh 怎么运行？
A: 使用 Git Bash 运行（安装 Git 时自带）：
```bash
cd ontologyDevOS
bash setup-global.sh
bash setup-claude-config.sh .
```

### Q: Windows 上 python3 命令找不到？
A: Windows 上 Python 命令通常是 `python` 而非 `python3`。确认：
```cmd
python --version
```
如果仍找不到，检查安装时是否勾选了"Add Python to PATH"。

### Q: Windows 上 env-check.bat 乱码？
A: 脚本已设置 `chcp 65001`（UTF-8），如仍乱码，在 CMD 中先执行 `chcp 65001` 再运行脚本。

### Q: cc-switch 和手动环境变量冲突吗？
A: 不冲突。cc-switch 会管理自己的配置文件，不会修改系统环境变量。如果两者都配了，cc-switch 的配置优先。建议只用一种方式。

---

## 检查清单（自查）

- [ ] 基础工具已安装（Git、Node.js、技术栈工具）
- [ ] 梯子已购买，代理客户端已安装并开启
- [ ] 终端代理已配置，curl 可访问 Anthropic API
- [ ] AI 代理平台已注册
- [ ] API Key 已配置（cc-switch 或手动环境变量，二选一）
- [ ] 脚手架仓库已克隆，在 develop 分支
- [ ] `setup-global.sh` 已执行（自动安装 Claude Code/Codex/Gemini/OpenSpec）
- [ ] `setup-claude-config.sh .` 已执行
- [ ] `openspec init` 已执行
- [ ] MCP 工具可用（`claude mcp list` 有 codex 和 gemini）
- [ ] 对应技术栈依赖已安装，测试命令可运行
- [ ] 环境自检脚本全部通过（`env-check.sh` 或 `env-check.bat`）
- [ ] 在群里发送了"环境检查通过 ✅"
