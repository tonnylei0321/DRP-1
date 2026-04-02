# Python 实战：日志清洗与告警 Webhook 服务

> 时间：13:30 - 16:30（3小时）
> 难度：中等
> 前置：Python 基础、了解 HTTP API

---

## 破冰第一步

拿到代码后按以下顺序操作：

1. `cd scaffold/ && pip install -r requirements.txt` — 安装依赖
2. `pytest tests/ -v` — 运行测试，看到 1 个 FAIL（示例测试，这是预期的 RED 状态）
3. **从 develop 创建自己的特性分支**：
   ```bash
   git checkout develop
   git checkout -b feature/training-{你的名字}
   ```
4. 启动 Claude Code：`claude`
5. 发送第一条指令：`请阅读 scaffold/ 目录下的代码结构，我需要实现一个日志清洗告警服务`

---

## 实践流程（严格按此顺序执行）

> 对齐 CLAUDE.md 规范：设计先行 → 三方审核 → 提案 → TDD 实现 → 三方审查

### 阶段1：需求分析与设计（13:40-14:00）

1. 在 Claude Code 中粘贴下方"主需求"，让 Claude 进行需求分析
2. 让 Claude 分析 API 设计、Pydantic 模型结构、服务层架构
3. **三方设计审核**：
   - 让 Claude 调用 Codex 审查 API 设计合理性和 Pydantic 模型完善度
   - 让 Claude 调用 Gemini 审查告警策略和场景覆盖度
   - 三方达成一致后，确认设计方案

### 阶段2：编写 OpenSpec 提案（14:00-14:20）

1. 用 Claude Code 生成 OpenSpec 提案：
   - `proposal.md`：Why + What Changes + Impact
   - `tasks.md`：bite-sized 实现步骤（每步含文件路径、代码要点、验证命令）
2. **三方提案审核**：Codex 审查 API 端点设计，Gemini 审查异常场景覆盖
3. 讲师审核通过 → **关卡1打卡**

### 阶段3：TDD 实现（14:20-15:00）

1. 按 tasks.md 步骤顺序实现
2. **每个 task 严格 TDD**：先写测试（RED）→ 实现代码（GREEN）→ 重构
3. **关卡2打卡**：POST/GET 接口正常 + 告警触发 + 测试通过

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

1. **Codex 审查**：Pydantic 模型完善度、并发数据一致性、内存 OOM 风险
2. **Gemini 审查**：告警去重时间窗口逻辑、功能覆盖度
3. 根据审查意见修复问题
4. 运行全部测试，确认通过
5. 提交到特性分支：`git add . && git commit -m "feat: 日志清洗告警服务"`
6. **关卡3打卡**：三方审查通过 + 测试全绿

---

## 业务背景

运维团队每天要手动翻看日志文件查找错误，发现问题后再手动发飞书/钉钉通知。这个过程低效且容易遗漏。需要实现一个自动化服务：接收日志流 → 解析提取 → 发现错误自动告警。

## 需求描述

### 主需求（14:00-15:00 完成）

实现一个 FastAPI 服务，接收日志数据并自动告警：

```
日志格式：
2026-03-09 14:30:15 [ERROR] UserService - 用户认证失败: user_id=12345, reason=token_expired
2026-03-09 14:30:16 [INFO]  OrderService - 订单创建成功: order_id=67890
2026-03-09 14:30:17 [WARN]  PaymentService - 支付超时重试: payment_id=11111, retry=2
```

**具体要求**：
1. `POST /api/logs` — 接收日志数据（JSON 数组格式）
   ```json
   {
     "logs": [
       {"timestamp": "2026-03-09 14:30:15", "level": "ERROR", "service": "UserService", "message": "用户认证失败: user_id=12345, reason=token_expired"},
       {"timestamp": "2026-03-09 14:30:16", "level": "INFO", "service": "OrderService", "message": "订单创建成功: order_id=67890"}
     ]
   }
   ```

2. `GET /api/logs/stats` — 获取日志统计信息
   ```json
   {
     "total": 100,
     "by_level": {"ERROR": 5, "WARN": 10, "INFO": 85},
     "by_service": {"UserService": 30, "OrderService": 70}
   }
   ```

3. 告警规则：收到 ERROR 级别日志时，调用 Webhook 发送告警
   - Webhook URL 通过环境变量 `WEBHOOK_URL` 配置
   - 告警内容包含：时间、服务名、错误信息
   - 实际实现时 mock Webhook 调用（print 即可）

4. 数据校验：使用 Pydantic 模型验证输入格式

### 中途变更（15:00 讲师宣布）

新增"告警去重"逻辑：

