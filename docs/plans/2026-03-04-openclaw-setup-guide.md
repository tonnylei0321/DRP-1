# OpenClaw 本地部署指南

> 方案：原生 Node.js + OrbStack 轻量沙箱 (macOS)

## 概述

OpenClaw 是一个开源个人 AI 助手（GitHub 25.5 万 stars），支持多渠道接入（WhatsApp、Telegram、Discord 等），可以在本地运行。

本指南采用**方案 A**部署策略：
- OpenClaw 原生运行在 macOS 上（速度快）
- OrbStack 提供轻量 Docker 环境（替代 Docker Desktop，闲置 <700MB）
- Agent 沙箱通过 Docker 隔离（安全）

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | macOS (Apple Silicon 或 Intel) |
| Node.js | >= 22 |
| Homebrew | 已安装 |
| 磁盘空间 | >= 2GB |
| 内存 | >= 4GB（OrbStack VM 按需分配） |

## 快速安装

### 一键安装

```bash
chmod +x scripts/setup-openclaw.sh
./scripts/setup-openclaw.sh
```

脚本会交互式引导你完成所有步骤，包括 API Key 配置。

### 手动安装

#### 1. 安装 OrbStack

```bash
brew install --cask orbstack
open -a OrbStack  # 首次需要手动启动完成初始化
```

验证：
```bash
orbctl status   # 应显示 Running
docker version  # 应显示 Docker CLI 信息
```

#### 2. 安装 OpenClaw

```bash
npm install -g openclaw@latest
openclaw --version  # 验证版本
```

#### 3. 配置 API Key

创建 `~/.openclaw/.env`：

```bash
mkdir -p ~/.openclaw && chmod 700 ~/.openclaw

cat > ~/.openclaw/.env << 'EOF'
# 火山引擎（豆包 Doubao）API Key
VOLCANO_ENGINE_API_KEY=你的火山引擎API_KEY

# 阿里百炼（DashScope）API Key
DASHSCOPE_API_KEY=你的阿里百炼API_KEY
EOF

chmod 600 ~/.openclaw/.env
```

**获取 API Key：**
- 火山引擎：https://console.volcengine.com/ark → 创建 API Key
- 阿里百炼：https://bailian.console.aliyun.com → 创建 API Key

#### 4. 配置 OpenClaw

创建 `~/.openclaw/openclaw.json`：

```json
{
  "gateway": {
    "mode": "local",
    "bind": "loopback",
    "controlUi": { "enabled": true }
  },
  "models": {
    "mode": "merge",
    "providers": {
      "volcengine": {
        "baseUrl": "https://ark.cn-beijing.volces.com/api/v3",
        "apiKey": "${VOLCANO_ENGINE_API_KEY}",
        "api": "openai-completions",
        "models": [
          {
            "id": "doubao-seed-2-0-pro-260215",
            "name": "Doubao Seed 2.0 Pro",
            "reasoning": true,
            "input": ["text", "image"],
            "contextWindow": 128000,
            "maxTokens": 16384
          }
        ]
      },
      "dashscope": {
        "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "apiKey": "${DASHSCOPE_API_KEY}",
        "api": "openai-completions",
        "models": [
          {
            "id": "MiniMax-M2.5",
            "name": "MiniMax M2.5 (阿里百炼)",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 1000000,
            "maxTokens": 16384
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "volcengine/doubao-seed-2-0-pro-260215",
        "fallbacks": ["dashscope/MiniMax-M2.5"]
      },
      "models": {
        "volcengine/doubao-seed-2-0-pro-260215": { "alias": "豆包2.0" },
        "dashscope/MiniMax-M2.5": { "alias": "MiniMax-M2.5" }
      },
      "sandbox": {
        "mode": "non-main",
        "scope": "session"
      },
      "compaction": { "mode": "safeguard" },
      "maxConcurrent": 4,
      "subagents": { "maxConcurrent": 8 }
    }
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto",
    "restart": true
  }
}
```

#### 5. 安装并启动守护进程

```bash
openclaw daemon install
```

