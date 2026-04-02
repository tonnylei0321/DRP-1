"""CTIO 本体集成测试

测试策略：
- 通过 GraphDB REST API 执行 SPARQL 查询
- 验证本体类和属性可访问
- 验证106项指标全部加载
- 验证四大红线指标存在
- 跳过条件：GraphDB 未运行（标记 @pytest.mark.integration）

运行方式：
    pytest backend/tests/test_ctio_ontology.py -v -m integration
"""

import os
import pytest
import httpx

GRAPHDB_URL = os.getenv("GRAPHDB_URL", "http://localhost:7200")
REPO = os.getenv("GRAPHDB_REPOSITORY", "drp")
SPARQL_ENDPOINT = f"{GRAPHDB_URL}/repositories/{REPO}"

CTIO_PREFIX = "PREFIX ctio: <https://drp.example.com/ontology/ctio/>"


def sparql_select(query: str) -> list[dict]:
    """执行 SPARQL SELECT 查询，返回绑定列表。"""
    resp = httpx.get(
        SPARQL_ENDPOINT,
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["results"]["bindings"]


def graphdb_available() -> bool:
    """检查 GraphDB 是否可用。"""
    try:
        r = httpx.get(f"{GRAPHDB_URL}/rest/repositories", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(autouse=False)
def require_graphdb():
    """在运行时检查 GraphDB 是否可用，不可用则跳过测试。"""
    if not graphdb_available():
        pytest.skip("GraphDB 未运行，跳过集成测试")


@pytest.mark.integration
def test_ctio_core_classes_exist(require_graphdb):
    """验证8个核心 CTIO 类已加载到图谱。

    注意：此测试检查各类 IRI 是否被声明为 owl:Class，
    不验证 FIBO 超类推理（FIBO 在此环境中可能未加载）。
    """
    query = f"""
    {CTIO_PREFIX}
    SELECT (COUNT(DISTINCT ?class) AS ?count)
    WHERE {{
        VALUES ?class {{
            ctio:DirectLinkedAccount
            ctio:InternalDepositAccount
            ctio:ControlToken
            ctio:CashPool
            ctio:RepaymentMilestone
            ctio:RiskEvent
            ctio:RegulatoryIndicator
            ctio:EndorsementChain
        }}
        ?class a <http://www.w3.org/2002/07/owl#Class> .
    }}
    """
    results = sparql_select(query)
    count = int(results[0]["count"]["value"])
    assert count == 8, f"期望8个核心类，实际找到 {count} 个"


@pytest.mark.integration
def test_indicator_total_count(require_graphdb):
    """验证106项监管指标全部加载。"""
    query = f"""
    {CTIO_PREFIX}
    SELECT (COUNT(?ind) AS ?count)
    WHERE {{
        ?ind a ctio:RegulatoryIndicator .
    }}
    """
    results = sparql_select(query)
    count = int(results[0]["count"]["value"])
    assert count == 106, f"期望106项指标，实际找到 {count} 项"


@pytest.mark.integration
def test_four_redline_indicators_exist(require_graphdb):
    """四个红线指标必须存在于图数据库中。"""
    query = """
        PREFIX ctio: <https://drp.example.com/ontology/ctio#>
        SELECT (COUNT(DISTINCT ?id) AS ?count)
        WHERE {
            ?ind a ctio:RegulatoryIndicator ;
                 ctio:indicatorId ?id .
            VALUES ?id { "IND-BA-002" "IND-CC-001" "IND-CC-002" "IND-ST-001" }
        }
    """
    results = sparql_select(query)
    count = int(results[0]["count"]["value"])
    assert count == 4, f"预期4个红线指标，实际找到 {count} 个"


@pytest.mark.integration
def test_indicators_cover_all_seven_domains(require_graphdb):
    """验证7个业务域全部有指标。"""
    expected_domains = {
        "银行账户监管域", "资金集中监管域", "结算监管域",
        "票据监管域", "债务融资监管域", "决策风险域", "国资委考核域"
    }
    query = f"""
    {CTIO_PREFIX}
    SELECT DISTINCT ?domain
    WHERE {{
        ?ind a ctio:RegulatoryIndicator ;
             ctio:businessDomain ?domain .
    }}
    """
    results = sparql_select(query)
    found_domains = {r["domain"]["value"] for r in results}
    missing = expected_domains - found_domains
    assert not missing, f"以下业务域缺少指标: {missing}"


@pytest.mark.integration
def test_shacl_graph_loaded(require_graphdb):
    """验证 SHACL 图已加载（存在 SHACL NodeShape）。"""
    query = """
    PREFIX sh: <http://www.w3.org/ns/shacl#>
    SELECT (COUNT(?shape) AS ?count)
    WHERE {
        ?shape a sh:NodeShape .
    }
    """
    results = sparql_select(query)
    count = int(results[0]["count"]["value"])
    assert count >= 4, f"期望至少4个 SHACL NodeShape（四大红线），实际 {count} 个"


@pytest.mark.integration
def test_named_graphs_exist(require_graphdb):
    """验证 CTIO Named Graph 已创建。"""
    query = """
    SELECT DISTINCT ?graph
    WHERE {
        GRAPH ?graph { ?s ?p ?o }
        FILTER(CONTAINS(STR(?graph), "drp.example.com"))
    }
    """
    results = sparql_select(query)
    graph_iris = {r["graph"]["value"] for r in results}
    expected_graphs = {
        "https://drp.example.com/graph/ctio-core",
        "https://drp.example.com/graph/ctio-indicators",
        "https://drp.example.com/graph/ctio-shacl",
    }
    missing = expected_graphs - graph_iris
    assert not missing, f"以下 Named Graph 未找到: {missing}"
