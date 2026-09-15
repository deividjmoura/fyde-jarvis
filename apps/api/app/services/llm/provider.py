import logging
import os

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
DEFAULT_MODEL = os.getenv(
    "LLM_MODEL",
    "anthropic/claude-3-haiku"
)

# === Ollama (modo 100% local/offline) ===
# Requer `ollama serve` rodando (https://ollama.com) — sem chave, sem custo.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


def _ollama_llm(model: str = None) -> ChatOpenAI:
    """LLM local via Ollama (expõe API compatível com OpenAI; a chave é
    exigida pelo client mas ignorada pelo Ollama)."""
    return ChatOpenAI(
        model=model or OLLAMA_MODEL,
        base_url=f"{OLLAMA_BASE_URL.rstrip('/')}/v1",
        api_key="ollama",
        temperature=0.7,
    )


def _openrouter_llm(model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],  # validado antes por get_llm
        temperature=0.7,
    )


def get_llm(
    provider: str = None,
    model: str = None,
):
    """Retorna o LLM configurado.

    - `LLM_PROVIDER=openrouter` (padrão): nuvem, precisa de OPENROUTER_API_KEY.
      Sem a chave → **fallback automático para Ollama local** (modo offline).
    - `LLM_PROVIDER=ollama`: 100% local. Rode `ollama serve` antes.
    """
    provider = provider or DEFAULT_PROVIDER
    model = model or DEFAULT_MODEL

    if provider == "openrouter":
        if not os.getenv("OPENROUTER_API_KEY"):
            logger.warning(
                "⚠️  OPENROUTER_API_KEY não definida — usando Ollama local "
                "(%s) como fallback offline. "
                "Garanta `ollama serve` rodando.", OLLAMA_MODEL,
            )
            return _ollama_llm()

        return _openrouter_llm(model)

    if provider == "ollama":
        # DEFAULT_MODEL é um modelo de nuvem; no modo local usa OLLAMA_MODEL
        return _ollama_llm(model if model != DEFAULT_MODEL else None)

    raise ValueError(
        f"Provider inválido: {provider}"
    )
