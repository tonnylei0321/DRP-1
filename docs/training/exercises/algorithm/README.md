# 算法实战：模型评估与可视化流水线

> 时间：13:30 - 16:30（3小时）
> 难度：中等
> 前置：Python 基础、了解分类模型评估指标

---

## 破冰第一步

拿到代码后按以下顺序操作：

1. `cd scaffold/ && pip install -r requirements.txt` — 安装依赖
2. `pytest tests/ -v` — 运行测试，看到 2 个 FAIL（示例测试，这是预期的 RED 状态）
3. `python src/evaluate.py --input data/sample_predictions.csv --output report/` — 确认 CLI 可运行
4. **从 develop 创建自己的特性分支**：
   ```bash
   git checkout develop
   git checkout -b feature/training-{你的名字}
   ```
5. 启动 Claude Code：`claude`
6. 发送第一条指令：`请阅读 scaffold/ 目录下的代码结构和 data/sample_predictions.csv 的数据格式，我需要实现一个模型评估流水线`

---

## 实践流程（严格按此顺序执行）

> 对齐 CLAUDE.md 规范：设计先行 → 三方审核 → 提案 → TDD 实现 → 三方审查

### 阶段1：需求分析与设计（13:40-14:00）

1. 在 Claude Code 中粘贴下方"主需求"，让 Claude 进行需求分析
2. 让 Claude 分析模块划分（metrics/visualizer/reporter）、CLI 参数设计、输出格式
3. **三方设计审核**：
   - 让 Claude 调用 Codex 审查指标计算方案和模块接口设计
   - 让 Claude 调用 Gemini 审查输出格式规范和场景覆盖度
   - 三方达成一致后，确认设计方案

### 阶段2：编写 OpenSpec 提案（14:00-14:20）

1. 用 Claude Code 生成 OpenSpec 提案：
   - `proposal.md`：Why + What Changes + Impact
   - `tasks.md`：bite-sized 实现步骤（每步含文件路径、代码要点、验证命令）
2. **三方提案审核**：Codex 审查指标计算逻辑，Gemini 审查输出格式和边界条件
3. 讲师审核通过 → **关卡1打卡**

### 阶段3：TDD 实现（14:20-15:00）

1. 按 tasks.md 步骤顺序实现
2. **每个 task 严格 TDD**：先写测试（RED）→ 实现代码（GREEN）→ 重构
3. **关卡2打卡**：指标计算正确 + 图表生成 + 报告输出 + 测试通过

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

1. **Codex 审查**：指标计算是否与 sklearn 一致、大数据量性能
2. **Gemini 审查**：图表美观性和可读性、报告格式规范性
3. 根据审查意见修复问题
4. 运行全部测试，确认通过
5. 提交到特性分支：`git add . && git commit -m "feat: 模型评估流水线"`
6. **关卡3打卡**：三方审查通过 + 测试全绿

---

## 业务背景

算法团队每次训练完模型后，都要手动计算评估指标、手动画图、手动写报告。不同人的评估代码格式不统一，图表风格各异，评估结果缺乏可比性。需要一个标准化的模型评估流水线。

## 需求描述

### 主需求（14:00-15:00 完成）

实现一个模型评估脚本，输入预测结果 CSV，输出评估报告：

**输入文件格式**（predictions.csv）：
```csv
sample_id,true_label,predicted_label,confidence
1,cat,cat,0.95
2,dog,cat,0.51
3,cat,cat,0.88
4,bird,bird,0.92
5,dog,dog,0.79
```

**具体要求**：
1. `evaluate.py` — 主评估脚本
   ```bash
   python evaluate.py --input predictions.csv --output report/
   ```

2. 计算以下指标：
   - 整体 Accuracy
   - 每个类别的 Precision、Recall、F1-Score
   - 加权平均 F1（weighted avg）
   - 输出为 JSON 格式的 metrics.json

3. 生成以下可视化：
   - 混淆矩阵热力图（confusion_matrix.png）
   - 各类别 F1-Score 柱状图（f1_scores.png）

4. 生成文本报告（report.txt）：
   ```
   === 模型评估报告 ===
   评估时间：2026-03-09 14:30:15
   样本总数：1000
   类别数量：3

   整体准确率：85.2%

   各类别指标：
   | 类别 | Precision | Recall | F1-Score | 样本数 |
   |------|-----------|--------|----------|--------|
   | cat  | 0.87      | 0.92   | 0.89     | 350    |
   | dog  | 0.83      | 0.78   | 0.80     | 330    |
   | bird | 0.86      | 0.85   | 0.85     | 320    |

   加权平均 F1：0.85
   ```

### 中途变更（15:00 讲师宣布）

新增"自定义阈值评估 + ROC 曲线"功能：