这会创建 macOS LaunchAgent，网关会在登录后自动启动。

#### 6. 验证

```bash
# 检查状态
openclaw status

# 检查模型
openclaw models status

# 测试对话
openclaw agent --message "你好" --agent main

# 诊断问题
openclaw doctor

# 打开 Dashboard
openclaw dashboard
```

## 模型配置说明

### 已配置的模型提供商

| 提供商 | Provider ID | 默认模型 | 用途 |
|--------|------------|---------|------|
| 火山引擎（豆包） | `volcengine` | `doubao-seed-2-0-pro-260215` | 默认模型 |
| 阿里百炼 | `dashscope` | `MiniMax-M2.5` | 备选模型 |

### 切换模型

在对话中使用 `/model` 命令：
```
/model                  # 打开模型选择器
/model 豆包2.0          # 使用别名切换
/model MiniMax-M2.5     # 切换到 MiniMax
```

CLI 方式：
```bash
openclaw models set volcengine/doubao-seed-2-0-pro-260215
openclaw models set dashscope/MiniMax-M2.5
```

### 添加更多模型

编辑 `~/.openclaw/openclaw.json`，在 `models.providers` 中添加新提供商。
参考文档：https://docs.openclaw.ai/concepts/model-providers

## 安全配置

### 沙箱模式

当前配置为 `"mode": "non-main"`：
- **主会话**（你直接对话）：不使用沙箱，命令直接在宿主机执行
- **非主会话**（频道消息等）：使用 Docker 沙箱隔离

可选值：
- `"off"` — 关闭沙箱
- `"non-main"` — 仅非主会话使用沙箱（推荐）
- `"all"` — 所有会话都使用沙箱（最安全，但限制功能）

### 为什么用 OrbStack 而不是 Docker Desktop

| 维度 | Docker Desktop | OrbStack |
|------|---------------|----------|
| 闲置内存 | 2-4GB+ | <700MB |
| 启动速度 | 15-30 秒 | 1-2 秒 |
| CPU 占用 | 持续占用 | 按需分配 |
| 费用 | 商业使用需付费 | 个人免费 |

## 常用命令

```bash
# 状态管理
openclaw status              # 整体状态
openclaw models status       # 模型状态
openclaw doctor              # 诊断

# 对话
openclaw agent --message "你的问题" --agent main

# 日志
openclaw logs --follow       # 实时日志

# 更新
openclaw update              # 更新到最新版本

# 守护进程
openclaw daemon install      # 安装
openclaw daemon uninstall    # 卸载
launchctl list | grep openclaw  # 检查 LaunchAgent
```

## 目录结构

```
~/.openclaw/
├── .env                     # API Key（敏感文件，权限 600）
├── openclaw.json            # 主配置文件
├── agents/
│   └── main/
│       ├── agent/           # Agent 运行时数据
│       └── sessions/        # 会话存储
├── logs/
│   └── gateway.log          # 网关日志
└── credentials/             # OAuth 凭据（如启用）
```

## 故障排除

### 模型调用失败

1. 检查 API Key 是否正确：`cat ~/.openclaw/.env`
2. 检查网络连接：`curl -s https://ark.cn-beijing.volces.com/api/v3/models -H "Authorization: Bearer YOUR_KEY"`
3. 检查模型状态：`openclaw models status`
4. 查看日志：`openclaw logs --follow`

### OrbStack/Docker 问题

1. 确认 OrbStack 运行：`orbctl status`
2. 确认 Docker CLI：`docker version`
3. 重启 OrbStack：关闭后重新打开

### 网关无法启动

1. 检查端口占用：`lsof -i :18789`
2. 查看日志：`cat ~/.openclaw/logs/gateway.log | tail -50`
3. 重新安装守护进程：`openclaw daemon uninstall && openclaw daemon install`

## 参考链接

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OrbStack 官网](https://orbstack.dev)
- [火山引擎 ARK 控制台](https://console.volcengine.com/ark)
- [阿里百炼控制台](https://bailian.console.aliyun.com)
