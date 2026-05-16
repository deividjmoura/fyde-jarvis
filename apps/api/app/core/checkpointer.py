from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from app.core.config import settings
import logging
from urllib.parse import urlparse, parse_qs, urlunparse

logger = logging.getLogger(__name__)

_pool = None

def _clean_connection_string(dsn: str) -> str:
    """Converte DATABASE_URL do SQLAlchemy para formato limpo do psycopg"""
    if dsn.startswith("postgresql+psycopg2://"):
        dsn = dsn.replace("postgresql+psycopg2://", "postgresql://", 1)
    
    parsed = urlparse(dsn)
    query = parse_qs(parsed.query)
    
    # Garante SSL para Neon
    if "sslmode" not in query:
        query["sslmode"] = ["require"]
    
    # Reconstrói a URL limpa
    new_query = "&".join(f"{k}={v[0]}" for k, v in query.items())
    clean_dsn = urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, new_query, parsed.fragment
    ))
    return clean_dsn


async def get_connection_pool():
    global _pool
    if _pool is None:
        try:
            raw_url = settings.DATABASE_URL
            clean_url = _clean_connection_string(raw_url)
            
            logger.info("🔧 Usando connection string limpa para Neon")

            _pool = AsyncConnectionPool(
                conninfo=clean_url,
                max_size=12,
                min_size=2,
                timeout=45,
                max_idle=600,
                kwargs={"autocommit": True},
                open=False
            )
            
            await _pool.open()
            await _pool.wait(timeout=30)
            
            logger.info("✅ Connection Pool com Neon criado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar pool: {e}")
            raise
    return _pool


async def get_checkpointer():
    pool = await get_connection_pool()
    checkpointer = AsyncPostgresSaver(pool)
    
    try:
        await checkpointer.setup()
        logger.info("✅ Tabelas de checkpoint criadas no Neon")
    except Exception as e:
        logger.warning(f"⚠️  Setup do checkpointer: {e} (pode já existir)")
    
    return checkpointer


async def close_connection_pool():
    global _pool
    if _pool:
        try:
            await _pool.close()
            _pool = None
            logger.info("✅ Pool fechado")
        except Exception as e:
            logger.error(f"Erro ao fechar pool: {e}")