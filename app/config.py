from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./data/biotech.db"
    session_secret: str = "change-this-for-local-development"
    jwt_secret: str = "local-jwt-secret-change-before-deployment-please"
    jwt_expiry_minutes: int = 60 * 12
    dev_auth: bool = False
    identifiable_records_enabled: bool = False
    patient_field_encryption_key: str = ""
    max_upload_mb: int = 20
    local_upload_dir: str = "./data/uploads"
    aws_region: str = "eu-west-1"
    s3_bucket: str = ""
    sqs_job_queue_url: str = ""
    ai_enabled: bool = False
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_monthly_request_limit: int = 100
    allowed_origins: str = "http://localhost:8000"
    editor_emails: str = ""

    @property
    def resolved_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://"):]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def validate_runtime_settings() -> None:
    if settings.app_env == "production":
        if settings.dev_auth:
            raise RuntimeError("DEV_AUTH must be false in production")
        if len(settings.session_secret) < 32 or settings.session_secret == "change-this-for-local-development":
            raise RuntimeError("SESSION_SECRET must be a unique value of at least 32 characters in production")
        if len(settings.jwt_secret) < 32 or settings.jwt_secret.startswith("local-jwt-secret"):
            raise RuntimeError("JWT_SECRET must be a unique random value of at least 32 characters")
        if not settings.resolved_database_url.startswith("postgresql+"):
            raise RuntimeError("Configure DATABASE_URL with your Neon PostgreSQL connection string")
        if settings.identifiable_records_enabled and not settings.patient_field_encryption_key:
            raise RuntimeError("Patient field encryption key is required when identifiable records are enabled")
        if settings.ai_enabled:
            from urllib.parse import urlparse
            if not all((settings.ai_base_url, settings.ai_api_key, settings.ai_model)):
                raise RuntimeError("AI provider configuration is incomplete")
            if urlparse(settings.ai_base_url).scheme != "https":
                raise RuntimeError("Production AI_BASE_URL must use HTTPS")
