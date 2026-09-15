"""Leitura de repositórios do GitHub.

Quatro tools sobre a API REST pública (api.github.com):

- `github_repo_info`   — metadados do repo (descrição, estrelas, linguagens…)
- `github_list_files`  — estrutura de pastas/arquivos
- `github_read_file`   — conteúdo de um arquivo (com limite de caracteres)
- `github_search_repos`— busca projetos no GitHub

Sem `GITHUB_TOKEN` funciona para repositórios públicos com rate limit baixo
(60 req/h por IP). Com o token (Settings → Developer settings → PAT, escopo
`repo` para privados), sobe para 5.000 req/h e lê privados. O token fica no
`.env` do servidor — nunca o exponha nas respostas ao usuário.
"""

import base64
import logging
import re

import httpx
from langchain_core.tools import tool

from app.core.config import settings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
_REPO_RE = re.compile(r"^[\w.\-]+/[\w.\-]+$")


def _headers(raw: bool = False) -> dict:
    headers = {
        "User-Agent": settings.HTTP_USER_AGENT,
        "Accept": ("application/vnd.github.raw+json" if raw
                   else "application/vnd.github+json"),
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return headers


def _repo_valido(repo: str) -> str | None:
    """Devolve mensagem de erro se o formato não for `dono/nome`."""
    if not repo or not _REPO_RE.match(repo.strip()):
        return (
            f"Formato inválido: {repo!r}. Me passe no padrão "
            "`dono/nome` — por exemplo, `deividjmoura/fyde-jarvis`."
        )
    return None


def _mensagem_de_status(exc: httpx.HTTPStatusError, alvo: str) -> str:
    code = exc.response.status_code
    if code == 404:
        return (
            f"Não encontrei {alvo} no GitHub. Ele existe e é público? "
            "Se for privado, o servidor precisa de um GITHUB_TOKEN com acesso."
        )
    if code in (401, 403):
        if exc.response.headers.get("X-RateLimit-Remaining") == "0":
            return (
                "Estamos sem crédito de chamadas na API do GitHub agora "
                "(rate limit). Configurar GITHUB_TOKEN no servidor resolve — "
                "sobe de 60 para 5.000 chamadas por hora."
            )
        return (
            f"O GitHub negou acesso a {alvo} (HTTP {code}). Sem token válido "
            "ou sem permissão para este repositório."
        )
    return f"O GitHub respondeu com erro {code} para {alvo}. Tenta de novo em instantes."


async def _chama(client: httpx.AsyncClient, path: str, *,
                 raw: bool = False, params: dict | None = None) -> httpx.Response:
    response = await client.get(f"{GITHUB_API}{path}",
                                headers=_headers(raw), params=params)
    response.raise_for_status()
    return response


@tool
async def github_repo_info(repo: str) -> str:
    """Obtém informações gerais de um repositório do GitHub: descrição, estrelas, forks, linguagem principal, licença, data do último push e tópicos. Use para resumos rápidos sobre projetos. O argumento deve ser `dono/nome`."""
    if erro := _repo_valido(repo):
        return erro
    repo = repo.strip()

    try:
        async with httpx.AsyncClient(
            timeout=settings.GITHUB_TIMEOUT_SECONDS,
            headers=_headers(),
            follow_redirects=True,
        ) as client:
            data = (await _chama(client, f"/repos/{repo}")).json()
            try:
                linguagens = (await _chama(client, f"/repos/{repo}/languages")).json()
            except httpx.HTTPError:
                linguagens = {}
    except httpx.HTTPStatusError as exc:
        return _mensagem_de_status(exc, f"o repositório `{repo}`")
    except httpx.TimeoutException:
        return "O GitHub demorou demais para responder. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha inesperada lendo repo %s", repo)
        return "Não consegui consultar o GitHub agora."

    langs = ", ".join(linguagens.keys()) or data.get("language") or "não detectada"
    licensed = (data.get("license") or {}).get("spdx_id") or "sem licença definida"
    topicos = ", ".join(data.get("topics") or []) or "nenhum"

    return (
        f"Repositório {data['full_name']}\n"
        f"- Descrição: {data.get('description') or 'sem descrição'}\n"
        f"- Estrelas: {data.get('stargazers_count', 0)} · Forks: {data.get('forks_count', 0)} "
        f"· Issues abertas: {data.get('open_issues_count', 0)}\n"
        f"- Linguagens: {langs}\n"
        f"- Licença: {licensed} · Branch padrão: {data.get('default_branch', 'main')}\n"
        f"- Criado: {str(data.get('created_at', ''))[:10]} · Último push: {str(data.get('pushed_at', ''))[:10]}\n"
        f"- Tópicos: {topicos}\n"
        f"- URL: {data.get('html_url', '')}"
    )


