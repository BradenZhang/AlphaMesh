from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AlphaMesh"
    app_version: str = "0.1.0"
    environment: str = "development"

    database_url: str = "sqlite:///./alphamesh.db"
    live_auto_enabled: bool = False

    llm_provider: str = "mock"
    llm_model_name: str = "mock-research-v1"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_profiles_json: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    single_symbol_max_position_pct: float = Field(default=0.35, gt=0, le=1)
    max_order_amount: float = Field(default=100_000.0, gt=0)
    max_drawdown_threshold: float = Field(default=0.2, gt=0, le=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
