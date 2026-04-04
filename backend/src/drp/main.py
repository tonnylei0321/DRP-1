from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from drp.auth.router import router as auth_router
from drp.config import settings
from drp.drill.router import router as drill_router
from drp.etl.router import router as etl_router
from drp.indicators.router import router as indicators_router
from drp.mapping.router import router as mappings_router
from drp.observability.health import router as health_router
from drp.observability.tracing import TracingMiddleware
from drp.org.router import router as org_router
from drp.tenants.router import router as tenants_router

app = FastAPI(
    title="DRP — 穿透式资金监管平台",
    version="0.1.0",
    docs_url="/api/docs" if settings.app_env == "development" else None,
    redoc_url=None,
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
