"""
日志处理服务
"""
import logging
from collections import defaultdict
from typing import List

from app.models.log import LogEntry, LogIngestResponse
from app.services.alert_service import AlertService
from app.stores.stats_store import StatsStore

logger = logging.getLogger(__name__)


class StorageUnavailableError(Exception):
    """存储层不可用异常"""
    pass


class LogService:
    """日志处理服务"""

    def __init__(self, stats_store: StatsStore):
        self.stats_store = stats_store

    def process_logs(self, logs: List[LogEntry], alert_service: AlertService) -> LogIngestResponse:
        """处理一批日志：先执行告警副作用，再原子提交统计"""
        alerts_triggered = 0
        alerts_failed = 0

        # 先聚合批次计数（不加锁，本地变量）
        batch_level: dict = defaultdict(int)
        batch_service: dict = defaultdict(int)

        for log_entry in logs:
            batch_level[log_entry.level] += 1
            batch_service[log_entry.service] += 1
            try:
                if alert_service.check_and_alert(log_entry):
                    alerts_triggered += 1
            except Exception:
                # 告警是副作用，失败不影响日志摄取
                alerts_failed += 1

        # 检查服务数量上限
        new_services = set(batch_service.keys())
        try:
            if not self.stats_store.check_service_limit(new_services):
                raise ValueError("服务数量超过上限，拒绝摄取")
        except ValueError:
            raise
        except Exception as e:
            logger.error(
                "stats_store_unavailable",
                extra={"operation": "check_service_limit", "error": str(e)},
                exc_info=True,
            )
            raise StorageUnavailableError(f"存储层不可用: {e}") from e

        # 原子提交统计
        try:
            self.stats_store.increment_stats(batch_level, batch_service, len(logs))
        except Exception as e:
            logger.error(
                "stats_store_unavailable",
                extra={"operation": "increment_stats", "error": str(e)},
                exc_info=True,
            )
            raise StorageUnavailableError(f"存储层不可用: {e}") from e

        return LogIngestResponse(
            accepted=len(logs),
            alerts_triggered=alerts_triggered,
            alerts_failed=alerts_failed,
        )

    def get_stats(self):
        """返回日志统计信息"""
        try:
            return self.stats_store.get_stats()
        except Exception as e:
            logger.error(
                "stats_store_unavailable",
                extra={"operation": "get_stats", "error": str(e)},
                exc_info=True,
            )
            raise StorageUnavailableError(f"存储层不可用: {e}") from e

    def reset(self) -> None:
        """重置内存状态（供测试使用）"""
        self.stats_store.reset()
