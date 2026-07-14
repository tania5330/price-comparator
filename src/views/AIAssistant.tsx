import { useState, useEffect, useRef } from 'react';
import { ApiService } from '../services/api';
import { Sparkles, Send, Bot, User, Trash2, X, AlertCircle } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useI18n } from '../context/I18nContext';

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
  const { theme } = useTheme();
  const { t } = useI18n();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: t('aiGreeting'),
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
          content: `${t('aiProductContextIntro')} **${initialProductContext.name}**. ${t('aiProductContextPrompt')}`,
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
          content: t('aiError'),
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
        content: t('aiClearChat'),
      },
    ]);
    handleRemoveContext();
  };

  const handleRemoveContext = () => {
    setProductContext(null);
    onClearProductContext();
  };

  const suggestions = [
    t('aiSug1'),
    t('aiSug2'),
    t('aiSug3'),
    t('aiSug4'),
  ];

  return (
    <div className={`flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto rounded-2xl border shadow-sm overflow-hidden ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
      {/* Header */}
      <div className={`px-6 py-4 border-b flex items-center justify-between ${theme === 'dark' ? 'bg-gray-900 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-xl ${theme === 'dark' ? 'bg-indigo-900/50 text-indigo-400' : 'bg-indigo-50 text-indigo-600'}`}>
            <Sparkles size={20} className="animate-pulse" />
          </div>
          <div>
            <h2 className={`font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{t('aiTitle')}</h2>
            <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{t('aiSubtitle')}</p>
          </div>
        </div>
        <button
          onClick={handleClearChat}
          title={t('aiClearBtn')}
          className={`p-2 rounded-xl transition-all ${theme === 'dark' ? 'text-gray-400 hover:text-red-400 hover:bg-red-900/20' : 'text-gray-400 hover:text-red-500 hover:bg-red-50'}`}
        >
          <Trash2 size={18} />
        </button>
      </div>

      {/* Product Context Banner */}
      {productContext && (
        <div className={`px-6 py-2 border-b flex items-center justify-between text-xs ${theme === 'dark' ? 'bg-indigo-900/20 border-indigo-900/50 text-indigo-300' : 'bg-indigo-50 border-indigo-100 text-indigo-900'}`}>
          <div className="flex items-center gap-1.5 font-medium truncate">
            <AlertCircle size={14} className={`shrink-0 ${theme === 'dark' ? 'text-indigo-400' : 'text-indigo-600'}`} />
            <span className="truncate">{t('aiProductContextBanner')} <strong className="font-semibold">{productContext.name}</strong></span>
          </div>
          <button
            onClick={handleRemoveContext}
            className={`p-1 rounded transition-colors ${theme === 'dark' ? 'hover:bg-indigo-900/50 text-indigo-400' : 'hover:bg-indigo-100 text-indigo-600'}`}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Messages */}
      <div className={`flex-1 overflow-y-auto p-6 space-y-4 ${theme === 'dark' ? 'bg-gray-900/30' : 'bg-gray-50/30'}`}>
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div key={index} className={`flex gap-3 max-w-[85%] ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}>
              <div
                className={`p-2 rounded-xl shrink-0 h-9 w-9 flex items-center justify-center border shadow-sm ${
                  isUser 
                    ? 'bg-indigo-600 text-white border-indigo-700' 
                    : `${theme === 'dark' ? 'bg-gray-800 text-gray-400 border-gray-700' : 'bg-white text-gray-600 border-gray-200'}`
                }`}
              >
                {isUser ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-line shadow-sm border ${
                  isUser
                    ? 'bg-indigo-600 text-white border-indigo-700 rounded-tr-none'
                    : `${theme === 'dark' ? 'bg-gray-800 text-gray-200 border-gray-700 rounded-tl-none' : 'bg-white text-gray-800 border-gray-200 rounded-tl-none'}`
                }`}
              >
                {msg.content}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex gap-3 max-w-[85%] mr-auto">
            <div className={`p-2 rounded-xl shrink-0 h-9 w-9 flex items-center justify-center border shadow-sm ${theme === 'dark' ? 'bg-gray-800 text-indigo-400 border-gray-700' : 'bg-white text-indigo-600 border-gray-200'}`}>
              <Bot size={16} className="animate-spin" />
            </div>
            <div className={`p-4 rounded-2xl rounded-tl-none text-sm shadow-sm flex items-center gap-1.5 border ${theme === 'dark' ? 'bg-gray-800 text-gray-400 border-gray-700' : 'bg-white text-gray-500 border-gray-200'}`}>
              <span>{t('aiThinking')}</span>
              <span className="flex gap-0.5 mt-1">
                <span className={`w-1.5 h-1.5 rounded-full animate-bounce delay-75 ${theme === 'dark' ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                <span className={`w-1.5 h-1.5 rounded-full animate-bounce delay-150 ${theme === 'dark' ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                <span className={`w-1.5 h-1.5 rounded-full animate-bounce delay-300 ${theme === 'dark' ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts (when no chat yet other than greeting) */}
      {messages.length === 1 && (
        <div className={`px-6 py-3 border-t ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'}`}>
          <p className={`text-xs font-semibold uppercase tracking-wider mb-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{t('aiSuggestionsLabel')}</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((sug, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(sug)}
                className={`text-xs px-3 py-2 rounded-xl font-medium transition-all text-left border ${
                  theme === 'dark' 
                    ? 'bg-gray-700 hover:bg-indigo-900/20 hover:text-indigo-400 border-gray-600 hover:border-indigo-800 text-gray-300' 
                    : 'bg-gray-100 hover:bg-indigo-50 hover:text-indigo-600 border-gray-200 hover:border-indigo-200 text-gray-600'
                }`}
              >
                {sug}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className={`p-4 border-t ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
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
                ? `${t('aiPlaceholderWithProduct')} ${productContext.name}...`
                : t('aiPlaceholderWithoutProduct')
            }
            className={`flex-1 px-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm disabled:opacity-50 ${
              theme === 'dark' 
                ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                : 'bg-white border-gray-200 text-gray-900'
            }`}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl disabled:bg-indigo-800 disabled:shadow-none shadow-md shadow-indigo-600/10 hover:shadow-indigo-600/20 transition-all shrink-0 flex items-center justify-center"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
