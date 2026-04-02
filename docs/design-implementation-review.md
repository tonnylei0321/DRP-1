# 设计-实现一致性报告

## 概述

本文档记录了设计文档 (`openspec/changes/add-code-ontology-capability/design.md`) 与实际实现之间的一致性分析，由 Claude、Codex 和 Gemini 共同审查。

**审查日期**：2026-02-02
**总体评估**：**高度一致**，存在少量差异

## 架构决策合规性

### AD-1：三层本体映射

| 方面 | 设计 | 实现 | 状态 |
|------|------|------|------|
| 实体层 | Requirement, Design, CodeElement, Test | 在 `rd-core.ttl` 中定义为 `owl:Class` | ✅ 合规 |
| 类层 | CodeClass, CodeInterface, CodeMethod 等 | 使用 `rdfs:subClassOf CodeElement` 定义 | ✅ 合规 |
| 实例层 | 具体实例 | 由 `TTLGenerator.element_to_ttl()` 生成 | ✅ 合规 |

**结论**：完全按设计实现。

### AD-2：命名空间设计

| 方面 | 设计 | 实现 | 状态 |
|------|------|------|------|
| 域命名空间 | `rd` | TTL 中使用 `rd:` 前缀 | ✅ 合规 |
| 类 IRI 模式 | `<file:////path/rd/class/{ClassName}>` | 与实现匹配 | ✅ 合规 |
| 实例 IRI 模式 | `<file:////path/rd/instance/{Type}/{StableId}>` | 与实现匹配 | ✅ 合规 |
| StableId 生成 | `sha1(full_name\|file_path\|line_number)` | 在 `TTLGenerator.generate_stable_id()` 中实现 | ✅ 已修复 |

**已修复**：创建了 `rd_ontology/iri_utils.py` 统一 ID 生成逻辑。

### AD-3：代码解析器迁移

| 组件 | 设计 | 实现 | 状态 |
|------|------|------|------|
| base_parser.py | CodeElement, CodeRelation, ProjectInfo | 完全迁移 | ✅ 合规 |
| java_parser.py | Java AST 解析 | 使用 javalang 迁移 | ✅ 合规 |
| python_parser.py | Python AST 解析 | 使用 ast 模块迁移 | ✅ 合规 |
| javascript_parser.py | JS/TS 解析 | 使用正则表达式迁移 | ✅ 合规 |
| parser_factory.py | 语言检测 | 完全迁移 | ✅ 合规 |
| document_generator.py | 修改为 TTL 输出 | 替换为 `ttl_generator.py` | ✅ 合规 |

**已修复**：`CodeElement` 中的 `parameters` 和 `return_type` 字段现已正确传播。

### AD-4：本体项目作为服务

| 方面 | 设计 | 实现 | 状态 |
|------|------|------|------|
| 基于文件的集成 | 生成 TTL 文件 | `TTLGenerator.save_ttl()` | ✅ 合规 |
| 基于 API 的集成 | 查询接口 | `OntologyClient.query()` | ✅ 合规 |
| TTL 上传 | 写入 ontology_build/ttl | `OntologyClient.upload_ttl()` | ✅ 合规 |

**结论**：按设计实现，采用基于文件的方式。

### AD-5：OpenSpec 文档解析

| 文档 | 设计提取 | 实现 | 状态 |
|------|----------|------|------|
| proposal.md → Requirement | 标题、Why、What Changes | `OpenSpecParser.parse_proposal()` | ✅ 合规 |
| design.md → Design | 架构决策 | `OpenSpecParser.parse_design()` | ✅ 已修复 |
| tasks.md → Task | 复选框项、文件路径 | `OpenSpecParser.parse_tasks()` | ✅ 已修复 |

**已修复**：
1. `affectsFile` 关系现已在 TTL 中生成
2. `design_to_ttl` 现支持 `List[Dict]` 和 `List[str]` 两种格式

### AD-6：代码-需求链接

| 方法 | 设计置信度 | 实现 | 状态 |
|------|------------|------|------|
| 显式注解 | 1.0 | `CONFIDENCE_ANNOTATION = 1.0` | ✅ 合规 |
| 文件路径匹配 | 0.9 | `CONFIDENCE_FILE_PATH = 0.9` | ✅ 合规 |
| Git 提交 | 0.8 | `CONFIDENCE_GIT_COMMIT = 0.8` | ✅ 合规 |
| 语义相似度 | 0.6 | 未实现（未来计划） | ⏳ 计划中 |

**已修复**：置信度分数现通过 RDF 具体化持久化到 TTL 输出。

## 组件设计合规性

### CodeElement 结构

