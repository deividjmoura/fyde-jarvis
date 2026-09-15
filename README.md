# Fyde Jarvis

**Assistente IA híbrido** — cérebro na nuvem (memória persistente + tools) + corpo local (voz + controle do PC).

> 🏆 Construído por **dois times humano+agente** coordenados por protocolo próprio
> ([AGENT_SYNC.md](./AGENT_SYNC.md)). Destaques: wake word 100% local, streaming
> SSE ponta-a-ponta, modo offline com fallback, segurança anti-`eval`.
> **Veja [ACHIEVEMENTS.md](./ACHIEVEMENTS.md).**

```
Você fala  →  Cliente local (Whisper)
                    ↓
              API FastAPI + LangGraph (memória Neon)
                    ↓
              Cliente local (Piper fala a resposta)
                    ↓
         (fase 2) executa ações no seu computador
```

---

## Arquitetura

| Camada | Pasta | Responsabilidade |
|--------|-------|------------------|
| **Cérebro** | `apps/api` | FastAPI + LangGraph + memória por usuário (Neon) + tools |
| **Interface web** | `apps/web` | React + Firebase Auth (opcional no modo pessoal) |
| **Corpo (voz)** | `voice-client/` | Microfone → Whisper → API → Piper |

---

## Pré-requisitos

- Linux (testado no **CachyOS**; qualquer distro glibc serve) + Python 3.11+
- Conta no [Neon](https://neon.tech) (Postgres gratuito) **ou** Docker p/ banco local
- Chave [OpenRouter](https://openrouter.ai) (ou `LLM_PROVIDER=ollama` p/ modo offline)
- (Opcional) Projeto Firebase se quiser auth
- Stack completa em 1 comando (só precisa de Docker): `docker compose --profile full up --build`

---

## 1. Backend (cérebro)

```bash
cd apps/api

# Ambiente virtual
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt

# Configuração
cp .env.example .env
# Edite o .env (veja seção abaixo)

# Sobe a API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API disponível em: `http://localhost:8000`  
Docs interativas: `http://localhost:8000/docs`

### Variáveis de ambiente (`apps/api/.env`)

```env
# Obrigatórias
DATABASE_URL=postgresql+psycopg2://user:pass@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
OPENROUTER_API_KEY=sk-or-v1-...
SECRET_KEY=uma-string-longa-e-aleatoria

# Firebase (só se for usar auth real)
FIREBASE_CREDENTIALS={"type":"service_account", ...}

# Opcional
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-3-haiku
```

> **Dica Neon:** no dashboard do Neon copie a connection string e troque o início para `postgresql+psycopg2://` se necessário.
>
> **Sem Neon?** Rode `docker compose up -d` na raiz do repo para subir um Postgres local e use:
> `DATABASE_URL=postgresql+psycopg2://fydeuser:fydepass@localhost:5432/fydejarvis?sslmode=disable`

### Endpoints principais

| Método | Rota | Auth | Uso |
|--------|------|------|-----|
| `POST` | `/agent/chat-test` | Não | Ideal para o cliente de voz e testes |
| `POST` | `/agent/chat-test-stream` | Não | Igual ao chat-test, mas responde em **SSE** (tempo real) |
| `POST` | `/agent/chat` | Sim (Firebase) | Chat autenticado |
| `GET`  | `/agent/history` | Sim | Histórico da conversa |
| `GET`  | `/auth/me` | Sim | Dados do usuário logado |
| `GET`  | `/` | Não | Health check |

**Exemplo de teste rápido:**

```bash
curl -X POST http://localhost:8000/agent/chat-test \
  -H "Content-Type: application/json" \
  -d '{"query": "Que horas são?"}'
```

---

## 2. Cliente de voz (corpo local)

O cliente fica na pasta `voice-client/` (mesmo repositório ou separado).

### Instalação no CachyOS / Arch

```bash
# Dependências de sistema
sudo pacman -S --needed portaudio python-pip python-virtualenv
paru -S piper-tts          # ou baixe o binário (veja voice-client/README)

cd voice-client
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Voz em português
mkdir -p models/piper && cd models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json
cd ../..

cp .env.example .env
# Edite: JARVIS_API_URL=http://localhost:8000
```

### Rodar

```bash
# Terminal 1 – API
cd apps/api && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 – Voz
cd voice-client && source .venv/bin/activate
python main.py
```

Fluxo:
1. Você fala
2. Whisper transcreve
3. Cliente chama `POST /agent/chat-test`
4. LangGraph responde (com memória)
5. Piper fala a resposta

---

## 3. Frontend web (opcional)

```bash
cd apps/web
npm install
# configure as variáveis do Firebase
npm run dev
```

---

## Roadmap

### Agora (híbrido básico)
- [x] API + memória persistente
- [x] Cliente de voz local → API
- [x] README e `.env.example` limpos

### Próximo
- [ ] Mais tools no LangGraph (busca web, clima, etc.)
- [ ] Cliente local executa comandos do sistema com confirmação verbal
- [ ] Modo 100% local (Ollama) quando a API estiver offline
- [x] Streaming de resposta (SSE — `POST /agent/chat-test-stream` + TTS por frases no voice-client)
- [ ] Wake word (“Jarvis”)

### Depois
- [ ] Múltiplas conversas por usuário
- [ ] Controle de desktop (abrir apps, digitar, etc.)
- [ ] Integração com MCP / skills

---

## Estrutura do repositório

```
fyde-jarvis/
├── apps/
│   ├── api/                 # Cérebro (FastAPI + LangGraph)
│   │   ├── app/
│   │   │   ├── api/routes/  # agent, auth, health
│   │   │   ├── core/        # config, checkpointer
│   │   │   ├── services/
│   │   │   │   ├── agents/  # first_agent.py
│   │   │   │   └── llm/     # provider.py
│   │   │   └── ...
│   │   ├── .env.example
│   │   └── requirements.txt
│   └── web/                 # Frontend React
├── voice-client/            # Cliente de voz local (Whisper + Piper)
├── docker-compose.yml
└── README.md
```

---

## Problemas comuns

**Erro de conexão com Neon**  
→ Verifique `sslmode=require` e se a connection string está limpa (sem `+psycopg2` no checkpointer se der conflito).

**`OPENROUTER_API_KEY` não encontrada**  
→ Confirme que o `.env` está em `apps/api/` e que você rodou o uvicorn de dentro dessa pasta.

**Cliente de voz não acha a API**  
→ `JARVIS_API_URL=http://localhost:8000` no `.env` do voice-client. Firewall/localhost ok?

**Piper não encontrado**  
→ Binário precisa estar no `PATH` (`which piper`).

---

## 🤝 Contribuindo (humanos + agentes de IA)

Este repo é mantido por **duas pessoas com seus respectivos agentes de IA**.
Antes de qualquer tarefa, leia e siga o [AGENT_SYNC.md](./AGENT_SYNC.md):
é onde os times reservam tarefas, registram decisões e trocam recados.

---

Desenvolvido com ❤️ por Deivid Moura  
Arquitetura híbrida evoluída com o Grok.


---

<p align="center">
  <a href="https://wa.me/55SEUNUMERO?text=Ol%C3%A1%20Deivid!%20Quero%20falar%20sobre%20parceria%20/%20projeto.">
    <img src="https://raw.githubusercontent.com/deividjmoura/deividjmoura/main/assets/logo-deivid-moura-dev.svg" alt="Deivid Moura DEV" width="140"/>
  </a><br/>
  <sub><b>Deivid Moura DEV</b> · parcerias e sistemas sob medida</sub>
</p>

