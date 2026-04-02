# 讲师手册

> 本手册面向培训讲师，包含每个环节的讲稿要点、演示脚本和注意事项。
> **本手册是讲师全天唯一需要跟读的文件**，所有环节的操作指引均在此文件中。

---

## 快速导航：讲师一天该看什么

### 全天版（09:30-18:00）

```
 09:30  打开本文件 → "环节0：开场与环境检查"
 10:00  OpenSpec 理论讲解 → 本文件 "环节1"
 10:50  Claude Code + MCP → 本文件 "环节2"
 11:40  Live Demo → 本文件 "环节3"
 12:10  午休
 13:30  分组实战 → 本文件 "下午分轨部分" + 对应组的题目文件
 15:00  需求变更 → 本文件 "各组中途需求变更内容"
 17:00  复盘展示 → 本文件 "傍晚复盘"
```

### 半天版（09:00-13:00）

```
 09:00  开场 + 环境确认（10min）→ 本文件 "环节0"（压缩版）
 09:10  OpenSpec 理论（15min）→ 本文件 "环节1"（只讲核心概念）
 09:25  Claude Code + MCP（10min）→ 本文件 "环节2"（只讲角色分工）
 09:35  Live Demo（10min）→ 本文件 "环节3"（快速演示）
 09:45  休息 10min
 09:55  分组实战 → 本文件 "下午分轨部分" + 对应组的题目文件
 11:00  需求变更
 12:00  复盘展示 → 本文件 "傍晚复盘"
```

> 半天版详细时间节点见 [agenda-halfday.md](agenda-halfday.md)

### 各组题目与脚手架位置

| 技术栈 | 题目说明（讲师+学员看） | 脚手架代码 |
|--------|----------------------|-----------|
| Java 后端 | [exercises/java-backend/README.md](exercises/java-backend/README.md) | `exercises/java-backend/scaffold/` |
| 前端 | [exercises/frontend/README.md](exercises/frontend/README.md) | `exercises/frontend/scaffold/react/` |
| Python | [exercises/python/README.md](exercises/python/README.md) | `exercises/python/scaffold/` |
| 算法 | [exercises/algorithm/README.md](exercises/algorithm/README.md) | `exercises/algorithm/scaffold/` |

> **题目 README 包含**：业务背景、需求描述（主需求 + 中途变更）、验收标准、脚手架说明、参考提示词、评分要点。
> **讲师应在培训前一天完整阅读对应组的题目 README，并亲自跑通脚手架。**

### 其他参考材料

| 材料 | 路径 | 用途 |
|------|------|------|
| 分钟级议程 | [agenda.md](agenda.md) | 时间节点参考 |
| 评分模板 | [templates/scoring.md](templates/scoring.md) | 打分用 |
| 环境检查脚本 | [templates/env-check.sh](templates/env-check.sh) | 培训前环境自检 |
| 上午统一练习 | [exercises/common/hello-claude.md](exercises/common/hello-claude.md) | 10:50 环节备用 |
| 训后 SOP | [post-training/daily-sop.md](post-training/daily-sop.md) | 17:40 行动计划发布 |

---

## 讲师角色分配

| 角色 | 负责环节 | 要求 |
|------|---------|------|
| 主讲师 | 上午理论 + Live Demo + 傍晚复盘 | 熟练使用 Claude Code + OpenSpec 全流程 |
| Java 组讲师 | 下午 Java 实战 | Java/Spring Boot 经验 + Claude Code 经验 |
| 前端组讲师 | 下午前端实战 | React/Vue 经验 + Claude Code 经验 |
| Python 组讲师 | 下午 Python 实战 | FastAPI/Django 经验 + Claude Code 经验 |
| 算法组讲师 | 下午算法实战 | 数据分析/ML 经验 + Claude Code 经验 |

---

## 上午统一部分：讲稿要点

### 环节0：开场与环境检查（09:30-10:00，30min）

#### 09:30-09:40 开场致辞脚本

**讲师开场词（建议逐字稿）**：

