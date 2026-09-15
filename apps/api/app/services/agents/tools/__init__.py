"""Tools do agente Fyde Jarvis.

Cada tool vive num módulo próprio. `ALL_TOOLS` é a lista canônica que
`first_agent.py` reexporta como `tools`.

⚠️  CONTRATO PÚBLICO: outros módulos do repo importam `tools` e
`SYSTEM_PROMPT` de `app.services.agents.first_agent`. Se você mudar o nome
desta lista ou reorganizar as exports, avise no AGENT_SYNC.md antes.
"""

from app.services.agents.tools.calculator import simple_calculator
from app.services.agents.tools.clock import get_current_time
from app.services.agents.tools.weather import get_weather
from app.services.agents.tools.search import web_search
from app.services.agents.tools.github import (
    github_list_files,
    github_read_file,
    github_repo_info,
    github_search_repos,
)
from app.services.agents.tools.github_write import (
    github_check_ci,
    github_commit_file,
    github_create_branch,
    github_open_pull_request,
)

ALL_TOOLS = [
    get_current_time,
    simple_calculator,
    get_weather,
    web_search,
    github_repo_info,
    github_list_files,
    github_read_file,
    github_search_repos,
    github_create_branch,
    github_commit_file,
    github_open_pull_request,
    github_check_ci,
]

__all__ = [
    "ALL_TOOLS",
    "get_current_time",
    "simple_calculator",
    "get_weather",
    "web_search",
    "github_repo_info",
    "github_list_files",
    "github_read_file",
    "github_search_repos",
    "github_create_branch",
    "github_commit_file",
    "github_open_pull_request",
    "github_check_ci",
]
