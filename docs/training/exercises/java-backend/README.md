# Java 后端实战：订单状态机服务

> 时间：13:30 - 16:30（3小时）
> 难度：中等
> 前置：Spring Boot 基础、Maven

---

## 破冰第一步

拿到代码后按以下顺序操作：

1. `cd scaffold/ && mvn compile` — 确认编译通过
2. `mvn test` — 运行测试，看到 1 个 FAIL（示例测试，这是预期的 RED 状态）
3. **从 develop 创建自己的特性分支**：
   ```bash
   git checkout develop
   git checkout -b feature/training-{你的名字}
   ```
4. 启动 Claude Code：`claude`
5. 发送第一条指令：`请阅读 scaffold/ 目录下的代码结构，我需要实现一个订单状态机服务`

---

## 实践流程（严格按此顺序执行）

> 对齐 CLAUDE.md 规范：设计先行 → 三方审核 → 提案 → TDD 实现 → 三方审查

### 阶段1：需求分析与设计（13:40-14:00）

1. 在 Claude Code 中粘贴下方"主需求"，让 Claude 进行需求分析
2. 让 Claude 分析状态机的组件设计、状态转换逻辑
3. **三方设计审核**：
   - 让 Claude 调用 Codex 审查技术可行性（状态转换是否线程安全？）
   - 让 Claude 调用 Gemini 审查场景覆盖度（所有非法转换是否都考虑到？）
   - 三方达成一致后，确认设计方案

### 阶段2：编写 OpenSpec 提案（14:00-14:20）

1. 用 Claude Code 生成 OpenSpec 提案：
   - `proposal.md`：Why + What Changes + Impact
   - `tasks.md`：bite-sized 实现步骤（每步含文件路径、代码要点、验证命令）
2. **三方提案审核**：Codex 审查 API 设计合理性，Gemini 审查边界条件
3. 讲师审核通过 → **关卡1打卡**

### 阶段3：TDD 实现（14:20-15:00）

1. 按 tasks.md 步骤顺序实现
2. **每个 task 严格 TDD**：先写测试（RED）→ 实现代码（GREEN）→ 重构
3. **关卡2打卡**：主功能测试通过

### 阶段4：需求变更（15:00-16:00）

**15:00-15:15 更新文档（强制停顿，禁止写代码）**：
1. 讲师宣布变更需求（见下方"中途变更"）
2. 更新 proposal.md：在 What Changes 中新增变更内容
3. 更新 tasks.md：新增实现步骤
4. **三方变更审核**：Codex/Gemini 审核变更方案的合理性

**15:15-16:00 变更实现**：
1. 按更新后的 tasks.md 继续 TDD 实现
2. 处理边界条件
3. 补充测试用例

### 阶段5：三方代码审查与验证（16:00-16:30）

1. **Codex 审查**：代码质量、安全性、线程安全
2. **Gemini 审查**：功能覆盖度、实现是否偏离 proposal
3. 根据审查意见修复问题
4. 运行全部测试，确认通过
5. 提交到特性分支：`git add . && git commit -m "feat: 订单状态机服务"`
6. **关卡3打卡**：三方审查通过 + 测试全绿

---

## 业务背景

你负责一个电商系统的订单模块。当前系统有基础的订单 CRUD，但状态管理是硬编码的字符串比较，既不安全也不可维护。需要实现一个正式的状态机来管理订单生命周期。

## 需求描述

### 主需求（14:00-15:00 完成）

实现订单状态流转 API：

```
订单状态：CREATED → PAID → SHIPPED → DELIVERED
                ↘ CANCELLED（可从 CREATED 和 PAID 取消）
```

**具体要求**：
1. `POST /api/orders` — 创建订单（初始状态 CREATED）
2. `PUT /api/orders/{id}/pay` — 支付订单（CREATED → PAID）
3. `PUT /api/orders/{id}/ship` — 发货（PAID → SHIPPED）
4. `PUT /api/orders/{id}/deliver` — 确认收货（SHIPPED → DELIVERED）
5. `PUT /api/orders/{id}/cancel` — 取消订单（仅 CREATED/PAID 可取消）
6. 非法状态转换返回 400 + 错误信息

### 中途变更（15:00 讲师宣布）

新增"退款"状态和流转：

```
PAID → REFUNDING → REFUNDED
DELIVERED → REFUNDING → REFUNDED（售后退款）
```