**变更要求**：
1. 新增 `--threshold` 参数，支持自定义置信度阈值（默认无阈值）：
   ```bash
   python evaluate.py --input predictions.csv --output report/ --threshold 0.7
   ```
   - 置信度低于阈值的预测标记为 "uncertain"（不参与正常指标计算）
   - 在报告中新增"不确定样本"统计
2. 新增 ROC 曲线图表（roc_curve.png，需将多分类转为 one-vs-rest）
3. 在报告中新增"阈值分析"部分：显示不同阈值下的准确率变化
4. 更新 proposal.md 和 tasks.md

### 边界条件
- CSV 文件不存在返回清晰错误信息
- CSV 列名不匹配返回格式错误提示
- 某类别样本数为 0 时，该类别指标显示 N/A
- 输出目录不存在时自动创建

---

## 验收标准

### 关卡1：OpenSpec 完成（14:20前）
- [ ] proposal.md 清晰描述工具目标和输入/输出格式
- [ ] tasks.md 包含指标计算、可视化、报告生成步骤
- [ ] 明确了 CLI 参数设计

### 关卡2：主功能通过（15:00前）
- [ ] 指标计算正确（Accuracy、P/R/F1）
- [ ] 混淆矩阵图表生成正确
- [ ] F1 柱状图生成正确
- [ ] 文本报告格式规范
- [ ] pytest 测试覆盖指标计算逻辑

### 关卡3：变更 + 交叉审查通过（16:30前）
- [ ] 阈值过滤功能正确
- [ ] ROC 曲线图表生成正确
- [ ] 阈值分析报告正确
- [ ] Codex 交叉审查通过

---

## 脚手架代码说明

```
scaffold/
├── pyproject.toml              # 项目配置
├── requirements.txt            # 依赖：pandas, numpy, matplotlib, scikit-learn, pytest
├── data/
│   └── sample_predictions.csv  # 示例数据（100条，3类别）
├── src/
│   ├── __init__.py
│   ├── evaluate.py             # 主入口脚本（CLI 参数解析已完成）
│   ├── metrics.py              # 指标计算模块（待实现）
│   ├── visualizer.py           # 可视化模块（待实现）
│   └── reporter.py             # 报告生成模块（待实现）
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures（示例数据 fixture 已完成）
│   └── test_metrics.py         # 指标测试（待编写）
└── README.md
```

**已完成的部分**：
- 项目配置和依赖
- CLI 参数解析（argparse）
- 示例数据文件（100 条记录，cat/dog/bird 三类）
- pytest conftest（示例数据 fixture）

**需要你实现的部分**：
- metrics.py：指标计算（可用 sklearn 辅助）
- visualizer.py：图表生成（matplotlib）
- reporter.py：文本报告生成
- evaluate.py：串联各模块的主流程
- test_metrics.py：测试用例

---

## 参考提示词

### 编写 OpenSpec
```
我需要实现一个模型评估与可视化流水线。请根据以下需求创建 OpenSpec 提案：
[粘贴主需求内容]
脚手架代码在 scaffold/ 目录。请先阅读 evaluate.py 的 CLI 参数定义
和 data/sample_predictions.csv 的数据格式。
```

### TDD 实现
```
按 tasks.md 的步骤 1.1，先为 metrics.py 编写测试：
使用 conftest.py 中的示例数据 fixture。
场景1：正确计算 3 类别的 Precision/Recall/F1
场景2：全部预测正确时 Accuracy = 1.0
场景3：某类别样本为 0 时返回 N/A
```

### 交叉审查（三方分工）
```
# 第一步：Codex 审查代码质量和安全性
请 Codex 审查评估流水线的实现：
1. 指标计算是否与 sklearn 一致？
2. 大数据量（100万条）时的性能？
3. 文件 I/O 异常处理是否完善？
4. 类别样本数为 0 时是否正确处理？

# 第二步：Gemini 审查功能覆盖度和可视化
请 Gemini 审查评估流水线的实现：
1. 图表美观性和可读性如何？轴标签、标题、颜色是否合理？
2. 文本报告格式是否规范、信息是否完整？
3. 输出文件是否齐全（metrics.json、2张图表、report.txt）？
4. 多模型对比时文件名冲突处理？

# 第三步：验证实现是否偏离设计
对照 proposal.md 检查：
1. 实现的功能是否和 What Changes 一致？
2. 是否有未在 proposal 中声明的变更？
```

---

## 评分要点

| 项目 | 权重 | 说明 |
|------|------|------|
| OpenSpec 质量 | 25% | 输入/输出格式清晰、CLI 设计合理 |
| 指标正确性 | 25% | 计算结果与 sklearn 一致 |
| 可视化质量 | 20% | 图表清晰、标签完整、颜色合理 |
| 交叉审查 | 15% | 使用了 Codex，修复了审查问题 |
| 变更管理 | 15% | 阈值功能增量实现，proposal 更新 |
