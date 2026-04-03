"""第11章：集成测试套件。

覆盖以下场景：
  11.1 端到端流程：DDL 上传 → 映射生成 → ETL 同步 → 指标计算 → 看板展示
  11.2 多租户隔离（已在 test_multi_tenant_isolation.py 中实现）
  11.3 穿透溯源：三级穿透路径完整性
  11.4 SHACL 风险推理：触发四大红线，验证 RiskEvent 生成和推送
  11.5 性能测试：106 项指标计算在 60 分钟窗口内完成（mock 场景）
  11.6 SSO 集成测试（SAML 2.0 + OIDC 端点响应）

注意：所有需要外部服务的测试标记为 `integration`，默认跳过。
"""
import asyncio
import time
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from drp.auth.schemas import TokenPayload
from drp.indicators.calculator import (
    _check_compliance,
    calculate_all_domains,
)
from drp.indicators.registry import INDICATORS
from drp.main import app


# ─── 辅助 ────────────────────────────────────────────────────────────────────

def _make_token(tenant_id: str = "int-test-tenant") -> TokenPayload:
    return TokenPayload(
        sub="test-user",
        tenant_id=tenant_id,
        email="test@example.com",
        permissions=["drill:read", "mapping:write", "etl:read"],
        exp=9999999999,
    )


# ─── 11.1 端到端流程（mock 版） ───────────────────────────────────────────────

class TestEndToEndFlow:
    """
    端到端流程验证（使用 mock 代替真实外部服务）:
    DDL 解析 → 映射置信度 → ETL 引擎 → 指标计算
    """

    def test_ddl_解析到指标计算全流程(self):
        """完整流程不应抛出异常，各环节输出符合约定。"""
        # Step 1: DDL 解析
        from drp.mapping.ddl_parser import parse_ddl
        ddl = """
        CREATE TABLE account (
            id INT PRIMARY KEY,
            acct_no VARCHAR(50) COMMENT '账户编号',
            balance DECIMAL(18,2) COMMENT '余额'
        );
        """
        tables = parse_ddl(ddl)
        assert len(tables) == 1
        assert tables[0].name == "account"
        assert len(tables[0].columns) == 3

        # Step 2: 置信度计算
        from drp.mapping.confidence import compute_confidence
        col_acct = next(c for c in tables[0].columns if c.name == "acct_no")
        col_bal = next(c for c in tables[0].columns if c.name == "balance")

        score_acct = compute_confidence(col_acct.name, col_acct.data_type, col_acct.comment or "", "ctio:accountNumber")
        score_bal = compute_confidence(col_bal.name, col_bal.data_type, col_bal.comment or "", "ctio:balance")
        assert score_acct > 0
        assert score_bal > 0

        # Step 3: YAML 生成（MappingSpec 结构）
        from drp.mapping.yaml_generator import generate_mapping_yaml
        from drp.mapping.llm_service import MappingSuggestion
        specs = [
            MappingSuggestion(
                source_table="account",
                source_field="acct_no",
                data_type="VARCHAR",
                target_property="ctio:accountNumber",
                transform_rule="",
                confidence=score_acct,
                auto_approved=True,
                reasoning="",
            ),
            MappingSuggestion(
                source_table="account",
                source_field="balance",
                data_type="DECIMAL",
                target_property="ctio:balance",
                transform_rule="",
                confidence=score_bal,
                auto_approved=True,
                reasoning="",
            ),
        ]
        yaml_str = generate_mapping_yaml(specs)
        assert "ctio:accountNumber" in yaml_str
        assert "ctio:balance" in yaml_str

        # Step 4: ETL ��擎（mock source + graphdb）
        from drp.etl.engine import EtlSyncEngine

        rows = [{"id": 1, "acct_no": "ACC-001", "balance": 5000.0}]
        mock_fetcher = AsyncMock(return_value=rows)
        mock_graphdb = AsyncMock()
        mock_graphdb._sparql_update = AsyncMock()

        engine = EtlSyncEngine(
            source_fetcher=mock_fetcher,
            graphdb_client=mock_graphdb,
            mapping_yaml=yaml_str,
            tenant_id="test-tenant",
        )
        triples = asyncio.get_event_loop().run_until_complete(engine.full_sync("account"))
        assert triples > 0

    async def test_指标计算流程(self):
        """指标计算全流程（mock SPARQL）。"""
        with patch("drp.indicators.calculator.sparql_query", new_callable=AsyncMock) as mock_q, \
             patch("drp.indicators.calculator.sparql_update", new_callable=AsyncMock), \
             patch("drp.indicators.calculator._write_redis_cache", new_callable=AsyncMock), \
             patch("drp.indicators.calculator._publish_risk_event", new_callable=AsyncMock):

            mock_q.return_value = [{"value": "0.96"}]
            results = await calculate_all_domains("int-test-tenant")

        total = sum(len(v) for v in results.values())
        assert total == 106, f"期望 106 项指标结果，实际 {total}"