@tool
async def github_list_files(repo: str, path: str = "") -> str:
    """Lista os arquivos e pastas de um caminho do repositório (a raiz se `path` for vazio). Use para entender a estrutura do projeto antes de ler arquivos. `repo` no formato `dono/nome`; `path` opcional (ex.: `src` ou `apps/api`)."""
    if erro := _repo_valido(repo):
        return erro
    repo, path = repo.strip(), path.strip().strip("/")

    try:
        async with httpx.AsyncClient(
            timeout=settings.GITHUB_TIMEOUT_SECONDS,
            headers=_headers(),
            follow_redirects=True,
        ) as client:
            data = (await _chama(client, f"/repos/{repo}/contents/{path}")).json()
    except httpx.HTTPStatusError as exc:
        return _mensagem_de_status(exc, f"`{path or '/'}` em `{repo}`")
    except httpx.TimeoutException:
        return "O GitHub demorou demais para responder. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha inesperada listando %s:%s", repo, path)
        return "Não consegui listar os arquivos agora."

    if isinstance(data, dict):  # um arquivo único, não uma lista de dir
        return (
            f"`{path}` é um arquivo, não uma pasta — use a tool de leitura "
            "para ver o conteúdo."
        )

    linhas = [f"Conteúdo de /{path or ''} em {repo}:"]
    for item in sorted(data, key=lambda i: (i["type"] != "dir", i["name"])):
        icone = "📁" if item["type"] == "dir" else "📄"
        tamanho = "" if item["type"] == "dir" else f" ({item.get('size', 0)} B)"
        linhas.append(f"{icone} {item['name']}{tamanho}")
    return "\n".join(linhas)


@tool
async def github_read_file(repo: str, path: str) -> str:
    """Lê o conteúdo de um arquivo do repositório (README, código-fonte, configs). Use depois de mapear a estrutura com listar arquivos. Requer `repo` (`dono/nome`) e `path` (ex.: `README.md` ou `src/main.py`)."""
    if erro := _repo_valido(repo):
        return erro
    if not path.strip():
        return "Preciso do caminho do arquivo (ex.: README.md)."
    repo, path = repo.strip(), path.strip().strip("/")

    try:
        async with httpx.AsyncClient(
            timeout=settings.GITHUB_TIMEOUT_SECONDS,
            headers=_headers(),
            follow_redirects=True,
        ) as client:
            data = (await _chama(client, f"/repos/{repo}/contents/{path}")).json()
    except httpx.HTTPStatusError as exc:
        return _mensagem_de_status(exc, f"`{path}` em `{repo}`")
    except httpx.TimeoutException:
        return "O GitHub demorou demais para responder. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha inesperada lendo %s:%s", repo, path)
        return "Não consegui ler o arquivo agora."

    if not isinstance(data, dict) or "content" not in data:
        return f"`{path}` parece ser uma pasta, não um arquivo. Liste os arquivos para escolher um."

    if data.get("encoding") == "base64":
        texto = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    else:
        texto = data.get("content", "")

    limite = settings.GITHUB_MAX_FILE_CHARS
    corte = ""
    if len(texto) > limite:
        texto = texto[:limite]
        corte = (f"\n\n[… arquivo cortado em {limite} caracteres; "
                 "peça outro trecho informando a linha aproximada.]")

    return f"Arquivo {path} ({data.get('size', '?')} B) de {repo}:\n\n{texto}{corte}"


@tool
async def github_search_repos(query: str) -> str:
    """Busca repositórios públicos no GitHub por termo (nome, descrição, tópico). Devolve os mais relevantes com estrelas e descrição, para você escolher qual analisar em seguida."""
    if not query.strip():
        return "Preciso de um termo para buscar repositórios."

    try:
        async with httpx.AsyncClient(
            timeout=settings.GITHUB_TIMEOUT_SECONDS,
            headers=_headers(),
            follow_redirects=True,
        ) as client:
            data = (await _chama(client, "/search/repositories", params={
                "q": query.strip(),
                "per_page": 5,
                "sort": "stars",
            })).json()
    except httpx.HTTPStatusError as exc:
        return _mensagem_de_status(exc, f"a busca `{query}`")
    except httpx.TimeoutException:
        return "O GitHub demorou demais para responder. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha inesperada buscando %r", query)
        return "Não consegui buscar repositórios agora."

    itens = data.get("items") or []
    if not itens:
        return f"Não achei repositórios para \"{query}\"."

    linhas = [f"Top resultados do GitHub para \"{query}\":"]
    for i, repo in enumerate(itens, 1):
        desc = (repo.get("description") or "sem descrição")[:120]
        linhas.append(
            f"{i}. **{repo['full_name']}** ⭐ {repo.get('stargazers_count', 0)} "
            f"· {repo.get('language') or '?'}\n   {desc}"
        )
    linhas.append("\nMe diga qual deles você quer que eu analise pelos próximos passos.")
    return "\n".join(linhas)
