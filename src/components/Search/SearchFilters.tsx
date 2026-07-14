import { useState } from 'react';
import { Star } from 'lucide-react';
import { FilterState } from '../../context/SearchContext';
import { useTheme } from '../../context/ThemeContext';
import { useI18n } from '../../context/I18nContext';

interface SearchFiltersProps {
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
  availableSources: string[];
}

export function SearchFilters({ filters, onFilterChange, availableSources }: SearchFiltersProps) {
    const [hoverRating, setHoverRating] = useState<number | null>(null);
    const { theme } = useTheme();
    const { t } = useI18n();

    const handleInputChange = (key: string, value: string | number) => {
        onFilterChange({ ...filters, [key]: value || undefined });
    };

    const handleClearFilters = () => {
        onFilterChange({});
    };

    return (
        <div className={`rounded-lg border p-4 space-y-4 transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <div className="flex items-center justify-between">
                <h3 className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{t('filtersTitle')}</h3>
                <button
                    onClick={handleClearFilters}
                    className={`text-sm hover:underline transition-colors ${theme === 'dark' ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-700'}`}
                >
                    {t('clearFilters')}
                </button>
            </div>

            <div>
                <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    {t('sortByLabel')}
                </label>
                <select
                    value={filters.sortBy || 'price_asc'}
                    onChange={(e) => handleInputChange('sortBy', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'}`}
                >
                    <option value="price_asc">{t('sortPriceAsc')}</option>
                    <option value="price_desc">{t('sortPriceDesc')}</option>
                    <option value="rating_desc">{t('sortRatingDesc')}</option>
                    <option value="reviews_desc">{t('sortReviewsDesc')}</option>
                    <option value="discount_desc">{t('sortDiscountDesc')}</option>
                </select>
            </div>

            <div>
                <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    {t('groupByLabel')}
                </label>
                <select
                    value={filters.groupBy || 'none'}
                    onChange={(e) => handleInputChange('groupBy', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'}`}
                >
                    <option value="none">{t('groupByNone')}</option>
                    <option value="source">{t('groupBySource')}</option>
                </select>
            </div>

            <div>
                <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    {t('sourceLabel')}
                </label>
                <select
                    value={filters.source || ''}
                    onChange={(e) => handleInputChange('source', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'}`}
                >
                    <option value="">{t('sourceAll')}</option>
                    {availableSources.map((source) => (
                        <option key={source} value={source}>
                            {source}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    {t('minRatingLabel')}
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
                                    : (theme === 'dark' ? 'text-gray-600' : 'text-gray-300')
                                    }`}
                            />
                        </button>
                    ))}
                    <span className={`ml-2 text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                        {(filters.minRating || 0) > 0 ? `${filters.minRating}+` : ''}
                    </span>
                </div>
            </div>

            <div>
                <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    {t('deliveryLabel')}
                </label>
                <select
                    value={filters.delivery || ''}
                    onChange={(e) => handleInputChange('delivery', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'}`}
                >
                    <option value="">{t('deliveryAny')}</option>
                    <option value="Gratis">{t('deliveryFree')}</option>
                    <option value="No gratis">{t('deliveryPaid')}</option>
                </select>
            </div>

            <div>
                <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    {t('priceRangeLabel')}
                </label>
                <div className="grid grid-cols-2 gap-2">
                    <input
                        type="number"
                        value={filters.minPrice || ''}
                        onChange={(e) => handleInputChange('minPrice', parseFloat(e.target.value))}
                        placeholder={t('priceMinPlaceholder')}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'}`}
                    />
                    <input
                        type="number"
                        value={filters.maxPrice || ''}
                        onChange={(e) => handleInputChange('maxPrice', parseFloat(e.target.value))}
                        placeholder={t('priceMaxPlaceholder')}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'}`}
                    />
                </div>
            </div>
        </div>
    );
}