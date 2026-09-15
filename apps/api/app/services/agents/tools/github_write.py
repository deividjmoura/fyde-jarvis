"""Escrita no GitHub — o "modo agente" do Jarvis deployado.

Dá ao agente a capacidade de contribuir código via API REST **sem precisar de
shell**: criar branch, commitar arquivo, abrir Pull Request e acompanhar o CI
(leitura) até ficar verde — o mesmo fluxo humano, só que LLM-acelerado.

Segurança, na mesma ordem em que é aplicada:

1. **OFF por padrão**: nada escreve enquanto `GITHUB_WRITE_ENABLED=false`.
2. Só funciona com `GITHUB_TOKEN` configurado (Contents+PR scopes).
3. **Nunca commita em branch protegida** (main/master/prod/develop) nem abre
   PR a partir delas — o fluxo é sempre branch → PR, como no AGENT_SYNC.md.
4. Mensagens de commit **validadas** contra Conventional Commits (o commitlint
   do CI reprovariá-las de qualquer forma, e o trailer `Co-authored-by`
   garante o crédito do humano que supervisiona).
5. Erros da API (409/422/412) devolvem explicações úteis ao modelo em PT-BR.

Guardrails atuais cobrem o MVP; um futuro "agente 4" completo acrescenta:
árvore inteira por commit (Git Trees API), rebase e comentários em PR.
"""

import base64
import logging
import re

import httpx
from langchain_core.tools import tool

from app.core.config import settings

from app.services.agents.tools.github import (
    GITHUB_API,
    _headers,
    _mensagem_de_status,
    _repo_valido,
)

logger = logging.getLogger(__name__)

# Branches onde o agente NUNCA escreve nem abre PR (regra dura do protocolo).
PROTECTED_BRANCHES = {"main", "master", "prod", "production", "develop"}

_CONVENTIONAL_RE = re.compile(
    r"^(feat|fix|docs|chore|ci|test|refactor|perf|style|sync|build|revert)"
    r"(\([\w.\-/]+\))?!?:\s+\S"
)
_COAUTHOR = "\n\nCo-authored-by: Deivid <86139999+deividjmoura@users.noreply.github.com>"


def _guard_write(alvo_branch: str | None = None) -> str | None:
    """Devolve mensagem de bloqueio quando a escrita não deve acontecer."""
    if not settings.GITHUB_WRITE_ENABLED:
        return (
            "A escrita no GitHub está DESATIVADA neste servidor "
            "(GITHUB_WRITE_ENABLED=false). Esse é um modo opt-in do dono do "
            "projeto — peça a ele para ativar quando quiser que eu contribua."
        )
    if not settings.GITHUB_TOKEN:
        return (
            "Escrita ativada, mas falta GITHUB_TOKEN no servidor com escopo "
            "de conteúdo/PR. Sem isso não consigo assinar commits."
        )
    if alvo_branch and alvo_branch.strip().lower() in PROTECTED_BRANCHES:
        return (
            f"Bloqueado por regra dura: **nunca** commito nem abro PR a partir "
            f"de `{alvo_branch}`. Crie uma branch de trabalho (ex.: "
            "`agente/minha-mudanca`), commite nela e abra o PR para revisão."
        )
    return None


def _mensagem_erro_escrita(exc: httpx.HTTPStatusError, alvo: str) -> str:
    code = exc.response.status_code
    if code == 422:
        return (
            f"O GitHub recusou {alvo} (422). Normalmente significa que já "
            "existe (branch/PR duplicado) ou falta algo no payload — "
            "tenta outro nome de branch ou verifique se já não está aberto."
        )
    if code == 409:
        return (
            f"Conflito de versão em {alvo} (409): alguém alterou o mesmo "
            "recurso entre a leitura e a escrita. Releia o estado atual e tente de novo."
        )
    if code == 412:
        return (
            f"Condição prévia falhou em {alvo} (412). A referência base mudou — "
            "releia a branch atual antes de recriar."
        )
    return _mensagem_de_status(exc, alvo)


# --------------------------------------------------------------------------
# 1. Criar branch
# --------------------------------------------------------------------------
@tool
async def github_create_branch(repo: str, branch: str, from_branch: str = "main") -> str:
    """Cria uma branch nova no repositório a partir de `from_branch` (padrão main). Use SEMPRE antes de commitar: o trabalho do agente acontece em branches, nunca na main direto."""
    if erro := _guard_write(branch):
        return erro
    if erro := _repo_valido(repo):
        return erro
    repo, branch = repo.strip(), branch.strip().replace(" ", "-")

    try:
        async with httpx.AsyncClient(
            timeout=settings.GITHUB_TIMEOUT_SECONDS,
            headers=_headers(),
            follow_redirects=True,
        ) as client:
            base = await client.get(f"{GITHUB_API}/repos/{repo}/git/ref/heads/{from_branch}")
            base.raise_for_status()
            sha = base.json()["object"]["sha"]
            resp = await client.post(
                f"{GITHUB_API}/repos/{repo}/git/refs",
                json={"ref": f"refs/heads/{branch}", "sha": sha},
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return _mensagem_erro_escrita(exc, f"criar a branch `{branch}`")
    except httpx.TimeoutException:
        return "O GitHub demorou demais. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha criando branch %s em %s", branch, repo)
        return "Não consegui criar a branch agora."

    return (f"Branch `{branch}` criada em {repo} a partir de `{from_branch}` "
            f"(sha {sha[:7]}). Agora commite nela com github_commit_file.")


