import { useState } from 'react';
import { Star } from 'lucide-react';
import { FilterState } from '../../context/SearchContext';

interface SearchFiltersProps {
    filters: FilterState;
    onFilterChange: (filters: FilterState) => void;
    availableSources: string[];
}

export function SearchFilters({ filters, onFilterChange, availableSources }: SearchFiltersProps) {
    const [hoverRating, setHoverRating] = useState<number | null>(null);

    const handleInputChange = (key: string, value: string | number) => {
        onFilterChange({ ...filters, [key]: value || undefined });
    };

    const handleClearFilters = () => {
        onFilterChange({});
    };

    return (
        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">Filtros</h3>
                <button
                    onClick={handleClearFilters}
                    className="text-sm text-blue-600 hover:text-blue-700"
                >
                    Limpiar
                </button>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ordenar por
                </label>
                <select
                    value={filters.sortBy || 'price_asc'}
                    onChange={(e) => handleInputChange('sortBy', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="price_asc">Precio: Menor a Mayor</option>
                    <option value="price_desc">Precio: Mayor a Menor</option>
                    <option value="rating_desc">Mejor Puntuado</option>
                    <option value="reviews_desc">Más Reseñado</option>
                    <option value="discount_desc">Mayor Descuento</option>
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Agrupar por
                </label>
                <select
                    value={filters.groupBy || 'none'}
                    onChange={(e) => handleInputChange('groupBy', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="none">Sin agrupar</option>
                    <option value="source">Tienda / Fuente</option>
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tienda / Fuente
                </label>
                <select
                    value={filters.source || ''}
                    onChange={(e) => handleInputChange('source', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">Todas las tiendas</option>
                    {availableSources.map((source) => (
                        <option key={source} value={source}>
                            {source}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Calificación mínima
                </label>
                <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                        <button
                            key={star}
                            type="button"
                            onClick={() => handleInputChange('minRating', star)}
                            onMouseEnter={() => setHoverRating(star)}
                            onMouseLeave={() => setHoverRating(null)}
                            className="focus:outline-none transition-colors"
                        >
                            <Star
                                size={24}
                                className={`${star <= (hoverRating ?? filters.minRating ?? 0)
                                    ? 'fill-yellow-400 text-yellow-400'
                                    : 'text-gray-300'
                                    }`}
                            />
                        </button>
                    ))}
                    <span className="ml-2 text-sm text-gray-600">
                        {(filters.minRating || 0) > 0 ? `${filters.minRating}+` : ''}
                    </span>
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Envío
                </label>
                <select
                    value={filters.delivery || ''}
                    onChange={(e) => handleInputChange('delivery', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">Cualquiera</option>
                    <option value="Gratis">Gratis</option>
                    <option value="No gratis">No gratis</option>
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rango de precio
                </label>
                <div className="grid grid-cols-2 gap-2">
                    <input
                        type="number"
                        value={filters.minPrice || ''}
                        onChange={(e) => handleInputChange('minPrice', parseFloat(e.target.value))}
                        placeholder="Mín"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                        type="number"
                        value={filters.maxPrice || ''}
                        onChange={(e) => handleInputChange('maxPrice', parseFloat(e.target.value))}
                        placeholder="Máx"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>
            </div>
        </div>
    );
}