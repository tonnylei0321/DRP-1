#!/bin/sh
set -e

GRAPHDB_URL="${GRAPHDB_URL:-http://graphdb:7200}"
REPO_ID="drp"
# 脚本所在目录（容器内为 /init，宿主机测试时为实际路径）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[init] 等待 GraphDB 就绪..."
until curl -sf "${GRAPHDB_URL}/rest/repositories" > /dev/null 2>&1; do
  echo "[init] GraphDB 尚未就绪，等待 5 秒..."
  sleep 5
done
echo "[init] GraphDB 已就绪"

# 检查仓库是否已存在
if curl -sf "${GRAPHDB_URL}/rest/repositories/${REPO_ID}" > /dev/null 2>&1; then
  echo "[init] 仓库 '${REPO_ID}' 已存在，跳过创建"
else
  echo "[init] 创建仓库 '${REPO_ID}'..."
  curl -sf -X POST "${GRAPHDB_URL}/rest/repositories" \
    -H "Content-Type: multipart/form-data" \
    -F "config=@${SCRIPT_DIR}/repo-config.ttl;type=text/turtle" \
    || { echo "[init] 仓库创建失败"; exit 1; }
  echo "[init] 仓库创建成功"
fi

# 加载 FIBO 核心模块（7个最小裁剪集，见 design.md 决策12）
# 格式：<模块路径>|<本地文件名>
FIBO_BASE="https://raw.githubusercontent.com/edmcouncil/fibo/master"
FIBO_MODULES="
FBC/FunctionalEntities/FinancialServicesEntities.rdf|FBC-FinancialServicesEntities.rdf
BE/LegalEntities/LegalPersons.rdf|BE-LegalPersons.rdf
BE/LegalEntities/CorporateBodies.rdf|BE-CorporateBodies.rdf
FND/Accounting/CurrencyAmount.rdf|FND-CurrencyAmount.rdf
FND/Relations/Relations.rdf|FND-Relations.rdf
FND/DatesAndTimes/FinancialDates.rdf|FND-FinancialDates.rdf
FND/Arrangements/ClassificationSchemes.rdf|FND-ClassificationSchemes.rdf
"

for ENTRY in $FIBO_MODULES; do
  MODULE_PATH="${ENTRY%%|*}"
  FILE_NAME="${ENTRY##*|}"
  LOCAL_PATH="/fibo/${FILE_NAME}"

  if [ -z "$MODULE_PATH" ]; then
    continue
  fi

  if [ ! -f "$LOCAL_PATH" ]; then
    echo "[init] 下载 FIBO 模块: ${FILE_NAME}..."
    curl -sL "${FIBO_BASE}/${MODULE_PATH}" -o "$LOCAL_PATH" 2>&1 || true
    if [ ! -s "$LOCAL_PATH" ]; then
      echo "[init]   下载失败（跳过）: ${FILE_NAME}"
      rm -f "$LOCAL_PATH"
      continue
    fi
    echo "[init]   下载成功: ${FILE_NAME}"
  else
    echo "[init] 使用本地缓存: ${FILE_NAME}"
  fi

  echo "[init] 加载: ${FILE_NAME}..."
  HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" -X POST \
    "${GRAPHDB_URL}/repositories/${REPO_ID}/statements" \
    -H "Content-Type: application/rdf+xml" \
    --data-binary "@${LOCAL_PATH}" 2>/dev/null || echo "000")

  if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "[init]   加载成功: ${FILE_NAME} (HTTP ${HTTP_CODE})"
  else
    echo "[init]   加载失败（跳过）: ${FILE_NAME} (HTTP ${HTTP_CODE})"
  fi
done

# 最终三元组统计
TRIPLE_COUNT=$(curl -sf -X POST \
  "${GRAPHDB_URL}/repositories/${REPO_ID}" \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  -d 'SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }' \
  2>/dev/null | grep -o '"[0-9]*"' | head -1 | tr -d '"')

echo "[init] GraphDB 初始化完成，当前三元组数量: ${TRIPLE_COUNT:-未知}"
