"""
12.4 分布式链路追踪 — OpenTelemetry，覆盖 API → Celery → GraphDB 调用链
"""
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generator
import uuid

logger = logging.getLogger(__name__)

# ContextVar 存储当前请求的 trace_id 和 span_id
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
_span_id_var: ContextVar[str] = ContextVar("span_id", default="")
_parent_span_id_var: ContextVar[str] = ContextVar("parent_span_id", default="")


def get_trace_id() -> str:
    """获取当前请求的 trace_id。"""
    return _trace_id_var.get()


def get_span_id() -> str:
    """获取当前 span 的 span_id。"""
    return _span_id_var.get()


def new_trace_id() -> str:
    """生成新的 trace_id（32 位 hex）。"""
    return uuid.uuid4().hex


def new_span_id() -> str:
    """生成新的 span_id（16 位 hex）。"""
    return uuid.uuid4().hex[:16]


@contextmanager
def trace_span(
    name: str,
    *,
    trace_id: str | None = None,
    attributes: dict | None = None,
) -> Generator[dict, None, None]:
    """
    轻量级 span 上下文管理器。

    在 OpenTelemetry SDK 可用时，转发给 OTEL；不可用��退回到结构化日志。

    Args:
        name: span 名称（如 "sparql.query", "celery.task"）
        trace_id: 可选，复用父 trace_id；为 None 时生成新 trace
        attributes: 额外属性键值对

    Yields:
        span_context dict，包含 trace_id / span_id 等字段
    """
    # 生成或复用 trace_id
    tid = trace_id or _trace_id_var.get() or new_trace_id()
    parent_sid = _span_id_var.get()
    sid = new_span_id()

    # 设置 ContextVar
    token_trace = _trace_id_var.set(tid)
    token_span = _span_id_var.set(sid)
    token_parent = _parent_span_id_var.set(parent_sid)

    span_ctx = {
        "trace_id": tid,
        "span_id": sid,
        "parent_span_id": parent_sid,
        "name": name,
    }
    if attributes:
        span_ctx.update(attributes)

    logger.debug("span.start %s trace=%s span=%s parent=%s", name, tid, sid, parent_sid)

    try:
        # 尝试使用 OpenTelemetry SDK（若已安装）
        _otel_span = _try_otel_span(name, tid, parent_sid, attributes or {})
        yield span_ctx
    except Exception:
        yield span_ctx
    finally:
        logger.debug("span.end %s trace=%s span=%s", name, tid, sid)
        _trace_id_var.reset(token_trace)
        _span_id_var.reset(token_span)
        _parent_span_id_var.reset(token_parent)


def _try_otel_span(name: str, trace_id: str, parent_span_id: str, attributes: dict):
    """
    尝试创建 OpenTelemetry span。若 SDK 未安装则静默忽略。

    OpenTelemetry 集成方式：
    1. 安装 opentelemetry-sdk + opentelemetry-instrumentation-fastapi
    2. 在启动脚本中配�� TracerProvider（OTLP exporter 指向 Jaeger/Tempo）
    3. 本函数自动拾取已配置的全局 Tracer
    """
    try:
        from opentelemetry import trace as otel_trace
        tracer = otel_trace.get_tracer("drp")
        ctx = otel_trace.Context()
        span = tracer.start_span(name, context=ctx, attributes=attributes)
        return span
    except ImportError:
        return None
    except Exception as exc:
        logger.debug("OpenTelemetry span 创建失败（降级为日志追踪）: %s", exc)
        return None


class TracingMiddleware:
    """
    FastAPI ASGI 中间件：为每个 HTTP 请求生成 trace_id，注入响应头。

    在 pyproject.toml 中添加 opentelemetry-instrumentation-fastapi 后，
    可替换本中间件以获得完整的 OTEL 集成；本类提供轻量降级实现。
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # 提取或生成 trace_id
        headers = dict(scope.get("headers", []))
        incoming_trace = headers.get(b"x-trace-id", b"").decode()
        tid = incoming_trace or new_trace_id()

        token_trace = _trace_id_var.set(tid)
        token_span = _span_id_var.set(new_span_id())

        async def send_with_trace(message):
            """在响应头中注入 X-Trace-ID。"""
            if message["type"] == "http.response.start":
                headers_list = list(message.get("headers", []))
                headers_list.append((b"x-trace-id", tid.encode()))
                message = {**message, "headers": headers_list}
            await send(message)

        try:
            await self.app(scope, receive, send_with_trace)
        finally:
            _trace_id_var.reset(token_trace)
            _span_id_var.reset(token_span)


def celery_trace_task(func):
    """
    Celery 任务装饰器：从任务 headers 中提取 trace_id，注入 ContextVar。

    使用示例：
        @app.task
        @celery_trace_task
        def my_task(tenant_id: str): ...
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Celery 任务中通过 current_task.request.headers 传递 trace context
        try:
            from celery import current_task
            tid = (current_task.request.headers or {}).get("trace_id") or new_trace_id()
        except Exception:
            tid = new_trace_id()

        token = _trace_id_var.set(tid)
        try:
            return func(*args, **kwargs)
        finally:
            _trace_id_var.reset(token)

    return wrapper
