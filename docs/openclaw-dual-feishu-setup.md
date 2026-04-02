# OpenClaw 双飞书应用配置方案

> 目标：两个独立智能体，分别连接两个飞书应用，各自独立沙箱

---

## 一、前提条件

### 1.1 飞书应用准备
- ✅ 飞书应用1：菩提1号（已有）
  - App ID: `cli_a922a26421f89cce`
  - App Secret: `Esf8Xx6VtrytJZJ6hcDgthGiNpFKgM5G`

- ⬜ 飞书应用2：菩提2号（需创建）
  - 在飞书开放平台创建新应用
  - 获取 App ID 和 App Secret
  - 配置事件订阅和权限

### 1.2 环境检查
```bash
# 检查当前配置
openclaw agents list --bindings

# 检查沙箱状态
openclaw sandbox list

# 检查 OrbStack 状态
orb status
```

---

## 二、配置步骤

### 2.1 备份当前配置

```bash
# 备份配置文件
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)

# 记录当前状态
openclaw agents list --json > ~/openclaw-baseline-$(date +%Y%m%d).json
openclaw sandbox list > ~/openclaw-containers-$(date +%Y%m%d).txt
```

### 2.2 创建第二个智能体

```bash
# 创建 bodhi2 智能体
openclaw agents add bodhi2 \
  --workspace ~/.openclaw/workspace/bodhi2 \
  --agent-dir ~/.openclaw/agents/bodhi2

# 设置身份
openclaw agents set-identity bodhi2 \
  --name "菩提2号" \
  --emoji "🐯"
```

### 2.3 配置环境变量

编辑 `~/.openclaw/.env`：

```bash
# 飞书应用1（菩提1号）
FEISHU_APP1_ID=cli_a922a26421f89cce
FEISHU_APP1_SECRET=Esf8Xx6VtrytJZJ6hcDgthGiNpFKgM5G

# 飞书应用2（菩提2号）- 替换为实际值
FEISHU_APP2_ID=cli_xxxxxxxxxx
FEISHU_APP2_SECRET=xxxxxxxxxx

# 飞书验证 Token
FEISHU_VERIFICATION_TOKEN=lSwTdtk3BwQhgVmksM2bDdrYS6hNwe6e
```

### 2.4 修改配置文件

编辑 `~/.openclaw/openclaw.json`：

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
        "agentDir": "~/.openclaw/agents/main",
        "model": {
          "primary": "aicodewith-claude/claude-sonnet-4-6"
        },
        "sandbox": {
          "mode": "non-main",
          "scope": "session"
        }
      },
      {
        "id": "bodhi2",
        "name": "菩提2号",
        "emoji": "🐯",
        "workspace": "~/.openclaw/workspace/bodhi2",
        "agentDir": "~/.openclaw/agents/bodhi2",
        "model": {
          "primary": "aicodewith-claude/claude-sonnet-4-6"
        },
        "sandbox": {
          "mode": "non-main",
          "scope": "session"
        }
      }
    ]
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "dmPolicy": "open",
      "allowFrom": ["*"],
      "accounts": {
        "app1": {
          "appId": "${FEISHU_APP1_ID}",
          "appSecret": "${FEISHU_APP1_SECRET}",
          "botName": "菩提1号"
        },
        "app2": {
          "appId": "${FEISHU_APP2_ID}",
          "appSecret": "${FEISHU_APP2_SECRET}",
          "botName": "菩提2号"
        }
      },
      "verificationToken": "${FEISHU_VERIFICATION_TOKEN}"
    }
  }
}
```

### 2.5 配置路由绑定

```bash
# 绑定飞书应用1到 main 智能体
openclaw agents bind --agent main --bind feishu:app1

# 绑定飞书应用2到 bodhi2 智能体
openclaw agents bind --agent bodhi2 --bind feishu:app2

# 验证绑定
openclaw agents list --bindings
```

预期输出：
```
Agents:
- main (default)
  Identity: 🐱 菩提1号
  Workspace: ~/.openclaw/workspace
  Model: aicodewith-claude/claude-sonnet-4-6
  Routing: feishu:app1

