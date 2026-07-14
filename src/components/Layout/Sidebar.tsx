import { LayoutDashboard, Search, Star, Bell, Sparkles } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useI18n } from '../../context/I18nContext';

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

export function Sidebar({ currentView, onViewChange }: SidebarProps) {
  const { theme } = useTheme();
  const { t } = useI18n();

  const menuItems = [
    { id: 'dashboard', label: t('dashboard'), icon: LayoutDashboard },
    { id: 'search', label: t('search'), icon: Search },
    { id: 'favorites', label: t('favorites'), icon: Star },
    { id: 'alerts', label: t('alerts'), icon: Bell },
    { id: 'assistant', label: t('aiAssistant'), icon: Sparkles },
  ];

  return (
    <aside className={`w-64 border-r min-h-screen transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
      <div className="p-6">
        <h1 className={`text-xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>{t('priceCompare')}</h1>
      </div>

      <nav className="px-3">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors ${isActive
                  ? (theme === 'dark' ? 'bg-blue-900/50 text-blue-400' : 'bg-blue-50 text-blue-600')
                  : (theme === 'dark' ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-50')
                }`}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
