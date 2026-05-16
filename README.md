# Fyde Jarvis

<div align="center">

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-success?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136.1-009688?style=for-the-badge&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2.0-4B0082?style=for-the-badge)
![Neon](https://img.shields.io/badge/Neon-Postgres-00B4D8?style=for-the-badge&logo=neon)

**Assistente IA inteligente com memória persistente por usuário**

</div>

## ✨ Funcionalidades

- **Memória Persistente por Usuário** usando Neon Postgres + LangGraph
- Autenticação segura com Firebase
- Agente Reativo com ferramentas (data/hora, calculadora, etc)
- System Prompt bem definido com personalidade brasileira
- Checkpointer assíncrono otimizado para Neon
- Pronto para produção (Render + Neon)

## 🛠 Tecnologias

- **FastAPI** — Framework principal
- **LangGraph** — Construção do agente e memória
- **Neon Postgres** — Banco de dados + checkpoints
- **Firebase Admin SDK** — Autenticação
- **OpenRouter** — Integração com Claude 3 Haiku
- **SQLAlchemy** — ORM

## 🚀 Como Executar

### 1. Clone o projeto

```bash
git clone https://github.com/deividjmoura/fyde-jarvis.git
cd fyde-jarvis
```

### 2. Configure e rode o Backend

```bash
cd apps/api

# Copie o arquivo de ambiente
cp .env.example .env

# Instale as dependências
pip install -r requirements.txt

# Rode o servidor
uvicorn app.main:app --reload
```

## 📡 Endpoints Principais

| Método | Rota | Descrição | Autenticação |
|--------|------|-----------|--------------|
| POST | /agent/chat | Conversa com o Jarvis | Sim |
| POST | /agent/chat-test | Teste rápido (sem token) | Não |
| GET | /auth/me | Informações do usuário logado | Sim |

## 🔑 Variáveis de Ambiente

- DATABASE_URL → URL do Neon Postgres
- OPENROUTER_API_KEY → Chave da OpenRouter
- FIREBASE_CREDENTIALS → JSON da Service Account do Firebase

## 🧠 Sobre a Memória

Cada usuário tem sua própria conversa persistente, vinculada ao firebase_uid. A memória não é perdida ao reiniciar o servidor.

## 🔮 Roadmap

- Múltiplas conversas por usuário
- Streaming de respostas em tempo real
- Endpoint de histórico completo
- Ferramentas avançadas (busca na internet, etc)
- Frontend web

---

Desenvolvido com ❤️ por Deivid Moura

