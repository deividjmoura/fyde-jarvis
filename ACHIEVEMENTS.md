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

## ✅ Cultura de testes (mesmo sem suíte formal)

Toda feature desta fase saiu com verificação executável:
calculadora vs. ataques · SSE vs. servidor fake · provider em 4 cenários ·
wake word vs. ruído/silêncio.

---

<sub>Mantido pelos times `arena-deivid` e `arena-irmao`. Atualizado em 2026-09-15.</sub>