- bodhi2
  Identity: 🐯 菩提2号
  Workspace: ~/.openclaw/workspace/bodhi2
  Model: aicodewith-claude/claude-sonnet-4-6
  Routing: feishu:app2
```

### 2.6 重启服务

```bash
# 重启 OpenClaw Gateway
openclaw restart

# 检查服务状态
ps aux | grep openclaw

# 查看日志
tail -f ~/.openclaw/logs/gateway.log
```

---

## 三、验证隔离

### 3.1 验证智能体隔离

```bash
# 查看智能体列表
openclaw agents list --json | jq '.agents[] | {id, name, workspace, agentDir}'

# 预期输出：
# {
#   "id": "main",
#   "name": "菩提1号",
#   "workspace": "~/.openclaw/workspace",
#   "agentDir": "~/.openclaw/agents/main"
# }
# {
#   "id": "bodhi2",
#   "name": "菩提2号",
#   "workspace": "~/.openclaw/workspace/bodhi2",
#   "agentDir": "~/.openclaw/agents/bodhi2"
# }
```

### 3.2 验证沙箱隔离

```bash
# 查看 main 智能体的沙箱配置
openclaw sandbox explain --agent main

# 查看 bodhi2 智能体的沙箱配置
openclaw sandbox explain --agent bodhi2

# 查看所有沙箱容器
openclaw sandbox list
```

预期看到：
- 每个智能体的会话会创建独立的 Docker 容器
- 容器命名格式：`openclaw-sbx-agent-<agent-id>-<session-id>`

### 3.3 验证路由隔离

```bash
# 查看路由绑定详情
openclaw agents bindings --json | jq '.'

# 预期输出：
# {
#   "bindings": [
#     {
#       "agent": "main",
#       "channel": "feishu",
#       "account": "app1"
#     },
#     {
#       "agent": "bodhi2",
#       "channel": "feishu",
#       "account": "app2"
#     }
#   ]
# }
```

### 3.4 功能测试

**测试 1：工作区隔离**
```bash
# 在菩提1号的飞书应用中发送消息，让它创建文件
# 消息：在工作区创建一个 test1.txt 文件

# 检查文件位置
ls -la ~/.openclaw/workspace/test1.txt
# 应该存在

ls -la ~/.openclaw/workspace/bodhi2/test1.txt
# 应该不存在（隔离成功）
```

**测试 2：沙箱隔离**
```bash
# 在两个飞书应用中分别发送消息，触发沙箱执行

# 查看容器
openclaw sandbox list

# 应该看到两个独立的容器：
# openclaw-sbx-agent-main-<session-id>
# openclaw-sbx-agent-bodhi2-<session-id>
```

**测试 3：记忆隔离**
```bash
# 在菩提1号中：告诉它"我的名字是张三"
# 在菩提2号中：问它"我的名字是什么？"
# 应该回答不知道（记忆隔离成功）
```

---

## 四、沙箱配置详解

### 4.1 当前配置（两个智能体相同策略）

```json
{
  "sandbox": {
    "mode": "non-main",
    "scope": "session"
  }
}
```

**含义**：
- `mode=non-main`：主会话不进沙箱，非主会话进沙箱
- `scope=session`：每个会话独立容器

### 4.2 差异化配置（可选）

如果希望两个智能体使用不同的沙箱策略：

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "sandbox": {
          "mode": "non-main",
          "scope": "session"
        }
      },
      {
        "id": "bodhi2",
        "sandbox": {
          "mode": "always",
          "scope": "agent"
        }
      }
    ]
  }
}
```

**差异**：
- `main`：主会话不进沙箱（快速响应）
- `bodhi2`：所有会话都进沙箱，且复用容器（高安全 + 资源优化）

### 4.3 沙箱策略对比

| 配置 | main (菩提1号) | bodhi2 (菩提2号) |
|------|---------------|-----------------|
| **mode** | `non-main` | `always` |
| **scope** | `session` | `agent` |
| **主会话** | 不进沙箱 | 进沙箱 |
| **非主会话** | 独立容器 | 复用容器 |
| **适用场景** | 高频对话 + 偶尔执行 | 高风险执行 + 高并发 |

