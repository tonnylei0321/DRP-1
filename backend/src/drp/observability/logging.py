"""
12.3 结构化日志配置 — JSON 格式，含 tenant_id / trace_id / run_id 字段。
12.6 SPARQL 慢日志采集 — 超过 10 秒的查询记录 query plan。
"""
import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any

# 全局 trace_id 上下文变量（由请求中间件或任务运行器注入）
_trace_ctx: ContextVar[str] = ContextVar("trace_id", default="")
_run_ctx: ContextVar[str] = ContextVar("run_id", default="")


def set_trace_id(trace_id: str | None = None) -> str:
    """设置（或生成新）trace_id，返回实际值。"""
    tid = trace_id or str(uuid.uuid4())
    _trace_ctx.set(tid)
    return tid


def set_run_id(run_id: str) -> None:
    """设置 Celery 任务的 run_id。"""
    _run_ctx.set(run_id)


def get_trace_id() -> str:
    return _trace_ctx.get() or ""


def get_run_id() -> str:
    return _run_ctx.get() or ""


class JsonFormatter(logging.Formatter):
    """将日志格式化为 JSON，自动注入 trace_id / run_id。"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": get_trace_id(),
            "run_id": get_run_id(),
        }
        # 注入额外字段（如 tenant_id）
        for key in ("tenant_id", "indicator_id", "job_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """配置全局 JSON 日志处理器。"""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


# ─── SPARQL 慢查询检测 ────────────────────────────────────────────────────────

SLOW_QUERY_THRESHOLD_SECONDS = 10.0
_slow_logger = logging.getLogger("drp.sparql.slow")


class SlowQueryDetector:
    """包装 SPARQL 执行，记录超时查询及其摘要。"""

    def __init__(self, threshold: float = SLOW_QUERY_THRESHOLD_SECONDS) -> None:
        self._threshold = threshold

    def wrap(self, sparql: str, tenant_id: str, elapsed: float) -> None:
        """若 elapsed 超过阈值，记录慢查询日志。"""
        if elapsed >= self._threshold:
            # 提取 SPARQL 前 200 字符作为 query plan 摘要
            summary = " ".join(sparql.split())[:200]
            _slow_logger.warning(
                "慢 SPARQL 查询: elapsed=%.2fs tenant=%s query=%s",
                elapsed, tenant_id, summary,
            )


slow_query_detector = SlowQueryDetector()


def timed_sparql_wrap(sparql: str, tenant_id: str):
    """上下文管理器��计时并自动触发慢查询检测。"""
    class _Timer:
        def __enter__(self):
            self._start = time.monotonic()
            return self

        def __exit__(self, *_):
            elapsed = time.monotonic() - self._start
            slow_query_detector.wrap(sparql, tenant_id, elapsed)

    return _Timer()
