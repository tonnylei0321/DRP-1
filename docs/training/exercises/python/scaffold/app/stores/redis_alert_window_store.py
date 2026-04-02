"""
Redis 告警窗口存储实现
"""
from datetime import datetime

import redis

from app.config import settings
from app.stores.alert_window_store import AlertWindowStore


class RedisAlertWindowStore(AlertWindowStore):
    """Redis 告警窗口存储（使用 Lua 脚本保证原子性）"""

    # Lua 脚本：原子检查窗口并设置
    CHECK_AND_SET_SCRIPT = """
    local key = KEYS[1]
    local window_seconds = tonumber(ARGV[1])
    local alert_id = ARGV[2]

    local existing = redis.call('GET', key)
    if existing then
        return 0  -- 窗口内，抑制
    end

    redis.call('SET', key, alert_id, 'EX', window_seconds)
    return 1  -- 窗口外，触发告警
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = settings.REDIS_KEY_PREFIX
        # 注册 Lua 脚本
        self._check_and_set_sha = self.redis.script_load(self.CHECK_AND_SET_SCRIPT)

    def _key(self, service: str, level: str, error_category: str) -> str:
        """生成带前缀的 Redis key（包含错误类型）"""
        return f"{self.prefix}:dedupe:{service}:{level}:{error_category}"

    def check_and_set_window(
        self,
        service: str,
        level: str,
        now: datetime,
        window_seconds: int,
        error_category: str = "unknown",
    ) -> bool:
        """原子操作：检查窗口并设置（使用 Lua 脚本，包含错误类型）"""
        key = self._key(service, level, error_category)
        alert_id = now.isoformat()

        try:
            # 使用预加载的 Lua 脚本
            result = self.redis.evalsha(
                self._check_and_set_sha,
                1,  # KEYS 数量
                key,
                window_seconds,
                alert_id,
            )
            return bool(result)
        except redis.exceptions.NoScriptError:
            # 脚本不存在（Redis 重启），重新加载
            self._check_and_set_sha = self.redis.script_load(self.CHECK_AND_SET_SCRIPT)
            result = self.redis.evalsha(
                self._check_and_set_sha,
                1,
                key,
                window_seconds,
                alert_id,
            )
            return bool(result)

    def reset(self) -> None:
        """重置窗口状态（删除所有 dedupe key）"""
        pattern = f"{self.prefix}:dedupe:*"
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                self.redis.delete(*keys)
            if cursor == 0:
                break
