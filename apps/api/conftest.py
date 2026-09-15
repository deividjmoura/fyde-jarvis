"""Ambiente mínimo para os testes.

`app.core.config` instancia `Settings` na importação e falha se faltar qualquer
campo obrigatório, então as variáveis são definidas AQUI — antes de qualquer
import de código da aplicação. Valores falsos de propósito: nenhum teste unitário
toca Postgres, Firebase ou OpenRouter.
"""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://test:test@localhost:5432/test?sslmode=disable",
)
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("FIREBASE_CREDENTIALS", "{}")
os.environ.setdefault("JARVIS_TIMEZONE", "UTC")
