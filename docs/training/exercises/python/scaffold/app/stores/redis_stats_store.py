"""
Redis 统计存储实现
"""
from typing import Dict

import redis

from app.config import settings
from app.models.log import LOG_LEVELS, LogLevelStats, LogStats
from app.stores.stats_store import StatsStore


class RedisStatsStore(StatsStore):
    """Redis 统计存储"""

    MAX_SERVICES = 10_000  # 服务数量上限

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = settings.REDIS_KEY_PREFIX

    def _key(self, suffix: str) -> str:
        """生成带前缀的 Redis key"""
        return f"{self.prefix}:stats:{suffix}"

    def increment_stats(self, batch_level: Dict[str, int], batch_service: Dict[str, int], total: int) -> None:
        """增量更新统计数据（使用 pipeline 批量操作）"""
        pipe = self.redis.pipeline()
        pipe.incrby(self._key("total"), total)

        for level, count in batch_level.items():
            pipe.hincrby(self._key("by_level"), level, count)

        for service, count in batch_service.items():
            pipe.hincrby(self._key("by_service"), service, count)

        pipe.execute()

    def get_stats(self) -> LogStats:
        """获取当前统计数据"""
        total = self.redis.get(self._key("total"))
        by_level = self.redis.hgetall(self._key("by_level"))
        by_service = self.redis.hgetall(self._key("by_service"))

        # Redis 返回 bytes，需要解码
        return LogStats(
            total=int(total) if total else 0,
            by_level=LogLevelStats(
                **{
                    level: int(by_level.get(level.encode(), b"0"))
                    for level in LOG_LEVELS
                }
            ),
            by_service={
                k.decode(): int(v) for k, v in by_service.items()
            } if by_service else {},
        )

    def reset(self) -> None:
        """重置统计数据"""
        self.redis.delete(
            self._key("total"),
            self._key("by_level"),
            self._key("by_service"),
        )

    def check_service_limit(self, new_services: set) -> bool:
        """检查新增服务是否超过上限"""
        current_count = self.redis.hlen(self._key("by_service"))
        existing_services = set()

        if new_services:
            # 批量检查哪些服务已存在
            pipe = self.redis.pipeline()
            for service in new_services:
                pipe.hexists(self._key("by_service"), service)
            results = pipe.execute()

            existing_services = {
                service for service, exists in zip(new_services, results) if exists
            }

        new_service_count = len(new_services - existing_services)
        return current_count + new_service_count <= self.MAX_SERVICES
