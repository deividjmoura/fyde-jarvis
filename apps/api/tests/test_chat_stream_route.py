"""Testes da rota SSE autenticada `POST /agent/chat-stream`.

Roda sem Postgres, Firebase nem LLM:
- a dependência `get_current_user` é sobrescrita por um usuário falso
  (`dependency_overrides` do FastAPI);
- o gerador `astream_agent_tokens` é trocado por um fake que **registra o
  thread_id recebido** e devolve tokens conhecidos — assim o teste prova o
  isolamento de memória por usuário sem tocar no LangGraph.

Convenções herdadas do arena-irmao: `asyncio_mode = auto` (sem marker) e
testes que fazem HTTP real são marcados `integration` (estes aqui usam
ASGITransport in-process, então são unitários).
"""

import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import agent as agent_routes
from app.dependencies.auth import get_current_user
from app.main import app


class FakeUser:
    """Mínimo de User que a rota usa: só o firebase_uid."""

    def __init__(self, uid: str):
        self.firebase_uid = uid
        self.email = f"{uid}@example.com"


def _eventos_sse(body: str) -> list[dict]:
    """Extrai os JSONs das linhas `data: ...` de uma resposta SSE."""
    eventos = []
    for linha in body.splitlines():
        linha = linha.strip()
        if linha.startswith("data: "):
            eventos.append(json.loads(linha[len("data: "):]))
    return eventos


@pytest.fixture
def fake_stream(monkeypatch):
    """Substitui o gerador de tokens; grava os thread_id chamados."""
    captura = {"thread_ids": [], "queries": []}

    async def fake_astream(query, thread_id):
        captura["thread_ids"].append(thread_id)
        captura["queries"].append(query)
        for pedaço in ["Olá, ", "operador", "!"]:
            yield pedaço

    monkeypatch.setattr(agent_routes, "astream_agent_tokens", fake_astream)
    return captura


async def test_chat_stream_autenticado_emite_tokens_e_done(fake_stream):
    app.dependency_overrides[get_current_user] = lambda: FakeUser("uid-777")
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/agent/chat-stream", json={"query": "saudação"}
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    # Desliga buffer de proxy (header do arena-deivid) tem que sobreviver.
    assert resp.headers.get("x-accel-buffering") == "no"

    eventos = _eventos_sse(resp.text)
    assert [e["type"] for e in eventos] == ["token", "token", "token", "done"]

    texto = "".join(e["content"] for e in eventos if e["type"] == "token")
    assert texto == "Olá, operador!"
    # Acentuação não pode virar lixo (UTF-8 é o contrato do SSE).
    assert "Olá" in resp.text


async def test_chat_stream_isola_thread_id_por_usuario(fake_stream):
    app.dependency_overrides[get_current_user] = lambda: FakeUser("uid-abc")
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/agent/chat-stream", json={"query": "oi"})
    finally:
        app.dependency_overrides.clear()

    # A rota autenticada NÃO pode usar o thread fixo "test_user_123".
    assert fake_stream["thread_ids"] == ["user_uid-abc"]
    assert fake_stream["queries"] == ["oi"]


async def test_chat_stream_sem_token_retorna_401(fake_stream):
    # Sem dependency_overrides: a dependência real exige o header e nega
    # antes de chegar no gerador — que, portanto, não pode ter sido chamado.
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/agent/chat-stream", json={"query": "oi"}
        )

    assert resp.status_code == 401
    assert fake_stream["thread_ids"] == []


async def test_chat_stream_emite_evento_error_quando_gerador_falha(monkeypatch):
    async def stream_que_falha(query, thread_id):
        raise RuntimeError("boom no cérebro")
        yield  # marca a função como async generator (inalcançável)

    monkeypatch.setattr(
        agent_routes, "astream_agent_tokens", stream_que_falha
    )

    app.dependency_overrides[get_current_user] = lambda: FakeUser("uid-1")
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/agent/chat-stream", json={"query": "oi"}
            )
    finally:
        app.dependency_overrides.clear()

    # SSE abre 200; a falha navega como evento `error` (contrato existente).
    assert resp.status_code == 200
    eventos = _eventos_sse(resp.text)
    assert eventos and eventos[-1]["type"] == "error"
    assert "boom" in eventos[-1]["detail"]
