import { useState, useEffect, useRef } from 'react';
import { ApiService } from '../../services/api';
import { Sparkles, X, Send, MessageSquare, Bot, User } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useI18n } from '../../context/I18nContext';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function AIFloatingChat() {
  const { theme } = useTheme();
  const { t } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: t('floatingGreeting'),
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
          content: t('floatingError'),
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
        <div className={`absolute bottom-16 right-0 w-80 sm:w-96 h-[480px] border rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-200 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          {/* Header */}
          <div className="bg-indigo-600 text-white px-4 py-3 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="animate-pulse" />
              <div>
                <h3 className="text-sm font-bold">{t('floatingTitle')}</h3>
                <span className="text-[10px] text-indigo-100">{t('floatingStatus')}</span>
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
          <div className={`flex-1 overflow-y-auto p-4 space-y-3 ${theme === 'dark' ? 'bg-gray-900/40' : 'bg-gray-50/40'}`}>
            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              return (
                <div key={idx} className={`flex gap-2 max-w-[85%] ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}>
                  <div
                    className={`h-7 w-7 rounded-lg flex items-center justify-center flex-shrink-0 text-xs shadow-sm border ${
                      isUser 
                        ? 'bg-indigo-600 border-indigo-700 text-white' 
                        : `${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-gray-400' : 'bg-white border-gray-200 text-gray-600'}`
                    }`}
                  >
                    {isUser ? <User size={13} /> : <Bot size={13} />}
                  </div>
                  <div
                    className={`p-3 rounded-xl text-xs leading-relaxed whitespace-pre-line shadow-sm border ${
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
              <div className="flex gap-2 max-w-[85%] mr-auto">
                <div className={`h-7 w-7 rounded-lg flex items-center justify-center border shadow-sm ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-indigo-400' : 'bg-white border-gray-200 text-indigo-600'}`}>
                  <Bot size={13} className="animate-spin" />
                </div>
                <div className={`p-3 rounded-xl rounded-tl-none text-[11px] shadow-sm flex items-center gap-1 border ${theme === 'dark' ? 'bg-gray-800 text-gray-400 border-gray-700' : 'bg-white text-gray-400 border-gray-200'}`}>
                  <span>{t('aiThinking')}</span>
                  <span className="flex gap-0.5 mt-0.5">
                    <span className={`w-1 h-1 rounded-full animate-bounce ${theme === 'dark' ? 'bg-gray-500' : 'bg-gray-300'}`}></span>
                    <span className={`w-1 h-1 rounded-full animate-bounce delay-100 ${theme === 'dark' ? 'bg-gray-500' : 'bg-gray-300'}`}></span>
                    <span className={`w-1 h-1 rounded-full animate-bounce delay-200 ${theme === 'dark' ? 'bg-gray-500' : 'bg-gray-300'}`}></span>
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={handleSend} className={`p-3 border-t flex gap-1.5 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              placeholder={t('floatingPlaceholder')}
              className={`flex-1 px-3 py-2 rounded-xl border focus:outline-none focus:ring-1 focus:ring-indigo-500 text-xs disabled:opacity-50 ${
                theme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-200 text-gray-900'
              }`}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="p-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 text-white rounded-xl shadow-md transition-all flex items-center justify-center"
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
        title={t('floatingTooltip')}
      >
        {isOpen ? <X size={20} /> : <MessageSquare size={20} />}
      </button>
    </div>
  );
}