> "各位同事，早上好！欢迎参加今天的 AI 驱动开发全员培训。
>
> 先问大家一个问题：过去一个月，你有多少次因为需求理解偏差返工？有多少次因为代码审查发现低级错误？有多少次因为手动测试遗漏导致线上 Bug？
>
> 今天我们要学习的新开发方式，可以帮你减少 50% 的返工、80% 的低级错误、90% 的测试遗漏。
>
> **今天的目标很简单**：每个人跑通一次完整的 AI 驱动开发闭环——从需求分析到代码实现到交叉审查，全程用 AI 辅助，但你是主导者。
>
> **今天结束后，你会带走什么**：
> 1. 一套规范驱动开发的心智模型（OpenSpec）
> 2. 一套多 AI 协同的工作流程（Claude + Codex + Gemini）
> 3. 一个完整的实战项目（你自己写的代码 + 测试 + 文档）
>
> 现在，让我们先确认环境就绪。"

#### 09:40-09:55 环境最终检查

**操作流程**：
1. 全员执行 `bash templates/env-check.sh`（前一天应已完成）
2. 举手示意：谁的环境有问题？
3. 助教现场处理（网络、API Key、依赖安装）
4. 发放分组手环/贴纸（标识 Java/前端/Python/算法）

**常见问题快速处理**：
- Claude Code 未安装 → `npm install -g @anthropic-ai/claude-code`
- API Key 未配置 → 发放统一 Key，`export ANTHROPIC_API_KEY=xxx`
- 网络不通 → 切换代理或手机热点

#### 09:55-10:00 分组确认

**操作流程**：
1. 公布下午分组安排（投影显示房间号/区域）
2. 介绍各组讲师和助教
3. 强调：上午统一理论，下午分组实战，傍晚统一复盘

---

### 环节1：OpenSpec 规范驱动开发（50min）

#### 开场故事（建议用真实案例）

> "上个月 XX 项目，产品说'加个筛选功能'，后端理解成 SQL WHERE 条件，前端理解成
> 前端本地过滤。两边各做了一周，联调时才发现对不上。返工 3 天。
>
> 如果当时有 OpenSpec，需求会写成：
> - 'API 端新增 filter 参数，支持 name、status 字段筛选'
> - '前端调用 API 传递 filter 参数，不做本地过滤'
>
> 两句话，省 3 天。这就是规范驱动开发的价值。"

#### 核心概念讲解脚本

**1. 目录模型（画在白板上）**

```
openspec/
├── specs/          ← "现在系统能做什么"（唯一真相）
│   └── user-search/
│       └── spec.md  ← 用户搜索功能的完整规范
│
└── changes/        ← "我要改什么"
    ├── add-filter/  ← 正在进行的变更
    │   ├── proposal.md  ← 为什么加、加什么、影响啥
    │   ├── tasks.md     ← 具体步骤清单
    │   └── specs/user-search/
    │       └── spec.md  ← 只写变化的部分（delta）
    │
    └── archive/     ← 变更历史（做完的放这里）
```

> 类比 Git：specs/ = 当前代码，archive/ = commit 历史。

**2. proposal.md 格式（展示真实示例）**

```markdown
# Change: 用户搜索新增筛选功能

## Why
当前用户列表无法按条件筛选，运营每次需要导出 Excel 手动查找，效率低下。

## What Changes
- 新增 API 查询参数：name（模糊匹配）、status（精确匹配）
- 前端新增筛选表单组件
- **BREAKING**：原 GET /api/users 响应格式变更（新增 meta.filters 字段）

## Impact
- Affected specs: user-search, user-api
- Affected code: UserController, UserService, UserListPage
```

**3. tasks.md 格式（强调 bite-sized）**

```markdown
## 1. Implementation
- [ ] 1.1 UserService 新增 filter 参数处理
      文件：src/service/UserService.java
      要点：name 用 LIKE，status 用 =
      验证：单元测试 testFilterByName, testFilterByStatus
- [ ] 1.2 UserController 新增查询参数绑定
      文件：src/controller/UserController.java
      要点：@RequestParam 绑定，参数校验
      验证：curl 测试 GET /api/users?name=张&status=active
- [ ] 1.3 前端筛选表单组件
      文件：src/components/UserFilter.tsx
      要点：防抖搜索，URL 参数同步
      验证：页面筛选功能可用
```

> **关键点**：每一步都有文件路径、代码要点、验证命令。粒度 2-5 分钟。

#### 互动环节操作指南

**给出模糊需求**："优化用户搜索体验"