**变更要求**：
1. 同一服务 + 同一错误信息在 5 分钟时间窗口内只告警一次
2. `GET /api/alerts` — 查看告警历史
   ```json
   {
     "alerts": [
       {
         "first_seen": "2026-03-09 14:30:15",
         "last_seen": "2026-03-09 14:33:20",
         "count": 5,
         "service": "UserService",
         "message": "用户认证失败",
         "status": "active"
       }
     ]
   }
   ```
3. 时间窗口可配置（默认 5 分钟）
4. 更新 proposal.md 和 tasks.md

### 边界条件
- 空日志数组返回 200 但不做处理
- 无效日期格式返回 422
- 未知 level 值（非 ERROR/WARN/INFO）记录但不告警
- Webhook 调用失败不影响日志接收（异常捕获）

---

## 验收标准

### 关卡1：OpenSpec 完成（14:20前）
- [ ] proposal.md 清晰描述问题和方案
- [ ] tasks.md 包含 API 端点、Pydantic 模型、服务层步骤
- [ ] 明确了告警策略

### 关卡2：主功能通过（15:00前）
- [ ] POST /api/logs 接收并存储日志
- [ ] GET /api/logs/stats 返回正确统计
- [ ] ERROR 日志触发告警（mock）
- [ ] pytest 测试覆盖核心场景

### 关卡3：变更 + 交叉审查通过（16:30前）
- [ ] 告警去重逻辑正确
- [ ] 时间窗口可配置
- [ ] GET /api/alerts 返回去重后的告警历史
- [ ] Codex 交叉审查通过

---

## 脚手架代码说明

```
scaffold/
├── pyproject.toml              # 项目配置（已含 fastapi, uvicorn, pydantic, pytest）
├── requirements.txt            # 依赖列表
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口（已完成基础配置）
│   ├── models/
│   │   ├── __init__.py
│   │   └── log.py              # Pydantic 模型（待实现）
│   ├── routers/
│   │   ├── __init__.py
│   │   └── logs.py             # 日志相关路由（待实现）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── log_service.py      # 日志处理服务（待实现）
│   │   └── alert_service.py    # 告警服务（待实现）
│   └── config.py               # 配置管理（已完成）
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures（已完成）
│   └── test_logs.py            # 测试文件（待编写）
└── README.md
```

**已完成的部分**：
- 项目配置和依赖
- FastAPI 应用基础配置（CORS、生命周期）
- pytest conftest（TestClient fixture）
- 配置管理（环境变量读取）

**需要你实现的部分**：
- Pydantic 请求/响应模型
- 日志接收和统计路由
- 日志处理服务（存储 + 统计）
- 告警服务（规则匹配 + Webhook 调用）
- pytest 测试用例

---

## 参考提示词

### 编写 OpenSpec
```
我需要实现一个日志清洗与告警 Webhook 服务。请根据以下需求创建 OpenSpec 提案：
[粘贴主需求内容]
脚手架代码在 scaffold/ 目录，使用 FastAPI + Pydantic。
请先阅读现有代码结构和 config.py。
```

### TDD 实现
```
按 tasks.md 的步骤 1.1，先为 POST /api/logs 接口编写 pytest 测试：
场景1：正常接收 3 条日志（含 1 条 ERROR）
场景2：空日志数组
场景3：无效日期格式返回 422
使用 conftest.py 中已有的 TestClient fixture。
```

### 交叉审查（三方分工）
```
# 第一步：Codex 审查代码质量和安全性
请 Codex 审查日志服务的实现：
1. Pydantic 模型是否完善（字段验证）？
2. 并发场景下数据一致性是否有问题？
3. 内存存储是否有 OOM 风险？
4. Webhook 调用失败的异常处理是否完善？

# 第二步：Gemini 审查功能覆盖度
请 Gemini 审查日志服务的实现：
1. 告警去重的时间窗口逻辑是否正确？
2. 所有 API 端点的场景是否覆盖完整？
3. 错误日志的告警触发是否可靠？
4. 统计信息是否准确反映实际数据？

# 第三步：验证实现是否偏离设计
对照 proposal.md 检查：
1. 实现的功能是否和 What Changes 一致？
2. 是否有未在 proposal 中声明的变更？
```

---

## 评分要点

| 项目 | 权重 | 说明 |
|------|------|------|
| OpenSpec 质量 | 25% | API 设计清晰、Pydantic 模型定义准确 |
| 代码正确性 | 25% | 接口功能正确、告警逻辑准确 |
| TDD 执行 | 20% | pytest 先行，覆盖正常 + 异常场景 |
| 交叉审查 | 15% | 使用了 Codex，修复了审查问题 |
| 变更管理 | 15% | 变更后 proposal 更新，去重逻辑增量实现 |
