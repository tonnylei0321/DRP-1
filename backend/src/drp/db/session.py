from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from drp.config import settings

_engine = create_async_engine(
    settings.postgres_dsn,
    pool_size=10,
    max_overflow=20,
    echo=settings.app_env == "development",
)

_session_factory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：提供数据库会话。"""
    async with _session_factory() as session:
        yield session


def get_engine():
    """返回当前 AsyncEngine 实例（测试用）。"""
    return _engine
