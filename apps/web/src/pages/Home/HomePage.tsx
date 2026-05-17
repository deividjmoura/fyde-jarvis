import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

import ParticleBackground from '../../components/background/ParticleBackground';
import './home.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function HomePage() {
  const { user, loading, logout, getToken } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_URL = 'https://fyde-jarvis-api.onrender.com';

  useEffect(() => {
    if (!loading && !user) navigate('/');
  }, [user, loading, navigate]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
  const loadHistory = async () => {
    if (!user) return;

    try {
      const token = await getToken();

      if (!token) return;

      const response = await axios.get(
        `${API_URL}/agent/history`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (response.data?.messages) {
        setMessages(
          response.data.messages.map((msg: any, index: number) => ({
            id: `${index}`,
            role: msg.role,
            content: msg.content,
            timestamp: new Date()
          }))
        );
      }

    } catch (error) {
      console.error("Erro ao carregar histórico:", error);
    }
  };

  loadHistory();
  }, [user]);
  
  const sendMessage = async () => {
    if (!input.trim() || isLoading || !user) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input.trim();
    setInput('');
    setIsLoading(true);

    try {
      const token = await getToken();
      if (!token) throw new Error("Token inválido");

      const response = await axios.post(
        `${API_URL}/agent/chat`,
        { query: currentInput },
        {
          timeout: 90000,
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          }
        }
      );

      let responseText = "Sem resposta";
      if (typeof response.data === 'string') responseText = response.data;
      else if (response.data?.response) responseText = response.data.response;
      else if (response.data?.content) responseText = response.data.content;
      else responseText = JSON.stringify(response.data);

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseText,
        timestamp: new Date()
      }]);

    } catch (error: any) {
      const msg = error.response?.status === 401 
        ? "❌ Sessão expirada. Faça login novamente." 
        : "❌ Erro ao conectar com o Jarvis.";

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: msg,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
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
                <div className="message-content">{msg.content}</div>
                <span style={{ fontSize: '11px', opacity: 0.5, marginTop: '6px', display: 'block' }}>
                  {msg.timestamp.toLocaleTimeString('pt-BR')}
                </span>
              </div>
            ))
          )}

          {isLoading && (
            <div className="message assistant">
              <div className="message-content">PROCESSANDO SINAL NEURAL...</div>
            </div>
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
          <button onClick={sendMessage} disabled={!input.trim() || isLoading}>
            TRANSMIT
          </button>
        </div>
      </div>
    </div>
  );
}