/**
 * Cliente da API do Jarvis.
 *
 * - `API_URL` vem de `VITE_API_URL` (com fallback para a URL de produção);
 * - `streamChat` consome o SSE do `POST /agent/chat-stream` (auth Firebase)
 *   via `fetch` + ReadableStream — EventSource não aceita POST nem header
 *   Authorization, por isso fetch é obrigatório, não estilo.
 * - `sendChatBlocking` é o caminho clássico (novo `/agent/chat`) e funciona
 *   como FALLBACK do streaming, seguindo o padrão do voice-client.
 */

import axios from 'axios';

const PROD_API_URL = 'https://fyde-jarvis-api.onrender.com';

export const API_URL = (
  import.meta.env.VITE_API_URL as string | undefined
)?.replace(/\/+$/, '') || PROD_API_URL;

export interface StreamChatHandlers {
  signal?: AbortSignal;
  onToken: (token: string) => void;
}

type SSEEvent =
  | { type: 'token'; content: string }
  | { type: 'done' }
  | { type: 'error'; detail: string };

/**
 * Parser incremental de SSE: recebe chunks Uint8String conforme chegam do
 * ReadableStream e devolve os eventos completos. Os eventos do Jarvis são
 * linhas `data: {json}` separadas por linha em branco (`\n\n`). Separar o
 * parser do fetch facilita testar a lógica de quebra de chunk — um token pode
 * chegar dividido entre dois reads, e um read pode trazer vários eventos.
 */
export class SSEStreamParser {
  private buffer = '';
  private readonly decoder = new TextDecoder('utf-8');

  feed(chunk: Uint8Array): SSEEvent[] {
    this.buffer += this.decoder.decode(chunk, { stream: true });
    const eventos: SSEEvent[] = [];

    let boundary: number;
    while ((boundary = this.buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = this.buffer.slice(0, boundary);
      this.buffer = this.buffer.slice(boundary + 2);

      for (const linha of rawEvent.split('\n')) {
        if (!linha.startsWith('data:')) continue;
        const json = linha.slice(5).trim();
        if (!json) continue;
        const payload = JSON.parse(json) as SSEEvent;
        eventos.push(payload);
      }
    }
    return eventos;
  }
}

/**
 * Envia a mensagem ao endpoint SSE autenticado e repassa cada token ao
 * callback. Lança:
 *  - `AbortError` se o signal for abortado (botão PARAR / troca de página);
 *  - `Error` com `detail` da API em evento `{type:"error"}`;
 *  - `Error` HTTP se o stream nem chegou a abrir.
 */
export async function streamChat(
  query: string,
  token: string,
  handlers: StreamChatHandlers,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/agent/chat-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ query }),
      signal: handlers.signal,
    });
  } catch (err) {
    // AbortController aborta aqui dentro do fetch; propaga como está.
    throw err;
  }

  if (!response.ok || !response.body) {
    throw new Error(`STREAM_HTTP_${response.status}`);
  }

  const reader = response.body.getReader();
  const parser = new SSEStreamParser();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    for (const evento of parser.feed(value)) {
      if (evento.type === 'token') {
        handlers.onToken(evento.content);
      } else if (evento.type === 'done') {
        await reader.cancel().catch(() => {});
        return;
      } else if (evento.type === 'error') {
        throw new Error(evento.detail || 'Erro desconhecido no stream');
      }
    }
  }
}

/**
 * Caminho clássico não-streaming (fallback). Devolve o texto da resposta.
 * Mantido como contraste ao streaming e rede de segurança se o SSE falhar
 * antes do primeiro token.
 */
export async function sendChatBlocking(
  query: string,
  token: string,
): Promise<string> {
  const response = await axios.post(
    `${API_URL}/agent/chat`,
    { query },
    {
      timeout: 90000,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (typeof response.data === 'string') return response.data;
  if (response.data?.response) return response.data.response;
  if (response.data?.content) return response.data.content;
  return JSON.stringify(response.data);
}

export const isAbortError = (err: unknown): boolean =>
  err instanceof DOMException
    ? err.name === 'AbortError'
    : err instanceof Error && err.name === 'AbortError';
