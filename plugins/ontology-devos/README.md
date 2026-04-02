# ontology-devos 插件

代码本体检索插件，为 Claude Code 提供代码上下文检索、修改影响分析和需求-代码链接能力。

## 功能

### MCP 工具

| 工具 | 功能 | 使用场景 |
|------|------|----------|
| `lookup_code_context` | 混合检索代码上下文 | 问代码相关问题时 |
| `check_modification_impact` | 分析代码修改影响 | 修改代码前评估影响 |
| `link_spec_to_code` | 需求-代码链接 | 追踪需求实现 |

### Hooks 自动触发

| Hook | 触发时机 | 行为 |
|------|----------|------|
| `UserPromptSubmit` | 用户提问时 | 代码相关问题自动调用 `lookup_code_context` |
| `PreToolUse` | 写入代码前 | 要求先做影响分析 |

## 前置条件

1. **Neo4j 数据库**：已导入代码本体数据
2. **ontology 项目**：包含 `graph_reasoning` 模块
3. **Python 环境**：安装了 `mcp` 和 `neo4j` 包

## 安装

### 方法 1：使用安装脚本（推荐）

```bash
# 在项目根目录运行
./plugins/ontology-devos/install.sh
```

### 方法 2：手动配置

1. 创建 `.ontology_config.json`：

```json
{
  "ontology_path": "/path/to/ontology",
  "neo4j_uri": "bolt://localhost:7687",
  "neo4j_user": "neo4j",
  "neo4j_password": "password",
  "neo4j_database": "ontologydevos"
}
```

2. 更新 `.mcp.json`：

```json
{
  "mcpServers": {
    "ontology-devos": {
      "type": "stdio",
      "command": "/path/to/ontology/venv/bin/python",
      "args": ["-u", "/path/to/plugins/ontology-devos/servers/ontology_mcp/server.py"],
      "env": {
        "ONTOLOGY_PROJECT_ROOT": "/path/to/project",
        "ONTOLOGY_PATH": "/path/to/ontology",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

3. 重启 Claude Code

## 使用方法

### 自动触发

插件会在以下场景自动触发：

1. **代码问题自动检索** (UserPromptSubmit)
   - 当你问关于代码的问题时，Claude 会自动调用 `lookup_code_context` 获取相关上下文

2. **写入前影响分析** (PreToolUse)
   - 当 Claude 要修改代码文件时，会先检查是否做过影响分析
   - 如果没有，会要求先调用 `check_modification_impact`

### 手动调用

你也可以直接让 Claude 调用这些工具：

```
"查询 PythonParser 相关的代码上下文"
→ 调用 lookup_code_context

"分析修改 code_processor/cli.py 的影响"
→ 调用 check_modification_impact

"将需求 '添加增量构建支持' 链接到相关代码"
→ 调用 link_spec_to_code
```

## 配置说明

### .ontology_config.json

| 字段 | 说明 | 必填 |
|------|------|------|
| `ontology_path` | ontology 项目路径 | 是 |
| `neo4j_uri` | Neo4j 连接 URI | 是 |
| `neo4j_user` | Neo4j 用户名 | 是 |
| `neo4j_password` | Neo4j 密码 | 是 |
| `neo4j_database` | Neo4j 数据库名 | 是 |
| `ttl_dir` | TTL 文件目录 | 否 |
| `domain` | 领域标识 | 否 |

### 环境变量（可选）

| 变量 | 说明 |
|------|------|
| `ONTOLOGY_CONFIG_PATH` | 配置文件路径 |
| `ONTOLOGY_PROJECT_ROOT` | 项目根目录 |
| `ONTOLOGY_PATH` | ontology 项目路径 |
| `EMBEDDING_API_BASE` | 嵌入 API 地址 |
| `EMBEDDING_API_KEY` | 嵌入 API 密钥 |
| `EMBEDDING_MODEL` | 嵌入模型名称 |

## 故障排除

### MCP 服务器未加载

1. 检查 `.mcp.json` 配置是否正确
2. 重启 Claude Code
3. 运行 `claude mcp list` 查看已加载的服务器

### Neo4j 连接失败

1. 检查 Neo4j 服务是否运行
2. 验证连接参数是否正确
3. 检查网络连接

### 工具调用失败

1. 检查 `ontology_path` 是否正确
2. 确保 `graph_reasoning` 模块可导入
3. 查看 MCP 服务器日志

## 目录结构

```
plugins/ontology-devos/
├── .claude-plugin/
│   └── plugin.json          # 插件元数据
├── .mcp.json                 # MCP 服务器配置模板
├── hooks/
│   └── hooks.json            # Hook 配置
├── servers/
│   └── ontology_mcp/
│       ├── pyproject.toml    # Python 项目配置
│       └── server.py         # MCP 服务器实现
├── install.sh                # 安装脚本
└── README.md                 # 本文档
```
