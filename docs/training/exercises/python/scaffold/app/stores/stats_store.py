"""
统计存储接口
"""
from abc import ABC, abstractmethod
from typing import Dict

from app.models.log import LogStats


class StatsStore(ABC):
    """统计存储抽象接口"""

    @abstractmethod
    def increment_stats(self, batch_level: Dict[str, int], batch_service: Dict[str, int], total: int) -> None:
        """增量更新统计数据"""
        pass

    @abstractmethod
    def get_stats(self) -> LogStats:
        """获取当前统计数据"""
        pass

    @abstractmethod
    def reset(self) -> None:
        """重置统计数据（供测试使用）"""
        pass

    @abstractmethod
    def check_service_limit(self, new_services: set) -> bool:
        """检查新增服务是否超过上限，返回 True 表示未超限"""
        pass
