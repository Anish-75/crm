from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "WooCommerce CRM API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Supabase (PRD Section 2, 3, 7)
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., description="Supabase service role secret key")
    SUPABASE_ANON_KEY: str = Field(default="", description="Supabase anon public key")
    SUPABASE_JWT_SECRET: Optional[str] = Field(default=None, description="Optional Supabase JWT secret for local verification")

    # WooCommerce (PRD Section 6)
    WOO_BASE_URL: str = Field(default="", description="WooCommerce store base URL")
    WOO_CONSUMER_KEY: str = Field(default="", description="WooCommerce REST API Consumer Key")
    WOO_CONSUMER_SECRET: str = Field(default="", description="WooCommerce REST API Consumer Secret")
    WOO_WEBHOOK_SECRET: str = Field(default="", description="WooCommerce Webhook HMAC secret")

    # Email provider (PRD Section 8)
    EMAIL_PROVIDER: str = Field(default="resend", description="Email provider: resend or smtp")
    RESEND_API_KEY: str = Field(default="", description="Resend API key")

    # CORS (PRD Section 7, 10)
    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:5173",
        description="Allowed frontend origin(s), comma-separated if multiple",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated FRONTEND_ORIGIN into a list of origins for CORS middleware."""
        if not self.FRONTEND_ORIGIN:
            return ["http://localhost:5173"]
        return [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings."""
    return Settings()

