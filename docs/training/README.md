# AI 驱动开发全员培训方案

> 一天实战训练 + 正式切换全员开发方式

## 培训目标

让研发部全体人员（Java 后端、前端、Python、算法）掌握以下开发范式：

1. **OpenSpec 规范驱动开发** — 先定义规范，再写代码
2. **Claude Code 主导编码** — AI 辅助编码的正确姿势
3. **多 AI 协同（MCP）** — Claude + Codex + Gemini 三方协作

## 培训理念

```
旧模式：需求口头传达 → 边想边写 → 人工 Review → 修修补补
新模式：OpenSpec 定义需求 → AI 生成代码 → 多 AI 交叉审查 → 自动验证
```

**核心转变**：从"边想边写"到"先规范后实现"，从"人写 AI 查"到"AI 写人审"。

## 培训架构：混合模式

```
上午（全员统一）        下午（分4组实战）         傍晚（全员统一）
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ 理论 + 演示   │ →  │ Java / 前端 /     │ →  │ 成果展示      │
│ 环境就绪      │    │ Python / 算法     │    │ 行动计划      │
└──────────────┘    └──────────────────┘    └──────────────┘
```

### 两个版本

| 版本 | 时长 | 议程文件 | 适用场景 |
|------|------|---------|---------|
| 全天版 | 09:30-18:00（含 80min 午休） | [agenda.md](agenda.md) | 首次培训、时间充裕 |
| 半天版 | 09:00-13:00（含 10min 休息） | [agenda-halfday.md](agenda-halfday.md) | 时间紧凑、复训 |

**半天版压缩策略**：理论从 2.5h 压缩到 45min，实战从 3h 压缩到 2h，复盘从 1h 压缩到 30min。所有核心环节（三方审核、TDD、需求变更、交叉审查）均保留。

## 文件清单

| 文件 | 说明 |
|------|------|
| [README.md](README.md) | 本文件，培训方案总纲 |
| [agenda.md](agenda.md) | 详细分钟级议程（全天版） |
| [agenda-halfday.md](agenda-halfday.md) | 详细分钟级议程（半天版 4h） |
| [instructor-guide.md](instructor-guide.md) | 讲师手册（含讲稿要点、演示脚本） |
| [exercises/common/](exercises/common/) | 上午统一练习 |
| [exercises/java-backend/](exercises/java-backend/) | Java 后端实战题目 + 脚手架 |
| [exercises/frontend/](exercises/frontend/) | 前端实战题目 + 脚手架 |
| [exercises/python/](exercises/python/) | Python 实战题目 + 脚手架 |
| [exercises/algorithm/](exercises/algorithm/) | 算法实战题目 + 脚手架 |
| [templates/scoring.md](templates/scoring.md) | 评分表模板 |
| [templates/env-check.sh](templates/env-check.sh) | 环境自检脚本（macOS/Linux） |
| [templates/env-check.bat](templates/env-check.bat) | 环境自检脚本（Windows） |
| [env-setup-guide.md](env-setup-guide.md) | 培训前环境准备引导（含 macOS + Windows） |
| [student-guide.md](student-guide.md) | 学员实战流程引导 |
| [post-training/daily-sop.md](post-training/daily-sop.md) | 训后日常 SOP |
| [post-training/champion-guide.md](post-training/champion-guide.md) | AI Champion 职责指南 |

## 前置准备清单

### 培训前 3 天
- [ ] 确认参训人员名单及分组
- [ ] 分配统一 API Key（Claude Code、Codex、Gemini）
- [ ] 准备 4 个分组教室/会议室
- [ ] 每组指定 1 名讲师 + 1 名助教

### 培训前 1 天
- [ ] 全员运行 `env-check.sh` 环境自检脚本
- [ ] 群内接龙确认环境就绪
- [ ] 发放脚手架代码仓库地址
- [ ] 各组 clone 对应脚手架并确认编译/启动成功
- [ ] 讲师彩排 Live Demo（端到端跑一遍）

### 培训当天
- [ ] 提前 30 分钟开放教室，处理遗留环境问题
- [ ] 确认网络、代理、API Key 全部可用
- [ ] 准备备用 API Key（防止限流）

## 人员配比

| 角色 | 数量 | 职责 |
|------|------|------|
| 主讲师 | 1 | 上午统一理论 + 傍晚复盘 |
| 分组讲师 | 4 | 下午各组实战指导 |
| 技术助教 | 4 | 环境问题排障 + 巡场答疑 |

> 讲师配比建议至少 1:15，否则实操阶段会严重卡顿。

## 成功标准

| 指标 | 目标 |
|------|------|
| 当天完成率 | 80%+ 学员完成最小闭环工件 |
| 流程合规率 | 90%+ 学员按 OpenSpec 流程执行 |
| 工件产出 | 每人产出 proposal.md + tasks.md + 代码 + 测试 |
| 满意度 | 培训满意度 4.0/5.0 以上 |
| 2 周采用率 | 50%+ 的 MR 附带 OpenSpec |
