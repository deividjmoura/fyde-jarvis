import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

import ParticleBackground from '../../components/background/ParticleBackground';
import {
  API_URL,
  streamChat,
  sendChatBlocking,
  isAbortError,
} from '../../lib/api';
import './home.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  streaming?: boolean;
}

export default function HomePage() {
  const { user, loading, logout, getToken } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading && !user) navigate('/');
  }, [user, loading, navigate]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const loadHistory = async () => {
      if (loading || !user) return;

      try {
        const token = await getToken();

        if (!token) return;

        const response = await axios.get(
          `${API_URL}/agent/history`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
        );

        if (response.data?.messages) {
          setMessages(
            response.data.messages.map((msg: any, index: number) => ({
              id: `${index}`,
              role: msg.role,
              content: msg.content,
              timestamp: new Date(),
            })),
          );
        }
      } catch (error) {
        console.error('Erro ao carregar histórico:', error);
      }
    };

    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, loading]);

  const patchMessage = (id: string, patch: Partial<Message>) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    );
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading || !user) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };
    const assistantId = (Date.now() + 1).toString();
    const assistantPlaceholder: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    const currentInput = input.trim();
    setInput('');
    setIsLoading(true);

    const token = await getToken();
    if (!token) {
      patchMessage(assistantId, {
        content: '❌ Sessão expirada. Faça login novamente.',
        streaming: false,
      });
      setIsLoading(false);
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    let recebeuToken = false;
    let textoParcial = '';

    try {
      // ---- Caminho principal: SSE token-a-token ----
      await streamChat(currentInput, token, {
        signal: controller.signal,
        onToken: (pedaco) => {
          recebeuToken = true;
          textoParcial += pedaco;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + pedaco }
                : m,
            ),
          );
        },
      });

      patchMessage(assistantId, { streaming: false });
    } catch (streamError: any) {
      if (isAbortError(streamError)) {
        // PARAR do operador: preserva o que já chegou.
        patchMessage(assistantId, {
          streaming: false,
          content: textoParcial || '⏹️ Geração interrompida.',
        });
      } else if (!recebeuToken) {
        // ---- Fallback: endpoint clássico (padrão do voice-client) ----
        console.warn('SSE falhou antes do 1º token, caindo no /agent/chat:', streamError);
        try {
          const texto = await sendChatBlocking(currentInput, token);
          patchMessage(assistantId, {
            content: texto || 'Sem resposta',
            streaming: false,
          });
        } catch (fallbackError: any) {
          const msg =
            fallbackError.response?.status === 401
              ? '❌ Sessão expirada. Faça login novamente.'
              : '❌ Erro ao conectar com o Jarvis.';
          patchMessage(assistantId, { content: msg, streaming: false });
        }
      } else {
        // Stream morreu no meio com texto parcial: avisa e mantém o texto.
        patchMessage(assistantId, {
          streaming: false,
          content: `${textoParcial}\n\n⚠️ Conexão interrompida.`,
        });
      }
    } finally {
      abortRef.current = null;
      setIsLoading(false);
    }
  };

  const pararGeracao = () => {
    abortRef.current?.abort();
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (loading) return <div className="login-screen">Carregando sistema...</div>;
  if (!user) return null;

  return (
    <div className="chat-screen">
      <ParticleBackground />

      <div className="corner corner-top">FYDE OS v0.8.4</div>
      <div className="corner corner-bottom">NEURAL LINK ACTIVE</div>

      <div className="chat-container">
        <div className="chat-header">
          <div className="system-info">
            <div className="terminal-dot"></div>
            JARVIS • ONLINE
          </div>
          <button onClick={logout} className="logout-btn">LOGOUT</button>
        </div>

        <div className="chat-messages" ref={messagesEndRef}>
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', marginTop: '80px', opacity: 0.8 }}>
              <h2 style={{ fontSize: '28px', marginBottom: '12px' }}>CONNECTION ESTABLISHED</h2>
              <p>Bem-vindo de volta, Operador.</p>
              <p className="text-green-400 mt-2">User ID: {user.email}</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-content">
                  {msg.content}
                  {msg.streaming && <span className="stream-cursor" />}
                </div>
                {!msg.streaming && (
                  <span style={{ fontSize: '11px', opacity: 0.5, marginTop: '6px', display: 'block' }}>
                    {msg.timestamp.toLocaleTimeString('pt-BR')}
                  </span>
                )}
                {msg.streaming && !msg.content && (
                  <span style={{ fontSize: '12px', opacity: 0.6, marginTop: '6px', display: 'block' }}>
                    PROCESSANDO SINAL NEURAL...
                  </span>
                )}
              </div>
            ))
          )}
        </div>

        <div className="chat-input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="DIGITE SUA MENSAGEM E PRESSIONE ENTER..."
            disabled={isLoading}
          />
          {isLoading ? (
            <button onClick={pararGeracao} className="stop-btn" title="Interromper geração">
              ■ PARAR
            </button>
          ) : (
            <button onClick={sendMessage} disabled={!input.trim()}>
              TRANSMIT
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
