"""Configuration centralisée, lue depuis l'environnement (.env)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    ENV: str = "development"
    APP_NAME: str = "ScanToExcel API"
    API_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://scantoexcel:scantoexcel@localhost:5432/scantoexcel"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth (Supabase-issued JWTs, verified with the project's JWT secret)
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = "change-me"
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    # Object storage (S3-compatible: AWS S3, Cloudflare R2, Supabase Storage)
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "auto"
    S3_BUCKET: str = "scantoexcel-documents"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_PUBLIC_BASE_URL: str = ""

    # Extraction (Claude, multimodal)
    ANTHROPIC_API_KEY: str = ""
    EXTRACTION_MODEL: str = "claude-sonnet-4-6"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PERSONAL: str = ""
    STRIPE_PRICE_ID_PRO: str = ""

    # Limites d'usage (plan gratuit)
    FREE_PLAN_PAGES_PER_MONTH: int = 20

    # Upload
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB
    ALLOWED_UPLOAD_TYPES: tuple[str, ...] = (
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    )
    ORIGINAL_FILE_RETENTION_HOURS: int = 24  # suppression auto après ce délai


@lru_cache
def get_settings() -> Settings:
    return Settings()
