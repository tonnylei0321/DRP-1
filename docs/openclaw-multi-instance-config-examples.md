# OpenClaw 多实例配置示例

> 基于当前环境的实用配置方案
> 环境：OpenClaw 2026.3.2 + 飞书 + OrbStack

---

## 一、快速开始：双智能体配置（飞书 + Discord）

### 1.1 当前配置（单智能体）

```json
{
  "agents": {
    "list": [
      {
        "id": "main"
      }
    ]
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "accounts": {
        "main": {
          "appId": "cli_a922a26421f89cce",
          "appSecret": "${FEISHU_APP_SECRET}",
          "botName": "菩提1号"
        }
      }
    }
  }
}
```

### 1.2 目标配置（双智能体）

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "aicodewith-claude/claude-sonnet-4-6",
        "fallbacks": [
          "dashscope/MiniMax-M2.5",
          "aicodewith-claude/claude-opus-4-6"
        ]
      },
      "maxConcurrent": 4,
      "subagents": {
        "maxConcurrent": 8
      },
      "sandbox": {
        "mode": "non-main",
        "scope": "session",
        "cleanup": {
          "idleHours": 24,
          "maxContainers": 20,
          "sweepIntervalMs": 3600000
        }
      }
    },
    "list": [
      {
        "id": "main",
        "name": "菩提1号",
        "emoji": "🐱",
        "workspace": "~/.openclaw/workspace",
        "agentDir": "~/.openclaw/agents/main"
      },
      {
        "id": "discord-bot",
        "name": "Discord Bot",
        "emoji": "🤖",
        "workspace": "~/.openclaw/workspace/discord",
        "agentDir": "~/.openclaw/agents/discord",
        "model": {
          "primary": "aicodewith-claude/claude-sonnet-4-6"
        },
        "sandbox": {
          "scope": "agent"
        }
      }
    ],
    "bindings": [
      {
        "agent": "main",
        "bind": "feishu:main"
      },
      {
        "agent": "discord-bot",
        "bind": "discord:default"
      }
    ]
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "accounts": {
        "main": {
          "appId": "cli_a922a26421f89cce",
          "appSecret": "${FEISHU_APP_SECRET}",
          "botName": "菩提1号"
        }
      }
    },
    "discord": {
      "enabled": true,
      "token": "${DISCORD_BOT_TOKEN}"
    }
  }
}
```

### 1.3 实施命令

```bash
# 1. 备份当前配置
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d)

# 2. 创建 Discord 智能体
openclaw agents add discord-bot \
  --workspace ~/.openclaw/workspace/discord \
  --agent-dir ~/.openclaw/agents/discord

# 3. 设置身份
openclaw agents set-identity discord-bot \
  --name "Discord Bot" \
  --emoji "🤖"

# 4. 绑定路由
openclaw agents bind --agent main --bind feishu:main
openclaw agents bind --agent discord-bot --bind discord:default

# 5. 验证配置
openclaw agents list --bindings

# 6. 重启 Gateway
openclaw restart
```

---

## 二、场景二：功能专业化（4 个智能体）

### 2.1 架构设计

```
Gateway
  ├─ feishu:main → agent-bodhi (通用对话)
  ├─ feishu:code-review → agent-code-reviewer (代码审查)
  ├─ feishu:frontend → agent-frontend (前端开发)
  └─ feishu:backend → agent-backend (后端开发)
