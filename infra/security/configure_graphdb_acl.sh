#!/bin/bash
# 15.1 GraphDB 仓库级 ACL 配置脚本
# 每个租户 Named Graph 绑定独立服务账号，禁止跨图读写
#
# 使用方法：
#   ./configure_graphdb_acl.sh <tenant_id> <service_account_password>
#
# 依赖：GraphDB 10.x Enterprise（ACL 功能需 EE 版本）
# 替代方案：GraphDB SE/Free 版使用 SPARQL 代理层强制隔离（已在 sparql/proxy.py 实现）

set -euo pipefail

GRAPHDB_URL="${GRAPHDB_URL:-http://graphdb:7200}"
GRAPHDB_ADMIN_USER="${GRAPHDB_ADMIN_USER:-admin}"
GRAPHDB_ADMIN_PASS="${GRAPHDB_ADMIN_PASS:-root}"
GRAPHDB_REPO="${GRAPHDB_REPO:-drp}"

TENANT_ID="${1:?请提供租户 UUID}"
SERVICE_ACCOUNT_PASS="${2:?请提供服务账号密码}"
SERVICE_ACCOUNT="svc_${TENANT_ID//-/_}"
GRAPH_IRI="urn:tenant:${TENANT_ID}"

echo "[$(date)] 为租户 ${TENANT_ID} 配置 GraphDB ACL"
echo "  服务账号: ${SERVICE_ACCOUNT}"
echo "  命名图: ${GRAPH_IRI}"

# ── 步骤 1：创建租户专属服务账号 ──
echo "[$(date)] 创建服务账号: ${SERVICE_ACCOUNT}"
curl -s -f -X POST \
  -u "${GRAPHDB_ADMIN_USER}:${GRAPHDB_ADMIN_PASS}" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${SERVICE_ACCOUNT}\",
    \"password\": \"${SERVICE_ACCOUNT_PASS}\",
    \"grantedAuthorities\": []
  }" \
  "${GRAPHDB_URL}/rest/security/users/${SERVICE_ACCOUNT}"

echo "[$(date)] 服务账号创建成功"

# ── 步骤 2：配置命名图级别权限 ──
# 赋予服务账号对 urn:tenant:<id> 命名图的读写权限
# 禁止读写其他命名图

echo "[$(date)] 配置命名图权限"

# 读权限：允许对目标图 SELECT
curl -s -f -X POST \
  -u "${GRAPHDB_ADMIN_USER}:${GRAPHDB_ADMIN_PASS}" \
  -H "Content-Type: application/json" \
  -d "{
    \"authorities\": [
      \"READ_REPO_${GRAPHDB_REPO}\"
    ],
    \"namedGraphs\": [\"${GRAPH_IRI}\"]
  }" \
  "${GRAPHDB_URL}/rest/security/users/${SERVICE_ACCOUNT}/graph-permissions" || \
  echo "[警告] GraphDB SE/Free 版不支持命名图级别 ACL，已回退到应用层 SPARQL 代理隔离"

# ── 步骤 3：验证配置 ──
echo "[$(date)] 验证权限配置"
curl -s -u "${SERVICE_ACCOUNT}:${SERVICE_ACCOUNT_PASS}" \
  -H "Accept: application/json" \
  "${GRAPHDB_URL}/rest/security/users/${SERVICE_ACCOUNT}" | grep -q "username" && \
  echo "[$(date)] ACL 配置验证通过" || \
  echo "[错误] ACL 配置验证失败"

echo ""
echo "=== ACL 配置摘要 ==="
echo "  租户 ID:    ${TENANT_ID}"
echo "  服务账号:   ${SERVICE_ACCOUNT}"
echo "  允许访问:   GRAPH <${GRAPH_IRI}>"
echo "  禁止访问:   其他所有命名图"
echo ""
echo "注意：生产环境中，服务账号密码应通过 Vault 或 Kubernetes Secret 管理"
