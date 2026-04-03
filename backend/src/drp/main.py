from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from drp.auth.router import router as auth_router
from drp.config import settings
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


app.include_router(auth_router)
app.include_router(tenants_router)


@app.get("/health", tags=["基础设施"])
async def health_check() -> dict:
    """服务健康检查端点。"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "env": settings.app_env,
    }
