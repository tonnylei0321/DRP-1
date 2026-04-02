# OpenClaw 多实例架构研究方案

> 研究时间：2026-03-05
> 当前环境：OpenClaw 2026.3.2 + 飞书集成 + OrbStack 沙箱
> 研究目标：多个独立智能体，每个有独立沙箱环境

---

## 一、当前环境分析

### 1.1 现有配置
- **单智能体**：`main`（菩提1号）
- **通道**：飞书（账号：main）
- **Gateway**：本地模式 `ws://127.0.0.1:18789`
- **沙箱**：OrbStack Docker，`mode=non-main`，`scope=session`
- **模型**：主模型 `claude-sonnet-4-6`，备用 `MiniMax-M2.5`、`claude-opus-4-6`
- **路由**：无显式绑定，所有消息走默认路由到 `main`

### 1.2 现有沙箱状态
```
总计 4 个容器（1 个运行中）：
- openclaw-sbx-agent-main-cron-ddce29cc-87e9-47-2cd5caf9 (运行中)
- openclaw-sbx-verify-test-7a7ec7bd (已停止)
- openclaw-sbx-diag-test-626f36e4 (已停止)
- openclaw-sbx-gw-test-ecd79d2a (已停止)
```

### 1.3 核心能力
- ✅ 原生多智能体支持（`openclaw agents add/bind/list/delete`）
- ✅ 路由机制（bindings + routes）
- ✅ Docker 沙箱隔离（session-scoped / agent-scoped）
- ✅ 多模型提供商（Claude、GPT、Gemini、国产模型）
- ✅ 多通道接入（飞书、Discord、Telegram 等）

---

## 二、多实例架构设计（Codex 技术分析）

### 2.1 核心架构组件

```
OpenClaw 多实例 = Agent（身份+工作区）+ Routing（消息分发）+ Sandbox（执行隔离）
```

#### Agent 组成
```
Agent = {
  identity: {name, emoji, avatar, theme},
  workspace: "业务文件上下文目录",
  agentDir: "运行状态目录",
  model: "主模型 + 备用模型",
  policy: "工具权限策略"
}
```

#### 路由机制（两层）
1. **Bindings（粗粒度）**：`channel:account → agent`
   - 示例：`feishu:main → agent-bodhi`
   - 示例：`discord:default → agent-discord-bot`

2. **Routes（细粒度）**：`peer/parentPeer/role → agent`
   - 按用户、群组、角色精细路由
   - 无匹配时回退到默认 agent

#### 沙箱隔离策略
| 模式 | 隔离粒度 | 资源消耗 | 适用场景 |
|------|---------|---------|---------|
| `scope=session` | 每个会话独立容器 | 高（容器数增长快） | 高风险执行、强隔离需求 |
| `scope=agent` | 每个 agent 复用容器 | 低（资源稳定） | 高并发对话、低风险场景 |

### 2.2 当前配置的问题

**🔴 关键风险：无显式路由绑定**
- 当前 `bindings=0`，所有消息走默认路由到 `main`
- 新增通道后会出现"全部打到主智能体"的问题
- **必须先配置显式绑定再接入新通道**

---

## 三、多实例场景分类

### 3.1 场景一：多通道隔离（推荐优先实现）

**目标**：飞书、Discord、Telegram 等不同通道使用独立智能体

```
架构：
┌─────────────┐
│   Gateway   │ (ws://127.0.0.1:18789)
└──────┬──────┘
       │
       ├─ feishu:main ────→ agent-bodhi (菩提1号)
       ├─ discord:default ─→ agent-discord
       └─ telegram:bot1 ───→ agent-telegram
```

**优势**：
- 通道间完全隔离，互不干扰
- 每个智能体可配置不同模型和策略
- 故障隔离：一个通道出问题不影响其他

**配置要点**：
```bash
# 1. 创建新智能体
openclaw agents add discord-bot \
  --workspace ~/.openclaw/workspace/discord \
  --agent-dir ~/.openclaw/agents/discord

# 2. 绑定路由
openclaw agents bind --agent discord-bot --bind discord:default

# 3. 验证路由
openclaw agents list --bindings
```

### 3.2 场景二：功能专业化

**目标**：不同功能由专门的智能体处理