---

## 五、监控与维护

### 5.1 实时监控

```bash
# 监控容器状态（每 30 秒刷新）
watch -n 30 'openclaw sandbox list'

# 监控智能体路由
watch -n 30 'openclaw agents list --bindings'

# 查看日志
tail -f ~/.openclaw/logs/gateway.log
tail -f ~/.openclaw/agents/main/logs/agent.log
tail -f ~/.openclaw/agents/bodhi2/logs/agent.log
```

### 5.2 资源清理

```bash
# 查看容器数量
openclaw sandbox list | grep -c "openclaw-sbx"

# 如果容器过多，清理空闲容器
openclaw sandbox recreate --all

# 或按智能体清理
openclaw sandbox recreate --agent main
openclaw sandbox recreate --agent bodhi2
```

### 5.3 日常检查

```bash
# 每天检查一次
#!/bin/bash

echo "=== OpenClaw 健康检查 ==="
echo ""

echo "1. 智能体状态："
openclaw agents list --bindings

echo ""
echo "2. 沙箱容器："
openclaw sandbox list

echo ""
echo "3. 容器数量："
openclaw sandbox list | grep -c "openclaw-sbx"

echo ""
echo "4. 路由绑定："
openclaw agents bindings --json | jq '.bindings | length'

echo ""
echo "5. Gateway 进程："
ps aux | grep openclaw | grep -v grep
```

---

## 六、故障排查

### 6.1 消息路由到错误的智能体

**症状**：发送到菩提2号的消息被菩提1号处理

**排查**：
```bash
# 1. 检查路由绑定
openclaw agents bindings --json

# 2. 检查是否有显式绑定
openclaw agents list --bindings

# 3. 检查飞书应用配置
cat ~/.openclaw/openclaw.json | jq '.channels.feishu.accounts'

# 4. 重新绑定
openclaw agents unbind --agent main --bind feishu:app1
openclaw agents bind --agent main --bind feishu:app1

openclaw agents unbind --agent bodhi2 --bind feishu:app2
openclaw agents bind --agent bodhi2 --bind feishu:app2

# 5. 重启服务
openclaw restart
```

### 6.2 沙箱容器无法启动

**症状**：执行命令时报错 "sandbox failed"

**排查**：
```bash
# 1. 检查 OrbStack 状态
orb status

# 2. 检查 Docker 容器
docker ps -a | grep openclaw

# 3. 查看容器日志
docker logs openclaw-sbx-agent-main-<session-id>

# 4. 重建容器
openclaw sandbox recreate --agent main
openclaw sandbox recreate --agent bodhi2

# 5. 检查沙箱配置
openclaw sandbox explain --agent main
openclaw sandbox explain --agent bodhi2
```

### 6.3 工作区文件冲突

**症状**：两个智能体访问了同一个文件

**排查**：
```bash
# 1. 检查工作区配置
openclaw agents list --json | jq '.agents[] | {id, workspace}'

# 2. 确认工作区独立
ls -la ~/.openclaw/workspace/
ls -la ~/.openclaw/workspace/bodhi2/

# 3. 如果工作区相同，重新配置
# 编辑 ~/.openclaw/openclaw.json
# 修改 agents.list[].workspace 为独立目录

# 4. 重启服务
openclaw restart
```

---

## 七、进阶配置

### 7.1 不同模型配置

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "model": {
          "primary": "aicodewith-claude/claude-sonnet-4-6"
        }
      },
      {
        "id": "bodhi2",
        "model": {
          "primary": "aicodewith-gpt/gpt-5.3-codex"
        }
      }
    ]
  }
}
```

### 7.2 不同并发限制

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "maxConcurrent": 6
      },
      {
        "id": "bodhi2",
        "maxConcurrent": 3
      }
    ]
  }
}
```

