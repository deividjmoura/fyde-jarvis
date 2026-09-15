"""
Cliente HTTP para o cérebro (fyde-jarvis API).
Usa os endpoints /agent/chat-test (clássico) e /agent/chat-test-stream (SSE).
"""

import json
import re

import requests

import config

# Fim de frase: pontuação final seguida de espaço(s) e o resto do texto.
# Heurística simples pensada para TTS — não precisa ser gramaticalmente perfeita.
_SENTENCE_END = re.compile(r"^(.*?[.!?…][\"')\]]*)\s+(.+)$", re.DOTALL)


def _pop_sentence(buffer: str):
    """Se o buffer tiver uma frase completa, retorna (frase, resto)."""
    match = _SENTENCE_END.match(buffer)
    if match:
        sentence = match.group(1).strip()
        return (sentence or None), match.group(2)
    return None, buffer


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

    def chat_stream(self, user_text: str):
        """Consome o endpoint SSE e emite FRASES completas conforme chegam.

        Permite ao Piper começar a falar a 1ª frase enquanto o resto da
        resposta ainda está sendo gerada — latência percebida cai muito.

        Levanta requests.HTTPError/ConnectionError se a API não suportar
        streaming (ex.: versão antiga) — o main faz fallback para .chat().
        """
        stream_url = f"{config.JARVIS_API_URL.rstrip('/')}/agent/chat-test-stream"

        with requests.post(
            stream_url,
            json={"query": user_text},
            stream=True,
            timeout=self.timeout,
        ) as r:
            r.raise_for_status()  # 404 em API antiga → fallback no main
            r.encoding = "utf-8"  # SSE/JSON é UTF-8; sem isso acentos quebram

            buffer = ""
            for raw_line in r.iter_lines(decode_unicode=True):
                if not raw_line or not raw_line.startswith("data: "):
                    continue

                try:
                    event = json.loads(raw_line[len("data: "):])
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type")

                if event_type == "token":
                    buffer += event.get("content", "")
                    sentence, buffer = _pop_sentence(buffer)
                    while sentence:
                        yield sentence
                        sentence, buffer = _pop_sentence(buffer)

                elif event_type == "done":
                    break

                elif event_type == "error":
                    detail = event.get("detail", "erro desconhecido")
                    print(f"[API] Erro no stream: {detail}")
                    break

            # Frase final sem pontuação de fechamento
            if buffer.strip():
                yield buffer.strip()
