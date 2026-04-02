# 代码本体构建流水线设计

> 日期: 2026-02-02
> 状态: 设计中
> 作者: Claude + Codex + Gemini 协作

## 1. 背景与问题

### 1.1 当前问题

1. **流程断裂**：
   - 文档生成后没有保存到磁盘
   - 直接调用 `CodeOntologyBuilder.build_from_documents()` 跳过了完整的 Pipeline
   - LLM 提取的实体没有稳定的 ID 锚点，导致关系无法正确链接

2. **文档质量问题**：
   - 当前的 `DocumentGenerator` 是"机械式翻译"，只是列出 AST 节点
   - 缺乏语义丰富的自然语言描述
   - LLM 无法从碎片信息中理解代码意图

3. **没有复用 ontology 项目的成熟能力**：
   - `DocumentKGPipeline` 的 5 阶段流水线
   - `LLMTripletPlugin` 的分片处理
   - `EntityResolver` 的实体消歧
   - `TTLParser + Neo4jImporter` 的 MERGE 语义导入

### 1.2 目标

1. **完整代码知识图谱**：包含所有代码元素（类、方法、字段）及其关系（继承、调用、依赖）
2. **SDD 追溯支持**：需求 → 代码 → 测试的完整追溯链
3. **变更影响分析**：基于知识图谱分析代码变更的影响范围

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ontologyDevOS                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │ code_       │    │ document_       │    │ ontology_client         │  │
│  │ processor   │───▶│ generator       │───▶│ (调用 ontology 服务)    │  │
│  │             │    │ (LLM 增强)      │    │                         │  │
│  └─────────────┘    └─────────────────┘    └───────────┬─────────────┘  │
│        │                    │                          │                │
│        │                    ▼                          │                │
│        │           ┌─────────────────┐                 │                │
│        │           │ docs/ontology/  │                 │                │
│        │           │ code_docs/      │                 │                │
│        │           └─────────────────┘                 │                │
│        │                                               │                │
│  ┌─────▼─────────────────────────────────────────────▼─────────────┐   │
│  │                    sdd_integration                               │   │
│  │  (需求-代码链接、变更影响分析)                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           ontology 项目                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐  │
│  │ DocumentKG      │    │ LLMTriplet      │    │ Entity              │  │
│  │ Pipeline        │───▶│ Plugin          │───▶│ Resolver            │  │
│  │ (5阶段流水线)   │    │ (分片+重试)     │    │ (实体消歧)          │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────┘  │
│                                                         │               │
│  ┌─────────────────┐    ┌─────────────────┐            │               │
│  │ TTL Parser      │◀───│ TTL Generator   │◀───────────┘               │
│  └────────┬────────┘    └─────────────────┘                            │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ Neo4j Importer  │───▶ Neo4j (ontologydevos 数据库)                   │
│  │ (MERGE 语义)    │                                                    │
│  └─────────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
源代码
  │
  ▼
code_processor.parse()
  │
  ▼
ProjectInfo / CodeElement / CodeRelation
  │
  ▼
DocumentGenerator.generate_all_documents() [LLM 增强]
  │
  ▼
DocumentWriter.save() → docs/ontology/code_docs/<project>/<build_id>/
  │
  ▼
OntologyClient.build_and_import_code_ontology(input_dir=...)
  │
  ▼
ontology.DocumentKGPipeline
  │
  ├─▶ 文档解析 (DocumentAdapter)
  ├─▶ 三元组抽取 (LLMTripletPlugin)
  ├─▶ 实体消歧 (EntityResolver)
  ├─▶ TTL 生成 (TTLGenerator)
  └─▶ Neo4j 导入 (Neo4jImporter)
  │
  ▼
