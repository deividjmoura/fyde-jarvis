from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Carrega apps/api/.env para os.environ ANTES de tudo —
# o provider de LLM (services/llm/provider.py) lê via os.getenv.
load_dotenv()


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