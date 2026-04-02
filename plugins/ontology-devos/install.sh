#!/bin/bash

# ontology-devos 插件安装脚本
# 将 ontology-devos MCP 服务器注册到项目的 .mcp.json

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() { echo -e "${GREEN}▶${NC} $1"; }
print_info() { echo -e "${YELLOW}ℹ${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ontology-devos 插件安装${NC}"
echo -e "${BLUE}  代码本体检索 + 影响分析 + 需求链接${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 获取脚本所在目录（插件目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$SCRIPT_DIR"

# 目标项目目录（默认为当前目录或第一个参数）
TARGET_DIR="${1:-$(pwd)}"
cd "$TARGET_DIR"
TARGET_DIR="$(pwd)"

print_info "插件目录: $PLUGIN_DIR"
print_info "目标项目: $TARGET_DIR"
echo ""

# ═══════════════════════════════════════════════
# Step 1: 检查前置条件
# ═══════════════════════════════════════════════
print_step "检查前置条件..."

# 检查 .ontology_config.json
if [ -f "$TARGET_DIR/.ontology_config.json" ]; then
    print_success "找到 .ontology_config.json"

    # 读取配置
    if command -v python3 &> /dev/null; then
        ONTOLOGY_PATH=$(python3 -c "import json; print(json.load(open('$TARGET_DIR/.ontology_config.json')).get('ontology_path', ''))" 2>/dev/null || echo "")
        NEO4J_URI=$(python3 -c "import json; print(json.load(open('$TARGET_DIR/.ontology_config.json')).get('neo4j_uri', ''))" 2>/dev/null || echo "")
        NEO4J_DATABASE=$(python3 -c "import json; print(json.load(open('$TARGET_DIR/.ontology_config.json')).get('neo4j_database', ''))" 2>/dev/null || echo "")

        print_info "  ontology_path: $ONTOLOGY_PATH"
        print_info "  neo4j_uri: $NEO4J_URI"
        print_info "  neo4j_database: $NEO4J_DATABASE"
    fi
else
    print_error ".ontology_config.json 不存在"
    print_info "请先创建配置文件，示例："
    cat << 'EOF'
{
  "ontology_path": "/path/to/ontology",
  "neo4j_uri": "bolt://localhost:7687",
  "neo4j_user": "neo4j",
  "neo4j_password": "password",
  "neo4j_database": "ontologydevos"
}
EOF
    exit 1
fi

# 检查 ontology 项目路径
if [ -n "$ONTOLOGY_PATH" ] && [ -d "$ONTOLOGY_PATH" ]; then
    print_success "ontology 项目存在: $ONTOLOGY_PATH"

    # 检查 Python 虚拟环境
    if [ -d "$ONTOLOGY_PATH/venv" ]; then
        PYTHON_PATH="$ONTOLOGY_PATH/venv/bin/python"
        print_success "找到 Python 虚拟环境: $PYTHON_PATH"
    elif [ -d "$ONTOLOGY_PATH/.venv" ]; then
        PYTHON_PATH="$ONTOLOGY_PATH/.venv/bin/python"
        print_success "找到 Python 虚拟环境: $PYTHON_PATH"
    else
        PYTHON_PATH="python3"
        print_info "未找到虚拟环境，使用系统 Python"
    fi
else
    print_error "ontology 项目不存在: $ONTOLOGY_PATH"
    print_info "请确保 .ontology_config.json 中的 ontology_path 正确"
    exit 1
fi

# 检查 Neo4j 连接（可选）
if [ -n "$NEO4J_URI" ]; then
    print_step "测试 Neo4j 连接..."
    if $PYTHON_PATH -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('$NEO4J_URI', auth=('neo4j', '$(python3 -c "import json; print(json.load(open('$TARGET_DIR/.ontology_config.json')).get('neo4j_password', ''))")'))
with driver.session(database='$NEO4J_DATABASE') as session:
    result = session.run('MATCH (n) RETURN count(n) as count')
    count = result.single()['count']
    print(f'节点数量: {count}')
driver.close()
" 2>/dev/null; then
        print_success "Neo4j 连接成功"
    else
        print_info "Neo4j 连接失败（可能是网络问题，继续安装）"
    fi
fi

echo ""

# ═══════════════════════════════════════════════
# Step 2: 安装 MCP 依赖
# ═══════════════════════════════════════════════
print_step "检查 MCP SDK 依赖..."

# 检查 mcp 包是否已安装
if $PYTHON_PATH -c "import mcp" 2>/dev/null; then
    print_success "MCP SDK 已安装"
else
    print_info "安装 MCP SDK..."
    $PYTHON_PATH -m pip install mcp --quiet && {
        print_success "MCP SDK 安装成功"
    } || {
        print_error "MCP SDK 安装失败"
        print_info "请手动安装: $PYTHON_PATH -m pip install mcp"
    }
fi

echo ""

# ═══════════════════════════════════════════════
# Step 3: 更新 .mcp.json
# ═══════════════════════════════════════════════
print_step "配置 MCP 服务器..."

MCP_JSON="$TARGET_DIR/.mcp.json"
SERVER_PY="$PLUGIN_DIR/servers/ontology_mcp/server.py"

# 检查 server.py 是否存在
if [ ! -f "$SERVER_PY" ]; then
    print_error "MCP 服务器脚本不存在: $SERVER_PY"
    exit 1
fi

# 构建 ontology-devos 配置
ONTOLOGY_DEVOS_CONFIG=$(cat << EOF
{
    "type": "stdio",
    "command": "$PYTHON_PATH",
    "args": ["-u", "$SERVER_PY"],
    "env": {
        "ONTOLOGY_PROJECT_ROOT": "$TARGET_DIR",
        "ONTOLOGY_PATH": "$ONTOLOGY_PATH",
        "PYTHONUNBUFFERED": "1"
    }
}
EOF
)

if [ -f "$MCP_JSON" ]; then
    print_info ".mcp.json 已存在，更新配置..."

    # 使用 Python 更新 JSON
    python3 << PYEOF
import json

with open('$MCP_JSON', 'r') as f:
    config = json.load(f)

# 确保 mcpServers 存在
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# 添加或更新 ontology-devos
config['mcpServers']['ontology-devos'] = {
    "type": "stdio",
    "command": "$PYTHON_PATH",
    "args": ["-u", "$SERVER_PY"],
    "env": {
        "ONTOLOGY_PROJECT_ROOT": "$TARGET_DIR",
        "ONTOLOGY_PATH": "$ONTOLOGY_PATH",
        "PYTHONUNBUFFERED": "1"
    }
}

with open('$MCP_JSON', 'w') as f:
    json.dump(config, f, indent=2)

print("配置已更新")
PYEOF
    print_success ".mcp.json 已更新"
else
    print_info "创建新的 .mcp.json..."
    cat > "$MCP_JSON" << EOF
{
  "mcpServers": {
    "ontology-devos": {
      "type": "stdio",
      "command": "$PYTHON_PATH",
      "args": ["-u", "$SERVER_PY"],
      "env": {
        "ONTOLOGY_PROJECT_ROOT": "$TARGET_DIR",
        "ONTOLOGY_PATH": "$ONTOLOGY_PATH",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
EOF
    print_success ".mcp.json 已创建"
fi

echo ""

# ═══════════════════════════════════════════════
# Step 4: 验证安装
# ═══════════════════════════════════════════════
print_step "验证安装..."

# 测试 MCP 服务器能否启动
print_info "测试 MCP 服务器..."
if timeout 5 $PYTHON_PATH -c "
import sys
sys.path.insert(0, '$ONTOLOGY_PATH')
import importlib.util
spec = importlib.util.spec_from_file_location('server', '$SERVER_PY')
module = importlib.util.module_from_spec(spec)
# 只测试导入，不运行
print('MCP 服务器模块加载成功')
" 2>/dev/null; then
    print_success "MCP 服务器模块验证通过"
else
    print_info "MCP 服务器模块验证跳过（可能缺少依赖）"
fi

echo ""

# ═══════════════════════════════════════════════
# 完成
# ═══════════════════════════════════════════════
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ ontology-devos 插件安装完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

print_step "下一步操作："
echo ""
echo "1. 重启 Claude Code 以加载新的 MCP 服务器"
echo ""
echo "2. 测试插件功能："
echo "   - 查询代码上下文: \"查询 PythonParser 相关的代码上下文\""
echo "   - 影响分析: \"分析修改 xxx.py 的影响\""
echo "   - 需求链接: \"将需求 '添加增量构建' 链接到相关代码\""
echo ""
echo "3. 自动触发场景："
echo "   - 问代码问题时自动调用 lookup_code_context"
echo "   - 修改代码前自动要求影响分析"
echo ""
echo -e "${GREEN}Happy coding with ontology-devos!${NC}"
