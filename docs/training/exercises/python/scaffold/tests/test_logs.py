"""
日志服务测试
"""
import uuid
from unittest.mock import patch

import httpx
import pytest

from app.config import settings


def test_post_logs_success(client, sample_logs):
    """正常接收日志 → 200，返回接收数量"""
    response = client.post("/api/logs", json=sample_logs)
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] == 3
    assert body["alerts_triggered"] == 1  # 只有一条 ERROR
    assert body["alerts_failed"] == 0


def test_post_logs_empty(client):
    """空数组 → 200，不报错"""
    response = client.post("/api/logs", json={"logs": []})
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] == 0
    assert body["alerts_failed"] == 0


def test_post_logs_invalid_timestamp(client):
    """无效日期格式 → 422"""
    response = client.post("/api/logs", json={"logs": [
        {"timestamp": "2026/03/09 14:30:15", "level": "INFO",
         "service": "Svc", "message": "msg"}
    ]})
    assert response.status_code == 422


def test_post_logs_invalid_level(client):
    """未知日志级别 → 422"""
    response = client.post("/api/logs", json={"logs": [
        {"timestamp": "2026-03-09 14:30:15", "level": "DEBUG",
         "service": "Svc", "message": "msg"}
    ]})
    assert response.status_code == 422


def test_post_logs_missing_logs_field(client):
    """缺少 logs 字段 → 422"""
    response = client.post("/api/logs", json={})
    assert response.status_code == 422


def test_post_logs_field_is_not_array(client):
    """logs 字段不是数组 → 422"""
    response = client.post("/api/logs", json={"logs": "not-an-array"})
    assert response.status_code == 422


def test_post_logs_null_logs_field(client):
    """logs 字段为 null → 422"""
    response = client.post("/api/logs", json={"logs": None})
    assert response.status_code == 422


@pytest.mark.parametrize("missing_field", ["timestamp", "level", "service", "message"])
def test_post_logs_missing_required_field(client, missing_field):
    """任一必填字段缺失 → 422"""
    log = {
        "timestamp": "2026-03-09 14:30:15",
        "level": "INFO",
        "service": "Svc",
        "message": "msg",
    }
    del log[missing_field]
    response = client.post("/api/logs", json={"logs": [log]})
    assert response.status_code == 422


def test_get_stats_correct(client, sample_logs):
    """GET /api/logs/stats 返回正确统计"""
    client.post("/api/logs", json=sample_logs)
    response = client.get("/api/logs/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["by_level"]["ERROR"] == 1
    assert body["by_level"]["INFO"] == 1
    assert body["by_level"]["WARN"] == 1
    assert body["by_service"]["UserService"] == 1


def test_stats_by_level_always_has_all_keys(client):
    """by_level 三个 key 始终存在，即使某级别没有日志"""
    response = client.get("/api/logs/stats")
    assert response.status_code == 200
    body = response.json()
    assert set(body["by_level"].keys()) == {"ERROR", "WARN", "INFO"}


def test_stats_by_service_empty_when_no_logs(client):
    """无日志时 by_service 为空对象"""
    body = client.get("/api/logs/stats").json()
    assert body["by_service"] == {}
    assert body["total"] == 0


def test_stats_by_service_multiple_services(client):
    """多服务计数各自正确"""
    client.post("/api/logs", json={"logs": [
        {"timestamp": "2026-03-09 14:30:00", "level": "INFO",
         "service": "SvcA", "message": "a"},
        {"timestamp": "2026-03-09 14:30:01", "level": "INFO",
         "service": "SvcA", "message": "a2"},
        {"timestamp": "2026-03-09 14:30:02", "level": "WARN",
         "service": "SvcB", "message": "b"},
    ]})
    body = client.get("/api/logs/stats").json()
    assert body["by_service"]["SvcA"] == 2
    assert body["by_service"]["SvcB"] == 1


def test_error_log_triggers_alert(client):
    """ERROR 日志触发告警，验证 payload 字段完整"""
    with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook:
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:15", "level": "ERROR",
             "service": "UserService", "message": "连接失败"}
        ]})
        assert mock_webhook.call_count == 1
        payload = mock_webhook.call_args[0][0]
        assert payload["service"] == "UserService"
        assert payload["level"] == "ERROR"
        assert payload["log_timestamp"] == "2026-03-09 14:30:15"
        assert "alert_timestamp" in payload
        assert "environment" in payload
        # alert_id 应为合法 UUID
        assert uuid.UUID(payload["alert_id"])


