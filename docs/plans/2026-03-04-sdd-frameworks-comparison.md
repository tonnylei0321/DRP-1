# SDD 框架深度对比分析报告

> **报告类型**: 技术调研与对比分析
> **日期**: 2026-03-04
> **分析方法**: 多 AI 联合分析（Claude 主导 + Codex 后端审查 + Gemini 全局分析）
> **分析对象**: BMAD Method v6 / GitHub Spec Kit / 社区 SpecKit / OpenSpec（当前使用）

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [被分析框架概览](#2-被分析框架概览)
3. [架构哲学对比](#3-架构哲学对比)
4. [多维度评估矩阵](#4-多维度评估矩阵)
5. [详细优劣势分析](#5-详细优劣势分析)
6. [OpenSpec 缺失能力分析](#6-openspec-缺失能力分析)
7. [过度设计风险评估](#7-过度设计风险评估)
8. [多 AI 分析分歧与裁决](#8-多-ai-分析分歧与裁决)
9. [推荐改进路线图](#9-推荐改进路线图)
10. [结论](#10-结论)
11. [参考资料](#11-参考资料)

---

## 1. 执行摘要

本报告对当前主流的四个规范驱动开发（Spec-Driven Development, SDD）框架进行了深度对比分析，旨在评估我们当前使用的 OpenSpec 流程的竞争力，并识别可借鉴的改进方向。

**核心发现**：

- OpenSpec 的**多 AI 协作架构（Claude+Codex+Gemini）和治理闭环**是四个框架中最适应未来的底座
- 主要缺失能力集中在三个方面：**需求歧义收敛关口**、**跨会话任务依赖图谱**、**流程文档单一真相**
- 不建议全面切换到任何其他框架，应**选择性吸收**各框架的优势能力
- 最高优先级改进：Clarify Gate（借鉴 Spec Kit）和 SSOT 清理（解决内部流程分叉）

**总策略**：保持 OpenSpec 为主框架，向上层吸收 Spec Kit 的强约束（clarify/checklist/constitution），向下层借鉴 SpecKit/Beads 的依赖图谱，侧面从 BMAD 借鉴 Token 优化和前端角色规则集。

---

## 2. 被分析框架概览

### 2.1 BMAD Method v6

- **全称**: Breakthrough Method for Agile AI-Driven Development
- **核心理念**: 用 AI Agent 模拟完整敏捷团队
- **维护方**: BMAD Code Organization ([bmad-code-org](https://github.com/bmad-code-org))
- **生态规模**: 312★ (Claude Code Skills), npm 包 `bmad-method`
- **安装**: `npx bmad-method install`
- **关键特性**:
  - 9 个专业化 Agent（Business Analyst, Product Manager, System Architect, Scrum Master, Developer, UX Designer, Builder, Creative Intelligence, BMad Master）
  - 4 阶段工作流：Analysis → Planning(PRD) → Solutioning(Architecture) → Implementation
  - Token 优化 70-85%（Helper pattern 减少重复嵌入）
  - Claude Code 原生集成（Skills/Commands/Hooks/Memory）
  - 自适应复杂度（从 bug fix 到企业系统）
  - Party Mode 多 Agent 协作
  - 34+ 工作流命令，15 个主要 Slash Commands
  - 模块化扩展（Test Architect, Game Dev, Creative Intelligence Suite）

### 2.2 GitHub Spec Kit（GitHub 官方）

- **全称**: Spec-Driven Development Toolkit
- **核心理念**: "Specifications become executable" — 规范即可执行物
- **维护方**: GitHub 官方
- **生态规模**: 73,744★
- **安装**: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
- **关键特性**:
  - SD-X（Spec-Driven X）哲学：Specs → AI → X (Anything)
  - 严格阶段管线：constitution → specify → clarify → plan → checklist → tasks → analyze → implement
  - Specify CLI 工具
  - 支持 20+ AI agents（Claude Code, Codex, Gemini, Cursor, Copilot, Windsurf, Kiro 等）
  - 技术无关的规范设计
  - Pivotal Labs 方法论基础
  - Constitution 机制（项目宪章，不可违背的铁律）

### 2.3 社区 SpecKit (jmanhype)

- **全称**: Specification-Driven Development with Beads Integration
- **核心理念**: 规范 + 可查询任务图谱 = 不遗忘
- **维护方**: 社区个人（jmanhype）
- **生态规模**: 10★
- **关键特性**:
  - 工作流同 Spec Kit：constitution → specify → clarify → plan → tasks → implement
  - Beads 持久记忆层（JSONL + SQLite / Dolt）
  - tasks.md 作为索引指向 Beads issues（实际工作状态存储在外部）
  - Pivotal Labs 实践（TDD, User Stories, Story States, Acceptance Criteria）
  - 依赖/阻塞关系可查询（`bd ready` 显示无阻塞工作）
  - Linear 项目管理集成
  - `test-gate.sh` 强制 100% 测试通过

### 2.4 OpenSpec（我们当前使用）

- **核心理念**: 规范先行，实现在后 + 多 AI 交叉验证
- **维护方**: 内部团队
- **关键特性**:
  - 三级任务分级（小/中/大），流程重量与任务规模匹配
  - 目录模型：`specs/`（当前真相）+ `changes/`（活跃变更）+ `archive/`（历史）
  - 多 AI 协同：Claude 主体思考 + Codex 后端审查 + Gemini 前端实现
  - Superpowers 技能系统（brainstorming, TDD, debugging, code-review, git-worktrees 等 15+ 技能）
  - OpenSpec 完整性检查（归档前验证 specs/design/delta/tasks）
  - Session state 持久化防上下文压缩
  - 提案触发器规则（自动判断是否需要 OpenSpec 提案）

---

## 3. 架构哲学对比

### 3.1 Codex 视角（技术架构维度）

| 框架 | 核心抽象 | 强项 |
|------|---------|------|
| BMAD | 角色编排驱动 — 把 SDLC 人员分工映射为 AI 分工 | 组织化执行 |
| Spec Kit | 规格工件驱动 — spec artifact pipeline | 规格到实现的标准化转换 |
| SpecKit | 规格 + 工作记忆驱动 — 任务执行状态外置 | 跨会话连续性 |
| OpenSpec | 治理与审查驱动 — 多 AI 交叉审查 + 归档验证 | 过程约束和可审计性 |

### 3.2 Gemini 视角（开发体验维度）

| 框架 | 定位 | 隐喻 |
|------|------|------|
| BMAD | 敏捷流程化 | 雇佣了一个完整的虚拟外包团队 |
| Spec Kit | 工业级标准化 | GitHub 官方认证的"规范工厂" |
| SpecKit | 外挂记忆库 | 给 AI 装了一个"永不遗忘"的外脑 |
| OpenSpec | 多模型协作流 | 多位顾问协作的治理委员会 |

### 3.3 综合判断

四个框架在 SDD 的不同维度上各有侧重，并非替代关系：

| 框架 | 核心哲学 | 一句话 |
|------|---------|--------|
| **BMAD** | 用 AI Agent 模拟完整敏捷团队 | 重在**分工** |
| **Spec Kit** | 规范即可执行物，规范驱动一切 | 重在**标准** |
| **SpecKit** | 规范 + 可查询任务图谱 = 不遗忘 | 重在**记忆** |
| **OpenSpec** | 规范先行 + 多 AI 交叉验证 + 归档闭环 | 重在**治理** |

---

## 4. 多维度评估矩阵

### 4.1 能力雷达图（5 分制）

| 维度 | BMAD | Spec Kit | SpecKit | OpenSpec |
|------|:----:|:--------:|:-------:|:-------:|
| 流程完整性 | ★★★★★ | ★★★★ | ★★★ | ★★★★ |
| 轻量灵活性 | ★★ | ★★★ | ★★★ | ★★★★★ |
| 前端适配性 | ★★★★ | ★★ | ★★ | ★★★★ |
| 跨会话记忆 | ★★★ | ★★ | ★★★★★ | ★★★ |
| 生态成熟度 | ★★★ | ★★★★★ | ★ | ★★ |
| 治理审计性 | ★★★ | ★★★ | ★★ | ★★★★★ |
| 多 AI 协同 | ★★ | ★★★ | ★★ | ★★★★★ |
| Token 效率 | ★★★★★ | ★★★ | ★★★ | ★★★ |

### 4.2 开发者体验 (DX) 评估

| 维度 | BMAD | Spec Kit | SpecKit | OpenSpec |
|------|------|----------|---------|---------|
| **学习曲线** | 陡峭（9 Agent + 4 Phase） | 中等（CLI 引导明确） | 平缓（映射到看板习惯） | 极低（Markdown 即配置） |
| **日常摩擦** | 高（角色切换成本） | 中（阶段门禁） | 低（熟悉的任务管理） | 低（三级分流减少冗余） |
| **上手速度** | 慢（需理解全部角色） | 中（CLI 教程引导） | 快（类似 Jira/Linear） | 快（读 CLAUDE.md 即可） |
| **自由度** | 低（高度结构化） | 中（强约束管线） | 高（灵活任务管理） | 最高（可跳过任何环节） |

### 4.3 规模适应性

| 场景 | 最优框架 | 原因 |
|------|---------|------|
| **个人项目 / Solo** | OpenSpec, SpecKit | 轻量目录结构不增加心智负担 |
| **小型团队 (2-5人)** | BMAD | Agent 角色补齐团队建制，Party Mode 提升吞吐 |
| **中型团队 (5-20人)** | Spec Kit | Constitution 保证跨团队架构一致性 |
| **企业级 (20+人)** | Spec Kit | 工业标准，官方背书，全平台兼容 |

### 4.4 前端开发场景适配

| 框架 | 前端支持 | 说明 |
|------|---------|------|
| **BMAD** | ★★★★ | 特设 UX Designer + Creative Intelligence Agent，组件拆分和视觉还原有专门角色 |
| **Spec Kit** | ★★ | 技术无关，不针对前端做特化，处理细粒度组件状态时规范可能过于宏大 |
| **SpecKit** | ★★ | 偏后端数据驱动，前端场景无特殊优化 |
| **OpenSpec** | ★★★★ | 显式指定 Gemini 负责前端，结合 Superpowers 调试能力处理前端问题精准 |

---

## 5. 详细优劣势分析

### 5.1 BMAD Method v6

**优势**：
- 复杂项目分工最清晰，每个 Agent 有明确职责边界
- Token 优化技术成熟（Helper pattern 节省 70-85%）
- 可按角色并行执行，适合大吞吐场景
- 前端有专门的 UX/Creative Agent，视觉还原质量高
- 自适应复杂度，从 Level 0 bug fix 到 Level 3 企业系统

**劣势**：
- 流程面最重，角色切换开销大
- 若问题规模小（单文件修改），9 Agent 编排显著过载
- 深度绑定 Claude Code，跨工具迁移成本高
- 对习惯直接写代码的开发者有强烈"失控感"

### 5.2 GitHub Spec Kit

**优势**：
- 官方背书，73,744 Stars，生态最成熟
- 全平台兼容（20+ AI agents），不锁定特定工具
- clarify/checklist 阶段对需求歧义有强抑制作用
- Constitution 机制保证大团队架构一致性
- Specify CLI 提供标准化入口，流程可移植

**劣势**：
- 默认不提供强持久记忆层
- 更多是"模板与命令编排"，非完整项目运行系统
- 在处理细粒度前端组件状态时规范可能过于宏大
- 没有多 AI 协同的内置支持

### 5.3 社区 SpecKit

**优势**：
- 任务执行从 Markdown 勾选升级到可查询图谱，依赖/阻塞关系可计算
- Beads 解决了超长期项目的记忆遗忘问题
- 贴近传统看板/Issue 驱动开发，不破坏现有工作流
- Pivotal Labs 实践基础扎实（TDD, User Stories 等）
- Linear 集成打通项目管理

**劣势**：
- 多一层状态系统就多一层一致性问题
- 外部系统耦合带来运维复杂度
- 社区规模极小（10★），维护风险高
- Beads 技术栈在演进中（Codex 指出：现已主推 Dolt，非最初的 JSONL+SQLite）

### 5.4 OpenSpec（我们当前使用）

**优势**：
- **多 AI 协作架构独一无二**：Claude 主体思考 + Codex 后端审查 + Gemini 前端实现
- 治理闭环最完整：提案触发 → 审批 → 实现 → 审查 → 验证 → 归档 → 完整性检查
- 三级任务分级直击痛点，避免小任务走重流程
- 最高自由度，基于文件目录完全透明
- Superpowers 技能系统覆盖开发全生命周期
- 学习曲线最低，Markdown 即配置

**劣势**：
- 缺少 clarify 阶段的强制收敛机制
- 缺少任务网络级依赖视图
- 流程文档存在分叉风险（全局 CLAUDE.md vs 项目 CLAUDE.md vs Skills）
- 纯文件系统记忆，大项目 specs/ 膨胀后 Token 成本飙升
- 流程执行更多依赖人工纪律而非工具强制

---

## 6. OpenSpec 缺失能力分析

以下缺失能力由 Codex 和 Gemini 独立分析后交叉验证确认。

### 6.1 需求歧义收敛关口（Clarify Gate）

**共识度**: ★★★★★（Codex 明确指出，Gemini 在 Constitution 建议中隐含）

**现状**：
brainstorming → proposal 之间没有强制的歧义消除步骤。用户审批 proposal 时可能存在未澄清的边界条件、失败语义、兼容性问题。

**Spec Kit 的做法**：
`clarify` 阶段会强制列出所有未决问题（Open Questions），每个问题必须有明确答案后才能进入 `plan` 阶段。

**建议改进**：
在 proposal 审批前增加 **Clarify Checklist**：
- 边界条件是否明确？
- 失败/异常语义是否定义？
- 向后兼容性如何保证？
- 回滚策略是什么？
- 可观测指标（metrics/logging）如何设计？
- 未关闭问题 > 0 → 不得进入实现

### 6.2 跨会话任务依赖图谱

**共识度**: ★★★★★（两者均独立提出）

**现状**：
tasks.md 是扁平 Checklist，无法表达 "Task A 完成后才能开始 Task B" 的依赖关系。大任务拆分后，依赖关系完全靠人脑追踪。

**SpecKit/Beads 的做法**：
tasks.md 作为索引，实际工作状态存储在 Beads 的可查询图谱中，支持 `bd ready` 查看无阻塞任务、`bd graph` 查看依赖关系。

**建议改进（渐进式）**：
- **Phase 1**（低成本）：在 tasks.md 中增加 `depends_on` 标注
  ```markdown
  - [ ] 1.1 创建数据库 schema
  - [ ] 1.2 实现 API 端点 [depends: 1.1]
  - [ ] 1.3 添加前端组件 [depends: 1.2]
  ```
- **Phase 2**（中成本）：用 YAML frontmatter 或 JSON 文件存储结构化依赖
- **Phase 3**（高成本）：引入轻量 SQLite 图谱（仅在数据证明 Phase 2 不足时）

### 6.3 项目宪章 (Constitution)

**共识度**: ★★★★（Gemini 强调，Codex 在 SSOT 建议中隐含）

**现状**：
架构约束散落在 CLAUDE.md 各处，没有集中的"不可违反规则"清单。新加入的 AI 或开发者可能不清楚哪些是铁律、哪些是建议。

**Spec Kit 的做法**：
项目根目录有 `constitution` 文件，定义绝对不可违背的原则，由 `/speckit.constitution` 命令创建。

**建议改进**：
创建 `openspec/constitution.md`，内容包括：
- 架构铁律（如"所有前端状态必须通过 X 管理"）
- 代码风格底线（如"所有 API 必须有 OpenAPI 文档"）
- 安全红线（如"禁止在前端存储敏感 token"）
- 所有 AI 提交前必须校验是否违背宪章

### 6.4 流程文档单一真相 (SSOT)

**共识度**: ★★★★（Codex 强烈指出，验证确认）

**现状**：
全局 `~/.claude/CLAUDE.md` 和项目 `/ontology/CLAUDE.md` 存在大量重复但不完全一致的流程描述。此外，Skills 中的 `openspec-workflow` 也有独立的流程定义。三处来源可能导致执行时"谁的规则为准"的困惑。

**具体问题**：
- 全局 CLAUDE.md Section 4 定义了"全局工作流程"
- 项目 CLAUDE.md Section 4 定义了"开发流程规范"
- openspec-workflow Skill 有自己的流程描述
- 三者存在细微差异

**建议改进**：
1. 选定一处为唯一权威（建议项目 CLAUDE.md）
2. 其他位置仅引用，不重复定义
3. 定期同步检查（可加入 OpenSpec 完整性检查流程）

### 6.5 可执行 Checklist 质量门禁

**共识度**: ★★★（Codex 独特发现）

**现状**：
归档前有完整性检查（Section 0.7），但检查项偏向"文档完整性"（spec/design/delta/tasks），缺少"工程质量"维度的标准化门禁。

**Spec Kit 的做法**：
`checklist` 阶段提供标准化的 DoD（Definition of Done）模板，涵盖安全、性能、回滚、兼容性、监控等。

**建议改进**：
在 `openspec validate` 中增加质量门禁模板：
```markdown
## Quality Gate Checklist
- [ ] 安全审查：OWASP Top 10 检查通过
- [ ] 性能基线：核心路径响应时间 < X ms
- [ ] 回滚方案：数据库迁移有 down migration
- [ ] 兼容性：不影响现有 API 消费者
- [ ] 监控覆盖：关键指标有 logging/metrics
- [ ] 测试覆盖：新增代码测试覆盖率 > 80%
```

### 6.6 Token 投影优化

**共识度**: ★★★（Gemini 重点强调，借鉴 BMAD）

**现状**：
每次 AI 读取 specs/ 时加载完整文件，随着项目迭代 specs/ 膨胀，Token 成本线性增长。

**BMAD 的做法**：
Helper pattern + 动态折叠 + 摘要 + 按需加载，Token 使用减少 70-85%。

**建议改进**：
- 建立 Hook 脚本，在传入上下文前按任务级别提取精简摘要
- 大型 spec 文件增加 `## TL;DR` 摘要段
- 大任务实现时只加载相关 capability 的 spec，不加载全量

---

## 7. 过度设计风险评估

| 框架 | 风险等级 | 主要风险 |
|------|---------|---------|
| **BMAD 全量落地** | 🔴 高 | 多角色+多阶段+多命令，若任务复杂度不足会把交付速度换成流程负担 |
| **SpecKit + Beads + PM 全耦合** | 🟡 中 | 获得追踪能力的同时引入状态同步、一致性、运维成本 |
| **Spec Kit 原生链路** | 🟢 中低 | 本身偏模板化，风险主要来自"所有任务都走全流程" |
| **OpenSpec 当前** | 🟡 中 | 风险不在"过度设计"，而在"**流程分叉**"——口头流程比文档流程更重 |

**关键洞察**（Codex）：OpenSpec 当前的风险不是流程不足，而是流程定义不统一。多处文档定义了略有差异的流程，执行时会出现"谁的规则为准"的困惑，这比缺少某个环节更危险。

---

## 8. 多 AI 分析分歧与裁决

本次分析中，Codex 和 Gemini 在大部分结论上高度一致，但存在以下分歧：

### 8.1 对 BMAD 的评价

| 维度 | Codex 观点 | Gemini 观点 | 最终裁决 |
|------|-----------|-------------|---------|
| 整体价值 | 谨慎——过度设计风险高，仅作"重型模式"备选 | 积极——UX/Creative Agent 对前端有特殊价值 | **采纳 Codex 立场**。BMAD 全量太重不适合日常使用，但应借鉴其 Token 优化技巧和 UX 角色规则集作为 Gemini 前端调用时的辅助 Prompt |

### 8.2 记忆持久化方案

| 维度 | Codex 观点 | Gemini 观点 | 最终裁决 |
|------|-----------|-------------|---------|
| 实现路径 | 渐进——先 YAML 依赖图在 tasks.md 中实现 | 激进——直接引入 SQLite 图谱引擎 | **采纳 Codex 的渐进路线**。先在 tasks.md 中增加 `depends_on` 标注，用数据证明不足后再考虑升级到外部存储 |

### 8.3 Token 优化优先级

| 维度 | Codex 观点 | Gemini 观点 | 最终裁决 |
|------|-----------|-------------|---------|
| 优先级 | 未重点讨论 | 强烈推荐借鉴 BMAD 70-85% 优化 | **采纳 Gemini 建议**。specs/ 膨胀后确实需要按任务级别提取精简摘要，但作为 P2 优先级，当前阶段 specs 尚未膨胀 |

### 8.4 Beads 技术细节

| 维度 | Codex 观点 | Gemini 观点 | 最终裁决 |
|------|-----------|-------------|---------|
| 技术栈 | 纠偏——Beads 现在主推 Dolt（可追溯关系数据库），非 JSONL+SQLite | 沿用 JSONL+SQLite 描述 | **Codex 更准确**。若未来引入 Beads，需基于其当前技术栈（Dolt）评估 |

---

## 9. 推荐改进路线图

### 9.1 优先级矩阵

| 优先级 | 改进项 | 借鉴来源 | 成本 | 收益 | 说明 |
|:------:|-------|---------|:----:|:----:|------|
| **P0** | Clarify Gate | Spec Kit `clarify` | 低 | 高 | 在 proposal 审批前强制歧义清零，增加标准问题集 |
| **P0** | SSOT 清理 | Codex 审查发现 | 低 | 高 | 合并两份 CLAUDE.md 中的流程定义，消除分叉 |
| **P1** | Checklist Gate | Spec Kit `checklist` | 低 | 高 | 标准化质量门禁模板（安全/性能/回滚/兼容/监控） |
| **P1** | Constitution | Spec Kit `constitution` | 低 | 中 | 架构铁律独立文件，AI 提交前校验 |
| **P2** | 任务依赖图 | SpecKit/Beads 理念 | 中 | 中 | tasks.md 增加 `depends_on`，渐进式实现 |
| **P2** | Token 投影 | BMAD Token 优化 | 中 | 中 | specs/ 摘要提取 Hook，按需加载 |
| **P3** | UX/前端规则集 | BMAD UX Agent | 低 | 中 | Gemini 前端调用时挂载可访问性/响应式规则 |
| **P3** | 度量体系 | Codex 建议 | 中 | 中 | 追踪 spec-to-merge lead time 等 |

### 9.2 实施建议

**第一批（立即执行，P0）**：
1. 在 `openspec-workflow` Skill 中增加 Clarify Gate 步骤
2. 审计两份 CLAUDE.md，选定一处为权威来源，另一处改为引用

**第二批（近期，P1）**：
3. 创建标准化质量门禁 Checklist 模板
4. 创建 `openspec/constitution.md`

**第三批（中期，P2）**：
5. tasks.md 格式升级，支持 `depends_on` 标注
6. specs/ 增加 TL;DR 摘要段

**第四批（远期，P3）**：
7. 前端 UX 规则集
8. 度量体系搭建

---

## 10. 结论

### 10.1 核心结论

OpenSpec 的**多 AI 协作架构（Claude+Codex+Gemini 黄金三角）和治理闭环**是四个框架中最适应未来的底座。不需要大换血。

### 10.2 总策略

```
保持 OpenSpec 为主框架
├── 向上层吸收 Spec Kit 的强约束（clarify / checklist / constitution）
├── 向下层借鉴 SpecKit/Beads 的依赖图谱（渐进式，先 YAML 后 DB）
├── 侧面从 BMAD 借鉴 Token 优化和前端角色规则集（轻量引入）
└── 立刻修复流程文档 SSOT 分叉问题
```

### 10.3 不建议做的事

- ❌ 全面切换到 BMAD — 过重，不适合当前团队规模
- ❌ 全量引入 Beads — 增加运维复杂度，当前 tasks.md 尚可应对
- ❌ 放弃 OpenSpec 换用 Spec Kit — 丧失多 AI 协作优势和治理深度
- ❌ 同时改进所有缺失项 — 应按优先级逐步推进

---

## 11. 参考资料

### 框架仓库

- **BMAD Method（原始）**: https://github.com/bmad-code-org/BMAD-METHOD
- **BMAD Claude Code Skills**: https://github.com/aj-geddes/claude-code-bmad-skills
- **BMAD npm 包**: https://www.npmjs.com/package/bmad-method
- **BMAD 文档站**: https://docs.bmad-method.org
- **GitHub Spec Kit**: https://github.com/github/spec-kit (73,744★)
- **社区 SpecKit**: https://github.com/jmanhype/speckit
- **Beads**: https://github.com/beads-app/beads
- **MetaSpec**: https://github.com/ACNet-AI/MetaSpec
- **Awesome Spec Kits**: https://github.com/acnlabs/awesome-spec-kits

### 相关生态

- **autospec CLI**: https://github.com/ariel-frischer/autospec (105★)
- **bmalph (BMAD+Ralph)**: 149★
- **Claude Code Everything Guide**: https://github.com/wesammustafa/Claude-Code-Everything-You-Need-to-Know (1,111★)
- **Joncik91/ucai**: https://github.com/Joncik91/ucai — "用工具原生架构解决 BMAD/GSD/Ralph 同类问题" (28★)

### 本地文件引用

- 全局配置: `~/.claude/CLAUDE.md`
- 项目配置: `/Users/work/GitHub/ontology/CLAUDE.md`
- OpenSpec AGENTS: `/Users/work/GitHub/ontology/purchase/openspec/AGENTS.md`

---

> **报告生成方法**: Claude Opus 4.6 主导分析 + Codex 后端技术审查 + Gemini 全局模式分析，三方交叉验证后由 Claude 综合裁决。