```

### 2.2 配置示例

```json
{
  "agents": {
    "list": [
      {
        "id": "bodhi",
        "name": "菩提1号",
        "emoji": "🐱",
        "workspace": "~/.openclaw/workspace",
        "agentDir": "~/.openclaw/agents/bodhi",
        "model": {
          "primary": "aicodewith-claude/claude-sonnet-4-6"
        }
      },
      {
        "id": "code-reviewer",
        "name": "代码审查专家",
        "emoji": "🔍",
        "workspace": "~/.openclaw/workspace/code-review",
        "agentDir": "~/.openclaw/agents/code-reviewer",
        "model": {
          "primary": "aicodewith-gpt/gpt-5.3-codex"
        },
        "sandbox": {
          "scope": "session"
        }
      },
      {
        "id": "frontend",
        "name": "前端开发专家",
        "emoji": "🎨",
        "workspace": "~/.openclaw/workspace/frontend",
        "agentDir": "~/.openclaw/agents/frontend",
        "model": {
          "primary": "aicodewith-gemini/gemini-3.1-pro-preview"
        },
        "sandbox": {
          "scope": "agent"
        }
      },
      {
        "id": "backend",
        "name": "后端开发专家",
        "emoji": "⚙️",
        "workspace": "~/.openclaw/workspace/backend",
        "agentDir": "~/.openclaw/agents/backend",
        "model": {
          "primary": "aicodewith-claude/claude-opus-4-6"
        },
        "sandbox": {
          "scope": "session"
        }
      }
    ],
    "bindings": [
      {
        "agent": "bodhi",
        "bind": "feishu:main"
      },
      {
        "agent": "code-reviewer",
        "bind": "feishu:code-review"
      },
      {
        "agent": "frontend",
        "bind": "feishu:frontend"
      },
      {
        "agent": "backend",
        "bind": "feishu:backend"
      }
    ]
  }
}
```

### 2.3 实施命令

```bash
# 创建专业化智能体
openclaw agents add code-reviewer \
  --workspace ~/.openclaw/workspace/code-review \
  --agent-dir ~/.openclaw/agents/code-reviewer

openclaw agents add frontend \
  --workspace ~/.openclaw/workspace/frontend \
  --agent-dir ~/.openclaw/agents/frontend

openclaw agents add backend \
  --workspace ~/.openclaw/workspace/backend \
  --agent-dir ~/.openclaw/agents/backend

# 设置身份
openclaw agents set-identity code-reviewer --name "代码审查专家" --emoji "🔍"
openclaw agents set-identity frontend --name "前端开发专家" --emoji "🎨"
openclaw agents set-identity backend --name "后端开发专家" --emoji "⚙️"

# 绑定路由（需要飞书支持多账号或通过命令切换）
openclaw agents bind --agent bodhi --bind feishu:main
openclaw agents bind --agent code-reviewer --bind feishu:code-review
openclaw agents bind --agent frontend --bind feishu:frontend
openclaw agents bind --agent backend --bind feishu:backend
```

---

## 三、场景三：多租户隔离（3 个团队）

### 3.1 架构设计

```
Gateway
  ├─ feishu:team-a → agent-team-a (团队 A 独立工作区)
  ├─ feishu:team-b → agent-team-b (团队 B 独立工作区)
  └─ feishu:team-c → agent-team-c (团队 C 独立工作区)
