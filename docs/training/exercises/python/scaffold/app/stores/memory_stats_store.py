"""
内存统计存储实现
"""
from collections import defaultdict
from threading import Lock
from typing import Dict

from app.models.log import LOG_LEVELS, LogLevelStats, LogStats
from app.stores.stats_store import StatsStore


class MemoryStatsStore(StatsStore):
    """内存统计存储（原实现）"""

    MAX_SERVICES = 10_000  # 服务数量上限

    def __init__(self):
        self._total = 0
        self._level_counts: dict = defaultdict(int)
        self._service_counts: dict = defaultdict(int)
        self._lock = Lock()

    def increment_stats(self, batch_level: Dict[str, int], batch_service: Dict[str, int], total: int) -> None:
        """增量更新统计数据"""
        with self._lock:
            self._total += total
            for level, count in batch_level.items():
                self._level_counts[level] += count
            for service, count in batch_service.items():
                self._service_counts[service] += count

    def get_stats(self) -> LogStats:
        """获取当前统计数据"""
        with self._lock:
            return LogStats(
                total=self._total,
                by_level=LogLevelStats(
                    **{level: self._level_counts.get(level, 0) for level in LOG_LEVELS}
                ),
                by_service=dict(self._service_counts),
            )

    def reset(self) -> None:
        """重置统计数据"""
        with self._lock:
            self._total = 0
            self._level_counts.clear()
            self._service_counts.clear()

    def check_service_limit(self, new_services: set) -> bool:
        """检查新增服务是否超过上限"""
        with self._lock:
            current_services = set(self._service_counts.keys())
            if len(current_services) + len(new_services - current_services) > self.MAX_SERVICES:
                return False
            return True
