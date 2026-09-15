# Arquitetura — Fyde Jarvis

## Visão geral

O Fyde Jarvis é um assistente IA **híbrido**:

- **Cérebro na nuvem** — API FastAPI com agente LangGraph, memória persistente
  em Postgres e LLM via OpenRouter. Roda igual para qualquer cliente.
- **Corpo local** — cliente de voz no seu PC: microfone → Whisper (STT) → API →
  Piper (TTS) fala a resposta. Futuro: executa ações locais com confirmação.
- **Interface web** — React com Firebase Auth para chat no navegador.

```
                     ┌─────────────────────────────────────────┐
                     │                 NUVEM                   │
                     │                                         │
                     │   apps/api · FastAPI                    │
                     │   ├─ POST /agent/chat      (Firebase)   │
                     │   ├─ POST /agent/chat-test (sem auth)   │
                     │   ├─ GET  /agent/history   (Firebase)   │
                     │   │                                     │
                     │   └─ LangGraph ReAct Agent              │
                     │        ├─ tools: hora, calculadora, ... │
                     │        ├─ checkpointer ──────────┐      │
                     │        └─ LLM via OpenRouter     │      │
                     └──────────▲───────────────────────┼──────┘
                                │ HTTPS                 │
              ┌─────────────────┴─────┐        ┌────────▼────────┐
              │  voice-client (local) │        │  Postgres       │
              │  mic → Whisper (STT)  │        │  (Neon ou       │
              │  API → Piper (TTS)    │        │   Docker local) │
              └───────────────────────┘        │  checkpointers  │
                                               │  + tabela users │
              ┌───────────────────────┐        └─────────────────┘
              │  apps/web (React)     │
              │  Firebase Auth (Google)
              │  Chat UI (em dev)     │
              └───────────────────────┘
```

## Componentes

### `apps/api` — Cérebro (FastAPI + LangGraph)

| Módulo | Responsabilidade |
|--------|------------------|
| `app/main.py` | App FastAPI, CORS, lifespan (cria tabelas, abre/fecha pool) |
| `app/core/config.py` | Settings via pydantic + `.env`; carrega dotenv 1× |
| `app/core/checkpointer.py` | Pool async Postgres + `AsyncPostgresSaver` (memória) |
| `app/services/llm/provider.py` | Fábrica de LLM (hoje: OpenRouter) |
| `app/services/agents/first_agent.py` | Agente ReAct + system prompt; reexporta `tools` |
| `app/services/agents/tools/` | Uma tool por módulo (`clock`, `calculator`, `weather`, `search`) |
| `app/services/agents/streaming.py` | Gerador async de tokens p/ SSE (`stream_mode="messages"`) |
| `app/api/routes/` | `agent`, `auth`, `health` |
| `app/dependencies/auth.py` | Valida Firebase ID Token |

### Tools disponíveis

| Tool | O que faz | Rede | Chave |
|------|-----------|------|-------|
| `get_current_time` | Data/hora no fuso `JARVIS_TIMEZONE` | não | — |
| `simple_calculator` | Aritmética via AST (sem `eval`) | não | — |
| `get_weather` | Clima atual + mín/máx do dia (Open-Meteo) | sim | não precisa |
| `web_search` | Busca: Wikipédia pt (padrão) ou Tavily | sim | só no Tavily |

Tools de rede são `async` com `httpx.AsyncClient` — uma tool síncrona bloquearia
o event loop do agente inteiro durante a chamada. Nenhuma tool levanta exceção:
todas devolvem uma string em pt-BR para que o agente explique o problema.

**Fluxo de um chat:**

1. Cliente envia `POST /agent/chat-test` (ou `/chat` com Firebase token)
2. Rota deriva `thread_id` (por usuário → memória isolada)
3. `run_first_agent` cria o agente ReAct com o checkpointer
4. LangGraph decide se chama tools e gera a resposta
5. Histórico é persistido automaticamente no Postgres (checkpointer)

### `voice-client` — Corpo local

Mic → `record_until_silence` → Whisper local → `POST /agent/chat-test` →
Piper TTS fala a resposta. Modelos de voz ficam em `models/piper/` (não versionados).

### `apps/web` — Interface

React + Vite + Firebase Auth (Google). Deploy no Netlify (`netlify.toml`).

## Decisões técnicas

| Decisão | Motivo |
|---------|--------|
| **Híbrido nuvem/local** | Cérebro pesado na nuvem; voz sensível processa 100% local |
| **Checkpointer Postgres** | Memória por usuário sobrevive a restart da API |
| **OpenRouter** | Um endpoint para trocar de modelo sem mudar código |
| **MySQL → Postgres** | LangGraph checkpointer exige Postgres; stack unificado |
| **eval() banido** | Calculadora usa parser AST com whitelist de operadores |
| **CORS via env** | Origens explícitas por ambiente (`ALLOWED_ORIGINS`) |

## Convenções

- Commits seguem **Conventional Commits** (commitlint + husky)
- `node_modules`, `.venv`, `__pycache__`, `.env` **nunca** são versionados
- Cada usuário tem um `thread_id` próprio (`user_<firebase_uid>`)
