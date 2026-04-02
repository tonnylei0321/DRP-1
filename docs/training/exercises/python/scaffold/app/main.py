"""
日志清洗与告警 Webhook 服务

AI驱动开发培训脚手架。基础配置已完成，业务逻辑待实现。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="日志告警服务",
    description="接收日志数据，自动检测错误并发送告警",
    version="1.0.0",
)

# CORS 配置：通过 ALLOWED_ORIGINS 环境变量控制，默认仅允许本地开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


from app.routers.logs import router as logs_router

# 日志相关路由（具体端点在 app/routers/logs.py 中实现）
app.include_router(logs_router, prefix="/api", tags=["logs"])


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {"status": "ok"}