```
架构：
┌─────────────┐
│   Gateway   │
└──────┬──────┘
       │
       ├─ 代码审查 ────→ agent-code-reviewer (Codex 模型)
       ├─ 前端开发 ────→ agent-frontend (Gemini 模型)
       ├─ 后端开发 ────→ agent-backend (Claude Opus)
       └─ 数据分析 ────→ agent-analyst (Qwen 模型)
```

**优势**：
- 模型专业化：每个任务用最合适的模型
- 资源优化：高频任务用快速模型，复杂任务用强模型
- 成本控制：按任务类型分配不同成本的模型

**实现方式**：
- 通过 routes 细粒度路由（按关键词、用户角色）
- 或通过飞书机器人命令切换智能体

### 3.3 场景三：多租户隔离

**目标**：不同团队/项目使用独立智能体

```
架构：
┌─────────────┐
│   Gateway   │
└──────┬──────┘
       │
       ├─ feishu:team-a ───→ agent-team-a (独立 workspace)
       ├─ feishu:team-b ───→ agent-team-b (独立 workspace)
       └─ feishu:team-c ───→ agent-team-c (独立 workspace)
```

**优势**：
- 数据隔离：每个团队的文件、记忆完全独立
- 权限隔离：不同团队可配置不同工具权限
- 计费隔离：按团队统计使用量

### 3.4 场景四：负载均衡（高级）

**目标**：多个相同配置的智能体分担负载

```
架构：
┌─────────────┐
│   Gateway   │
└──────┬──────┘
       │
       ├─ feishu:main ─┬─→ agent-worker-1
       │               ├─→ agent-worker-2
       │               └─→ agent-worker-3
```

**注意**：OpenClaw 当前不直接支持负载均衡，需要自定义路由逻辑

---

## 四、资源治理策略

### 4.1 容器生命周期管理

**配置参数**（在 `openclaw.json` 中）：
```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "cleanup": {
          "idleHours": 24,        // 空闲 24 小时后清理
          "maxContainers": 20,    // 最多保留 20 个容器
          "sweepIntervalMs": 3600000  // 每小时扫描一次
        }
      }
    }
  }
}
```

**手动管理命令**：
```bash
# 查看所有容器
openclaw sandbox list

# 重建容器（强制更新配置）
openclaw sandbox recreate --all
openclaw sandbox recreate --agent bodhi
openclaw sandbox recreate --session main
```

### 4.2 并发控制

**全局并发限制**：
```json
{
  "agents": {
    "defaults": {
      "maxConcurrent": 4,      // 每个 agent 最多 4 个并发会话
      "subagents": {
        "maxConcurrent": 8     // 子智能体最多 8 个并发
      }
    }
  }
}
```

**按 agent 定制**：
```json
{
  "agents": {
    "list": [
      {
        "id": "high-priority",
        "maxConcurrent": 10    // 高优先级智能体更高并发
      },
      {
        "id": "low-priority",
        "maxConcurrent": 2     // 低优先级智能体限制并发
      }
    ]
  }
}
```

### 4.3 沙箱策略选择

**决策树**：
```
任务类型？
├─ 高风险执行（代码编译、系统命令）
│   → scope=session（强隔离）
│
├─ 高并发对话（客服、咨询）
│   → scope=agent（资源复用）
│
└─ 混合场景
    → 主会话 mode=non-main（不进沙箱）
    → 非主会话 scope=session（进沙箱）
```

---

## 五、迁移路径（最小风险）

### 5.1 阶段一：准备与验证（1-2 天）

**目标**：不影响现有服务，先建立多实例基础

```bash
# 1. 备份当前配置
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d)

# 2. 记录当前状态
openclaw agents list --json --bindings > ~/openclaw-baseline.json

# 3. 创建测试智能体（不绑定路由）
openclaw agents add test-agent \
  --workspace ~/.openclaw/workspace/test \
  --agent-dir ~/.openclaw/agents/test

# 4. 验证隔离
openclaw sandbox explain --agent test-agent
```

### 5.2 阶段二：新建专用智能体（2-3 天）

**目标**：为不同通道/功能创建专用智能体

```bash
# 示例：创建 Discord 专用智能体
openclaw agents add discord-bot \
  --workspace ~/.openclaw/workspace/discord \
  --agent-dir ~/.openclaw/agents/discord

# 配置身份
openclaw agents set-identity discord-bot \
  --name "Discord Bot" \
  --emoji "🤖"

# 配置模型（可选，在 openclaw.json 中）
# agents.list[].model.primary = "aicodewith-claude/claude-sonnet-4-6"
```