def test_non_error_log_does_not_trigger_alert(client):
    """INFO / WARN 日志不触发告警"""
    with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook:
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:15", "level": "INFO",
             "service": "Svc", "message": "正常日志"},
            {"timestamp": "2026-03-09 14:30:16", "level": "WARN",
             "service": "Svc", "message": "警告日志"},
        ]})
        mock_webhook.assert_not_called()


def test_batch_multiple_errors_triggers_once_per_service(client):
    """同一服务批量 ERROR 在窗口内只触发一次，且对应第一条日志"""
    with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook:
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:15", "level": "ERROR",
             "service": "UserService", "message": "第一次失败"},
            {"timestamp": "2026-03-09 14:31:00", "level": "ERROR",
             "service": "UserService", "message": "第二次失败"},
        ]})
        assert mock_webhook.call_count == 1
        assert mock_webhook.call_args[0][0]["log_timestamp"] == "2026-03-09 14:30:15"


def test_alert_window_suppression_different_services(client):
    """不同服务的 ERROR 各自独立触发告警"""
    with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook:
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:15", "level": "ERROR",
             "service": "ServiceA", "message": "A 失败"},
            {"timestamp": "2026-03-09 14:30:16", "level": "ERROR",
             "service": "ServiceB", "message": "B 失败"},
        ]})
        assert mock_webhook.call_count == 2


def test_alert_window_resets_after_expiry(client):
    """超出窗口时间后，同一服务再次触发告警"""
    from datetime import datetime, timezone, timedelta
    base_time = datetime(2026, 3, 9, 14, 30, 0, tzinfo=timezone.utc)

    with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook, \
         patch("app.services.alert_service.datetime") as mock_datetime:
        # 第一次请求：服务端时间 14:30:00
        mock_datetime.now.return_value = base_time
        mock_datetime.strftime = datetime.strftime
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "UserService", "message": "第一次"},
        ]})
        assert mock_webhook.call_count == 1

        # 第二次请求：服务端时间 14:36:00（6分钟后，超出5分钟窗口）
        mock_datetime.now.return_value = base_time + timedelta(minutes=6)
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:36:00", "level": "ERROR",
             "service": "UserService", "message": "6分钟后，超出5分钟窗口"},
        ]})
        assert mock_webhook.call_count == 2


def test_alert_window_boundary_exact(client):
    """恰好在窗口边界（5分钟整）视为超出窗口，触发告警（实现使用严格 <）"""
    from datetime import datetime, timezone, timedelta
    base_time = datetime(2026, 3, 9, 14, 30, 0, tzinfo=timezone.utc)

    with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook, \
         patch("app.services.alert_service.datetime") as mock_datetime:
        # 第一次请求：服务端时间 14:30:00
        mock_datetime.now.return_value = base_time
        mock_datetime.strftime = datetime.strftime
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "UserService", "message": "第一次"},
        ]})
        assert mock_webhook.call_count == 1

        # 第二次请求：服务端时间 14:35:00（恰好5分钟，等于窗口）
        mock_datetime.now.return_value = base_time + timedelta(minutes=5)
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:35:00", "level": "ERROR",
             "service": "UserService", "message": "恰好5分钟，等于窗口，触发"},
        ]})
        assert mock_webhook.call_count == 2  # 差值 == window，不满足 <，触发


def test_alerts_triggered_count_in_response(client):
    """alerts_triggered 返回值与实际触发次数一致"""
    response = client.post("/api/logs", json={"logs": [
        {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
         "service": "SvcA", "message": "错误A"},
        {"timestamp": "2026-03-09 14:30:01", "level": "ERROR",
         "service": "SvcB", "message": "错误B"},
        {"timestamp": "2026-03-09 14:30:02", "level": "INFO",
         "service": "SvcC", "message": "正常"},
    ]})
    body = response.json()
    assert body["alerts_triggered"] == 2
    assert body["accepted"] == 3