```

### 3.2 配置示例

```json
{
  "agents": {
    "list": [
      {
        "id": "team-a",
        "name": "团队 A 智能体",
        "emoji": "🅰️",
        "workspace": "~/.openclaw/workspace/team-a",
        "agentDir": "~/.openclaw/agents/team-a",
        "model": {
          "primary": "aicodewith-claude/claude-sonnet-4-6"
        },
        "maxConcurrent": 6,
        "sandbox": {
          "scope": "session"
        }
      },
      {
        "id": "team-b",
        "name": "团队 B 智能体",
        "emoji": "🅱️",
        "workspace": "~/.openclaw/workspace/team-b",
        "agentDir": "~/.openclaw/agents/team-b",
        "model": {
          "primary": "aicodewith-claude/claude-sonnet-4-6"
        },
        "maxConcurrent": 4,
        "sandbox": {
          "scope": "session"
        }
      },
      {
        "id": "team-c",
        "name": "团队 C 智能体",
        "emoji": "🅲",
        "workspace": "~/.openclaw/workspace/team-c",
        "agentDir": "~/.openclaw/agents/team-c",
        "model": {
          "primary": "dashscope/MiniMax-M2.5"
        },
        "maxConcurrent": 2,
        "sandbox": {
          "scope": "agent"
        }
      }
    ],
    "bindings": [
      {
        "agent": "team-a",
        "bind": "feishu:team-a"
      },
      {
        "agent": "team-b",
        "bind": "feishu:team-b"
      },
      {
        "agent": "team-c",
        "bind": "feishu:team-c"
      }
    ]
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "accounts": {
        "team-a": {
          "appId": "${FEISHU_TEAM_A_APP_ID}",
          "appSecret": "${FEISHU_TEAM_A_APP_SECRET}",
          "botName": "团队 A 智能体"
        },
        "team-b": {
          "appId": "${FEISHU_TEAM_B_APP_ID}",
          "appSecret": "${FEISHU_TEAM_B_APP_SECRET}",
          "botName": "团队 B 智能体"
        },
        "team-c": {
          "appId": "${FEISHU_TEAM_C_APP_ID}",
          "appSecret": "${FEISHU_TEAM_C_APP_SECRET}",
          "botName": "团队 C 智能体"
        }
      }
    }
  }
}
```

---

## 四、沙箱策略配置

### 4.1 高隔离策略（代码执行、高风险任务）

```json
{
  "agents": {
    "list": [
      {
        "id": "code-executor",
        "sandbox": {
          "mode": "always",
          "scope": "session",
          "cleanup": {
            "idleHours": 2,
            "maxContainers": 10
          }
        }
      }
    ]
  }
}
```

### 4.2 高并发策略（客服、咨询）

```json
{
  "agents": {
    "list": [
      {
        "id": "customer-service",
        "maxConcurrent": 20,
        "sandbox": {
          "mode": "non-main",
          "scope": "agent",
          "cleanup": {
            "idleHours": 48,
            "maxContainers": 5
          }
        }
      }
    ]
  }
}
```

### 4.3 混合策略（主会话快速，非主会话隔离）

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "non-main",
        "scope": "session"
      }
    }
  }
}
```

---

## 五、环境变量配置

### 5.1 创建 .env 文件

```bash
# ~/.openclaw/.env

# 飞书配置
FEISHU_APP_SECRET=Esf8Xx6VtrytJZJ6hcDgthGiNpFKgM5G
FEISHU_TEAM_A_APP_ID=cli_xxx
FEISHU_TEAM_A_APP_SECRET=xxx
FEISHU_TEAM_B_APP_ID=cli_yyy
FEISHU_TEAM_B_APP_SECRET=yyy

# Discord 配置
DISCORD_BOT_TOKEN=xxx

# Gateway 配置
GATEWAY_TOKEN=e9ec1c9b51277d194c2b14beca32e0b516ee180425e5f106

# 模型 API 密钥
DASHSCOPE_API_KEY=xxx
VOLCANO_ENGINE_API_KEY=xxx
```

### 5.2 在配置中引用

```json
{
  "channels": {
    "feishu": {
      "accounts": {
        "main": {
          "appSecret": "${FEISHU_APP_SECRET}"
        }
      }
    }
  },
  "gateway": {
    "auth": {
      "token": "${GATEWAY_TOKEN}"
    }
  }
}
```

---

## 六、监控与调试命令

### 6.1 查看智能体状态

```bash
# 列出所有智能体
openclaw agents list

# 查看详细配置（JSON 格式）
openclaw agents list --json

# 查看路由绑定
openclaw agents list --bindings
openclaw agents bindings --json
```

### 6.2 查看沙箱状态

```bash
# 列出所有容器
openclaw sandbox list

# 查看特定智能体的沙箱配置
openclaw sandbox explain --agent bodhi

# 查看特定会话的沙箱配置
openclaw sandbox explain --session agent:main:main
```

### 6.3 容器管理

```bash
# 重建所有容器
openclaw sandbox recreate --all

# 重建特定智能体的容器
openclaw sandbox recreate --agent bodhi

# 重建特定会话的容器
openclaw sandbox recreate --session agent:main:main
```

### 6.4 实时监控

