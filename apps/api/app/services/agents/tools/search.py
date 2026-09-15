"""Busca na web.

Dois providers, escolhidos por `WEB_SEARCH_PROVIDER`:

- `wikipedia` (padrão, **sem API key**) — busca na Wikipédia em português e
  devolve o resumo do melhor resultado + títulos relacionados.
- `tavily` (requer `TAVILY_API_KEY`) — busca web real, com URLs de verdade.

Escolha documentada: a API "Instant Answer" do DuckDuckGo foi testada e devolve
HTTP 202 com `AbstractText` vazio (rate-limit/challenge), então não é confiável
como provider sem chave. A Wikipédia responde HTTP 200 com conteúdo estável.
O texto retornado **avisa o modelo** que a fonte é enciclopédica, para ele não
afirmar que vasculhou a web inteira.
"""

import logging

import httpx
from langchain_core.tools import tool

from app.core.config import settings

logger = logging.getLogger(__name__)

WIKIPEDIA_SEARCH_URL = "https://pt.wikipedia.org/w/api.php"
WIKIPEDIA_SUMMARY_URL = "https://pt.wikipedia.org/api/rest_v1/page/summary/"
TAVILY_URL = "https://api.tavily.com/search"

_SOURCE_NOTE = (
    "Fonte: Wikipédia em português. Isso é uma busca enciclopédica, não a web "
    "inteira — se precisar de notícias ou dados muito recentes, avise o usuário."
)


async def _wikipedia_summary(client: httpx.AsyncClient, title: str) -> str:
    """Resumo do artigo; string vazia se não houver (sem derrubar a busca)."""
    response = await client.get(WIKIPEDIA_SUMMARY_URL + title)
    if response.status_code != 200:
        return ""
    return (response.json().get("extract") or "").strip()


async def _search_wikipedia(query: str) -> str:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srprop": "",
        "srlimit": settings.WEB_SEARCH_MAX_RESULTS,
        "format": "json",
    }
    async with httpx.AsyncClient(
        timeout=settings.WEB_SEARCH_TIMEOUT_SECONDS,
        headers={"User-Agent": settings.HTTP_USER_AGENT},
        follow_redirects=True,
    ) as client:
        response = await client.get(WIKIPEDIA_SEARCH_URL, params=params)
        response.raise_for_status()
        hits = (response.json().get("query") or {}).get("search") or []
        if not hits:
            return f"Não encontrei nada sobre \"{query}\"."

        top = hits[0].get("title", "")
        summary = await _wikipedia_summary(client, top)

        lines = [f"Sobre \"{query}\":", ""]
        lines.append(f"{top} — {summary}" if summary else f"{top} (sem resumo disponível).")

        others = [h.get("title") for h in hits[1:] if h.get("title")]
        if others:
            lines.append("")
            lines.append("Artigos relacionados: " + ", ".join(others) + ".")

        lines.append("")
        lines.append(_SOURCE_NOTE)
        return "\n".join(lines)


async def _search_tavily(query: str) -> str:
    if not settings.TAVILY_API_KEY:
        return (
            "Busca web via Tavily está selecionada, mas falta TAVILY_API_KEY no .env. "
            "Defina WEB_SEARCH_PROVIDER=wikipedia para usar a busca sem chave."
        )
    async with httpx.AsyncClient(
        timeout=settings.WEB_SEARCH_TIMEOUT_SECONDS,
        headers={"User-Agent": settings.HTTP_USER_AGENT},
    ) as client:
        response = await client.post(
            TAVILY_URL,
            json={
                "api_key": settings.TAVILY_API_KEY,
                "query": query,
                "max_results": settings.WEB_SEARCH_MAX_RESULTS,
            },
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        if not results:
            return f"Não encontrei nada sobre \"{query}\"."

        lines = [f"Resultados da web para \"{query}\":", ""]
        for item in results:
            title = item.get("title") or "Sem título"
            snippet = (item.get("content") or "").strip()
            url = item.get("url") or ""
            lines.append(f"- {title}: {snippet}")
            if url:
                lines.append(f"  {url}")
        return "\n".join(lines)


@tool
async def web_search(query: str) -> str:
    """Pesquisa informações na web. Use para fatos, pessoas, lugares, conceitos e qualquer coisa que você não tenha certeza ou que possa ter mudado depois do seu treinamento."""
    termo = (query or "").strip()
    if not termo:
        return "Preciso de um termo para pesquisar."

    provider = settings.WEB_SEARCH_PROVIDER.strip().lower()
    try:
        if provider == "tavily":
            return await _search_tavily(termo)
        return await _search_wikipedia(termo)
    except httpx.TimeoutException:
        logger.warning("Timeout na busca web (%s) por %r", provider, termo)
        return "A busca demorou demais para responder. Tenta de novo em instantes."
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "HTTP %s na busca web (%s) por %r",
            exc.response.status_code, provider, termo,
        )
        return "O serviço de busca respondeu com erro agora. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha inesperada na busca web por %r", termo)
        return "Não consegui pesquisar agora."
