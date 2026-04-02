"""
Redis 存储测试
"""
import pytest
from fakeredis import FakeRedis, FakeServer

from app.models.log import LOG_LEVELS, LogLevelStats, LogStats
from app.stores.redis_alert_window_store import RedisAlertWindowStore
from app.stores.redis_stats_store import RedisStatsStore
from datetime import datetime, timezone


@pytest.fixture
def redis_client():
    """Fake Redis 客户端（启用 Lua 支持）"""
    server = FakeServer()
    server.lua_modules = {}  # 启用 Lua
    return FakeRedis(server=server, decode_responses=False)


@pytest.fixture
def stats_store(redis_client):
    """Redis 统计存储"""
    return RedisStatsStore(redis_client)


@pytest.fixture
def window_store(redis_client):
    """Redis 告警窗口存储"""
    return RedisAlertWindowStore(redis_client)


def test_redis_stats_increment(stats_store):
    """Redis 统计增量更新"""
    batch_level = {"ERROR": 2, "INFO": 3}
    batch_service = {"Svc1": 3, "Svc2": 2}

    stats_store.increment_stats(batch_level, batch_service, 5)

    stats = stats_store.get_stats()
    assert stats.total == 5
    assert stats.by_level.ERROR == 2
    assert stats.by_level.INFO == 3
    assert stats.by_level.WARN == 0
    assert stats.by_service == {"Svc1": 3, "Svc2": 2}


def test_redis_stats_multiple_increments(stats_store):
    """Redis 统计多次增量"""
    stats_store.increment_stats({"ERROR": 1}, {"Svc1": 1}, 1)
    stats_store.increment_stats({"ERROR": 2}, {"Svc1": 2}, 2)

    stats = stats_store.get_stats()
    assert stats.total == 3
    assert stats.by_level.ERROR == 3
    assert stats.by_service == {"Svc1": 3}


def test_redis_stats_reset(stats_store):
    """Redis 统计重置"""
    stats_store.increment_stats({"ERROR": 5}, {"Svc1": 5}, 5)
    stats_store.reset()

    stats = stats_store.get_stats()
    assert stats.total == 0
    assert stats.by_level.ERROR == 0
    assert stats.by_service == {}


def test_redis_stats_service_limit(stats_store):
    """Redis 统计服务数量上限检查"""
    stats_store.MAX_SERVICES = 2

    # 前两个服务未超限
    assert stats_store.check_service_limit({"Svc1", "Svc2"}) is True

    # 写入前两个服务
    stats_store.increment_stats({}, {"Svc1": 1, "Svc2": 1}, 2)

    # 第三个服务超限
    assert stats_store.check_service_limit({"Svc3"}) is False

    # 已存在的服务不算新增
    assert stats_store.check_service_limit({"Svc1"}) is True


@pytest.mark.skip(reason="FakeRedis 不支持 Lua 脚本，需要真实 Redis 进行集成测试")
def test_redis_window_check_and_set(redis_client):
    """Redis 窗口原子检查并设置（需要真实 Redis）"""
    pass


@pytest.mark.skip(reason="FakeRedis 不支持 Lua 脚本，需要真实 Redis 进行集成测试")
def test_redis_window_different_services(redis_client):
    """Redis 窗口不同服务独立（需要真实 Redis）"""
    pass


@pytest.mark.skip(reason="FakeRedis 不支持 Lua 脚本，需要真实 Redis 进行集成测试")
def test_redis_window_reset(redis_client):
    """Redis 窗口重置（需要真实 Redis）"""
    pass


@pytest.mark.skip(reason="FakeRedis 不支持 Lua 脚本，需要真实 Redis 进行集成测试")
def test_redis_window_expiry(redis_client):
    """Redis 窗口过期后自动删除（需要真实 Redis）"""
    pass
