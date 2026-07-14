import { Search, Star, Bell, Sun, Moon, Globe } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useI18n } from '../../context/I18nContext';

interface HeaderProps {
  onSearch: (payload: { query: string; location: string }) => void;
  onViewChange: (view: string) => void;
}

export function Header({ onSearch, onViewChange }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useI18n();

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    const query = (formData.get("search") as string)?.trim();
    const location = (formData.get("location") as string)?.trim();

    if (query) {
      onSearch({
        query,
        location: location || "United States" // fallback seguro
      });
    }
  };

  return (
    <header className={`border-b sticky top-0 z-10 transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
      <div className="px-6 py-4 flex items-center justify-between gap-6">
        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-2xl">
          <div className="flex gap-3 items-center">

            {/* Input de búsqueda */}
            <div className="relative flex-1">
              <Search
                size={18}
                className={`absolute left-3 top-1/2 -translate-y-1/2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}
              />
              <input
                type="text"
                name="search"
                placeholder={t('searchPlaceholder')}
                className={`w-full pl-10 pr-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'}`}
              />
            </div>

            {/* Selector de ubicación */}
            <select
              name="location"
              className={`w-52 pr-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
            >
              <option value="">{t('usaDefault')}</option>
              <option value="New York, New York, United States">{t('newYork')}</option>
              <option value="Los Angeles, California, United States">{t('losAngeles')}</option>
              <option value="Chicago, Illinois, United States">{t('chicago')}</option>
              <option value="Houston, Texas, United States">{t('houston')}</option>
              <option value="Miami, Florida, United States">{t('miami')}</option>
            </select>

            {/* Botón submit oculto para que Enter funcione */}
            <button type="submit" className="hidden"></button>
          </div>
        </form>

        <div className="flex items-center gap-2">
          {/* Language switch */}
          <button
            onClick={() => setLanguage(language === 'es' ? 'en' : 'es')}
            className={`p-2 rounded-lg transition-colors flex items-center gap-1 ${theme === 'dark' ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'}`}
            title={language === 'es' ? 'Cambiar a inglés' : 'Switch to Spanish'}
          >
            <Globe size={20} />
            <span className="text-sm font-medium">{language === 'es' ? 'EN' : 'ES'}</span>
          </button>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-lg transition-colors ${theme === 'dark' ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'}`}
            title={theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>

          <button
            onClick={() => onViewChange('favorites')}
            className={`p-2 rounded-lg transition-colors ${theme === 'dark' ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'}`}
            title={t('favorites')}
          >
            <Star size={20} />
          </button>

          <button
            onClick={() => onViewChange('alerts')}
            className={`p-2 rounded-lg transition-colors ${theme === 'dark' ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'}`}
            title={t('alerts')}
          >
            <Bell size={20} />
          </button>
        </div>
      </div>
    </header>
  );
}