Neo4j (ontologydevos 数据库)
```

## 3. 组件设计

### 3.1 LLM 增强文档生成器

**位置**: `code_processor/nlp_generator.py` (新增)

**功能**: 参考 mcp-graphrag 的 NLPGenerator，为代码元素生成高质量的自然语言描述

```python
class NLPGenerator:
    """
    LLM 增强的自然语言生成器

    为代码元素生成业务意图描述，而非简单的 AST 翻译
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.business_terms = self._load_business_terms()

    def generate_class_description(self, element: CodeElement) -> str:
        """
        生成类的业务意图描述

        输入: 类的代码 + 父类 + 调用的方法 + 导入的模块
        输出: 解释这个类的业务意图，不仅是做什么，而是为什么这么做
        """
        pass

    def generate_method_description(self, element: CodeElement) -> str:
        """生成方法的业务意图描述"""
        pass

    def _load_business_terms(self) -> Dict[str, str]:
        """
        加载业务术语映射

        例如: Service → 服务类, Controller → 控制器, Repository → 数据访问层
        """
        return {
            'Service': '服务类，提供业务逻辑处理',
            'Controller': '控制器，处理 HTTP 请求',
            'Repository': '数据访问层，负责数据持久化',
            'Factory': '工厂类，负责对象创建',
            'Builder': '构建器，用于复杂对象的构建',
            'Handler': '处理器，处理特定类型的事件或请求',
            'Manager': '管理器，协调多个组件的工作',
            'Validator': '验证器，负责数据验证',
            'Parser': '解析器，负责数据解析',
            'Generator': '生成器，负责内容生成',
        }
```

### 3.2 文档写入器

**位置**: `code_processor/document_writer.py` (新增)

**功能**: 负责文档落盘和构建 ID 管理

```python
class DocumentWriter:
    """
    文档写入器

    负责将生成的文档保存到磁盘，管理构建 ID
    """

    def __init__(self, base_dir: str = "docs/ontology/code_docs"):
        self.base_dir = Path(base_dir)

    def save(
        self,
        project_name: str,
        documents: List[Document],
        build_id: Optional[str] = None
    ) -> str:
        """
        保存文档到磁盘

        目录结构:
        docs/ontology/code_docs/<project>/<build_id>/
        ├── project.md
        ├── packages/
        │   └── <pkg>.md
        ├── elements/
        │   └── <full_name>.md
        └── relations.md

        Returns:
            构建目录路径
        """
        pass

    def _generate_build_id(self) -> str:
        """生成构建 ID (时间戳 + 短哈希)"""
        pass
```

### 3.3 文档格式

**带 Frontmatter 的 Markdown 格式**:

```markdown
---
doc_type: class
name: UserService
full_name: app.services.UserService
file_path: app/services/user.py
line_number: 12
language: python
package: app.services
element_id: code:app.services.UserService
modifiers:
  - public
annotations:
  - "@Service"
---

# 类: UserService

## 业务意图

UserService 是用户管理的核心服务类，负责处理用户认证、授权和账户管理等业务逻辑。
它依赖 UserRepository 进行数据持久化，使用 TokenService 进行令牌管理。

## 关键职责

1. **用户认证**: 验证用户凭据，生成访问令牌
2. **用户管理**: 创建、更新、删除用户账户
3. **权限验证**: 检查用户是否有权限执行特定操作

## 方法列表

### authenticate(username: str, password: str) -> Optional[User]

验证用户凭据。首先检查用户是否存在，然后验证密码哈希。
如果验证成功，返回用户对象；否则返回 None。

**关联实体**: User, PasswordHasher

### create_user(user_data: UserCreateDTO) -> User

创建新用户。验证输入数据，生成密码哈希，保存到数据库。

**关联实体**: UserCreateDTO, UserRepository

## 依赖关系

- **UserRepository**: 数据持久化
- **TokenService**: 令牌管理
- **PasswordHasher**: 密码加密

## 被依赖

- **AuthController**: 认证控制器
- **UserController**: 用户管理控制器
```

### 3.4 实体 ID 规范

**格式**: `code:<language>:<project>:<full_name>`

**示例**:
- `code:python:ontologyDevOS:code_processor.parser_factory.ParserFactory`
- `code:python:ontologyDevOS:ontology_client.client.OntologyClient.build_code_ontology`

**用途**:
1. 作为 Neo4j 节点的唯一标识
2. 作为 LLM 输出的锚点，确保实体可回指
3. 作为关系链接的目标

### 3.5 OntologyClient 改造

**位置**: `ontology_client/client.py`

**改造点**:
1. 新增 `build_and_import_code_ontology()` 方法，使用完整的 Pipeline
2. 废弃直接调用 `CodeOntologyBuilder.build_from_documents()`

```python
class OntologyClient:

    def build_and_import_code_ontology(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        domain: str = "rd",
        database: str = "ontologydevos"
    ) -> BuildResult:
        """
        构建代码本体并导入 Neo4j（使用完整 Pipeline）

        流程:
        1. 加载文档目录
        2. 使用 LLMTripletPlugin 抽取三元组
        3. 使用 EntityResolver 消歧
        4. 生成 TTL
        5. 使用 Neo4jImporter 导入（MERGE 语义）

        Args:
            input_dir: 文档目录（由 DocumentWriter 生成）
            output_dir: TTL 输出目录
            domain: 本体域名
            database: Neo4j 数据库名

        Returns:
            构建结果
        """
        pass
```

## 4. SDD 链接设计

### 4.1 链接策略

**双向锚点 + 语义匹配**:

1. **代码侧锚点**: 使用 `element_id` 作为唯一标识
2. **需求侧锚点**: 使用 OpenSpec 的 `change_id` 或 `requirement_id`
3. **语义匹配**: 使用 Embedding 向量计算相似度

### 4.2 链接流程

```
OpenSpec 文档 (proposal/design/specs)
  │
  ▼
SDD Parser → Requirement / Design / Task
  │
  ▼
Embedding Generator → 需求向量
  │
  ▼
Semantic Matcher ← 代码元素向量 (从文档 frontmatter 提取)
  │
  ▼
Link Candidates (requirement_id, element_id, confidence, reason)
  │
  ▼
Link Validator (验证 element_id 存在)
  │
  ▼
Neo4j: (:Requirement)-[:implementsRequirement]->(:CodeElement)
```

### 4.3 关系类型

| 关系 | 源 | 目标 | 描述 |
|------|-----|------|------|
| `implementsRequirement` | CodeElement | Requirement | 代码实现需求 |
| `realizesDesign` | CodeElement | Design | 代码实现设计 |
| `testsCode` | Test | CodeElement | 测试验证代码 |
| `validatesRequirement` | Test | Requirement | 测试验证需求 |
| `affectsFile` | Task | CodeElement | 任务影响代码 |

## 5. 实现计划

### Phase 1: 文档生成增强 (1-2 天)

1. 新增 `code_processor/nlp_generator.py` - LLM 增强描述生成
2. 新增 `code_processor/document_writer.py` - 文档落盘
3. 改造 `code_processor/document_generator.py` - 集成 NLPGenerator
4. 定义文档格式规范（带 frontmatter）

### Phase 2: Pipeline 集成 (1-2 天)

1. 改造 `ontology_client/client.py` - 新增 `build_and_import_code_ontology()`
2. 集成 ontology 项目的 `DocumentKGPipeline`
3. 配置代码特定的实体/关系类型
4. 测试完整流程

### Phase 3: SDD 链接增强 (1-2 天)

1. 改造 `sdd_integration/linker.py` - 添加语义匹配
2. 实现 Embedding 生成和相似度计算
3. 实现链接验证和导入
4. 测试需求-代码追溯

### Phase 4: CLI 和测试 (1 天)

1. 更新 `code_processor/cli.py` - 新增完整构建命令
2. 编写集成测试
3. 更新文档

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LLM 调用成本高 | 构建时间长、费用高 | 增量构建、缓存机制 |
| LLM 输出不稳定 | 实体/关系提取失败 | JSON Schema 验证、重试机制 |
| 实体消歧不准确 | 关系链接错误 | 使用稳定 ID、人工审核 |
| Neo4j 性能问题 | 大项目导入慢 | 批量导入、索引优化 |

## 7. 成功标准

1. **文档质量**: 生成的文档包含业务意图描述，而非简单的 AST 翻译
2. **实体准确率**: LLM 提取的实体 90%+ 能正确链接到代码元素
3. **关系完整性**: 继承、调用、依赖关系正确建立
4. **SDD 追溯**: 能够从需求追溯到代码，从代码追溯到测试
5. **查询性能**: Neo4j 查询响应时间 < 1s

## 8. 参考资料

- mcp-graphrag: `/Users/work/iuapgit/mcp-graphrag`
- ontology 项目: `/Users/work/iuapgit/ontology`
- OpenSpec 规范: `/Users/work/iuapgit/ontologyDevOS/openspec/`
