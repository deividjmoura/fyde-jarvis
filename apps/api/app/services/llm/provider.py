from langchain_openai import ChatOpenAI
import os


def get_llm(provider: str = "openrouter", model: str = None):

    if provider == "openrouter":

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY não encontrada")

        return ChatOpenAI(
            model=model or "anthropic/claude-3-haiku",
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            temperature=0.7,
        )

    raise ValueError(f"Provider inválido: {provider}")