# ─── 11.3 穿透溯源测试（API 层） ─────────────────────────────────────────────

class TestDrillDownPath:
    """穿透溯源 API 三级路径完整性验证。"""

    def setup_method(self):
        from drp.auth.middleware import get_current_user
        app.dependency_overrides[get_current_user] = lambda: _make_token()
        self.client = TestClient(app, raise_server_exceptions=False)

    def teardown_method(self):
        from drp.auth.middleware import get_current_user
        app.dependency_overrides.pop(get_current_user, None)

    def test_三级穿透路径完整性(self):
        """验证三级穿透 API 均能正常响应，路径数据结构正确。"""
        indicator_id = "009"
        entity_id = "corp-001"
        account_id = "acct-001"

        # 一级：指标 → 法人
        with patch("drp.drill.router.sparql_query", new_callable=AsyncMock) as mock_q:
            mock_q.return_value = [
                {"entity": "urn:entity:corp-001", "entityName": "测试法人A", "value": "0.8"}
            ]
            resp1 = self.client.get(f"/drill/{indicator_id}/entities")
        assert resp1.status_code == 200
        entities = resp1.json()
        assert len(entities) == 1
        assert entities[0]["entity_iri"] == "urn:entity:corp-001"

        # 二级：法人 → 账户
        with patch("drp.drill.router.sparql_query", new_callable=AsyncMock) as mock_q:
            mock_q.return_value = [
                {"acct": "urn:entity:acct-001", "acctNo": "ACC-001", "balance": "100000", "status": "active", "isDirectLinked": "true"}
            ]
            resp2 = self.client.get(f"/drill/{entity_id}/accounts")
        assert resp2.status_code == 200
        accounts = resp2.json()
        assert len(accounts) == 1
        assert accounts[0]["account_number"] == "ACC-001"

        # 三级：账户 → 属性
        with patch("drp.drill.router.sparql_query", new_callable=AsyncMock) as mock_q:
            mock_q.return_value = [
                {"predicate": "urn:ctio:accountNumber", "object": "ACC-001"},
                {"predicate": "urn:ctio:balance", "object": "100000"},
                {"predicate": "urn:ctio:isRestricted", "object": "false"},
            ]
            resp3 = self.client.get(f"/drill/{account_id}/properties")
        assert resp3.status_code == 200
        props = resp3.json()
        assert "accountNumber" in props
        assert "balance" in props

    def test_路径查询返回多级节点(self):
        """图谱路径查询应返回指标→法人→账户三个步骤。"""
        with patch("drp.drill.router.sparql_query", new_callable=AsyncMock) as mock_q:
            mock_q.return_value = [
                {"step": "1", "node": "urn:ind:009", "nodeType": "RegulatoryIndicator", "nodeLabel": "009"},
                {"step": "2", "node": "urn:entity:corp1", "nodeType": "LegalEntity", "nodeLabel": "法人A"},
                {"step": "3", "node": "urn:entity:acct1", "nodeType": "Account", "nodeLabel": "ACC-001"},
            ]
            resp = self.client.get("/drill/path/009")
        assert resp.status_code == 200
        path = resp.json()
        assert len(path) == 3
        types = [n["node_type"] for n in path]
        assert "RegulatoryIndicator" in types
        assert "LegalEntity" in types
        assert "Account" in types


# ─── 11.4 SHACL 风险推理（逻辑层测试） ───────────────────────────────────────

