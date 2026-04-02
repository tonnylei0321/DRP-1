"""
告警窗口存储接口
"""
from abc import ABC, abstractmethod
from datetime import datetime


class AlertWindowStore(ABC):
    """告警窗口存储抽象接口"""

    @abstractmethod
    def check_and_set_window(
        self,
        service: str,
        level: str,
        now: datetime,
        window_seconds: int,
        error_category: str = "unknown",
    ) -> bool:
        """
        原子操作：检查窗口并设置

        key = (service, level, error_category)，不同错误类型独立去重

        返回 True 表示应该触发告警（窗口外或首次）
        返回 False 表示应该抑制（窗口内）
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """重置窗口状态（供测试使用）"""
        pass
