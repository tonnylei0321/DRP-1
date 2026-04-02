"""
配置管理

从环境变量读取配置，提供默认值。此文件已完成。
"""
import os


class Settings:
    """应用配置"""

    # Webhook 配置
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "https://example.com/webhook")

    # 环境标识：prod / staging / dev
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    # CORS 配置：逗号分隔的允许域名列表，生产环境应明确设置
    ALLOWED_ORIGINS: list = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]

    # 告警配置
    ALERT_WINDOW_MINUTES: int = int(os.getenv("ALERT_WINDOW_MINUTES", "5"))
    ALERT_FREQUENCY_THRESHOLD: int = int(os.getenv("ALERT_FREQUENCY_THRESHOLD", "10"))
    WEBHOOK_TIMEOUT_SECONDS: float = float(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "5.0"))
    WEBHOOK_MAX_RETRIES: int = int(os.getenv("WEBHOOK_MAX_RETRIES", "3"))

    # 服务配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Redis 配置
    USE_REDIS: bool = os.getenv("USE_REDIS", "false").lower() == "true"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_KEY_PREFIX: str = os.getenv("REDIS_KEY_PREFIX", f"log-alert:{ENVIRONMENT}")


settings = Settings()