def test_webhook_failure_does_not_break_ingest(client):
    """webhook 失败不影响日志摄取，alerts_failed 计数，统计正确写入"""
    with patch("app.services.alert_service.AlertService._send_webhook",
               side_effect=RuntimeError("网络超时")):
        response = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:15", "level": "ERROR",
             "service": "UserService", "message": "连接失败"}
        ]})
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] == 1
    assert body["alerts_triggered"] == 0
    assert body["alerts_failed"] == 1
    stats = client.get("/api/logs/stats").json()
    assert stats["total"] == 1
    assert stats["by_level"]["ERROR"] == 1


def test_service_with_special_characters_rejected(client):
    """service 含特殊字符 → 422"""
    response = client.post("/api/logs", json={"logs": [
        {"timestamp": "2026-03-09 14:30:15", "level": "INFO",
         "service": "Svc/Path", "message": "msg"}
    ]})
    assert response.status_code == 422


def test_service_with_newline_rejected(client):
    """service 含换行符 → 422"""
    response = client.post("/api/logs", json={"logs": [
        {"timestamp": "2026-03-09 14:30:15", "level": "INFO",
         "service": "Svc\nName", "message": "msg"}
    ]})
    assert response.status_code == 422


def test_service_count_limit_exceeded(client):
    """服务数量超过 MAX_SERVICES → 500"""
    from app.routers.logs import _log_service
    original_max = _log_service.stats_store.MAX_SERVICES
    _log_service.stats_store.MAX_SERVICES = 2  # 临时降低上限

    try:
        # 前两个服务正常
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "INFO", "service": "Svc1", "message": "a"},
            {"timestamp": "2026-03-09 14:30:01", "level": "INFO", "service": "Svc2", "message": "b"},
        ]})
        # 第三个服务超限
        response = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:02", "level": "INFO", "service": "Svc3", "message": "c"}
        ]})
        assert response.status_code == 500
        assert "服务数量超过上限" in response.json()["detail"]
    finally:
        _log_service.stats_store.MAX_SERVICES = original_max


def test_alert_window_out_of_order_logs(client):
    """日志乱序到达时，窗口判断基于日志时间而非到达顺序"""
    with patch("app.services.alert_service.AlertService._send_webhook") as mock:
        # 先到达未来时间的日志
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:35:00", "level": "ERROR",
             "service": "Svc", "message": "后发生的错误"}
        ]})
        assert mock.call_count == 1

        # 后到达过去时间的日志（乱序）
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "Svc", "message": "先发生的错误"}
        ]})
        # 当前实现：14:30:00 - 14:35:00 = -5min < 5min → 被抑制
        # 固化当前行为：乱序日志被抑制（假设日志按时间顺序到达）
        assert mock.call_count == 1


def test_alert_lru_eviction_when_limit_exceeded(client):
    """超过 MAX_ALERT_KEYS 时，LRU 淘汰最旧的 key"""
    from app.routers.logs import _alert_service
    from app.stores.memory_alert_window_store import MemoryAlertWindowStore

    # 只有内存存储才有 MAX_ALERT_KEYS 和 _last_alert
    if not isinstance(_alert_service.window_store, MemoryAlertWindowStore):
        import pytest
        pytest.skip("此测试仅适用于内存存储")

    original_max = _alert_service.window_store.MAX_ALERT_KEYS
    _alert_service.window_store.MAX_ALERT_KEYS = 2

    try:
        with patch("app.services.alert_service.AlertService._send_webhook") as mock:
            # 填满 2 个 key
            client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
                 "service": "Svc1", "message": "a"},
                {"timestamp": "2026-03-09 14:30:01", "level": "ERROR",
                 "service": "Svc2", "message": "b"},
            ]})
            assert mock.call_count == 2
            assert len(_alert_service.window_store._last_alert) == 2

            # 第 3 个 key 触发 LRU 淘汰（Svc1 最旧）
            client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:02", "level": "ERROR",
                 "service": "Svc3", "message": "c"}
            ]})
            assert mock.call_count == 3
            assert len(_alert_service.window_store._last_alert) == 2
            # key 现在是 (service, level, error_category)
            assert ("Svc1", "ERROR", "unknown") not in _alert_service.window_store._last_alert

            # Svc1 被淘汰，再次发送 Svc1 应触发告警
            client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:03", "level": "ERROR",
                 "service": "Svc1", "message": "d"}
            ]})
            assert mock.call_count == 4
            assert ("Svc1", "ERROR", "unknown") in _alert_service.window_store._last_alert
    finally:
        _alert_service.window_store.MAX_ALERT_KEYS = original_max


