import { useState, useRef, useEffect } from 'react';
import axios from 'axios';     // ← Esta linha é obrigatória

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function HomePage() {
 
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

 const sendMessage = async () => {
  if (!input.trim() || isLoading) return;

  const userMessage = {
    id: Date.now().toString(),
    role: 'user' as const,
    content: input.trim(),
    timestamp: new Date()
  };

  setMessages(prev => [...prev, userMessage]);
  const currentInput = input.trim();
  setInput('');
  setIsLoading(true);

  try {
    const API_URL = 'https://fyde-jarvis-api.onrender.com';

    const response = await axios.post(
      `${API_URL}/agent/chat-test`,
      { 
        query: currentInput 
      },
      {
        timeout: 60000,
        headers: { 'Content-Type': 'application/json' }
      }
    );

    let responseText = "Sem resposta";

    if (typeof response.data === 'string') {
      responseText = response.data;
    } else if (response.data?.response) {
      responseText = response.data.response;
    } else if (response.data?.content) {
      responseText = response.data.content;
    } else {
      responseText = JSON.stringify(response.data);
    }

    setMessages(prev => [...prev, {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: responseText,
      timestamp: new Date()
    }]);

  } catch (error: any) {
    console.error("Erro completo:", error);

    let msg = "❌ Erro ao conectar com o Jarvis.";

    if (error.response?.status === 405) {
      msg = "❌ Method Not Allowed\nCertifique-se que está usando POST";
    } else if (error.response?.data?.detail) {
      msg = `❌ ${error.response.data.detail}`;
    } else if (error.code === 'ERR_NETWORK') {
      msg = "❌ Erro de rede - API pode estar hibernando (Render Free)";
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

  const handleKeyPress = (e: any) => {
    if (e.key === 'Enter') sendMessage();
  };

  return (
    <div className="flex h-screen bg-black text-white flex-col">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-2xl">Fyde Jarvis - Teste Mínimo</h1>
      </div>

      <div className="flex-1 p-6 overflow-auto space-y-4">
        {messages.length === 0 && (
          <p className="text-gray-400">Digite algo e pressione Enter...</p>
        )}
        
        {messages.map((m, i) => (
          <div key={i} className={`p-3 rounded-lg ${m.role === 'user' ? 'bg-blue-600 ml-auto' : 'bg-gray-800'}`}>
            {m.content}
          </div>
        ))}

        {isLoading && <p>Pensando...</p>}
      </div>

      <div className="p-4 border-t border-gray-800">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Digite aqui..."
          className="w-full bg-gray-900 p-4 rounded-xl border border-gray-700"
        />
      </div>
    </div>
  );
}