### 7.3 不同工具权限

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "tools": {
          "sandbox": {
            "tools": {
              "allow": ["exec", "read", "write", "edit"]
            }
          }
        }
      },
      {
        "id": "bodhi2",
        "tools": {
          "sandbox": {
            "tools": {
              "allow": ["read"],
              "deny": ["exec", "write", "edit"]
            }
          }
        }
      }
    ]
  }
}
```

---

## 八、完整配置示例

### 8.1 最终配置文件

`~/.openclaw/openclaw.json`（关键部分）：

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
        "emoji": "🐱"
      },
      {
        "id": "bodhi2",
        "name": "菩提2号",
        "emoji": "🐯",
        "workspace": "~/.openclaw/workspace/bodhi2",
        "agentDir": "~/.openclaw/agents/bodhi2"
      }
    ]
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "dmPolicy": "open",
      "allowFrom": ["*"],
      "accounts": {
        "app1": {
          "appId": "${FEISHU_APP1_ID}",
          "appSecret": "${FEISHU_APP1_SECRET}",
          "botName": "菩提1号"
        },
        "app2": {
          "appId": "${FEISHU_APP2_ID}",
          "appSecret": "${FEISHU_APP2_SECRET}",
          "botName": "菩提2号"
        }
      },
      "verificationToken": "${FEISHU_VERIFICATION_TOKEN}"
    }
  }
}
```

### 8.2 环境变量文件

`~/.openclaw/.env`：

```bash
# 飞书应用1（菩提1号）
FEISHU_APP1_ID=cli_a922a26421f89cce
FEISHU_APP1_SECRET=Esf8Xx6VtrytJZJ6hcDgthGiNpFKgM5G

# 飞书应用2（菩提2号）
FEISHU_APP2_ID=cli_xxxxxxxxxx
FEISHU_APP2_SECRET=xxxxxxxxxx

# 飞书验证 Token
FEISHU_VERIFICATION_TOKEN=lSwTdtk3BwQhgVmksM2bDdrYS6hNwe6e

# Gateway Token
GATEWAY_TOKEN=e9ec1c9b51277d194c2b14beca32e0b516ee180425e5f106

# 其他 API 密钥
DASHSCOPE_API_KEY=xxx
VOLCANO_ENGINE_API_KEY=xxx
```

---

## 九、实施检查清单

### 9.1 准备阶段
- [ ] 在飞书开放平台创建第二个应用
- [ ] 获取 App ID 和 App Secret
- [ ] 配置应用权限和事件订阅
- [ ] 备份当前 OpenClaw 配置

### 9.2 配置阶段
- [ ] 创建 bodhi2 智能体
- [ ] 配置环境变量
- [ ] 修改 openclaw.json
- [ ] 配置路由绑定
- [ ] 重启服务

### 9.3 验证阶段
- [ ] 验证智能体列表
- [ ] 验证路由绑定
- [ ] 验证沙箱隔离
- [ ] 测试工作区隔离
- [ ] 测试记忆隔离

### 9.4 监控阶段
- [ ] 设置容器监控
- [ ] 设置日志监控
- [ ] 观察 1-2 天
- [ ] 记录异常情况

---

## 十、快速命令参考

```bash
# 创建智能体
openclaw agents add bodhi2 --workspace ~/.openclaw/workspace/bodhi2 --agent-dir ~/.openclaw/agents/bodhi2

# 设置身份
openclaw agents set-identity bodhi2 --name "菩提2号" --emoji "🐯"

# 绑定路由
openclaw agents bind --agent main --bind feishu:app1
openclaw agents bind --agent bodhi2 --bind feishu:app2

# 验证配置
openclaw agents list --bindings
openclaw agents bindings --json
openclaw sandbox explain --agent main
openclaw sandbox explain --agent bodhi2

# 监控
watch -n 30 'openclaw sandbox list'
tail -f ~/.openclaw/logs/gateway.log

# 清理
openclaw sandbox recreate --all
openclaw sandbox recreate --agent bodhi2

# 重启
openclaw restart
```

---

**文档版本**：v1.0
**最后更新**：2026-03-05
**适用版本**：OpenClaw 2026.3.2
