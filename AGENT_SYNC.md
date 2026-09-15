# 🤝 AGENT_SYNC.md — Ponto de sincronização entre agentes

> **Se você é um agente de IA (Arena, Cursor, etc.) trabalhando neste repo:**
> **LEIA ESTE ARQUIVO INTEIRO ANTES DE ESCREVER QUALQUER CÓDIGO.**
>
> Se você é humano: peça sempre ao seu agente — *"leia o AGENT_SYNC.md antes de começar"*.

Este arquivo é o "quadro de avisos" dos times. Ele evita que dois agentes
(humano A + agente / humano B + agente) trabalhem na mesma coisa ou desfaçam
decisões um do outro. **Não é tempo real** — a sincronização acontece via
`git pull`/`push`, então atualize-o com frequência.

---

## 🔄 Protocolo obrigatório

1. `git pull` antes de começar **e de novo antes de dar push**.
2. Leia **🚧 Em andamento** e **🏛️ Decisões de arquitetura** abaixo.
3. **Reserve sua tarefa**: adicione uma linha em "Em andamento" + a branch que
   vai usar → `commit` + `push` imediato (mensagem: `sync: claim <tarefa>`).
4. Trabalhe **somente na branch que você declarou**.
5. Ao terminar: mova a linha para **✅ Concluído**, deixe recado no **💬 Mural**
   se a mudança afetar o outro time, e faça merge/PR da sua branch.
6. **Proibido:** `push --force` na `main` · commit direto na `main` ·
   mexer em arquivos que constam "Em andamento" por outro agente.
7. Este arquivo viaja **no mesmo commit** da mudança que ele descreve.

---

## 🆔 Identidades em uso

| Identidade do agente | Humano |
|---|---|
| `arena-deivid` | Deivid |
| `arena-irmao` | irmão do Deivid _(troquem pelo nome real)_ |

---

## 🚧 Em andamento

| Agente | Tarefa / arquivos | Branch | Desde |
|---|---|---|---|
| _(livre)_ | — | — | — |

## ✅ Concluído (mais recente no topo)

| Data | Agente | Entrega |
|---|---|---|
| 2026-09-15 | `arena-deivid` | Limpeza técnica: `node_modules` fora do git + histórico purgado (44 MB → 273 KB) · `eval()` → parser AST · CORS via `ALLOWED_ORIGINS` · compose MySQL→Postgres · `docs/architecture.md` · este arquivo |

---

## 🏛️ Decisões de arquitetura

> ⛔ Não desfaça sem antes deixar recado no **💬 Mural** e alinhar.

| Data | Decisão | Motivo | Autor |
|---|---|---|---|
| 2026-09-15 | Banco = **Postgres** (Docker local, Neon em prod) | checkpointer do LangGraph exige Postgres | `arena-deivid` |
| 2026-09-15 | **`eval()` banido** — calculadora com AST + whitelist | segurança | `arena-deivid` |
| 2026-09-15 | CORS via `ALLOWED_ORIGINS` (sem `*` + credentials) | segurança | `arena-deivid` |
| 2026-09-15 | `load_dotenv()` **somente** em `core/config.py` | centralização | `arena-deivid` |
| 2026-09-15 | Conventional Commits + branch por tarefa | commitlint/husky ativos | `arena-deivid` |
| legado | Voz 100% local (Whisper/Piper), cérebro na nuvem | privacidade e custo | Deivid |

---

## 💬 Mural (mais recente no topo)

> **[2026-09-15 · arena-deivid]**
> Histórico reescrito com `git filter-repo` (44 MB → 273 KB, 44/44 commits
> preservados). **Quem tem clone antigo: re-clone ou `git fetch && git reset --hard origin/main`.**
> Backlog abaixo tá aberto — reserve o seu item e manda ver! 👋

---

## 🗺️ Backlog acordado (ordem de prioridade)

- [ ] Mais tools no agente: busca web, clima — `apps/api/app/services/agents/`
- [ ] Streaming de respostas (SSE) — `api/routes/agent.py` + `voice-client/`
- [ ] Wake word "Jarvis" — `voice-client/`
- [ ] Modo offline c/ Ollama — `apps/api/app/services/llm/provider.py`
- [ ] Chat UI no frontend — `apps/web/`

_(Pegou um item? Mova para "🚧 Em andamento" no seu primeiro commit.)_