**变更要求**：
1. `PUT /api/orders/{id}/refund` — 申请退款
2. `PUT /api/orders/{id}/confirm-refund` — 确认退款
3. 退款需要记录退款原因（reason 字段）
4. 更新 proposal.md 和 tasks.md

### 边界条件
- 订单不存在返回 404
- 重复操作（如已支付再支付）返回 409
- 所有状态变更记录操作日志（谁在什么时间做了什么操作）

---

## 验收标准

### 关卡1：OpenSpec 完成（14:20前）
- [ ] proposal.md 包含 Why、What Changes、Impact
- [ ] tasks.md 包含 4+ 个 bite-sized 步骤
- [ ] 每步有文件路径、代码要点、验证命令

### 关卡2：主功能通过（15:00前）
- [ ] 所有状态流转 API 可用
- [ ] 非法转换返回 400
- [ ] 单元测试覆盖所有合法/非法转换
- [ ] 测试全绿通过

### 关卡3：变更 + 交叉审查通过（16:30前）
- [ ] 退款功能实现
- [ ] proposal.md 已更新
- [ ] Codex 交叉审查通过
- [ ] 无 SQL 注入、无状态不一致风险

---

## 脚手架代码说明

脚手架位于 `scaffold/` 目录，结构如下：

```
scaffold/
├── pom.xml                          # Maven 配置（已含 Spring Boot Starter）
├── src/
│   ├── main/java/com/training/order/
│   │   ├── OrderApplication.java    # 启动类（已完成）
│   │   ├── model/
│   │   │   ├── Order.java           # 订单实体（待完善）
│   │   │   └── OrderStatus.java     # 状态枚举（待实现）
│   │   ├── controller/
│   │   │   └── OrderController.java # 控制器（待实现）
│   │   ├── service/
│   │   │   └── OrderService.java    # 服务层（待实现）
│   │   └── repository/
│   │       └── OrderRepository.java # 数据层（已完成，内存Map）
│   └── test/java/com/training/order/
│       └── OrderServiceTest.java    # 测试类（待编写）
└── README.md
```

**已完成的部分**：
- Spring Boot 启动类
- Maven 依赖配置
- 内存版 Repository（不需要数据库）
- 基础 Order 实体骨架

**需要你实现的部分**：
- OrderStatus 枚举 + 合法转换定义
- OrderService 业务逻辑
- OrderController REST API
- OrderServiceTest 单元测试

---

## 参考提示词（可以给 Claude Code 的指令）

### 编写 OpenSpec
```
我需要实现一个订单状态机服务。请根据以下需求创建 OpenSpec 提案：
[粘贴主需求内容]
脚手架代码在 scaffold/ 目录，请先阅读现有代码结构。
```

### TDD 实现
```
按 tasks.md 的步骤 1.1，先为 OrderStatus 的状态转换编写测试用例。
测试场景：
1. CREATED → PAID 合法
2. CREATED → SHIPPED 非法
3. CANCELLED → 任何状态都非法
```

### 交叉审查（三方分工）
```
# 第一步：Codex 审查代码质量和安全性
请 Codex 审查 OrderService 的实现：
1. 状态转换是否线程安全？
2. 是否有状态不一致的风险？
3. 错误处理是否完善？
4. 是否有 SQL 注入或其他安全隐患？

# 第二步：Gemini 审查功能覆盖度
请 Gemini 审查订单状态机的实现：
1. 所有合法状态转换是否都已实现？
2. 所有非法转换是否都正确拒绝？
3. 是否有遗漏的边界条件？
4. 测试用例是否覆盖了所有场景？

# 第三步：验证实现是否偏离设计
对照 proposal.md 检查：
1. 实现的功能是否和 What Changes 一致？
2. 是否有未在 proposal 中声明的变更？
```

---

## 评分要点

| 项目 | 权重 | 说明 |
|------|------|------|
| OpenSpec 质量 | 25% | proposal 清晰、tasks 粒度合理 |
| 代码正确性 | 25% | 状态转换逻辑正确、边界处理完善 |
| TDD 执行 | 20% | 先写测试再实现，测试覆盖充分 |
| 交叉审查 | 15% | 使用了 MCP 工具，修复了审查问题 |
| 变更管理 | 15% | 变更后更新了 proposal，增量实现 |
