from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")


    openai_api_key: str = ""          
    llm_model_name: str = "gpt-4.1-mini"
    env: str = "dev"
    prompt_version: str = "v1"
    langsmith_api_key: str | None = None
    langsmith_project: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