### 5.3 阶段三：逐步绑定路由（3-5 天）

**目标**：分批切换流量，观察稳定性

```bash
# 1. 先绑定低流量通道测试
openclaw agents bind --agent discord-bot --bind discord:default

# 2. 验证路由生效
openclaw agents list --bindings
openclaw agents bindings --json

# 3. 观察 1-2 天，确认无问题

# 4. 继续绑定其他通道
openclaw agents bind --agent telegram-bot --bind telegram:bot1
```

### 5.4 阶段四：资源调优（持续）

**目标**：根据实际负载调整沙箱策略

```bash
# 1. 监控容器数量
watch -n 60 'openclaw sandbox list'

# 2. 根据负载调整 scope
# 高并发 agent → scope=agent
# 高风险 agent → scope=session

# 3. 调整并发限制
# 在 openclaw.json 中按 agent 定制 maxConcurrent
```

### 5.5 阶段五：清理与优化（1 周后）

**目标**：删除不再使用的智能体和容器

```bash
# 1. 确认所有通道都有显式绑定
openclaw agents bindings --json | jq '.bindings | length'

# 2. 删除测试智能体
openclaw agents delete test-agent

# 3. 清理旧容器
openclaw sandbox recreate --all
```

---

## 六、最佳实践与反模式

### 6.1 ✅ 最佳实践

1. **显式路由优先**
   - 所有生产通道都配置显式 bindings
   - 不依赖默认路由
   - 上线前审计：`openclaw agents list --bindings`

2. **独立工作区**
   - 每个 agent 独立 workspace 和 agentDir
   - 避免状态串扰和文件冲突

3. **分层隔离策略**
   - 主会话（高频低风险）：`mode=non-main`
   - 非主会话（低频高风险）：`scope=session`
   - 高并发场景：`scope=agent`

4. **密钥管理**
   - 迁移明文密钥到环境变量
   - 使用 `${ENV_VAR}` 引用
   - 定期轮换密钥

5. **资源限制**
   - 设置 `cleanup.maxContainers` 和 `idleHours`
   - 按 agent 设置 `maxConcurrent`
   - 监控容器数量和资源使用

### 6.2 ❌ 反模式

1. **依赖默认路由**
   - ❌ 不配置 bindings，依赖默认路由
   - ✅ 所有通道显式绑定到 agent

2. **共享工作区**
   - ❌ 多个 agent 共享同一个 workspace
   - ✅ 每个 agent 独立目录

3. **过度隔离**
   - ❌ 所有场景都用 `scope=session`，容器爆炸
   - ✅ 根据风险和并发选择合适的 scope

4. **明文密钥**
   - ❌ 在 `openclaw.json` 中硬编码密钥
   - ✅ 使用环境变量或密钥管理服务

5. **无监控上线**
   - ❌ 直接切换生产流量，无观察期
   - ✅ 分批切换，观察 1-2 天再继续

---

## 七、推荐实施方案（针对当前环境）

### 7.1 短期目标（1-2 周）：多通道隔离

**目标**：飞书、Discord 使用独立智能体

```
当前：
  feishu:main → agent-main (菩提1号)

目标：
  feishu:main → agent-bodhi (菩提1号，保持不变)
  discord:default → agent-discord (新建)
```

**实施步骤**：
1. 创建 `agent-discord`
2. 配置身份和模型
3. 绑定 `discord:default → agent-discord`
4. 验证路由和沙箱隔离
5. 观察 3-5 天，确认稳定

### 7.2 中期目标（1-2 个月）：功能专业化

**目标**：代码审查、前端开发、后端开发使用专门智能体

```
架构：
  feishu:main → agent-bodhi (通用对话)
  feishu:main + 关键词"代码审查" → agent-code-reviewer
  feishu:main + 关键词"前端" → agent-frontend
  feishu:main + 关键词"后端" → agent-backend
```

**实施方式**：
- 通过飞书机器人命令切换智能体
- 或通过 routes 细粒度路由（需要自定义逻辑）

### 7.3 长期目标（3-6 个月）：多租户隔离

**目标**：不同团队使用独立智能体和工作区

```
架构：
  feishu:team-a → agent-team-a
  feishu:team-b → agent-team-b
  feishu:team-c → agent-team-c
```

