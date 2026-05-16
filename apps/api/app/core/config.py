from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Fyde Jarvis"

    DATABASE_URL: str

    OPENROUTER_API_KEY: str

    SECRET_KEY: str

    FIREBASE_CREDENTIALS: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()