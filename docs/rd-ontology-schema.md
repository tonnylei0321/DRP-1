# R&D 本体模式参考

## 概述

R&D 本体 (`rd-core.ttl`) 定义了软件开发制品的语义模型，支持需求、设计、代码和测试的知识图谱表示。

## 命名空间

```turtle
@prefix rd: <file:////ontology_build/rd/> .
```

## 类层次结构

```
owl:Thing
├── rd:class/Requirement          # 软件需求
├── rd:class/Design               # 设计文档
├── rd:class/Test                 # 测试用例
├── rd:class/Task                 # 开发任务
└── rd:class/CodeElement          # 抽象代码元素
    ├── rd:class/CodeClass        # 类定义
    ├── rd:class/CodeInterface    # 接口定义
    ├── rd:class/CodeModule       # 模块/包
    ├── rd:class/CodeEnum         # 枚举
    ├── rd:class/CodeField        # 字段/变量
    ├── rd:class/CodeComponent    # UI 组件
    └── rd:class/CodeMethod       # 方法/函数
        ├── rd:class/CodeConstructor  # 构造函数
        └── rd:class/CodeProperty     # 属性访问器
```

## 对象属性（关系）

### 可追溯性关系

| 属性 | 定义域 | 值域 | 描述 |
|------|--------|------|------|
| `implementsRequirement` | CodeElement | Requirement | 代码实现需求 |
| `realizesDesign` | CodeElement | Design | 代码实现设计 |
| `testsCode` | Test | CodeElement | 测试验证代码 |
| `validatesRequirement` | Test | Requirement | 测试验证需求 |
| `affectsFile` | Task | CodeElement | 任务影响的代码文件 |
| `belongsToRequirement` | Task | Requirement | 任务所属需求 |

### 代码结构关系

| 属性 | 定义域 | 值域 | 描述 |
|------|--------|------|------|
| `inherits` | CodeClass | CodeClass | 类继承 |
| `implements` | CodeClass | CodeInterface | 接口实现 |
| `extends` | CodeElement | CodeElement | 扩展关系 |
| `contains` | CodeElement | CodeElement | 包含关系 |
| `calls` | CodeMethod | CodeMethod | 方法调用 |
| `dependsOn` | CodeElement | CodeElement | 依赖关系 |
| `imports` | CodeElement | CodeModule | 模块导入 |
| `overrides` | CodeMethod | CodeMethod | 方法重写 |
| `decorates` | CodeElement | CodeElement | 装饰器应用 |
| `uses` | CodeElement | CodeElement | 使用关系 |

## 数据属性（特性）

### 代码元素属性

| 属性 | 定义域 | 值域 | 描述 |
|------|--------|------|------|
| `fullName` | CodeElement | xsd:string | 完全限定名 |
| `filePath` | CodeElement | xsd:string | 源文件路径 |
| `lineNumber` | CodeElement | xsd:integer | 行号 |
| `language` | CodeElement | xsd:string | 编程语言 |
| `package` | CodeElement | xsd:string | 包/模块名 |
| `modifier` | CodeElement | xsd:string | 访问修饰符（多值） |
| `annotation` | CodeElement | xsd:string | 注解（多值） |
| `docstring` | CodeElement | xsd:string | 文档字符串 |
| `returnType` | CodeMethod | xsd:string | 返回类型 |
| `parameterName` | CodeElement | xsd:string | 参数名 |
| `parameterType` | CodeElement | xsd:string | 参数类型 |

### 需求/设计属性

| 属性 | 定义域 | 值域 | 描述 |
|------|--------|------|------|
| `rationale` | Requirement | xsd:string | 需求存在的原因 |
| `scope` | Requirement | xsd:string | 包含的变更范围 |
| `decision` | Design | xsd:string | 架构决策 |
| `changeId` | Requirement | xsd:string | OpenSpec 变更 ID |

### 链接属性

| 属性 | 定义域 | 值域 | 描述 |
|------|--------|------|------|
| `confidence` | - | xsd:decimal | 链接置信度 (0.0-1.0) |
| `linkMethod` | - | xsd:string | 链接创建方式 |

## IRI 模式

### 类 IRI
```
<file:////ontology_build/rd/class/{类名}>
```

示例：
- `<file:////ontology_build/rd/class/CodeClass>`
- `<file:////ontology_build/rd/class/Requirement>`

### 属性 IRI
```
<file:////ontology_build/rd/property/{属性名}>
```

示例：
- `<file:////ontology_build/rd/property/implementsRequirement>`
- `<file:////ontology_build/rd/property/fullName>`

