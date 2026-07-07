import { Search, Star, Bell } from 'lucide-react';

interface HeaderProps {
  onSearch: (payload: { query: string; location: string }) => void;
  onViewChange: (view: string) => void;
}

export function Header({ onSearch, onViewChange }: HeaderProps) {
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
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="px-6 py-4 flex items-center justify-between gap-6">
        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-2xl">
          <div className="flex gap-3 items-center">

            {/* Input de búsqueda */}
            <div className="relative flex-1">
              <Search
                size={18}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
              />
              <input
                type="text"
                name="search"
                placeholder="Buscar productos..."
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Selector de ubicación */}
            <select
              name="location"
              className="w-52 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">USA (default)</option>
              <option value="New York, New York, United States">New York, NY</option>
              <option value="Los Angeles, California, United States">Los Angeles, CA</option>
              <option value="Chicago, Illinois, United States">Chicago, IL</option>
              <option value="Houston, Texas, United States">Houston, TX</option>
              <option value="Miami, Florida, United States">Miami, FL</option>
            </select>

            {/* Botón submit oculto para que Enter funcione */}
            <button type="submit" className="hidden"></button>
          </div>
        </form>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onViewChange('favorites')}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Favoritos"
          >
            <Star size={20} />
          </button>

          <button
            onClick={() => onViewChange('alerts')}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Alertas"
          >
            <Bell size={20} />
          </button>
        </div>
      </div>
    </header>
  );
}