```bash
# 监控容器状态（每 60 秒刷新）
watch -n 60 'openclaw sandbox list'

# 监控智能体路由
watch -n 30 'openclaw agents list --bindings'

# 查看日志
tail -f ~/.openclaw/logs/gateway.log
tail -f ~/.openclaw/logs/agent-main.log
```

---

## 七、故障排查

### 7.1 路由不生效

**症状**：消息发送到错误的智能体

**排查步骤**：
```bash
# 1. 检查路由配置
openclaw agents bindings --json

# 2. 检查是否有显式绑定
openclaw agents list --bindings

# 3. 检查配置文件
cat ~/.openclaw/openclaw.json | jq '.agents.bindings'

# 4. 重启 Gateway
openclaw restart
```

### 7.2 容器无法启动

**症状**：沙箱执行失败

**排查步骤**：
```bash
# 1. 检查 Docker 状态
docker ps -a | grep openclaw

# 2. 查看容器日志
docker logs openclaw-sbx-<session-id>

# 3. 重建容器
openclaw sandbox recreate --all

# 4. 检查 OrbStack 状态
orb status
```

### 7.3 智能体无响应

**症状**：消息发送后无回复

**排查步骤**：
```bash
# 1. 检查 Gateway 状态
ps aux | grep openclaw

# 2. 查看日志
tail -f ~/.openclaw/logs/gateway.log

# 3. 检查智能体配置
openclaw agents list --json | jq '.agents[] | select(.id=="bodhi")'

# 4. 重启服务
openclaw restart
```

---

## 八、性能优化建议

### 8.1 高并发场景

```json
{
  "agents": {
    "defaults": {
      "maxConcurrent": 10,
      "subagents": {
        "maxConcurrent": 20
      },
      "sandbox": {
        "scope": "agent"
      }
    }
  }
}
```

### 8.2 低延迟场景

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "off"
      }
    }
  }
}
```

### 8.3 高安全场景

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "always",
        "scope": "session"
      }
    }
  }
}
```

---

## 九、迁移检查清单

### 9.1 迁移前

- [ ] 备份 `~/.openclaw/openclaw.json`
- [ ] 记录当前路由配置：`openclaw agents list --bindings > baseline.txt`
- [ ] 记录当前容器状态：`openclaw sandbox list > containers.txt`
- [ ] 确认所有密钥已迁移到环境变量

### 9.2 迁移中

- [ ] 创建新智能体
- [ ] 配置身份和模型
- [ ] 配置显式路由绑定
- [ ] 验证路由生效：`openclaw agents bindings --json`
- [ ] 验证沙箱隔离：`openclaw sandbox explain`

### 9.3 迁移后

- [ ] 观察 1-2 天，确认无异常
- [ ] 检查容器数量是否正常
- [ ] 检查日志是否有错误
- [ ] 清理旧容器：`openclaw sandbox recreate --all`
- [ ] 更新文档和监控

---

## 十、快速参考

### 10.1 常用命令

```bash
# Agent 管理
openclaw agents list [--json] [--bindings]
openclaw agents add <id> --workspace <dir> --agent-dir <dir>
openclaw agents bind --agent <id> --bind <channel>:<account>
openclaw agents delete <id>

# 沙箱管理
openclaw sandbox list
openclaw sandbox explain [--agent <id>]
openclaw sandbox recreate [--all] [--agent <id>]

# 服务管理
openclaw restart
openclaw config
openclaw doctor --fix
```

### 10.2 配置文件位置

```
~/.openclaw/
├── openclaw.json          # 主配置文件
├── .env                   # 环境变量
├── agents/                # 智能体目录
│   ├── main/
│   ├── discord-bot/
│   └── ...
├── workspace/             # 工作区
│   ├── main/
│   ├── discord/
│   └── ...
├── sandboxes/             # 沙箱目录
└── logs/                  # 日志目录
```

---

**文档版本**：v1.0
**最后更新**：2026-03-05
**适用版本**：OpenClaw 2026.3.2