def test_concurrent_alerts_same_service(client):
    """多线程同时发送同一 service 的 ERROR，只应触发 1 次告警"""
    import threading
    from datetime import datetime, timezone
    from app.routers.logs import _alert_service

    # 提高频率阈值，避免并发测试中触发聚合告警
    original_threshold = _alert_service._frequency_threshold
    _alert_service._frequency_threshold = 100

    try:
        base_time = datetime(2026, 3, 9, 14, 30, 0, tzinfo=timezone.utc)
        results = []

        def send_log():
            response = client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
                 "service": "ConcurrentSvc", "message": "并发错误"}
            ]})
            results.append(response.json()["alerts_triggered"])

        with patch("app.services.alert_service.httpx.post") as mock_post, \
             patch("app.services.alert_service.datetime") as mock_datetime:
            mock_datetime.now.return_value = base_time
            mock_datetime.strftime = datetime.strftime
            mock_response = type("Response", (), {
                "status_code": 200,
                "raise_for_status": lambda self: None,
            })()
            mock_post.return_value = mock_response

            # 启动 10 个并发线程
            threads = [threading.Thread(target=send_log) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # 只有 1 个线程成功触发告警
            assert sum(results) == 1
            assert mock_post.call_count == 1
    finally:
        _alert_service._frequency_threshold = original_threshold


def test_concurrent_alerts_different_services(client):
    """多线程同时发送不同 service 的 ERROR，应该都触发告警"""
    import threading
    from datetime import datetime, timezone

    base_time = datetime(2026, 3, 9, 14, 30, 0, tzinfo=timezone.utc)
    results = []

    def send_log(service_name):
        response = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": service_name, "message": "并发错误"}
        ]})
        results.append(response.json()["alerts_triggered"])

    with patch("app.services.alert_service.httpx.post") as mock_post, \
         patch("app.services.alert_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = base_time
        mock_datetime.strftime = datetime.strftime
        mock_response = type("Response", (), {
            "status_code": 200,
            "raise_for_status": lambda self: None,
        })()
        mock_post.return_value = mock_response

        # 启动 5 个并发线程，每个发送不同 service
        threads = [threading.Thread(target=send_log, args=(f"Svc{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 5 个不同 service 都应该触发告警
        assert sum(results) == 5
        assert mock_post.call_count == 5


def test_alert_success_logging(client, caplog):
    """成功告警应记录结构化日志，包含 alert_id, service, level"""
    import logging
    from datetime import datetime, timezone

    base_time = datetime(2026, 3, 9, 14, 30, 0, tzinfo=timezone.utc)

    with caplog.at_level(logging.INFO), \
         patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook, \
         patch("app.services.alert_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = base_time
        mock_datetime.strftime = datetime.strftime

        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "LogTestSvc", "message": "测试日志"}
        ]})

        # 验证日志记录
        assert any("alert_sent" in record.message for record in caplog.records)
        log_record = [r for r in caplog.records if "alert_sent" in r.message][0]
        assert log_record.service == "LogTestSvc"
        assert log_record.levelno == logging.INFO
        assert hasattr(log_record, "alert_id")


def test_alert_failure_logging(client, caplog):
    """告警失败应记录错误日志，包含 alert_id, error, error_type"""
    import logging
    from datetime import datetime, timezone

    base_time = datetime(2026, 3, 9, 14, 30, 0, tzinfo=timezone.utc)

    with caplog.at_level(logging.ERROR), \
         patch("app.services.alert_service.AlertService._send_webhook",
               side_effect=RuntimeError("Webhook 超时")) as mock_webhook, \
         patch("app.services.alert_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = base_time
        mock_datetime.strftime = datetime.strftime

        response = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "FailSvc", "message": "测试失败"}
        ]})

        # 验证告警失败被记录
        assert response.json()["alerts_failed"] == 1
        assert any("alert_failed" in record.message for record in caplog.records)

        log_record = [r for r in caplog.records if "alert_failed" in r.message][0]
        assert log_record.service == "FailSvc"
        assert log_record.error_type == "RuntimeError"
        assert "Webhook 超时" in log_record.error


