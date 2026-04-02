# ontology-devos MCP 插件

<cite>
**本文档引用的文件**
- [README.md](file://plugins/ontology-devos/README.md)
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py)
- [.mcp.json](file://plugins/ontology-devos/.mcp.json)
- [hooks.json](file://plugins/ontology-devos/hooks/hooks.json)
- [install.sh](file://plugins/ontology-devos/install.sh)
- [client.py](file://ontology_client/client.py)
- [config.py](file://ontology_client/config.py)
- [__init__.py](file://code_processor/__init__.py)
- [parser_factory.py](file://code_processor/parser_factory.py)
- [base_parser.py](file://code_processor/base_parser.py)
- [document_generator.py](file://code_processor/document_generator.py)
- [incremental_processor.py](file://code_processor/incremental_processor.py)
- [settings.json](file://settings.json)
- [.ontology_config.json](file://.ontology_config.json)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构概览](#架构概览)
5. [详细组件分析](#详细组件分析)
6. [依赖关系分析](#依赖关系分析)
7. [性能考虑](#性能考虑)
8. [故障排除指南](#故障排除指南)
9. [结论](#结论)

## 简介

ontology-devos MCP 插件是一个专为 Claude Code 设计的代码本体检索插件，提供了强大的代码上下文检索、修改影响分析和需求-代码链接能力。该插件基于 Neo4j 图数据库和 ontology 项目构建，能够智能地理解和检索代码知识图谱中的信息。

该插件的核心功能包括：
- **混合检索**：结合全文检索、语义检索和图结构扩展的多维度代码上下文检索
- **影响分析**：在修改代码前自动分析潜在影响范围
- **需求链接**：将需求文档与相关代码元素建立关联
- **自动化钩子**：智能触发机制，提升开发效率

## 项目结构

```mermaid
graph TB
subgraph "插件核心"
A[plugins/ontology-devos/]
B[servers/ontology_mcp/]
C[.mcp.json]
D[hooks/]
E[install.sh]
F[README.md]
end
subgraph "核心服务"
G[FastMCP 服务器]
H[MCP 工具实现]
I[Hook 系统]
end
subgraph "知识图谱"
J[Neo4j 数据库]
K[代码本体]
L[需求本体]
end
subgraph "代码处理"
M[代码解析器]
N[文档生成器]
O[增量处理器]
end
A --> G
B --> H
D --> I
G --> J
H --> K
I --> L
M --> N
N --> O
```

**图表来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L1-L271)
- [hooks.json](file://plugins/ontology-devos/hooks/hooks.json#L1-L28)

**章节来源**
- [README.md](file://plugins/ontology-devos/README.md#L1-L161)
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L1-L271)

## 核心组件

### MCP 服务器组件

插件的核心是一个基于 FastMCP 的 Python 服务器，提供了三个主要的工具：

1. **lookup_code_context** - 代码上下文检索工具
2. **check_modification_impact** - 修改影响分析工具  
3. **link_spec_to_code** - 需求-代码链接工具

### Hook 系统

插件实现了两个智能 Hook：
- **UserPromptSubmit**：用户提交问题时自动触发代码上下文检索
- **PreToolUse**：代码写入前强制执行影响分析

### 配置管理系统

插件支持多种配置方式：
- 环境变量配置
- JSON 配置文件
- 自动安装脚本

**章节来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L147-L267)
- [hooks.json](file://plugins/ontology-devos/hooks/hooks.json#L1-L28)
- [config.py](file://ontology_client/config.py#L1-L129)

## 架构概览

```mermaid
graph TD
subgraph "用户界面层"
U[Claude Code 用户]
P[插件工具调用]
end
subgraph "MCP 层"
S[FastMCP 服务器]
T[工具实现]
H[Hook 系统]
end
subgraph "知识图谱层"
N[Neo4j 数据库]
R[ReasoningClient]
end
subgraph "代码处理层"
C[代码解析器]
D[文档生成器]
I[增量处理器]
end
U --> P
P --> S
S --> T
S --> H
T --> R
H --> N
R --> N
C --> D
D --> I
I --> R
```

**图表来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L106-L142)
- [client.py](file://ontology_client/client.py#L76-L156)

## 详细组件分析

### FastMCP 服务器实现

服务器采用 FastMCP 框架，提供了高性能的 MCP 协议实现：

```mermaid
classDiagram
class FastMCP {
+tool() decorator
+run() void
+register_tool() void
}
class ReasoningClient {
+lookup_context() ContextResult
+analyze_impact() ImpactResult
+link_requirements() LinkResult
+switch_database() bool
+health_check() dict
}
class LookupCodeContextInput {
+str query
+Optional~str~ project_name
+int top_k
+int max_nodes
+int k_hops
+bool enable_fulltext
+bool enable_semantic
+bool enable_structural
+str context_format
+float min_score
+bool include_properties
+Optional~str~ fulltext_index
+Optional~str~ text_vector_index
}
FastMCP --> ReasoningClient : "uses"
FastMCP --> LookupCodeContextInput : "validates"
```

**图表来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L29-L142)
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L52-L98)

### Hook 触发机制

插件实现了智能的自动化触发系统：

```mermaid
sequenceDiagram
participant User as 用户
participant Claude as Claude Code
participant Hook as Hook 系统
participant Tool as MCP 工具
participant Neo4j as Neo4j 数据库
User->>Claude : 提交代码相关问题
Claude->>Hook : UserPromptSubmit 事件
Hook->>Tool : 调用 lookup_code_context
Tool->>Neo4j : 执行混合检索
Neo4j-->>Tool : 返回上下文结果
Tool-->>Hook : 格式化响应
Hook-->>Claude : 注入系统消息
Claude-->>User : 提供增强的答案
User->>Claude : 准备修改代码
Claude->>Hook : PreToolUse 事件
Hook->>Tool : 要求 check_modification_impact
Tool->>Neo4j : 分析影响范围
Neo4j-->>Tool : 返回影响分析
Tool-->>Hook : 影响分析结果
Hook-->>Claude : 允许或要求分析
```

**图表来源**
- [hooks.json](file://plugins/ontology-devos/hooks/hooks.json#L4-L25)
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L147-L267)

### 安装和配置流程

```mermaid
flowchart TD
A[开始安装] --> B{检查 .ontology_config.json}
B --> |存在| C[读取配置]
B --> |不存在| D[创建配置文件]
C --> E{验证 ontology_path}
E --> |有效| F[检查 Python 环境]
E --> |无效| G[错误: 路径无效]
F --> H{检查 Neo4j 连接}
H --> |成功| I[安装 MCP SDK]
H --> |失败| J[跳过连接测试]
I --> K[更新 .mcp.json]
J --> K
K --> L[测试服务器]
L --> M[完成安装]
D --> E
```

**图表来源**
- [install.sh](file://plugins/ontology-devos/install.sh#L44-L110)
- [install.sh](file://plugins/ontology-devos/install.sh#L137-L214)

**章节来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L1-L271)
- [hooks.json](file://plugins/ontology-devos/hooks/hooks.json#L1-L28)
- [install.sh](file://plugins/ontology-devos/install.sh#L1-L263)

## 依赖关系分析

### 外部依赖

插件的主要外部依赖包括：

```mermaid
graph LR
subgraph "核心依赖"
A[mcp] --> B[FastMCP 框架]
C[neo4j] --> D[Neo4j 驱动]
E[pydantic] --> F[数据验证]
end
subgraph "项目依赖"
G[ontology_sdk] --> H[ReasoningClient]
I[code_processor] --> J[代码解析]
K[rd_ontology] --> L[本体模式]
end
subgraph "工具链"
M[FastMCP] --> N[工具注册]
O[Pydantic] --> P[模型验证]
Q[Logging] --> R[日志记录]
end
```

**图表来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L18-L47)
- [install.sh](file://plugins/ontology-devos/install.sh#L119-L130)

### 内部模块依赖

```mermaid
graph TD
A[server.py] --> B[ontology_sdk.ReasoningClient]
A --> C[FastMCP 框架]
A --> D[Pydantic 模型]
E[client.py] --> F[OntologyConfig]
E --> G[CodeOntologyBuilder]
E --> H[DocumentKGPipeline]
I[parser_factory.py] --> J[BaseCodeParser]
I --> K[LanguageType]
I --> L[ProjectInfo]
M[document_generator.py] --> N[CodeElement]
M --> O[CodeRelation]
M --> P[NLPGenerator]
```

**图表来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L106-L142)
- [client.py](file://ontology_client/client.py#L88-L156)
- [parser_factory.py](file://code_processor/parser_factory.py#L20-L171)

**章节来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L1-L271)
- [client.py](file://ontology_client/client.py#L1-L800)
- [parser_factory.py](file://code_processor/parser_factory.py#L1-L248)

## 性能考虑

### 检索优化策略

插件采用了多种性能优化策略：

1. **索引优化**：支持全文索引和向量索引的组合使用
2. **缓存机制**：单例模式管理 ReasoningClient 实例
3. **增量处理**：支持代码变更检测和增量更新
4. **并发控制**：合理设置 top_k 和 max_nodes 参数

### 内存管理

```mermaid
flowchart TD
A[启动服务器] --> B[初始化 ReasoningClient]
B --> C[设置日志级别]
C --> D[注册工具函数]
D --> E[等待请求]
F[处理请求] --> G[获取客户端实例]
G --> H{客户端存在?}
H --> |否| I[创建新客户端]
H --> |是| J[复用现有客户端]
I --> K[执行查询]
J --> K
K --> L[返回结果]
M[退出程序] --> N[清理资源]
N --> O[关闭数据库连接]
```

**图表来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L106-L142)
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L133-L142)

## 故障排除指南

### 常见问题及解决方案

| 问题类型 | 症状 | 解决方案 |
|---------|------|----------|
| MCP 服务器未加载 | Claude 显示插件不可用 | 检查 .mcp.json 配置，重启 Claude Code |
| Neo4j 连接失败 | 连接超时或认证错误 | 验证连接参数，检查网络连通性 |
| 工具调用失败 | 返回错误信息 | 检查 ontology_path 配置，确认模块可导入 |
| Hook 未触发 | 自动功能不工作 | 检查 Hook 配置，验证权限设置 |

### 日志和调试

插件提供了详细的日志记录功能：

```mermaid
graph LR
A[日志级别] --> B[DEBUG]
A --> C[INFO]
A --> D[WARNING]
A --> E[ERROR]
F[日志输出] --> G[控制台]
F --> H[文件]
F --> I[系统日志]
J[关键日志点] --> K[服务器启动]
J --> L[工具调用]
J --> M[数据库操作]
J --> N[Hook 触发]
```

**图表来源**
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L24-L27)
- [install.sh](file://plugins/ontology-devos/install.sh#L225-L237)

**章节来源**
- [README.md](file://plugins/ontology-devos/README.md#L125-L144)
- [server.py](file://plugins/ontology-devos/servers/ontology_mcp/server.py#L133-L142)

## 结论

ontology-devos MCP 插件是一个功能强大、架构清晰的代码本体检索解决方案。它通过以下特点为开发者提供了卓越的价值：

### 主要优势

1. **智能化的自动化**：通过 Hook 系统实现代码相关问题的自动检索和修改前的影响分析
2. **多维度检索能力**：结合全文、语义和结构化检索，提供准确的代码上下文
3. **完整的开发流程集成**：从代码分析到本体构建，再到知识图谱查询的完整链路
4. **灵活的配置选项**：支持多种配置方式，适应不同的部署环境

### 应用场景

- **代码审查**：自动获取相关上下文，提高审查效率
- **需求管理**：建立需求与代码的直接关联
- **技术债务管理**：分析修改的影响范围，降低重构风险
- **知识传承**：通过本体化知识，减少人员流动带来的损失

### 发展前景

该插件为后续的功能扩展奠定了良好的基础，包括：
- 更丰富的检索算法
- 更智能的代码理解能力
- 更完善的本体构建工具链
- 更好的可视化界面

通过持续的优化和扩展，ontology-devos MCP 插件将成为开发团队不可或缺的智能助手。