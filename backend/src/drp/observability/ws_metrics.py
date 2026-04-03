"""
12.7 WebSocket 连接数和消息延迟监控
提供 Prometheus 兼容指标，供 prometheus.yml 采集
"""
import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class _WsMetricsStore:
    """内存指标存储（单进程模型；多进程场景应改用 Redis 计数器）。"""
    # 当前活跃连接数，key = tenant_id
    active_connections: dict[str, int] = field(default_factory=dict)
    # 最近 1000 条消息推送延迟（秒），用于计算 P95
    message_latencies: deque = field(default_factory=lambda: deque(maxlen=1000))
    # 总推送消息数
    messages_sent_total: int = 0
    # 总断开连接数
    disconnections_total: int = 0


_store = _WsMetricsStore()


def ws_connection_opened(tenant_id: str) -> None:
    """WebSocket 连接建立时调用。"""
    _store.active_connections[tenant_id] = _store.active_connections.get(tenant_id, 0) + 1
    logger.debug("WebSocket 连接建立 tenant=%s 当前活跃=%d", tenant_id, ws_total_connections())


def ws_connection_closed(tenant_id: str) -> None:
    """WebSocket 连接关闭时调用。"""
    current = _store.active_connections.get(tenant_id, 0)
    if current > 0:
        _store.active_connections[tenant_id] = current - 1
    _store.disconnections_total += 1
    logger.debug("WebSocket 连接关闭 tenant=%s 当前活跃=%d", tenant_id, ws_total_connections())


def ws_message_sent(latency_seconds: float) -> None:
    """每次推送消息完成后调用，记录延迟。"""
    _store.message_latencies.append(latency_seconds)
    _store.messages_sent_total += 1


def ws_total_connections() -> int:
    """返回全局活跃 WebSocket 连接总数。"""
    return sum(_store.active_connections.values())


def ws_connections_by_tenant() -> dict[str, int]:
    """返回每个租户的活跃连接数。"""
    return dict(_store.active_connections)


def ws_p95_latency_ms() -> float:
    """返回消息推送延迟 P95（毫秒）。若无数据返回 0.0。"""
    if not _store.message_latencies:
        return 0.0
    sorted_latencies = sorted(_store.message_latencies)
    idx = int(len(sorted_latencies) * 0.95)
    return sorted_latencies[min(idx, len(sorted_latencies) - 1)] * 1000


def ws_messages_sent_total() -> int:
    """返回累计推送消息数。"""
    return _store.messages_sent_total


def ws_disconnections_total() -> int:
    """返回累计断开连接数。"""
    return _store.disconnections_total


def prometheus_metrics_text() -> str:
    """
    生成 Prometheus text format 指标，供 GET /metrics 端点输出。

    返回的文本包含：
    - drp_websocket_connections_total: 当前活跃连接总数
    - drp_websocket_connections_by_tenant: 各租户活跃连接数
    - drp_websocket_message_latency_p95_ms: 消息延迟 P95（毫秒）
    - drp_websocket_messages_sent_total: 累计推送消息数
    - drp_websocket_disconnections_total: 累计断开连接数
    """
    lines = [
        "# HELP drp_websocket_connections_total 当前活跃 WebSocket 连接总数",
        "# TYPE drp_websocket_connections_total gauge",
        f"drp_websocket_connections_total {ws_total_connections()}",
        "",
        "# HELP drp_websocket_connections_by_tenant 各租户活跃 WebSocket 连接数",
        "# TYPE drp_websocket_connections_by_tenant gauge",
    ]
    for tenant_id, count in ws_connections_by_tenant().items():
        lines.append(f'drp_websocket_connections_by_tenant{{tenant_id="{tenant_id}"}} {count}')

    lines += [
        "",
        "# HELP drp_websocket_message_latency_p95_ms 消息推送延迟 P95（毫秒）",
        "# TYPE drp_websocket_message_latency_p95_ms gauge",
        f"drp_websocket_message_latency_p95_ms {ws_p95_latency_ms():.3f}",
        "",
        "# HELP drp_websocket_messages_sent_total 累计推送消息数",
        "# TYPE drp_websocket_messages_sent_total counter",
        f"drp_websocket_messages_sent_total {ws_messages_sent_total()}",
        "",
        "# HELP drp_websocket_disconnections_total 累计断开连接数",
        "# TYPE drp_websocket_disconnections_total counter",
        f"drp_websocket_disconnections_total {ws_disconnections_total()}",
        "",
    ]
    return "\n".join(lines)
