from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从环境变量或 .env 文件加载。"""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # GraphDB
    graphdb_url: str = "http://localhost:7200"
    graphdb_repository: str = "drp"
    graphdb_username: str = "admin"
    graphdb_password: str = "root"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "drp"
    postgres_user: str = "drp"
    postgres_password: str = "drp_dev"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Claude / Anthropic API
    claude_api_key: str = ""
    anthropic_api_key: str = ""

    @property
    def postgres_dsn(self) -> str:
        """异步 PostgreSQL 连接字符串。"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