def test_alert_error_category_classification(client):
    """不同错误类型应该分别告警，不互相抑制"""
    from datetime import datetime, timezone

    base_time = datetime(2026, 3, 9, 14, 30, 0, tzinfo=timezone.utc)

    with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook, \
         patch("app.services.alert_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = base_time
        mock_datetime.strftime = datetime.strftime

        # 数据库错误
        response1 = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "Svc1", "message": "Database connection failed"}
        ]})
        assert response1.json()["alerts_triggered"] == 1
        assert mock_webhook.call_count == 1
        assert "db_error" in str(mock_webhook.call_args[0][0])

        # Redis 错误（不同类型，应该触发）
        response2 = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:01", "level": "ERROR",
             "service": "Svc1", "message": "Redis timeout"}
        ]})
        assert response2.json()["alerts_triggered"] == 1
        assert mock_webhook.call_count == 2
        assert "cache_error" in str(mock_webhook.call_args[0][0])

        # 再次数据库错误（窗口内，应该被抑制）
        response3 = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:02", "level": "ERROR",
             "service": "Svc1", "message": "Database query timeout"}
        ]})
        assert response3.json()["alerts_triggered"] == 0
        assert mock_webhook.call_count == 2  # 不增加


def test_alert_error_category_unknown(client):
    """未匹配的错误归类为 unknown"""
    from datetime import datetime, timezone

    base_time = datetime(2026, 3, 9, 14, 30, 0, tzinfo=timezone.utc)

    with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook, \
         patch("app.services.alert_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = base_time
        mock_datetime.strftime = datetime.strftime

        response = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "Svc1", "message": "Some unknown error"}
        ]})
        assert response.json()["alerts_triggered"] == 1
        assert "unknown" in str(mock_webhook.call_args[0][0])


def test_redis_connection_failure_on_increment(client):
    """Redis 连接失败时返回 503"""
    from app.routers.logs import _log_service
    import redis

    # 模拟 Redis 连接失败
    with patch.object(_log_service.stats_store, 'increment_stats',
                      side_effect=redis.ConnectionError("Connection refused")):
        response = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "INFO",
             "service": "Svc1", "message": "test"}
        ]})
        assert response.status_code == 503
        assert "存储层不可用" in response.json()["detail"]


def test_redis_connection_failure_on_get_stats(client):
    """Redis 连接失败时 GET /stats 返回 503"""
    from app.routers.logs import _log_service
    import redis

    with patch.object(_log_service.stats_store, 'get_stats',
                      side_effect=redis.ConnectionError("Connection refused")):
        response = client.get("/api/logs/stats")
        assert response.status_code == 503
        assert "存储层不可用" in response.json()["detail"]


def test_redis_connection_failure_on_check_limit(client):
    """Redis 连接失败时检查服务上限返回 503"""
    from app.routers.logs import _log_service
    import redis

    with patch.object(_log_service.stats_store, 'check_service_limit',
                      side_effect=redis.ConnectionError("Connection refused")):
        response = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "INFO",
             "service": "Svc1", "message": "test"}
        ]})
        assert response.status_code == 503
        assert "存储层不可用" in response.json()["detail"]


def test_alert_frequency_threshold_triggers_aggregated_alert(client):
    """窗口内累计达到阈值时触发聚合告警"""
    from app.routers.logs import _alert_service
    original_threshold = _alert_service._frequency_threshold
    _alert_service._frequency_threshold = 3  # 降低阈值便于测试

    try:
        with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook:
            # 第 1 次：首次告警（窗口外）
            client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
                 "service": "Svc1", "message": "Database error"}
            ]})
            assert mock_webhook.call_count == 1
            assert mock_webhook.call_args[0][0]["frequency"] == 1

            # 第 2 次：窗口内，被抑制
            client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:01", "level": "ERROR",
                 "service": "Svc1", "message": "Database error"}
            ]})
            assert mock_webhook.call_count == 1

            # 第 3 次：达到阈值，触发聚合告警
            client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:02", "level": "ERROR",
                 "service": "Svc1", "message": "Database error"}
            ]})
            assert mock_webhook.call_count == 2
            payload = mock_webhook.call_args[0][0]
            assert payload["frequency"] == 3
            assert "累计 3 次" in payload["message"]
    finally:
        _alert_service._frequency_threshold = original_threshold


