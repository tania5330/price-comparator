import { useState, useEffect, useRef } from 'react';
import { ApiService } from '../../services/api';
import { Sparkles, X, Send, MessageSquare, Bot, User } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function AIFloatingChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '¡Hola! 🤖 Soy PriceBot, tu asistente de compras flotante. Preguntame lo que quieras sobre ofertas y precios.',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [isOpen, messages, isLoading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const chatHistory = [...messages, userMessage].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const reply = await ApiService.sendAIChatMessage(chatHistory);
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch (err) {
      console.error('Error in floating chat:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Ups, tuve un problema. Por favor, intentá de nuevo.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-40 font-sans">
      {/* Chat Window Panel */}
      {isOpen && (
        <div className="absolute bottom-16 right-0 w-80 sm:w-96 h-[480px] bg-white border border-gray-200 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-200">
          {/* Header */}
          <div className="bg-indigo-600 text-white px-4 py-3 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="animate-pulse" />
              <div>
                <h3 className="text-sm font-bold">Asistente PriceBot</h3>
                <span className="text-[10px] text-indigo-150">Online • GPT-4o-mini</span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 hover:bg-indigo-700/50 rounded-lg transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50/40">
            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              return (
                <div key={idx} className={`flex gap-2 max-w-[85%] ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}>
                  <div
                    className={`h-7 w-7 rounded-lg flex items-center justify-center flex-shrink-0 text-xs shadow-sm border ${
                      isUser ? 'bg-indigo-600 border-indigo-700 text-white' : 'bg-white border-gray-200 text-gray-600'
                    }`}
                  >
                    {isUser ? <User size={13} /> : <Bot size={13} />}
                  </div>
                  <div
                    className={`p-3 rounded-xl text-xs leading-relaxed whitespace-pre-line shadow-sm border ${
                      isUser
                        ? 'bg-indigo-600 text-white border-indigo-700 rounded-tr-none'
                        : 'bg-white text-gray-800 border-gray-150 rounded-tl-none'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              );
            })}
            {isLoading && (
              <div className="flex gap-2 max-w-[85%] mr-auto">
                <div className="h-7 w-7 rounded-lg flex items-center justify-center bg-white border border-gray-200 text-indigo-600 shadow-sm">
                  <Bot size={13} className="animate-spin" />
                </div>
                <div className="bg-white text-gray-400 border border-gray-150 p-3 rounded-xl rounded-tl-none text-[11px] shadow-sm flex items-center gap-1">
                  <span>Pensando</span>
                  <span className="flex gap-0.5 mt-0.5">
                    <span className="w-1 h-1 bg-gray-300 rounded-full animate-bounce"></span>
                    <span className="w-1 h-1 bg-gray-300 rounded-full animate-bounce delay-100"></span>
                    <span className="w-1 h-1 bg-gray-300 rounded-full animate-bounce delay-200"></span>
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={handleSend} className="p-3 border-t border-gray-150 bg-white flex gap-1.5">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              placeholder="Preguntale algo a la IA..."
              className="flex-1 px-3 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 text-xs disabled:bg-gray-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="p-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-xl shadow-md transition-all flex items-center justify-center"
            >
              <Send size={14} />
            </button>
          </form>
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="h-12 w-12 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center shadow-lg shadow-indigo-600/30 hover:scale-110 active:scale-95 transition-all cursor-pointer"
        title="Chatear con IA"
      >
        {isOpen ? <X size={20} /> : <MessageSquare size={20} />}
      </button>
    </div>
  );
}
