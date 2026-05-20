from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///./data/warranty_ai.db", alias="DATABASE_URL")
    sample_data_dir: str = Field(default="./data/sample", alias="SAMPLE_DATA_DIR")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    llm_provider: str = Field(default="none", alias="LLM_PROVIDER")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def sample_path(self) -> Path:
        return Path(self.sample_data_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