**引导问题**：
1. "优化"是什么意思？速度快？功能多？UI 好看？
2. 谁在用这个搜索？运营？终端用户？
3. 当前的痛点是什么？数据量大？查不到？
4. 有没有具体的指标？响应时间 < 200ms？

**展示转化结果**：
```
模糊需求："优化用户搜索体验"
↓ 经过追问和分析
↓
清晰 proposal：
- Why: 当前搜索无筛选功能，运营查找用户平均耗时 5 分钟
- What: 新增 name/status 筛选 + 分页优化（每页 20→50）
- Impact: API 变更（BREAKING），前端新增组件
```

---

### 环节2：Claude Code + MCP 协同（50min）

#### 演示脚本

**1. Claude Code 基本操作（现场演示）**

```bash
# 启动 Claude Code（确保学员看到完整启动过程）
claude

# 演示：阅读文件
> 读一下 src/service/UserService.java

# 演示：搜索代码
> 搜索所有使用 UserService 的地方

# 演示：编辑文件
> 给 getUserList 方法添加 name 参数

# 演示：运行测试
> 运行 UserService 的单元测试
```

**2. MCP 协同演示**

```bash
# 演示：调用 Codex 审查代码
> 请 Codex 审查刚才修改的 UserService 代码，
> 关注安全性和性能

# 演示：调用 Gemini 分析
> 请 Gemini 分析 UserListPage 组件结构，
> 建议如何添加筛选功能
```

**3. 刹车机制演示（非常重要）**

故意制造一个 AI 失败的场景：
```bash
# 给一个错误的指令
> 修复这个 bug（不给任何上下文）

# AI 会乱改代码 → 展示如何 Ctrl+C 中断
# 然后展示正确做法：
> 这个 bug 的现象是 XXX，错误日志是 YYY，
> 我怀疑是 ZZZ 导致的，请检查并修复
```

---

### 环节3：Live Demo 脚本（30min）

#### 场景：实现"获取用户列表并支持分页"API

**步骤1：创建 OpenSpec（8min）**

```bash
# 在 Claude Code 中
> 我需要实现一个获取用户列表并支持分页的 API。
> 帮我创建 OpenSpec 提案。
>
> 需求：
> - GET /api/users?page=1&size=20
> - 返回用户列表 + 分页信息
> - 支持按 name 模糊搜索
```

展示 Claude Code 生成的 proposal.md 和 tasks.md，简单调整后确认。

**步骤2：TDD 实现（10min）**

```bash
# 按 tasks.md 第一步
> 按照 tasks.md 的 1.1，先为 getUserList 写测试用例，
> 包含正常分页、空结果、搜索三个场景

# 运行测试（应该失败 — RED）
> 运行测试

# 实现代码
> 现在实现 getUserList 方法，让测试通过

# 运行测试（应该通过 — GREEN）
> 运行测试
```

**步骤3：交叉审查（7min）**

```bash
# 调用 Codex 审查
> 请 Codex 审查刚才实现的分页接口，
> 关注 SQL 注入风险和大数据量性能

# 根据审查意见修复
> Codex 提到了 XXX 风险，请修复
```

**步骤4：归档（5min）**

```bash
> 所有测试通过，请归档这个变更，
> 更新 specs/ 目录
```

---

## 下午分轨部分：讲师操作指南

### 实战完整流程（所有组统一，严格对齐 CLAUDE.md）

```
从 develop 创建特性分支
    ↓
需求分析 + 架构设计（brainstorming）
    ↓
三方设计审核（Claude + Codex + Gemini 达成一致）
    ↓
编写 OpenSpec 提案（proposal.md + tasks.md）
    ↓
三方提案审核（确认 API 设计、场景覆盖）
    ↓
按 tasks.md 逐步 TDD 实现（RED → GREEN → REFACTOR）
    ↓
15:00 需求变更 → 更新 proposal + tasks → 继续实现
    ↓
三方代码审查（Codex 审查质量安全 + Gemini 审查功能覆盖 + Claude 综合判断）
    ↓
验证：实现是否符合需求和设计？测试是否全绿？
    ↓
提交到特性分支
```

### 13:30-13:40 题目讲解 + 破冰

1. 发放题目说明书（投影对应组的 `exercises/{tech}/README.md`）
2. 带着学员过一遍脚手架代码结构
3. 明确三个关卡打卡机制
4. **关键步骤：引导每人创建自己的特性分支**
   ```bash
   git checkout develop
   git checkout -b feature/training-{你的名字}
   ```
