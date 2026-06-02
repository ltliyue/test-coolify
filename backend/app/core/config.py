from __future__ import annotations
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq_platform"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://receptiviq:receptiviq@localhost:5432/receptiviq_platform"
    # PR 2: per-Agency DB provisioning. ``PLATFORM_DATABASE_URL`` is the
    # admin DSN used by tenant_provisioner to CREATE DATABASE; falls back
    # to DATABASE_URL when unset. ``TENANT_PROVISION_MODE`` selects the
    # backend (``managed_db`` for local Postgres, ``neon_api`` for Neon).
    PLATFORM_DATABASE_URL: str = ""
    TENANT_PROVISION_MODE: str = "managed_db"
    NEON_API_KEY: str = ""

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Encryption (Fernet key for credential vault)
    ENCRYPTION_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"

    # Storage (MinIO)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_EXTERNAL_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "receptiviq"
    MINIO_USE_SSL: bool = False

    # Snowflake
    SNOWFLAKE_ACCOUNT: str = ""
    SNOWFLAKE_USER: str = ""
    SNOWFLAKE_PASSWORD: str = ""
    SNOWFLAKE_DATABASE: str = "RECEPTIVIQ"
    SNOWFLAKE_SCHEMA: str = "RAW"
    SNOWFLAKE_WAREHOUSE: str = "ETL_WH"
    SNOWFLAKE_ROLE: str = "RECEPTIVIQ_ETL"

    # Airflow — H-06: no weak default credentials — require environment variable config
    AIRFLOW_BASE_URL: str = "http://airflow-webserver:8080"
    AIRFLOW_USERNAME: str = ""
    AIRFLOW_PASSWORD: str = ""

    # AI
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_TEXT_MODEL: str = "anthropic/claude-sonnet-4-6"
    OPENROUTER_IMAGE_MODEL: str = "google/gemini-2.5-flash-image"
    PERSONA_MODEL: str = "anthropic/claude-opus-4-6"
    CREATIVE_MODEL: str = "anthropic/claude-sonnet-4-6"
    ATTRIBUTION_MODEL: str = "anthropic/claude-sonnet-4-6"

    # Observability
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    SENTRY_DSN: str = ""

    # SMTP (report delivery)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "reports@receptiviq.com"
    SMTP_FROM_NAME: str = "ReceptivIQ Reports"
    SMTP_USE_TLS: bool = True

    # Frontend base URL (used to build invitation links etc.)
    frontend_base_url: str = "http://localhost:5173"

    # HIPAA session timeout (seconds)
    HIPAA_SESSION_TIMEOUT: int = 900   # 15 min
    DEFAULT_SESSION_TIMEOUT: int = 3600  # 60 min

    # RBAC enforcement mode (PR 3). "shadow" audits denials but still
    # allows them through; "enforce" returns HTTP 403 on denial.
    RBAC_ENFORCEMENT_MODE: str = "shadow"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
