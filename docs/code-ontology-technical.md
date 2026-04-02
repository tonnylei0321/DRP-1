# 代码本体技术文档

## 概述

代码本体系统通过将代码分析能力与 SDD（规范驱动开发）工作流集成，实现对代码结构的语义理解。它将源代码转换为知识图谱，链接需求、设计、代码元素和测试。

## 架构

### 数据流

```
源代码 → code_processor → DocumentGenerator → ontology_client → ontology 项目 → Neo4j
```

1. **代码解析**: `code_processor` 解析源代码，提取 `CodeElement` 和 `CodeRelation`
2. **文档生成**: `DocumentGenerator` 将结构化数据转换为描述文档
3. **本体构建**: `ontology_client` 调用 ontology 项目的 `CodeOntologyBuilder`
4. **LLM 提取**: `LLMPluginManager` 使用 LLM 从文档中提取实体和关系
5. **TTL 生成**: 生成 Turtle 格式的本体文件
6. **知识图谱**: 导入 Neo4j 形成可查询的知识图谱

### 三层本体模型

| 层级 | 用途 | 示例 |
|------|------|------|
| Entity 层 | 核心概念 | Requirement, Design, CodeElement, Test |
| Class 层 | 代码类型 | CodeClass, CodeInterface, CodeMethod |
| Instance 层 | 具体实例 | UserService, authenticate() |

## 模块说明

### code_processor

多语言代码解析模块，支持 Java、Python、JavaScript/TypeScript。

- `ParserFactory`: 解析器工厂
- `DocumentGenerator`: 文档生成器
- `CodeElement`: 代码元素数据结构

### ontology_client

ontology 项目客户端。

- `build_code_ontology()`: 构建代码本体
- `build_sdd_ontology()`: 构建 SDD 本体
- `query()`: 执行 Cypher 查询

### sdd_integration

SDD 工作流集成模块。

- `CodeRequirementLinker`: 代码-需求链接器
- `Link`: 链接数据结构

### rd_ontology

R&D 本体模式定义（rd-core.ttl）。

**注意：** TTL 生成逻辑已移至 ontology 项目的 `CodeOntologyBuilder`。

## CLI 使用

```bash
python -m code_processor.cli analyze /path/to/project
python -m code_processor.cli docs /path/to/project --output docs/
python -m code_processor.cli build /path/to/project --output ontology.ttl
python -m code_processor.cli info
```

## 配置

创建 `.ontology_config.json`：

```json
{
  "ontology_path": "/path/to/ontology",
  "domain": "rd",
  "neo4j_uri": "bolt://localhost:7687"
}
```
