"""
Cliente HTTP para o cérebro (fyde-jarvis API).
Usa o endpoint /agent/chat-test (sem autenticação) no modo pessoal.
"""

import requests
import config


class JarvisAPI:
    def __init__(self):
        self.url = config.CHAT_ENDPOINT
        self.timeout = 90
        print(f"[API] Cérebro → {self.url}")

        # Teste rápido de conexão
        try:
            r = requests.get(config.JARVIS_API_URL.rstrip("/") + "/", timeout=5)
            if r.ok:
                print("[API] Backend online.")
            else:
                print(f"[API] Aviso: backend respondeu {r.status_code}")
        except requests.exceptions.ConnectionError:
            print(
                f"[API] ⚠️  Não consegui conectar em {config.JARVIS_API_URL}\n"
                "     Suba a API antes:  cd apps/api && uvicorn app.main:app --reload"
            )

    def chat(self, user_text: str) -> str:
        """Envia a frase do usuário e retorna a resposta do agente."""
        payload = {"query": user_text}
        try:
            r = requests.post(self.url, json=payload, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            return data.get("response", "Não recebi resposta do cérebro.").strip()
        except requests.exceptions.Timeout:
            return "O cérebro demorou demais para responder. Tente de novo."
        except requests.exceptions.ConnectionError:
            return "Não consegui falar com o cérebro. A API está rodando?"
        except Exception as e:
            return f"Erro na comunicação com o cérebro: {e}"
