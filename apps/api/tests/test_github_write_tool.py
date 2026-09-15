"""Tools de escrita no GitHub: guardrails sempre testados, HTTP mockado."""

import base64

import httpx
import pytest
import respx

from app.core.config import settings
from app.services.agents.tools import github_write as gw
from app.services.agents.tools.github import GITHUB_API

REPO = "deividjmoura/fyde-jarvis"
BRANCH = "agente/corrige-readme"


@pytest.fixture
def escrita_on(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_WRITE_ENABLED", True)
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "ghp_teste")


@pytest.fixture
def escrita_off(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_WRITE_ENABLED", False)
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "ghp_teste")


# ------------------------------ guardrails ---------------------------------
async def test_escrita_desativada_bloqueia_educadamente(escrita_off):
    for tool, args in [
        (gw.github_create_branch, {"repo": REPO, "branch": BRANCH}),
        (gw.github_commit_file, {"repo": REPO, "branch": BRANCH, "path": "a.md",
                                 "content": "x", "message": "docs: ok"}),
        (gw.github_open_pull_request, {"repo": REPO, "branch": BRANCH, "title": "t"}),
    ]:
        saida = await tool.ainvoke(args)
        assert "DESATIVADA" in saida
        assert "opt-in" in saida


async def test_sem_token_avisa(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_WRITE_ENABLED", True)
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "")
    saida = await gw.github_create_branch.ainvoke({"repo": REPO, "branch": BRANCH})
    assert "GITHUB_TOKEN" in saida


@pytest.mark.parametrize("protegida", ["main", "master", "prod", "develop", "MAIN"])
async def test_nunca_commita_em_branch_protegida(escrita_on, protegida):
    saida = await gw.github_commit_file.ainvoke({
        "repo": REPO, "branch": protegida, "path": "x.txt",
        "content": "x", "message": "docs: tentativa"})
    assert "regra dura" in saida
    assert "branch de trabalho" in saida


async def test_mensagem_deve_ser_conventional(escrita_on):
    saida = await gw.github_commit_file.ainvoke({
        "repo": REPO, "branch": BRANCH, "path": "a.md",
        "content": "x", "message": "update arquivo"})
    assert "Conventional Commits" in saida


# --------------------------- criar branch ----------------------------------
@respx.mock
async def test_criar_branch_fluxo_completo(escrita_on):
    respx.get(f"{GITHUB_API}/repos/{REPO}/git/ref/heads/main").mock(
        return_value=httpx.Response(200, json={"object": {"sha": "abc123def"}}))
    post = respx.post(f"{GITHUB_API}/repos/{REPO}/git/refs").mock(
        return_value=httpx.Response(201, json={"ref": f"refs/heads/{BRANCH}"}))

    saida = await gw.github_create_branch.ainvoke({"repo": REPO, "branch": BRANCH})

    assert f"Branch `{BRANCH}` criada" in saida
    assert "abc123d" in saida
    assert post.calls[0].request.content.__contains__(b"refs/heads/" + BRANCH.encode())


@respx.mock
async def test_criar_branch_duplicada_422(escrita_on):
    respx.get(f"{GITHUB_API}/repos/{REPO}/git/ref/heads/main").mock(
        return_value=httpx.Response(200, json={"object": {"sha": "abc123"}}))
    respx.post(f"{GITHUB_API}/repos/{REPO}/git/refs").mock(
        return_value=httpx.Response(422, json={"message": "Reference already exists"}))

    saida = await gw.github_create_branch.ainvoke({"repo": REPO, "branch": BRANCH})
    assert "422" in saida
    assert "duplicado" in saida


