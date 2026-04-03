"""Celery 应用工厂与队列配置。"""
from celery import Celery

from drp.config import settings

celery_app = Celery(
    "drp",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "drp.etl.tasks",
        "drp.indicators.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    # 重试策略默认值（可被 task 级别覆盖）
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # 结果过期 24 小时
    result_expires=86400,
    # Beat 定时任务
    beat_schedule={
        "incremental-sync-every-60min": {
            "task": "drp.etl.tasks.trigger_incremental_sync_all_tenants",
            "schedule": 3600,  # 秒
        },
        "indicator-calc-every-60min": {
            "task": "drp.indicators.tasks.trigger_indicator_calc_all_tenants",
            "schedule": 3600,
        },
    },
)
