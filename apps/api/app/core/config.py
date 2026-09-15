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

    # Opcional: só é lido de verdade quando uma rota autenticada
    # (/agent/chat, /auth/me) é chamada. Com o default "{}" a API sobe e o
    # /agent/chat-test funciona normalmente; /chat devolve 401 explicando.
    FIREBASE_CREDENTIALS: str = "{}"

    # Origens permitidas no CORS, separadas por vírgula.
    # Inclua aqui a URL do frontend em produção.
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ---------- Tools do agente ----------
    # Tudo abaixo é OPCIONAL (tem padrão) — não precisa mexer no seu .env.

    # Fuso da tool de data/hora. A API roda em UTC na nuvem, então o padrão
    # é o fuso do usuário e não o relógio do servidor.
    JARVIS_TIMEZONE: str = "America/Sao_Paulo"

    # Clima (Open-Meteo — não exige API key).
    WEATHER_TIMEOUT_SECONDS: float = 10.0

    # Busca web: "wikipedia" (padrão, sem chave) ou "tavily" (exige chave).
    WEB_SEARCH_PROVIDER: str = "wikipedia"
    WEB_SEARCH_MAX_RESULTS: int = 3
    WEB_SEARCH_TIMEOUT_SECONDS: float = 10.0
    TAVILY_API_KEY: str = ""

    # User-Agent enviado a APIs públicas (a Wikipédia pede um identificável).
    HTTP_USER_AGENT: str = "FydeJarvis/1.0 (https://github.com/deividjmoura/fyde-jarvis)"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()