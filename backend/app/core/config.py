from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AlphaMesh"
    app_version: str = "0.1.0"
    environment: str = "development"

    database_url: str = "sqlite:///./alphamesh.db"
    live_auto_enabled: bool = False

    default_market_provider: str = "mock"
    default_execution_provider: str = "mock"
    default_account_provider: str = "mock"

    llm_provider: str = "mock"
    llm_model_name: str = "mock-research-v1"
    llm_base_url: str | None = None
    llm_api_key: SecretStr | None = None
    llm_profiles_json: str | None = None
    llm_timeout: float = Field(default=60.0, gt=0)
    llm_max_retries: int = Field(default=3, ge=0)
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None

    longbridge_transport: str = "cli"
    longbridge_cli_path: str = "longbridge"
    longbridge_mcp_url: str | None = None

    futu_transport: str = "opend"
    futu_opend_host: str = "127.0.0.1"
    futu_opend_port: int = 11111
    futu_trd_env: str = "SIMULATE"

    eastmoney_transport: str = "api"
    eastmoney_base_url: str | None = None
    eastmoney_api_key: SecretStr | None = None

    ibkr_transport: str = "client_portal"
    ibkr_base_url: str | None = None
    ibkr_account_id: str | None = None

    scheduler_simple_profile: str | None = None
    scheduler_moderate_profile: str | None = None
    scheduler_complex_profile: str | None = None

    single_symbol_max_position_pct: float = Field(default=0.35, gt=0, le=1)
    max_order_amount: float = Field(default=100_000.0, gt=0)
    max_drawdown_threshold: float = Field(default=0.2, gt=0, le=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
