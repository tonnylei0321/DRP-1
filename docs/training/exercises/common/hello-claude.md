# 上午统一练习：Hello Claude Code

> 目标：确保每个人的工具链可用，体验 Claude Code 基本操作。
> 时间：10:45 - 12:00 中的练习部分（约 30min）

---

## 练习1：基础交互（10min）

### 1.1 启动 Claude Code

```bash
# 打开终端，进入任意工作目录
cd ~/training-workspace
mkdir hello-claude && cd hello-claude
git init

# 启动 Claude Code
claude
```

### 1.2 创建文件

在 Claude Code 中输入：

```
创建一个 Python 文件 hello.py，功能是：
1. 读取当前目录下的 data.json 文件
2. 按 age 字段降序排序
3. 输出排序后的结果
```

检查点：确认 hello.py 已创建且代码合理。

### 1.3 创建测试数据

```
创建 data.json 测试数据，包含 5 条用户记录，
每条有 name 和 age 字段
```

### 1.4 运行代码

```
运行 hello.py，确认输出正确
```

---

## 练习2：MCP 工具体验（10min）

### 2.1 调用 Codex 审查

```
请 Codex 审查 hello.py 的代码质量，
给出改进建议
```

观察 Codex 的回复，理解 MCP 协同的感觉。

### 2.2 调用 Gemini 分析

```
请 Gemini 分析 hello.py，建议如何增加
错误处理和命令行参数支持
```

---

## 练习3：OpenSpec 体验（10min）

### 3.1 编写 proposal

```
我要给 hello.py 新增一个功能：支持按指定字段排序。
帮我创建一个 OpenSpec proposal。

需求：
- 命令行参数指定排序字段（name 或 age）
- 命令行参数指定排序方向（asc 或 desc）
- 默认按 age 降序
```

### 3.2 检查产出

确认 Claude Code 生成了：
- [ ] proposal.md — 包含 Why、What Changes、Impact
- [ ] tasks.md — 包含 bite-sized 步骤

---

## 验收标准

完成以上练习后，你应该：
- [x] 能启动 Claude Code 并进行基本交互
- [x] 能让 Claude Code 创建、修改、运行代码
- [x] 能调用 Codex 和 Gemini MCP 工具
- [x] 能用 Claude Code 生成 OpenSpec 文档
- [x] 理解 proposal.md 和 tasks.md 的格式

**完成后在群里发"环节1完成"。**