# --------------------------------------------------------------------------
# 2. Commitar arquivo
# --------------------------------------------------------------------------
@tool
async def github_commit_file(repo: str, branch: str, path: str,
                             content: str, message: str) -> str:
    """Cria ou atualiza UM arquivo em uma branch de trabalho do repositório (conteúdo completo, não diff). A mensagem DEVE seguir Conventional Commits (ex.: `docs(readme): corrige typo no título`) — o CI reprova colocar só 'update x'."""
    if erro := _guard_write(branch):
        return erro
    if erro := _repo_valido(repo):
        return erro
    if not path.strip() or path.strip().endswith("/"):
        return "Preciso de um caminho de arquivo válido (ex.: docs/guia.md)."
    if not _CONVENTIONAL_RE.match(message.strip()):
        return (
            "Mensagem de commit fora do padrão Conventional Commits. Use "
            "`tipo(escopo): descrição` — ex.: `fix(api): trata timeout no clima`."
        )

    mensagem_final = message.strip() + _COAUTHOR

    try:
        async with httpx.AsyncClient(
            timeout=settings.GITHUB_TIMEOUT_SECONDS,
            headers=_headers(),
            follow_redirects=True,
        ) as client:
            atual = await client.get(
                f"{GITHUB_API}/repos/{repo}/contents/{path.strip()}",
                params={"ref": branch.strip()},
            )
            sha_existente = None
            if atual.status_code == 200:
                sha_existente = atual.json().get("sha")
            elif atual.status_code != 404:
                atual.raise_for_status()

            payload = {
                "message": mensagem_final,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch.strip(),
            }
            if sha_existente:
                payload["sha"] = sha_existente

            resp = await client.put(
                f"{GITHUB_API}/repos/{repo}/contents/{path.strip()}",
                json=payload,
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return _mensagem_erro_escrita(exc, f"commitar `{path}`")
    except httpx.TimeoutException:
        return "O GitHub demorou demais. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha commitando %s em %s/%s", path, repo, branch)
        return "Não consegui commitar o arquivo agora."

    data = resp.json()
    verbo = "Atualizado" if sha_existente else "Criado"
    return (f"{verbo} `{path}` em `{branch}` ({repo}) — commit "
            f"{data['commit']['sha'][:7]}. Próximo passo: abra o PR com "
            "github_open_pull_request e acompanhe o CI com github_check_ci.")


# --------------------------------------------------------------------------
# 3. Abrir Pull Request
# --------------------------------------------------------------------------
@tool
async def github_open_pull_request(repo: str, branch: str, title: str,
                                   body: str = "", base: str = "main") -> str:
    """Abre um Pull Request da `branch` para `base` (padrão main). Sempre que o trabalho estiver na branch, abra PR — código nunca vai direto pra main, e a revisão do time acontece aqui."""
    if erro := _guard_write(branch):
        return erro
    if erro := _repo_valido(repo):
        return erro

    try:
        async with httpx.AsyncClient(
            timeout=settings.GITHUB_TIMEOUT_SECONDS,
            headers=_headers(),
            follow_redirects=True,
        ) as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{repo}/pulls",
                json={"title": title.strip(), "head": branch.strip(),
                      "base": base.strip(), "body": body},
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 422:
            return (
                f"O GitHub recusou abrir PR de `{branch}` (422) — a mais "
                "comum: já existe PR aberto para essa branch. "
                "Use github_check_ci para ver o estado ou me diga se quer outra branch."
            )
        return _mensagem_erro_escrita(exc, f"abrir o PR de `{branch}`")
    except httpx.TimeoutException:
        return "O GitHub demorou demais. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha abrindo PR %s em %s", branch, repo)
        return "Não consegui abrir o PR agora."

    data = resp.json()
    return (f"PR #{data['number']} aberto: {data['title']}\n{data['html_url']}\n"
            "Acompanhe os checks com github_check_ci.")


# --------------------------------------------------------------------------
# 4. CI — leitura (sem gate: read-only, serve como feedback loop)
# --------------------------------------------------------------------------
@tool
async def github_check_ci(repo: str, branch: str, limit: int = 3) -> str:
    """Confere o estado do CI (GitHub Actions) das últimas runs de uma branch. Use depois de commitar ou abrir PR: se o CI falhou, leia a mensagem de erro, corrija o arquivo e commite de novo até ficar verde. Ferramenta de leitura — funciona mesmo com a escrita desativada."""
    if erro := _repo_valido(repo):
        return erro

    try:
        async with httpx.AsyncClient(
            timeout=settings.GITHUB_TIMEOUT_SECONDS,
            headers=_headers(),
            follow_redirects=True,
        ) as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{repo}/actions/runs",
                params={"branch": branch.strip(), "per_page": limit},
            )
            resp.raise_for_status()
            runs = resp.json().get("workflow_runs") or []
    except httpx.HTTPStatusError as exc:
        return _mensagem_de_status(exc, f"as runs de CI de `{branch}`")
    except httpx.TimeoutException:
        return "O GitHub demorou demais. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha lendo CI de %s em %s", branch, repo)
        return "Não consegui checar o CI agora."

    if not runs:
        return (f"Nenhuma run de CI em `{branch}` ainda — pode levar alguns "
                "segundos após o push. Tente de novo em instantes.")

    linhas = [f"CI em `{branch}` ({repo}):"]
    for run in runs:
        icone = {"success": "✅", "failure": "❌"}.get(run.get("conclusion"), "⏳")
        msg = (run.get("head_commit") or {}).get("message", "").split("\n")[0][:60]
        linhas.append(
            f"{icone} {msg!r} — {run.get('status')}/{run.get('conclusion') or 'rodando'}"
        )
    if any(r.get("conclusion") == "failure" for r in runs):
        linhas.append("\n⚠️ Há run com falha. Leia a mensagem de erro, corrija o "
                      "arquivo afetado e commite novamente na branch até ficar verde.")
    return "\n".join(linhas)
