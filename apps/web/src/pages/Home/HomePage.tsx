import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function HomePage() {
  const { user, loading, logout, getToken } = useAuth();   // ← getToken aqui
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_URL = 'https://fyde-jarvis-api.onrender.com';

  useEffect(() => {
    if (!loading && !user) {
      navigate('/');
    }
  }, [user, loading, navigate]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

      if (!token) {
        throw new Error("Não foi possível obter token de autenticação");
      }

      const response = await axios.post(
        `${API_URL}/agent/chat-test`,
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
      console.error("Erro completo:", error);
      let msg = "❌ Erro ao conectar com o Jarvis.";

      if (error.response?.status === 401) {
        msg = "❌ Sessão expirada. Faça login novamente.";
      } else if (error.response?.data?.detail) {
        msg = `❌ ${error.response.data.detail}`;
      }

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

  if (loading) return <div className="h-screen flex items-center justify-center bg-[#060b16] text-white">Carregando...</div>;
  if (!user) return null;

  // ... (o resto do return com o JSX continua igual ao que eu te mandei antes)

  return (
    <div className="flex h-screen bg-[#060b16] text-white">
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">

        {/* Header */}
        <div className="border-b border-gray-800 p-4 flex items-center justify-between bg-[#0a0f1c]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-2xl">
              🤖
            </div>
            <div>
              <h1 className="text-2xl font-semibold">Fyde Jarvis</h1>
              <p className="text-sm text-emerald-400">● Online • Memória ativa</p>
            </div>
          </div>

          <button
            onClick={logout}
            className="px-5 py-2 bg-gray-800 hover:bg-red-500/20 hover:text-red-400 rounded-lg transition-colors"
          >
            Sair
          </button>
        </div>

        {/* Área de Mensagens */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#060b16]">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="text-6xl mb-6">👋</div>
              <h2 className="text-3xl font-light mb-2">Olá, {user.email?.split('@')[0]}!</h2>
              <p className="text-gray-400 max-w-md">
                Como posso te ajudar hoje? Pode falar naturalmente.
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-5 py-3.5 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 rounded-br-none'
                      : 'bg-gray-800 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  <span className="text-[10px] opacity-60 mt-2 block">
                    {msg.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 rounded-2xl px-5 py-3 rounded-bl-none">
                Jarvis está pensando...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 border-t border-gray-800 bg-[#060b16]">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua mensagem aqui..."
              className="flex-1 bg-gray-900 border border-gray-700 rounded-2xl px-6 py-4 focus:outline-none focus:border-blue-500 transition"
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 px-8 rounded-2xl font-medium transition"
            >
              Enviar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}