### 实例 IRI
```
<file:////ontology_build/rd/instance/{类型}/{稳定ID}>
```

其中 `稳定ID = sha1(full_name|file_path|line_number)[:16]`

示例：
- `<file:////ontology_build/rd/instance/CodeClass/a1b2c3d4e5f6g7h8>`
- `<file:////ontology_build/rd/instance/Requirement/x9y8z7w6v5u4t3s2>`

## TTL 输出示例

### 代码元素实例

```turtle
<file:////ontology_build/rd/instance/CodeClass/abc123def456>
    a <file:////ontology_build/rd/class/CodeClass> ;
    rdfs:label "UserService" ;
    <file:////ontology_build/rd/property/fullName> "com.example.UserService" ;
    <file:////ontology_build/rd/property/filePath> "src/main/java/com/example/UserService.java" ;
    <file:////ontology_build/rd/property/lineNumber> 15 ;
    <file:////ontology_build/rd/property/package> "com.example" ;
    <file:////ontology_build/rd/property/language> "java" ;
    <file:////ontology_build/rd/property/modifier> "public" ;
    <file:////ontology_build/rd/property/annotation> "Service" ;
    <file:////ontology_build/rd/property/docstring> "用户管理服务" .
```

### 需求实例

```turtle
<file:////ontology_build/rd/instance/Requirement/req789xyz>
    a <file:////ontology_build/rd/class/Requirement> ;
    rdfs:label "添加用户认证" ;
    <file:////ontology_build/rd/property/changeId> "add-authentication" ;
    <file:////ontology_build/rd/property/rationale> "用户需要安全登录" ;
    <file:////ontology_build/rd/property/scope> "添加基于 JWT 的认证" .
```

### 关系三元组

```turtle
<file:////ontology_build/rd/instance/CodeClass/abc123def456>
    <file:////ontology_build/rd/property/implementsRequirement>
    <file:////ontology_build/rd/instance/Requirement/req789xyz> .
```

## SPARQL 查询示例

### 查找实现某需求的代码

```sparql
PREFIX rd: <file:////ontology_build/rd/>

SELECT ?code ?file ?line
WHERE {
    ?code rd:property/implementsRequirement ?req .
    ?req rdfs:label "添加用户认证" .
    ?code rd:property/filePath ?file .
    ?code rd:property/lineNumber ?line .
}
```

### 查找某包中的所有类

```sparql
PREFIX rd: <file:////ontology_build/rd/>

SELECT ?class ?name
WHERE {
    ?class a rd:class/CodeClass .
    ?class rd:property/package "com.example" .
    ?class rdfs:label ?name .
}
```

### 查找继承层次

```sparql
PREFIX rd: <file:////ontology_build/rd/>

SELECT ?child ?parent
WHERE {
    ?child rd:property/inherits ?parent .
    ?child rdfs:label ?childName .
    ?parent rdfs:label ?parentName .
}
```

## 架构说明

### 本体构建流程

```
源代码 → code_processor → DocumentGenerator → ontology_client → ontology 项目 → Neo4j
```

1. **代码解析**：`code_processor` 解析源代码，提取 `CodeElement` 和 `CodeRelation`
2. **文档生成**：`DocumentGenerator` 将结构化数据转换为自然语言描述文档
3. **本体构建**：`ontology_client` 调用 ontology 项目的 `CodeOntologyBuilder`
4. **LLM 提取**：ontology 项目使用 LLM 从文档中提取实体和关系
5. **TTL 生成**：生成符合本模式的 Turtle 格式本体文件
6. **知识图谱**：导入 Neo4j 形成可查询的知识图谱

### 职责分离

| 组件 | 职责 |
|------|------|
| `code_processor` | 代码解析、文档生成 |
| `ontology_client` | 调用 ontology 服务 |
| `ontology` 项目 | LLM 提取、TTL 生成、Neo4j 导入 |
| `rd_ontology` | 仅提供模式定义 (rd-core.ttl) |

## 兼容性

R&D 本体设计兼容以下标准：

- **OWL 2**：使用 `owl:Class`、`owl:ObjectProperty`、`owl:DatatypeProperty`
- **RDFS**：使用 `rdfs:label`、`rdfs:subClassOf`、`rdfs:domain`、`rdfs:range`
- **XSD**：使用标准 XML Schema 数据类型

本体可加载到以下系统：
- Neo4j（通过 neosemantics/n10s 插件）
- Apache Jena
- RDF4J
- GraphDB
- 任何符合 SPARQL 标准的三元组存储