**前提条件**：
- 飞书支持多账号/多机器人
- 或通过 routes 按群组路由

---

## 八、技术挑战与解决方案

### 8.1 路由歧义/错投

**问题**：多账号场景下，channel-only 绑定会按默认/字典序推断账号，容易误路由

**解决方案**：
- 显式写 `channel:accountId`
- 不使用 channel-only 绑定
- 上线前审计：`openclaw agents bindings --json`

### 8.2 容器膨胀

**问题**：`scope=session` 下，容器数随会话数线性增长

**解决方案**：
- 设置 `cleanup.maxContainers` 和 `idleHours`
- 高并发 agent 改用 `scope=agent`
- 监控容器数量：`watch -n 60 'openclaw sandbox list'`

### 8.3 跨会话状态泄漏

**问题**：`scope=agent` 下，同 agent 的不同会话共享容器环境

**解决方案**：
- 敏感 agent 保持 `scope=session`
- 普通 agent 才用 `scope=agent`
- 定期重建容器：`openclaw sandbox recreate --agent <id>`

### 8.4 网关单点

**问题**：统一 Gateway 入口，单点故障风险

**解决方案**：
- 短期：监控 Gateway 健康状态，自动重启
- 长期：考虑多 Gateway 实例（需要改不同端口/配置文件）

### 8.5 密钥治理

**问题**：`openclaw.json` 存在多处明文密钥

**解决方案**：
```bash
# 1. 迁移到环境变量
export FEISHU_APP_SECRET="Esf8Xx6VtrytJZJ6hcDgthGiNpFKgM5G"
export GATEWAY_TOKEN="e9ec1c9b51277d194c2b14beca32e0b516ee180425e5f106"

# 2. 在 openclaw.json 中引用
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

# 3. 定期轮换密钥
```

---

## 九、参考资料

### 9.1 官方文档
- https://docs.openclaw.ai/cli/agents
- https://docs.openclaw.ai/channel-routing
- https://docs.openclaw.ai/agents/multi-agent-sandbox-tools
- https://docs.openclaw.ai/sandboxing/
- https://docs.openclaw.ai/cli/sandbox
- https://docs.openclaw.ai/configuration/reference
- https://docs.openclaw.ai/sessions

### 9.2 配置文件位置
- 主配置：`~/.openclaw/openclaw.json`
- Agent 目录：`~/.openclaw/agents/<agent-id>/`
- 工作区：`~/.openclaw/workspace/`
- 沙箱目录：`~/.openclaw/sandboxes/`

### 9.3 关键命令
```bash
# Agent 管理
openclaw agents list [--json] [--bindings]
openclaw agents add <id> [--workspace <dir>] [--agent-dir <dir>]
openclaw agents bind --agent <id> --bind <channel>:<account>
openclaw agents unbind --agent <id> --bind <channel>:<account>
openclaw agents delete <id>
openclaw agents set-identity <id> --name <name> --emoji <emoji>

# 沙箱管理
openclaw sandbox list [--browser]
openclaw sandbox explain [--agent <id>] [--session <key>]
openclaw sandbox recreate [--all] [--agent <id>] [--session <key>]

# 路由审计
openclaw agents bindings [--json]
```

---

## 十、下一步行动

### 10.1 立即行动（本周）
1. ✅ 完成多实例架构研究（本文档）
2. ⬜ 备份当前配置
3. ⬜ 创建测试智能体，验证隔离机制
4. ⬜ 设计具体的多实例配置方案

### 10.2 短期计划（1-2 周）
1. ⬜ 实施多通道隔离（飞书 + Discord）
2. ⬜ 配置显式路由绑定
3. ⬜ 验证沙箱隔离和资源管理
4. ⬜ 观察稳定性 3-5 天

### 10.3 中期计划（1-2 个月）
1. ⬜ 实施功能专业化（代码审查、前端、后端）
2. ⬜ 优化沙箱策略（scope 选择）
3. ⬜ 建立监控和告警机制

### 10.4 长期计划（3-6 个月）
1. ⬜ 实施多租户隔离
2. ⬜ 探索负载均衡方案
3. ⬜ 建立完整的可观测性体系

---

**文档版本**：v1.0
**最后更新**：2026-03-05
**维护者**：Claude Code + Codex 技术分析
