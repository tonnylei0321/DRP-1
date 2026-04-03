"""
15.3 SPARQL 注入防护 — 拒绝 UPDATE/DROP/CLEAR 等写操作
15.4 API 请求频率限制 — Redis 令牌桶，租户级别
15.5 LLM API 调用内容过滤 — 确保 DDL 中不含业务数据
"""
import re
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# ─── 15.3 SPARQL 注入防护 ─────────────────────────────────────────────────────

# 禁止的 SPARQL 写操作关键词（大小写不敏感）
_FORBIDDEN_OPERATIONS = re.compile(
    r"\b(INSERT\s+DATA|DELETE\s+DATA|DELETE\s+WHERE|DROP\s+(GRAPH|SILENT)|"
    r"CLEAR\s+(GRAPH|SILENT|ALL|DEFAULT|NAMED)|CREATE\s+(SILENT\s+)?GRAPH|"
    r"LOAD|COPY|MOVE|ADD)\b",
    re.IGNORECASE,
)

# 允许的 SPARQL 查询类型（只读）
_ALLOWED_TYPES = re.compile(
    r"^\s*(SELECT|CONSTRUCT|ASK|DESCRIBE)\b",
    re.IGNORECASE,
)


class SparqlInjectionError(ValueError):
    """SPARQL 注入攻击检测到。"""


def validate_sparql_query(sparql: str) -> None:
    """
    验证 SPARQL 语句是否为安全的只读操作。

    规则：
    1. 必须以 SELECT / CONSTRUCT / ASK / DESCRIBE 开头
    2. 不得包含任何写操作关键词

    Raises:
        SparqlInjectionError: 检测到危险操作
    """
    stripped = sparql.strip()

    if not _ALLOWED_TYPES.match(stripped):
        raise SparqlInjectionError(
            f"SPARQL 注入防护：仅允许 SELECT/CONSTRUCT/ASK/DESCRIBE，"
            f"拒绝语句: {stripped[:80]}..."
        )

    match = _FORBIDDEN_OPERATIONS.search(stripped)
    if match:
        raise SparqlInjectionError(
            f"SPARQL 注入防护：检测到禁止操作 '{match.group()}'，请求被拒绝"
        )


# ─── 15.4 API 频率限制（令牌桶） ──────────────────────────────────────────────

class RateLimitExceeded(Exception):
    """超过 API 请求频率限制。"""


class TokenBucketRateLimiter:
    """
    Redis 令牌桶速率限制器。

    Key 格式: rate_limit:{tenant_id}:{endpoint}
    策略: 每个租户每分钟最多 {max_requests} 次请求
    """

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check(
        self,
        tenant_id: str,
        endpoint: str,
        redis_client=None,
    ) -> None:
        """
        检查速率限制。

        Raises:
            RateLimitExceeded: 超过限制
        """
        key = f"rate_limit:{tenant_id}:{endpoint}"

        try:
            if redis_client is not None:
                r = redis_client
            else:
                import redis.asyncio as aioredis
                from drp.config import settings
                r = aioredis.from_url(settings.redis_url)

            # 滑动窗口计数器
            pipe = r.pipeline()
            now_ms = int(time.time() * 1000)
            window_start = now_ms - self.window_seconds * 1000

            # 移除窗口外的记录，添加当前请求，统计窗口内请求数
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now_ms): now_ms})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds * 2)

            results = await pipe.execute()
            request_count = results[2]

            if request_count > self.max_requests:
                raise RateLimitExceeded(
                    f"租户 {tenant_id} 在 {self.window_seconds}s 内请求次数 {request_count} "
                    f"超过限制 {self.max_requests}"
                )
        except RateLimitExceeded:
            raise
        except Exception as exc:
            # Redis 不可用时降级放行（避免级联故障）
            logger.warning("速率限制检查失败（Redis 不可达），降级放行: %s", exc)


# ─── 15.5 LLM 内容过滤 ───────────────────────────────────────────────────────

# 业务数据泄露检测模式（身份证、手机号、银行卡号等）
_SENSITIVE_PATTERNS = [
    (re.compile(r"\b\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dX]\b"), "身份证号"),
    (re.compile(r"\b1[3-9]\d{9}\b"), "手机号"),
    (re.compile(r"\b\d{16,19}\b"), "银行卡号"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "UUID（可能为账号）"),
    # 金额数字（超过 8 位）
    (re.compile(r"\b\d{8,}\.\d{2}\b"), "大额金融数据"),
]


class SensitiveDataError(ValueError):
    """DDL 中检测到敏感业务数据。"""


def filter_ddl_content(ddl: str) -> None:
    """
    检查 DDL 中是否含有业务敏感数据（身份证、手机号、银行卡号等）。

    DDL 应只包含表结构定义，不应包含实际业务数据。
    发现敏感数据时抛出异常，阻止上传到 LLM。

    Raises:
        SensitiveDataError: 检测到敏感数据
    """
    for pattern, data_type in _SENSITIVE_PATTERNS:
        match = pattern.search(ddl)
        if match:
            raise SensitiveDataError(
                f"DDL 中疑似含有业务敏感数据（{data_type}），"
                f"已阻止上传到 LLM API。请检查并移除真实数据后重试。"
            )
