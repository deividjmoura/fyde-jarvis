# 🏆 Achievements — Fyde Jarvis

> Conquistas técnicas do projeto, escritas para quem avalia: cada item diz
> **o que foi feito** e **por que é difícil/relevante**.
> Todo o histórico é verificável nos commits (`git log`) e em
> [AGENT_SYNC.md](./AGENT_SYNC.md).

---

## 🤖🤝🤖 Desenvolvimento multi-agente coordenado

Dois times (humano + agente de IA, em **duplas independentes**) evoluem o mesmo
repositório usando um protocolo próprio definido em projeto: o **AGENT_SYNC.md**.

- Claims públicos de tarefas, mural de recados técnico-temporais e tabela de
  decisões de arquitetura (ADR-lite) — tudo versionado junto ao código.
- **Colisão real resolvida pelo protocolo:** dois agentes reservaram a mesma
  feature no mesmo minuto; o `git` rejeitou o push tardio, o protocolo
  "first come, first served" decidiu, e o segundo agente assumiu outra tarefa
  **sem intervenção humana** e sem retrabalho.
- Convenção de commits `sync:` para mensagens entre agentes direto na `main`.

**Por que importa:** orquestração de agentes de IA em times mistos é um dos
desafios práticos de 2026; aqui está uma implementação simples, documentada
e *testada em produção* no próprio projeto.

---

## 🛡️ Segurança ofensiva→defensiva

- Eliminação de `eval()` (RCE em potencial via prompt do usuário) por um parser
  **AST com whitelist** de operadores — validado com 5 payloads de ataque
  (`__import__`, traversal de `__class__.__bases__`, `open()`, names, índices).
- CORS restrito por ambiente (`ALLOWED_ORIGINS`); fim do wildcard+credentials.
- Auditoria de segredos em **todo o histórico** git (nenhum vazamento).

## ⚡ Tempo real: streaming ponta-a-ponta

- SSE nativo (`StreamingResponse`) token-a-token do LangGraph
  (`stream_mode="messages"`, filtragem por nó do agente).
- Voice-client corta **frases completas em voo** e o Piper começa a falar
  durante a geração — latência percebida cai de "esperar tudo" para
  "primeira frase imediata"; **fallback automático** para o modo clássico.
- Bug real de encoding caçado por teste de integração com servidor SSE fake
  (requests assume ISO-8859-1; resposta é UTF-8).

## 🗣️ Wake word 100% local ("Jarvis")

- `openWakeWord` com modelo `hey_jarvis` **embutido no pacote** — nenhum byte
  de áudio sai da máquina até o assistente ser chamado (privacidade by design).
- Detector com debounce/cooldown, compatível com 3 versões da API da lib
  (0.4/0.5/0.6), validado sem falsos positivos em ruído e silêncio.

## 🔌 Resiliência: modo offline com fallback automático

- `LLM_PROVIDER=ollama` roda **100% local** (Ollama via API OpenAI-compatível,
  zero dependências novas). Sem chave de nuvem configurada, a API **degrada
  graciosamente** para o modelo local em vez de quebrar.

## 🧠 Memória persistente por usuário

- Checkpointer LangGraph em Postgres (Neon) com pool async, `thread_id`
  isolado por usuário — a conversa sobrevive a restarts e deploys.

## 🧹 Engenharia de repositório

- Purga de 22.319 arquivos (`node_modules`) do histórico com `git filter-repo`:
  **44 MB → 273 KB** preservando os 44 commits (backup em bundle antes).
- Conventional Commits enforced por commitlint + husky; histórico atômico e legível.

## 🧰 Tools do agente com provedores plugáveis

- `get_weather` (Open-Meteo, **zero API key**) e `web_search` (Wikipédia pt por
  padrão, Tavily opcional via `WEB_SEARCH_PROVIDER`).
- Escolha de provedor por **evidência, não por achismo**: a API *Instant Answer*
  do DuckDuckGo foi testada e devolve HTTP 202 com `AbstractText` vazio
  (challenge de rate-limit) — por isso ficou de fora e a Wikipédia entrou.
- Tools de rede são `async` com `httpx.AsyncClient` (uma tool síncrona bloquearia
  o event loop do agente ReAct inteiro) e **nenhuma levanta exceção**: devolvem
  texto em pt-BR para o agente explicar a falha em vez de quebrar o turno.
- Fuso horário explícito (`JARVIS_TIMEZONE`): na nuvem o relógio é UTC e o
  assistente brasileiro devolvia hora errada.

## ✅ Cultura de testes: de verificação manual a suíte formal

- **52 testes unitários + 2 de integração** (`pytest` + `respx` +
  `pytest-asyncio`), reproduzidos num clone limpo do remote.
- **Teste de contrato entre times:** `test_contract.py` quebra a suíte se alguém
  remover `SYSTEM_PROMPT`/`tools` de `first_agent.py` — exatamente o import que o
  `streaming.py` do outro time usa. Conflito vira erro de teste, não bug em prod.
- **Teste de ponta a ponta do grafo ReAct** com LLM falso: prova que tool `async`
  executa dentro do LangGraph (`human → ai(tool_call) → tool → ai`).
- Calculadora vs. 8 payloads de ataque · clima e busca com HTTP mockado e real.
- CI proposto em `docs/ci.yml.proposed` (testes em 3.11/3.13, commitlint, build
  do web) — aguardando token com permissão `Workflows` para ser ativado.

---

<sub>Mantido pelos times `arena-deivid`, `arena-irmao` e `arena-c3`. Atualizado em 2026-09-15.</sub>
