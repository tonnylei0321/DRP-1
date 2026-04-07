import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from drp.auth.router import router as auth_router
from drp.config import settings
from drp.drill.router import router as drill_router
from drp.etl.router import router as etl_router
from drp.indicators.router import router as indicators_router
from drp.mapping.router import router as mappings_router
from drp.observability.health import router as health_router
from drp.observability.tracing import TracingMiddleware
from drp.org.router import router as org_router
from drp.scope.dept_router import router as dept_router
from drp.scope.router import router as scope_router
from drp.tenants.router import router as tenants_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期：启动时加载注册表并扫描路由。"""
    from drp.scope.registry import build_registry
    from drp.scope.route_guard import scan_unguarded_routes

    registry = build_registry()
    logger.info("Business_Table_Registry 加载完成，共 %d 张表", len(registry))

    # do_orm_execute 事件监听器已在 interceptor.py 中通过装饰器自动注册
    import drp.scope.interceptor  # noqa: F401

    # 路由安全扫描
    unguarded = scan_unguarded_routes(application, registry)
    if unguarded:
        logger.warning(
            "以下路由查询了已注册业务表但未使用 require_data_scope 依赖: %s",
            unguarded,
        )

    yield


app = FastAPI(
    title="DRP — 穿透式资金监管平台",
    version="0.1.0",
    docs_url="/api/docs" if settings.app_env == "development" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TracingMiddleware)


app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(mappings_router)
app.include_router(etl_router)
app.include_router(drill_router)
app.include_router(org_router)
app.include_router(indicators_router)
app.include_router(health_router)
app.include_router(scope_router)
app.include_router(dept_router)