| 字段 | 设计 | 实现 | 状态 |
|------|------|------|------|
| element_type | ElementType | ✅ | ✅ |
| name | str | ✅ | ✅ |
| full_name | str | ✅ | ✅ |
| file_path | str | ✅ | ✅ |
| line_number | int | ✅ | ✅ |
| package | str | ✅ | ✅ |
| modifiers | List[str] | ✅ | ✅ |
| annotations | List[str] | ✅ | ✅ 已修复（含装饰器） |
| docstring | str | ✅ | ✅ |
| parameters | List[Dict] | ✅ | ✅ 已修复 |
| return_type | str | ✅ | ✅ 已修复 |
| children | List[CodeElement] | ✅ | ✅ |

### TTLGenerator 方法

| 方法 | 设计 | 实现 | 状态 |
|------|------|------|------|
| `__init__(base_path)` | ✅ | ✅ | ✅ |
| `generate_instance_iri()` | ✅ | ✅ | ✅ |
| `element_to_ttl()` | ✅ | ✅ | ✅ |
| `relation_to_ttl()` | ✅ | ✅ | ✅ |
| `project_to_ttl()` | ✅ | ✅ | ✅ |

### OntologyClient 方法

| 方法 | 设计 | 实现 | 状态 |
|------|------|------|------|
| `upload_ttl()` | 返回 bool | 返回 str（路径） | ⚠️ 不同 |
| `query()` | ✅ | ✅ | ✅ |
| `search()` | ✅ | 未实现 | ❌ 缺失 |

## 差异汇总

### 高优先级（已修复 ✅）

1. ~~**StableId 不一致**：Linker 生成的 ID 与 TTLGenerator 不同~~ → **已修复**：创建了 `rd_ontology/iri_utils.py` 共享 ID 生成函数
2. ~~**参数未传播**：Python 解析器中方法参数丢失~~ → **已修复**：更新 `CodeElement.__init__` 接受 `parameters` 和 `return_type` 作为显式参数

### 中优先级（已修复 ✅）

3. ~~**置信度未持久化**：链接置信度分数未写入 TTL~~ → **已修复**：在 `linker.py` 中实现 RDF 具体化以持久化 confidence 和 linkMethod
4. ~~**affectsFile 缺失**：任务-文件关系未生成~~ → **已修复**：更新 `task_to_ttl` 包含 `affectsFile` 属性
5. ~~**装饰器未映射**：Python 装饰器未包含在 `annotations` 中~~ → **已修复**：更新 `element_to_ttl` 将装饰器映射到 annotation 属性，带 `@` 前缀
6. ~~**设计解析不匹配**：`decisions` 类型不匹配~~ → **已修复**：更新 `design_to_ttl` 同时处理 `List[str]` 和 `List[Dict]` 格式

### 低优先级（待处理）

7. **OntologyClient API 差异**：`upload_ttl` 返回类型不同，缺少 `search()`
8. **changeId 域**：Schema 仅限于 Requirement

## 已应用的修复（2026-02-02）

| 问题 | 修复 | 修改的文件 |
|------|------|------------|
| StableId 不一致 | 创建共享 `iri_utils.py` 模块 | `rd_ontology/iri_utils.py`（新）、`ttl_generator.py`、`linker.py` |
| 参数未传播 | 添加显式 `parameters` 和 `return_type` 参数 | `code_processor/base_parser.py` |
| 置信度未持久化 | 实现 RDF 具体化 | `sdd_integration/linker.py` |
| affectsFile 缺失 | 为 `task_to_ttl` 添加 `file_paths` 参数 | `rd_ontology/ttl_generator.py` |
| 装饰器未映射 | 将装饰器映射到 annotation 属性 | `rd_ontology/ttl_generator.py` |
| 设计解析不匹配 | 支持字符串和字典两种格式 | `rd_ontology/ttl_generator.py` |

## 建议（已更新）

1. ~~**统一 ID 生成**：创建 StableId 共享工具~~ ✅ 完成
2. ~~**修复参数传播**：更新 Python 解析器设置 `parameters` 和 `return_type`~~ ✅ 完成
3. ~~**实现具体化**：使用 RDF 具体化存储链接置信度~~ ✅ 完成
4. ~~**添加 affectsFile**：在 TTL 中生成任务-文件关系~~ ✅ 完成
5. ~~**映射装饰器**：将装饰器包含在 annotations 或单独属性中~~ ✅ 完成
6. ~~**更新设计文档**：与实现决策对齐~~ ✅ 完成
7. **待处理**：对齐 OntologyClient API（返回类型，添加 `search()`）
8. **待处理**：扩展 changeId 域以包含 Design 和 Task

## 审查者备注

### Gemini 评估
> "实现与设计意图高度一致。三层映射正确实现。主要差异在数据流的'加载'和'查询'部分。"

### Codex 评估
> "部分合规。核心结构已实现，但 StableId、置信度持久化和任务-文件关系存在明显差异。"

### Claude 综合
实现成功交付了核心架构。识别的差异主要在数据完整性（置信度分数、参数）而非架构偏差。这些可以增量解决，无需重构。