# ---------------------------- commit arquivo -------------------------------
@respx.mock
async def test_commit_arquivo_novo_com_trailer(escrita_on):
    respx.get(url__startswith=f"{GITHUB_API}/repos/{REPO}/contents/").mock(
        return_value=httpx.Response(404, json={}))
    put = respx.put(url__startswith=f"{GITHUB_API}/repos/{REPO}/contents/").mock(
        return_value=httpx.Response(201, json={"commit": {"sha": "c0ffee1"}}))

    saida = await gw.github_commit_file.ainvoke({
        "repo": REPO, "branch": BRANCH, "path": "docs/guia.md",
        "content": "# Guia", "message": "docs(guia): adiciona guia inicial"})

    assert "Criado `docs/guia.md`" in saida
    assert "c0ffee1" in saida
    corpo = put.calls[0].request.content.decode()
    assert "Co-authored-by: Deivid" in corpo
    assert "docs(guia): adiciona guia inicial" in corpo
    assert base64.b64encode(b"# Guia").decode() in corpo


@respx.mock
async def test_commit_atualizando_arquivo_envia_sha(escrita_on):
    respx.get(url__startswith=f"{GITHUB_API}/repos/{REPO}/contents/").mock(
        return_value=httpx.Response(200, json={"sha": "file_sha_9"}))
    put = respx.put(url__startswith=f"{GITHUB_API}/repos/{REPO}/contents/").mock(
        return_value=httpx.Response(200, json={"commit": {"sha": "bee5ec5"}}))

    saida = await gw.github_commit_file.ainvoke({
        "repo": REPO, "branch": BRANCH, "path": "README.md",
        "content": "novo", "message": "docs(readme): corrige typo"})

    assert "Atualizado `README.md`" in saida
    assert "file_sha_9" in put.calls[0].request.content.decode()


@respx.mock
async def test_commit_conflito_409_orienta_relita(escrita_on):
    respx.get(url__startswith=f"{GITHUB_API}/repos/{REPO}/contents/s.txt").mock(
        return_value=httpx.Response(404, json={}))
    respx.put(url__startswith=f"{GITHUB_API}/repos/{REPO}/contents/s.txt").mock(
        return_value=httpx.Response(409, json={"message": "is at ..."}))

    saida = await gw.github_commit_file.ainvoke({
        "repo": REPO, "branch": BRANCH, "path": "s.txt",
        "content": "x", "message": "fix: algo"})
    assert "409" in saida
    assert "Releia" in saida


# ------------------------------- abrir PR ----------------------------------
@respx.mock
async def test_abrir_pr_retorna_url(escrita_on):
    respx.post(f"{GITHUB_API}/repos/{REPO}/pulls").mock(
        return_value=httpx.Response(201, json={
            "number": 12, "title": "Corrige readme",
            "html_url": f"https://github.com/{REPO}/pull/12"}))

    saida = await gw.github_open_pull_request.ainvoke({
        "repo": REPO, "branch": BRANCH, "title": "Corrige readme"})

    assert "PR #12 aberto" in saida
    assert "/pull/12" in saida


@respx.mock
async def test_pr_duplicado_422(escrita_on):
    respx.post(f"{GITHUB_API}/repos/{REPO}/pulls").mock(
        return_value=httpx.Response(422, json={"message": "A pull request already exists"}))

    saida = await gw.github_open_pull_request.ainvoke({
        "repo": REPO, "branch": BRANCH, "title": "x"})
    assert "já existe PR" in saida


# ------------------------------ check CI -----------------------------------
@respx.mock
async def test_check_ci_sem_gate_mesmo_desligado(escrita_off):
    """Leitura do CI funciona mesmo com escrita desligada."""
    respx.get(f"{GITHUB_API}/repos/{REPO}/actions/runs").mock(
        return_value=httpx.Response(200, json={"workflow_runs": [
            {"status": "completed", "conclusion": "success",
             "head_commit": {"message": "docs: algo"}},
            {"status": "completed", "conclusion": "failure",
             "head_commit": {"message": "fix: quebrou"}},
        ]}))

    saida = await gw.github_check_ci.ainvoke({"repo": REPO, "branch": BRANCH})
    assert "✅" in saida and "❌" in saida
    assert "corrija" in saida


@respx.mock
async def test_check_ci_sem_runs(escrita_off):
    respx.get(f"{GITHUB_API}/repos/{REPO}/actions/runs").mock(
        return_value=httpx.Response(200, json={"workflow_runs": []}))

    saida = await gw.github_check_ci.ainvoke({"repo": REPO, "branch": BRANCH})
    assert "Nenhuma run" in saida
