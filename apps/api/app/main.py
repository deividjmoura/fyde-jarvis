from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import health, auth, agent
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.core.checkpointer import close_connection_pool
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup e shutdown da aplicação"""
    # Startup
    logger.info(f"🚀 Iniciando {settings.APP_NAME}")
    
    # Cria tabelas do banco (users, etc)
    Base.metadata.create_all(bind=engine)
    
    # Testa conexão com o checkpointer (memória)
    try:
        from app.core.checkpointer import get_checkpointer
        await get_checkpointer()
        logger.info("✅ Memória persistente (LangGraph + Neon) pronta")
    except Exception as e:
        logger.error(f"⚠️ Erro ao inicializar checkpointer: {e}")

    yield

    # Shutdown
    logger.info("⏻ Desligando aplicação...")
    await close_connection_pool()
    logger.info("✅ Aplicação encerrada com sucesso")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Assistente IA modular com memória por usuário",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(agent.router)


@app.get("/")
def root():
    return {
        "project": settings.APP_NAME,
        "status": "online",
        "memory": "persistente (Postgres)"
    }