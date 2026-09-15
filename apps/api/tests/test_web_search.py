"""Tool de busca web, nos dois providers, com HTTP mockado."""

import httpx
import pytest
import respx

from app.core.config import settings
from app.services.agents.tools import search

WIKI_HITS = {
    "query": {
        "search": [
            {"title": "Itajaí"},
            {"title": "Rio Itajaí-Açu"},
            {"title": "Porto de Itajaí"},
        ]
    }
}

WIKI_SUMMARY = {
    "title": "Itajaí",
    "extract": "Itajaí é um município brasileiro localizado no estado de Santa Catarina.",
}


@pytest.fixture
def wikipedia_provider(monkeypatch):
    monkeypatch.setattr(settings, "WEB_SEARCH_PROVIDER", "wikipedia")
    monkeypatch.setattr(settings, "WEB_SEARCH_MAX_RESULTS", 3)


@pytest.fixture
def tavily_provider(monkeypatch):
    monkeypatch.setattr(settings, "WEB_SEARCH_PROVIDER", "tavily")


@respx.mock
async def test_wikipedia_devolve_resumo_e_relacionados(wikipedia_provider):
    respx.get(search.WIKIPEDIA_SEARCH_URL).mock(
        return_value=httpx.Response(200, json=WIKI_HITS)
    )
    respx.get(url__startswith=search.WIKIPEDIA_SUMMARY_URL).mock(
        return_value=httpx.Response(200, json=WIKI_SUMMARY)
    )

    saida = await search.web_search.ainvoke({"query": "Itajaí"})

    assert "Itajaí — Itajaí é um município brasileiro" in saida
    assert "Rio Itajaí-Açu" in saida and "Porto de Itajaí" in saida
    # O texto precisa avisar o modelo de que não é a web inteira.
    assert "Wikipédia" in saida and "não a web inteira" in saida


@respx.mock
async def test_wikipedia_sem_resultados(wikipedia_provider):
    respx.get(search.WIKIPEDIA_SEARCH_URL).mock(
        return_value=httpx.Response(200, json={"query": {"search": []}})
    )

    saida = await search.web_search.ainvoke({"query": "xyzabc123"})

    assert 'Não encontrei nada sobre "xyzabc123"' in saida


@respx.mock
async def test_wikipedia_artigo_sem_resumo(wikipedia_provider):
    respx.get(search.WIKIPEDIA_SEARCH_URL).mock(
        return_value=httpx.Response(200, json={"query": {"search": [{"title": "X"}]}})
    )
    respx.get(url__startswith=search.WIKIPEDIA_SUMMARY_URL).mock(
        return_value=httpx.Response(404)
    )

    saida = await search.web_search.ainvoke({"query": "X"})

    assert "sem resumo disponível" in saida


async def test_consulta_vazia_nao_chama_rede(wikipedia_provider):
    assert "Preciso de um termo" in await search.web_search.ainvoke({"query": "  "})


async def test_tavily_sem_chave_explica_o_problema(tavily_provider, monkeypatch):
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "")

    saida = await search.web_search.ainvoke({"query": "jarvis"})

    assert "TAVILY_API_KEY" in saida


@respx.mock
async def test_tavily_com_chave(tavily_provider, monkeypatch):
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "tvly-teste")
    respx.post(search.TAVILY_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Fyde Jarvis",
                        "content": "Assistente híbrido.",
                        "url": "https://exemplo.com/jarvis",
                    }
                ]
            },
        )
    )

    saida = await search.web_search.ainvoke({"query": "jarvis"})

    assert "Fyde Jarvis" in saida
    assert "https://exemplo.com/jarvis" in saida


@respx.mock
async def test_erro_http_vira_mensagem_amigavel(wikipedia_provider):
    respx.get(search.WIKIPEDIA_SEARCH_URL).mock(
        return_value=httpx.Response(500)
    )

    saida = await search.web_search.ainvoke({"query": "qualquer coisa"})

    assert "respondeu com erro" in saida


@respx.mock
async def test_timeout_vira_mensagem_amigavel(wikipedia_provider):
    respx.get(search.WIKIPEDIA_SEARCH_URL).mock(
        side_effect=httpx.ConnectTimeout("boom")
    )

    saida = await search.web_search.ainvoke({"query": "qualquer coisa"})

    assert "demorou demais" in saida
