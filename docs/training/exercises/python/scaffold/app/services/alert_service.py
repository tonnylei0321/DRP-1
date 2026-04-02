"""
告警服务
"""
import logging
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from threading import Lock

import httpx

from app.config import settings
from app.models.log import LOG_TIME_FORMAT, LogEntry
from app.stores.alert_window_store import AlertWindowStore

logger = logging.getLogger(__name__)


class AlertService:
    """告警服务，支持时间窗口内去重"""

    # 错误分类规则（按 message 前缀匹配）
    ERROR_PATTERNS = {
        r"(?i)database.*": "db_error",
        r"(?i)redis.*": "cache_error",
        r"(?i)http.*": "http_error",
        r"(?i)timeout.*": "timeout_error",
        r"(?i)connection.*": "connection_error",
        r"(?i)auth.*": "auth_error",
        r"(?i)permission.*": "permission_error",
    }

    def __init__(self, window_store: AlertWindowStore):
        self._webhook_url = settings.WEBHOOK_URL
        self._window = timedelta(minutes=settings.ALERT_WINDOW_MINUTES)
        self._environment = settings.ENVIRONMENT
        self._frequency_threshold = settings.ALERT_FREQUENCY_THRESHOLD
        self.window_store = window_store

        # 窗口内频率计数
        self._window_counts: dict = defaultdict(int)
        self._window_start: dict = {}  # key → 窗口开始时间
        self._counts_lock = Lock()

    def _classify_error(self, message: str) -> str:
        """根据错误消息分类错误类型"""
        for pattern, category in self.ERROR_PATTERNS.items():
            if re.match(pattern, message):
                return category
        return "unknown"

    def _update_frequency(self, key: tuple, now: datetime) -> int:
        """更新频率计数，返回当前窗口内的累计次数"""
        with self._counts_lock:
            # 检查窗口是否过期
            if key in self._window_start:
                elapsed = (now - self._window_start[key]).total_seconds()
                if elapsed >= self._window.total_seconds():
                    # 窗口过期，重置计数
                    self._window_counts[key] = 0
                    self._window_start[key] = now
            else:
                # 首次，初始化窗口
                self._window_start[key] = now

            # 增加计数
            self._window_counts[key] += 1
            return self._window_counts[key]

    def check_and_alert(self, log_entry: LogEntry) -> bool:
        """检查日志是否需要告警：ERROR 级别且不在窗口抑制期内则触发"""
        if log_entry.level != "ERROR":
            return False

        now: datetime = datetime.now(timezone.utc)  # 使用服务端时间
        window_seconds = int(self._window.total_seconds())

        # 错误分类
        error_category = self._classify_error(log_entry.message)
        key = (log_entry.service, log_entry.level, error_category)

        # 更新频率计数
        frequency = self._update_frequency(key, now)

        # 原子检查窗口并设置（包含错误类型）
        should_alert = self.window_store.check_and_set_window(
            log_entry.service,
            log_entry.level,
            now,
            window_seconds,
            error_category  # 新增参数
        )

        # 首次告警或达到频率阈值
        if should_alert or frequency >= self._frequency_threshold:
            alert_id = str(uuid.uuid4())
            payload = {
                "alert_id": alert_id,
                "alert_timestamp": now.strftime(LOG_TIME_FORMAT),
                "log_timestamp": log_entry.timestamp.strftime(LOG_TIME_FORMAT),
                "level": log_entry.level,
                "service": log_entry.service,
                "message": log_entry.message,
                "error_category": error_category,
                "frequency": frequency,  # 新增字段
                "environment": self._environment,
            }

            # 频率告警时更新消息
            if frequency >= self._frequency_threshold and not should_alert:
                payload["message"] = f"{log_entry.message} (窗口内累计 {frequency} 次)"

            try:
                self._send_webhook(payload)
                logger.info(
                    "alert_sent",
                    extra={
                        "alert_id": alert_id,
                        "service": log_entry.service,
                        "level": log_entry.level,
                        "error_category": error_category,
                        "frequency": frequency,
                        "webhook_url": self._webhook_url,
                    }
                )
            except Exception as e:
                logger.error(
                    "alert_failed",
                    extra={
                        "alert_id": alert_id,
                        "service": log_entry.service,
                        "level": log_entry.level,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                raise

            # 频率告警后重置窗口（避免重复告警）
            if frequency >= self._frequency_threshold:
                with self._counts_lock:
                    self._window_counts[key] = 0
                    self._window_start[key] = now

            return True

        return False

    def _send_webhook(self, data: dict) -> None:
        """发送 Webhook 通知（带超时和重试）"""
        max_retries = settings.WEBHOOK_MAX_RETRIES
        timeout = settings.WEBHOOK_TIMEOUT_SECONDS

        for attempt in range(max_retries):
            try:
                response = httpx.post(
                    self._webhook_url,
                    json=data,
                    timeout=timeout,
                )
                response.raise_for_status()
                logger.debug(
                    "webhook_sent",
                    extra={
                        "alert_id": data.get("alert_id"),
                        "attempt": attempt + 1,
                        "status_code": response.status_code,
                    }
                )
                return  # 成功，退出
            except httpx.TimeoutException as e:
                logger.warning(
                    "webhook_timeout",
                    extra={
                        "alert_id": data.get("alert_id"),
                        "attempt": attempt + 1,
                        "timeout": timeout,
                    }
                )
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避：1s, 2s, 4s
                else:
                    raise  # 最后一次重试失败，抛出异常
            except httpx.HTTPError as e:
                logger.warning(
                    "webhook_http_error",
                    extra={
                        "alert_id": data.get("alert_id"),
                        "attempt": attempt + 1,
                        "error": str(e),
                    }
                )
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def reset(self) -> None:
        """重置窗口状态（供测试使用）"""
        self.window_store.reset()
        with self._counts_lock:
            self._window_counts.clear()
            self._window_start.clear()
