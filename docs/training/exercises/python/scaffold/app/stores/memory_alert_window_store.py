"""
内存告警窗口存储实现
"""
from collections import OrderedDict
from datetime import datetime
from threading import Lock

from app.stores.alert_window_store import AlertWindowStore


class MemoryAlertWindowStore(AlertWindowStore):
    """内存告警窗口存储（改用 OrderedDict）"""

    MAX_ALERT_KEYS = 50_000

    def __init__(self):
        self._last_alert: OrderedDict = OrderedDict()
        self._lock = Lock()

    def check_and_set_window(
        self,
        service: str,
        level: str,
        now: datetime,
        window_seconds: int,
        error_category: str = "unknown",
    ) -> bool:
        """原子操作：检查窗口并设置（包含错误类型）"""
        key = (service, level, error_category)

        with self._lock:
            last = self._last_alert.get(key)

            # 窗口内抑制
            if last is not None:
                elapsed = (now - last).total_seconds()
                if elapsed < window_seconds:
                    # LRU: 访问时移到末尾
                    self._last_alert.move_to_end(key)
                    return False

            # 窗口外或首次，设置窗口
            self._last_alert[key] = now
            self._last_alert.move_to_end(key)

            # LRU 淘汰
            if len(self._last_alert) > self.MAX_ALERT_KEYS:
                self._last_alert.popitem(last=False)

            return True

    def reset(self) -> None:
        """重置窗口状态"""
        with self._lock:
            self._last_alert.clear()
