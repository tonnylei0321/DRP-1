"""
日志相关路由
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.models.log import LogBatchRequest, LogIngestResponse, LogStats
from app.services.alert_service import AlertService
from app.services.log_service import LogService, StorageUnavailableError
from app.stores.alert_window_store import AlertWindowStore
from app.stores.memory_alert_window_store import MemoryAlertWindowStore
from app.stores.memory_stats_store import MemoryStatsStore
from app.stores.stats_store import StatsStore

router = APIRouter()

# 模块级单例，通过 Depends 注入，方便测试覆盖
_stats_store: StatsStore = None
_window_store: AlertWindowStore = None
_log_service: LogService = None
_alert_service: AlertService = None


def _init_stores():
    """初始化存储层（根据配置选择内存或 Redis）"""
    global _stats_store, _window_store, _log_service, _alert_service

    if settings.USE_REDIS:
        # Redis 模式
        import redis
        from app.stores.redis_alert_window_store import RedisAlertWindowStore
        from app.stores.redis_stats_store import RedisStatsStore

        redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=False)
        _stats_store = RedisStatsStore(redis_client)
        _window_store = RedisAlertWindowStore(redis_client)
    else:
        # 内存模式（��认）
        _stats_store = MemoryStatsStore()
        _window_store = MemoryAlertWindowStore()

    _log_service = LogService(_stats_store)
    _alert_service = AlertService(_window_store)


# 初始化
_init_stores()


def get_log_service() -> LogService:
    return _log_service


def get_alert_service() -> AlertService:
    return _alert_service


@router.post(
    "/logs",
    response_model=LogIngestResponse,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"description": "请求体校验失败"},
        500: {"description": "服务数量超限"},
        503: {"description": "存储层不可用"},
    },
)
def ingest_logs(
    payload: LogBatchRequest,
    log_service: Annotated[LogService, Depends(get_log_service)],
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
) -> LogIngestResponse:
    """接收批量日志，返回接收数量和触发告警数"""
    try:
        return log_service.process_logs(payload.logs, alert_service)
    except ValueError as exc:
        # 业务错误（如服务数量超限）
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    except StorageUnavailableError as exc:
        # 存储层不可用
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.get(
    "/logs/stats",
    response_model=LogStats,
    status_code=status.HTTP_200_OK,
    responses={
        503: {"description": "存储层不可用"},
    },
)
def get_log_stats(
    log_service: Annotated[LogService, Depends(get_log_service)],
) -> LogStats:
    """获取日志统计信息"""
    try:
        return log_service.get_stats()
    except StorageUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
