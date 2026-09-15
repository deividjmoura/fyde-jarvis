"""Tools do GitHub, com HTTP mockado via respx."""

import base64

import httpx
import pytest
import respx

from app.services.agents.tools import github

REPO = "deividjmoura/fyde-jarvis"

REPO_INFO = {
    "full_name": REPO,
    "description": "Assistente de voz e chat auto-hospedado",
    "stargazers_count": 3,
    "forks_count": 1,
    "open_issues_count": 2,
    "language": "Python",
    "license": {"spdx_id": "MIT"},
    "default_branch": "main",
    "created_at": "2026-07-01T12:00:00Z",
    "pushed_at": "2026-09-15T15:00:00Z",
    "topics": ["agente", "langgraph", "voz"],
    "html_url": "https://github.com/deividjmoura/fyde-jarvis",
}

DIR_LISTING = [
    {"name": "apps", "type": "dir", "size": 0},
    {"name": "voice-client", "type": "dir", "size": 0},
    {"name": "README.md", "type": "file", "size": 4200},
    {"name": "AGENT_SYNC.md", "type": "file", "size": 9100},
]

FILE_B64 = {
    "name": "README.md",
    "size": 13,
    "encoding": "base64",
    "content": base64.b64encode("Olá, Jarvis!".encode()).decode(),
}

SEARCH_HITS = {
    "items": [
        {"full_name": "rhasspy/piper", "stargazers_count": 1000,
         "language": "C++", "description": "TTS neural local e rápido para o Raspberry Pi"},
        {"full_name": "langchain-ai/langgraph", "stargazers_count": 9000,
         "language": "Python", "description": "Grafos de agentes com LangChain"},
    ]
}


# --------------------------- github_repo_info ------------------------------
@respx.mock
async def test_repo_info_sucesso():
    respx.get(f"{github.GITHUB_API}/repos/{REPO}").mock(
        return_value=httpx.Response(200, json=REPO_INFO))
    respx.get(f"{github.GITHUB_API}/repos/{REPO}/languages").mock(
        return_value=httpx.Response(200, json={"Python": 80000, "TypeScript": 20000}))

    saida = await github.github_repo_info.ainvoke({"repo": REPO})

    assert REPO in saida
    assert "Estrelas: 3 · Forks: 1" in saida
    assert "Python, TypeScript" in saida
    assert "MIT" in saida
    assert "langgraph" in saida


@respx.mock
async def test_repo_info_sem_linguagens_nao_quebra():
    respx.get(f"{github.GITHUB_API}/repos/{REPO}").mock(
        return_value=httpx.Response(200, json=REPO_INFO))
    respx.get(f"{github.GITHUB_API}/repos/{REPO}/languages").mock(
        return_value=httpx.Response(404, json={}))

    saida = await github.github_repo_info.ainvoke({"repo": REPO})
    assert "Python" in saida  # cai no campo `language` do repo


@respx.mock
async def test_repo_inexistente_mensagem_amigavel():
    respx.get(url__startswith=f"{github.GITHUB_API}/repos/").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"}))

    saida = await github.github_repo_info.ainvoke({"repo": "ninguem/inexistente"})
    assert "Não encontrei" in saida and "privado" in saida


async def test_repo_formato_invalido():
    saida = await github.github_repo_info.ainvoke({"repo": "só-um-nome"})
    assert "Formato inválido" in saida
    assert "dono/nome" in saida


# --------------------------- github_list_files -----------------------------
@respx.mock
async def test_list_files_pastas_primeiro():
    respx.get(f"{github.GITHUB_API}/repos/{REPO}/contents/").mock(
        return_value=httpx.Response(200, json=DIR_LISTING))

    saida = await github.github_list_files.ainvoke({"repo": REPO, "path": ""})

    idx_apps = saida.index("apps")
    idx_readme = saida.index("README.md")
    assert idx_apps < idx_readme  # 📁 antes de 📄
    assert "AGENT_SYNC.md" in saida


@respx.mock
async def test_list_files_aponta_para_arquivo():
    respx.get(f"{github.GITHUB_API}/repos/{REPO}/contents/README.md").mock(
        return_value=httpx.Response(200, json={"type": "file", "name": "README.md"}))

    saida = await github.github_list_files.ainvoke({"repo": REPO, "path": "README.md"})
    assert "é um arquivo" in saida


# --------------------------- github_read_file ------------------------------
@respx.mock
async def test_read_file_decodifica_base64():
    respx.get(f"{github.GITHUB_API}/repos/{REPO}/contents/README.md").mock(
        return_value=httpx.Response(200, json=FILE_B64))

    saida = await github.github_read_file.ainvoke({"repo": REPO, "path": "README.md"})
    assert "Olá, Jarvis!" in saida


@respx.mock
async def test_read_file_trunca_arquivos_grandes(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "GITHUB_MAX_FILE_CHARS", 50)
    payload = dict(FILE_B64)
    payload["content"] = base64.b64encode(("x" * 500).encode()).decode()
    respx.get(f"{github.GITHUB_API}/repos/{REPO}/contents/grande.txt").mock(
        return_value=httpx.Response(200, json=payload))

    saida = await github.github_read_file.ainvoke({"repo": REPO, "path": "grande.txt"})
    assert "arquivo cortado em 50 caracteres" in saida


@respx.mock
async def test_rate_limit_orienta_configurar_token(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "")
    respx.get(url__startswith=f"{github.GITHUB_API}/repos/").mock(
        return_value=httpx.Response(
            403, json={"message": "rate limit"},
            headers={"X-RateLimit-Remaining": "0"}))

    saida = await github.github_repo_info.ainvoke({"repo": REPO})
    assert "rate limit" in saida.lower()
    assert "GITHUB_TOKEN" in saida


@respx.mock
async def test_token_configurado_vai_no_header(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "ghp_teste123")
    route = respx.get(f"{github.GITHUB_API}/repos/{REPO}").mock(
        return_value=httpx.Response(200, json=REPO_INFO))
    respx.get(f"{github.GITHUB_API}/repos/{REPO}/languages").mock(
        return_value=httpx.Response(200, json={}))

    await github.github_repo_info.ainvoke({"repo": REPO})
    assert route.calls[0].request.headers["Authorization"] == "Bearer ghp_teste123"


# --------------------------- github_search_repos ---------------------------
@respx.mock
async def test_search_retorna_ranking():
    respx.get(f"{github.GITHUB_API}/search/repositories").mock(
        return_value=httpx.Response(200, json=SEARCH_HITS))

    saida = await github.github_search_repos.ainvoke({"query": "tts local"})
    assert "rhasspy/piper" in saida
    assert "⭐ 1000" in saida
    assert "analise" in saida  # convite ao próximo passo


@respx.mock
async def test_search_vazio():
    respx.get(f"{github.GITHUB_API}/search/repositories").mock(
        return_value=httpx.Response(200, json={"items": []}))

    saida = await github.github_search_repos.ainvoke({"query": "xyzabc"})
    assert "Não achei repositórios" in saida