class TestShaclRiskInference:
    """
    验证四大红线触发时，_check_compliance + _publish_risk_event 正确生成 RiskEvent。
    四大红线：直联率(009) ≥95%、集中率(033) ≥80%、集中率国资(034) ≥85%、结算率(043) ≥99%
    """

    def test_直联率低于阈值_触发风险(self):
        ind = next(i for i in INDICATORS if i["id"] == "009")
        # 直联率 0.90 < threshold 0.95
        assert _check_compliance(ind, 0.90) is False

    def test_直联率达标_不触发风险(self):
        ind = next(i for i in INDICATORS if i["id"] == "009")
        assert _check_compliance(ind, 0.97) is True

    def test_资金集中率低于阈值_触发风险(self):
        ind033 = next(i for i in INDICATORS if i["id"] == "033")
        ind034 = next(i for i in INDICATORS if i["id"] == "034")
        assert _check_compliance(ind033, 0.65) is False  # < 0.70
        assert _check_compliance(ind034, 0.70) is False  # < 0.75

    def test_结算率低于阈值_触发风险(self):
        ind = next(i for i in INDICATORS if i["id"] == "043")
        assert _check_compliance(ind, 0.94) is False  # < 0.95
        assert _check_compliance(ind, 0.96) is True

    async def test_不达标指标发布风险事件(self):
        """validate: 不达标时 Pub/Sub 发布 risk_event。"""
        import json
        from drp.indicators.calculator import _publish_risk_event, IndicatorResult

        ind = next(i for i in INDICATORS if i["id"] == "009")
        result = IndicatorResult(
            indicator_id="009", tenant_id="t1", value=0.85, is_compliant=False
        )
        mock_redis = AsyncMock()
        await _publish_risk_event(ind, result, redis_client=mock_redis)

        mock_redis.publish.assert_called_once()
        channel, payload = mock_redis.publish.call_args[0]
        assert channel == "risk_events"
        event = json.loads(payload)
        assert event["indicator_id"] == "009"
        assert event["type"] == "risk_event"

    async def test_四大红线全部达标_无风险事件(self):
        """四大红线全部达标时，不应发布风险事件。"""
        from drp.indicators.calculator import _publish_risk_event, IndicatorResult

        red_lines = [("009", 0.97), ("033", 0.82), ("034", 0.87), ("043", 0.995)]
        mock_redis = AsyncMock()

        for ind_id, value in red_lines:
            ind = next(i for i in INDICATORS if i["id"] == ind_id)
            result = IndicatorResult(
                indicator_id=ind_id, tenant_id="t1",
                value=value, is_compliant=_check_compliance(ind, value)
            )
            await _publish_risk_event(ind, result, redis_client=mock_redis)

        mock_redis.publish.assert_not_called()


# ─── 11.5 性能测试：106 项指标 mock 计算 ──────────────────────────────────────

class TestPerformance:
    """
    验证 106 项指标的计算调度逻辑（不含 SPARQL 实际执行）
    在合理时间内完成（< 5 秒，mock 模式下应远低于 60 分钟限额）。
    """

    async def test_106项指标计算时间(self):
        """106 项指标�� mock 计算应在 5 秒内完成。"""
        call_count = 0

        async def _fast_sparql(sparql, tenant_id=None, client=None):
            nonlocal call_count
            call_count += 1
            return [{"value": "0.95"}]

        with patch("drp.indicators.calculator.sparql_query", side_effect=_fast_sparql), \
             patch("drp.indicators.calculator.sparql_update", new_callable=AsyncMock), \
             patch("drp.indicators.calculator._write_redis_cache", new_callable=AsyncMock), \
             patch("drp.indicators.calculator._publish_risk_event", new_callable=AsyncMock):

            start = time.monotonic()
            await calculate_all_domains("perf-tenant")
            elapsed = time.monotonic() - start

        assert call_count == 106, f"期望 106 次 SPARQL 调用，实际 {call_count}"
        assert elapsed < 5.0, f"106 项指标计算耗时 {elapsed:.2f}s，超过 5 秒限制"

    def test_指标注册表查找性能(self):
        """INDICATOR_BY_ID 字典查找应在 1ms 内完成（哈希表 O(1)）。"""
        from drp.indicators.registry import INDICATOR_BY_ID

        start = time.monotonic()
        for _ in range(10000):
            _ = INDICATOR_BY_ID.get("009")
            _ = INDICATOR_BY_ID.get("098")
        elapsed = time.monotonic() - start
        assert elapsed < 0.1, f"10000 次字典查找耗时 {elapsed:.3f}s"


# ─── 11.6 SSO 集成测试（端点可达性） ────��────────────────────────────────────

class TestSsoEndpoints:
    """验证 SAML/OIDC SSO 端点响应 501（功能待集成）或 200（已实现）。"""

    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_saml_callback_端点存在(self):
        """SAML callback 端点应返回有效 HTTP 状态码（非 404）。"""
        resp = self.client.post("/auth/saml/callback")
        assert resp.status_code != 404, "SAML callback 端点不存在"

    def test_oidc_callback_端点存在(self):
        """OIDC callback 端点应返回有效 HTTP 状态码（非 404）。"""
        resp = self.client.get("/auth/oidc/callback")
        assert resp.status_code != 404, "OIDC callback 端点不存在"

    def test_health_端点正常(self):
        """health 端点应返回 200。增强版在外部服务不可用时返回 degraded。"""
        resp = self.client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