def test_alert_frequency_resets_after_aggregated_alert(client):
    """聚合告警后频率计数重置"""
    from app.routers.logs import _alert_service
    original_threshold = _alert_service._frequency_threshold
    _alert_service._frequency_threshold = 2

    try:
        with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook:
            # 触发首次告警
            client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
                 "service": "Svc1", "message": "Database error"}
            ]})
            assert mock_webhook.call_count == 1

            # 达到阈值，触发聚合告警
            client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:01", "level": "ERROR",
                 "service": "Svc1", "message": "Database error"}
            ]})
            assert mock_webhook.call_count == 2

            # 聚合告警后计数重置，下一次不触发（窗口内）
            client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:02", "level": "ERROR",
                 "service": "Svc1", "message": "Database error"}
            ]})
            assert mock_webhook.call_count == 2  # 不增加
    finally:
        _alert_service._frequency_threshold = original_threshold


def test_alert_frequency_payload_contains_frequency_field(client):
    """告警 payload 包含 frequency 字段"""
    with patch("app.services.alert_service.AlertService._send_webhook") as mock_webhook:
        client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "Svc1", "message": "Database error"}
        ]})
        payload = mock_webhook.call_args[0][0]
        assert "frequency" in payload
        assert payload["frequency"] == 1


def test_webhook_timeout_triggers_alert_failed(client):
    """Webhook 超时后所有重试失败，alerts_failed 计数"""
    from app.routers.logs import _alert_service
    original_retries = _alert_service._frequency_threshold

    with patch("app.services.alert_service.httpx.post",
               side_effect=httpx.TimeoutException("timeout")), \
         patch("app.services.alert_service.time.sleep"):  # 跳过退避等待
        response = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "Svc1", "message": "err"}
        ]})
        assert response.status_code == 200
        assert response.json()["alerts_failed"] == 1
        assert response.json()["accepted"] == 1  # 日志仍然被接受


def test_webhook_retry_succeeds_on_second_attempt(client):
    """Webhook 第一次超时，第二次成功"""
    call_count = {"n": 0}

    def mock_post(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise httpx.TimeoutException("timeout")
        mock_response = type("Response", (), {
            "status_code": 200,
            "raise_for_status": lambda self: None,
        })()
        return mock_response

    with patch("app.services.alert_service.httpx.post", side_effect=mock_post), \
         patch("app.services.alert_service.time.sleep"):
        response = client.post("/api/logs", json={"logs": [
            {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
             "service": "Svc1", "message": "err"}
        ]})
        assert response.status_code == 200
        assert response.json()["alerts_triggered"] == 1
        assert response.json()["alerts_failed"] == 0
        assert call_count["n"] == 2  # 重试了一次


def test_webhook_timeout_does_not_block_ingest(client):
    """Webhook 超时不阻塞日志摄取（超时时间可配置）"""
    import time as time_module
    from app.routers.logs import _alert_service
    original_timeout = settings.WEBHOOK_TIMEOUT_SECONDS
    original_retries = settings.WEBHOOK_MAX_RETRIES
    settings.WEBHOOK_TIMEOUT_SECONDS = 0.1  # 100ms 超时
    settings.WEBHOOK_MAX_RETRIES = 1  # 只重试 1 次

    try:
        with patch("app.services.alert_service.httpx.post",
                   side_effect=httpx.TimeoutException("timeout")), \
             patch("app.services.alert_service.time.sleep"):
            start = time_module.time()
            response = client.post("/api/logs", json={"logs": [
                {"timestamp": "2026-03-09 14:30:00", "level": "ERROR",
                 "service": "Svc1", "message": "err"}
            ]})
            duration = time_module.time() - start

            assert response.status_code == 200
            assert duration < 2.0  # 应该快速返回
    finally:
        settings.WEBHOOK_TIMEOUT_SECONDS = original_timeout
        settings.WEBHOOK_MAX_RETRIES = original_retries
