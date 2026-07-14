import { useState, useEffect, useRef } from 'react';
import { ApiService } from '../services/api';
import { Sparkles, Send, Bot, User, Trash2, X, AlertCircle } from 'lucide-react';

interface ProductContext {
  id: string;
  name: string;
}

interface AIAssistantProps {
  initialProductContext: ProductContext | null;
  onClearProductContext: () => void;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function AIAssistant({ initialProductContext, onClearProductContext }: AIAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '¡Hola! Soy tu asistente de compras inteligente. 🤖\n\n¿En qué te puedo ayudar hoy? Podés preguntarme sobre productos específicos, presupuestos, o cuándo conviene comprar.',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [productContext, setProductContext] = useState<ProductContext | null>(initialProductContext);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setProductContext(initialProductContext);
    if (initialProductContext) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Entendido. Vamos a hablar sobre **${initialProductContext.name}**. ¿Qué te gustaría saber sobre este producto? (por ejemplo, si conviene comprarlo o si hay mejores opciones).`,
        },
      ]);
    }
  }, [initialProductContext]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: textToSend };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Build the message payload for API
      const chatHistory = [...messages, userMessage].map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const reply = await ApiService.sendAIChatMessage(chatHistory, productContext?.id);
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch (err) {
      console.error('Error in chat:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Disculpame, tuve un problema al procesar tu consulta. Por favor, intentá de nuevo en unos instantes.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Chat reiniciado. ¿En qué te puedo ayudar hoy?',
      },
    ]);
    handleRemoveContext();
  };

  const handleRemoveContext = () => {
    setProductContext(null);
    onClearProductContext();
  };

  const suggestions = [
    '¿Qué celular me recomendás con buena cámara?',
    '¿Cómo sé si un producto está a buen precio?',
    '¿Qué es conveniente comprar hoy?',
    'Dame consejos para ahorrar en mis compras online',
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
            <Sparkles size={20} className="animate-pulse" />
          </div>
          <div>
            <h2 className="font-bold text-gray-900">Asistente de Compras IA</h2>
            <p className="text-xs text-gray-500">Respondido por ChatGPT (gpt-4o-mini)</p>
          </div>
        </div>
        <button
          onClick={handleClearChat}
          title="Limpiar chat"
          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
        >
          <Trash2 size={18} />
        </button>
      </div>

      {/* Product Context Banner */}
      {productContext && (
        <div className="px-6 py-2 bg-indigo-50 border-b border-indigo-100 flex items-center justify-between text-xs text-indigo-900">
          <div className="flex items-center gap-1.5 font-medium truncate">
            <AlertCircle size={14} className="text-indigo-600 shrink-0" />
            <span className="truncate">Preguntando sobre: <strong className="font-semibold">{productContext.name}</strong></span>
          </div>
          <button
            onClick={handleRemoveContext}
            className="p-1 hover:bg-indigo-100 rounded text-indigo-600 transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50/30">
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div key={index} className={`flex gap-3 max-w-[85%] ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}>
              <div
                className={`p-2 rounded-xl shrink-0 h-9 w-9 flex items-center justify-center border shadow-sm ${
                  isUser ? 'bg-indigo-600 text-white border-indigo-700' : 'bg-white text-gray-600 border-gray-200'
                }`}
              >
                {isUser ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-line shadow-sm border ${
                  isUser
                    ? 'bg-indigo-600 text-white border-indigo-700 rounded-tr-none'
                    : 'bg-white text-gray-800 border-gray-200 rounded-tl-none'
                }`}
              >
                {msg.content}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex gap-3 max-w-[85%] mr-auto">
            <div className="p-2 rounded-xl shrink-0 h-9 w-9 flex items-center justify-center bg-white text-indigo-600 border border-gray-200 shadow-sm">
              <Bot size={16} className="animate-spin" />
            </div>
            <div className="bg-white text-gray-500 border border-gray-200 p-4 rounded-2xl rounded-tl-none text-sm shadow-sm flex items-center gap-1.5">
              <span>Pensando</span>
              <span className="flex gap-0.5 mt-1">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-75"></span>
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-150"></span>
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-300"></span>
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts (when no chat yet other than greeting) */}
      {messages.length === 1 && (
        <div className="px-6 py-3 border-t border-gray-100 bg-white">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Preguntas sugeridas</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((sug, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(sug)}
                className="text-xs bg-gray-100 hover:bg-indigo-50 hover:text-indigo-600 border border-gray-200 hover:border-indigo-200 text-gray-600 px-3 py-2 rounded-xl font-medium transition-all text-left"
              >
                {sug}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend(input);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder={
              productContext
                ? `Preguntale a la IA sobre ${productContext.name}...`
                : 'Escribí tu consulta sobre ofertas, precios...'
            }
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm disabled:bg-gray-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl disabled:bg-indigo-300 disabled:shadow-none shadow-md shadow-indigo-600/10 hover:shadow-indigo-600/20 transition-all shrink-0 flex items-center justify-center"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
