"""Inicialização do Firebase **preguiçosa**.

Antes, `credentials.Certificate(...)` e `firebase_admin.initialize_app(...)`
rodavam na importação do módulo. Como `routes/agent.py` importa a dependência de
auth no topo, a API inteira **não subia** sem uma credencial Firebase válida —
nem mesmo com o `{}` sugerido no `.env.example`, porque
`credentials.Certificate({})` lança exceção.

Agora o init só acontece na primeira verificação de token. Consequência:

- `/agent/chat-test` (sem auth) funciona sem nenhuma credencial;
- `/agent/chat` e `/auth/me` devolvem 401 com mensagem clara se o Firebase não
  estiver configurado, em vez de derrubar o boot.
"""

import json
import logging
import threading

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from app.core.config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_inicializado = False


def _is_blank(raw: str) -> bool:
    return not raw or not raw.strip() or raw.strip() == "{}"


def _ensure_firebase() -> None:
    """Inicializa o app Firebase uma única vez; lança se não configurado."""
    global _inicializado
    with _lock:
        if _inicializado:
            return

        raw = settings.FIREBASE_CREDENTIALS
        if _is_blank(raw):
            raise RuntimeError(
                "Firebase não configurado (FIREBASE_CREDENTIALS vazio). "
                "Rota autenticada indisponível — use /agent/chat-test ou "
                "defina a credencial no .env."
            )

        cred = credentials.Certificate(json.loads(raw))
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        _inicializado = True
        logger.info("✅ Firebase inicializado")


def verify_firebase_token(token: str):
    """Verifica o JWT do Firebase. Lança se o token ou a config forem inválidos."""
    _ensure_firebase()
    return firebase_auth.verify_id_token(token)
