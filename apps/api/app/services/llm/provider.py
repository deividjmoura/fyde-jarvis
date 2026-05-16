from langchain_openai import ChatOpenAI
import os


DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
DEFAULT_MODEL = os.getenv(
    "LLM_MODEL",
    "anthropic/claude-3-haiku"
)


def get_llm(
    provider: str = None,
    model: str = None,
):

    provider = provider or DEFAULT_PROVIDER
    model = model or DEFAULT_MODEL

    if provider == "openrouter":

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY não encontrada"
            )

        return ChatOpenAI(
            model=model,
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            temperature=0.7,
        )

    raise ValueError(
        f"Provider inválido: {provider}"
    )