5. 强调：不会的先问 Claude Code，再问讲师

### 13:40-14:00 监督需求设计与 brainstorming

- 确保每人在 Claude Code 中进行需求分析，而不是直接写代码
- 引导使用 brainstorming 模式：让 Claude 分析需求、提出组件/模块设计方案
- **监督三方设计审核**：确保每人让 Codex 和 Gemini 审查了设计方案
- 常见问题：
  - 跳过设计直接写代码 → **叫停！** 回到设计环节
  - 只用 Claude 不用 Codex/Gemini → 引导调用 MCP 工具

### 14:00-14:20 监督 OpenSpec 提案编写

- 巡场检查每个人的 proposal.md 和 tasks.md
- 常见问题：
  - proposal 太模糊 → 引导细化 Why 和 What Changes
  - tasks 粒度太大 → 帮助拆分成 2-5 分钟可完成的步骤
  - 缺少验证命令 → 提醒每步都要有测试或命令可验证
- **确认三方提案审核**：proposal 需经 Codex/Gemini 审查后才开始编码
- **关卡1打卡**

### 14:20-16:30 实战巡场检查点

| 时间 | 检查内容 | 发现问题怎么办 |
|------|---------|--------------|
| 13:45 | 是否创建了特性分支 | 引导创建分支，禁止在 develop 直接开发 |
| 14:00 | 是否完成了设计分析 | 催促完成，不要跳过直接写代码 |
| 14:15 | proposal + tasks 质量 | 快速审核，引导修改 |
| 14:40 | TDD 是否执行 | 检查是否先写测试 |
| 15:00 | 需求变更前检查进度 | 落后的先完成主需求核心部分 |
| 15:30 | 变更后 proposal 是否更新 | 提醒更新文档 |
| 16:15 | 三方代码审查是否执行 | 引导使用 Codex/Gemini 审查代码 |
| 16:25 | 是否提交到特性分支 | 引导 git commit + push |

### 16:30-17:00 自由答疑与展示准备

**16:30-16:45 自由答疑**：
- 巡场处理个别学员的遗留问题
- 未完成的学员继续完成（降低预期，至少完成主需求）
- 已完成的学员整理代码、准备展示材料

**16:45-17:00 准备展示**：
- 每组选出 1-2 名代表准备 Show & Tell
- 提醒展示时间 10 分钟，重点讲收获和坑

---

## 常见问题应对

### 技术问题

| 问题 | 应对 |
|------|------|
| API Key 限流 | 切换备用 Key，降低请求频率 |
| 网络不稳定 | 切换代理，用手机热点临时替代 |
| Claude Code 报错 | 检查版本，`claude update` |
| AI 生成的代码编译不通过 | 这是正常的！引导人工修复 |
| 某人进度远远落后 | 助教 1 对 1 辅导，降低预期 |

### 态度问题

| 问题 | 应对 |
|------|------|
| "我觉得不如自己写" | 尊重感受，建议先跑完再评价 |
| "AI 生成的代码质量不行" | 引导优化 Prompt，展示上下文的重要性 |
| "OpenSpec 太麻烦了" | 解释长期 ROI：前期多投入 10%，减少 50% 返工 |
| "我的技术栈用不上" | 展示通用价值，约定后续定制支持 |

---

## 傍晚复盘：主持脚本

### Show & Tell（40min）

每组 10 分钟，格式：

1. **30 秒**：一句话总结做了什么
2. **3 分钟**：展示 proposal.md 和关键代码
3. **3 分钟**：展示交叉审查发现的问题
4. **2 分钟**：最大收获 + 最深的坑
5. **1.5 分钟**：Q&A

**主持人引导问题**：
- "你觉得 OpenSpec 最有价值的地方是什么？"
- "如果不用 AI，这个任务你要做多久？"
- "交叉审查发现了什么你自己没注意到的问题？"

### 行动计划发布要点

**必须宣布的制度**：
1. 从下周一开始，试点期：预估 > 1 人天的新功能或重要重构，MR 须附带 OpenSpec（详见 daily-sop.md 渐进推广方案）
2. 每周五站会新增"AI 提效案例"分享环节（每组 1 个）
3. 2 周后（__月__日）安排半天复训
4. AI Champion 名单（现场宣布或后续公布）
