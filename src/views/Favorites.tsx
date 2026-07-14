import { useState } from 'react';
import { Star } from 'lucide-react';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { useFavorites } from '../context/FavoritesContext';
import { useTheme } from '../context/ThemeContext';
import { useI18n } from '../context/I18nContext';
import { ProductCard } from '../components/Product/ProductCard';
import { ProductModal } from '../components/Product/ProductModal';
import { SearchResult } from '../types';

export function Favorites() {
  const { favorites, isLoading } = useFavorites();
  const { theme } = useTheme();
  const { t } = useI18n();
  const [selectedProduct, setSelectedProduct] = useState<SearchResult | null>(null);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {t('favoritesTitle')}
          </h1>
          <p className={`mt-1 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            {t('favoritesSubtitle')}
          </p>
        </div>
      </div>

      {favorites.length === 0 ? (
        <div className={`rounded-lg border p-12 text-center ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <Star className={`mx-auto mb-4 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`} size={48} />
          <h3 className={`text-lg font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {t('noFavoritesTitle')}
          </h3>
          <p className={`mb-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            {t('noFavoritesDesc')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {favorites.map((favorite) => {
            // Ensure we have valid product data to display
            const productData = favorite.product_data || {
              id: favorite.product_id,
              name: favorite.product_name,
              image: favorite.product_image,
              price: favorite.current_price,
              // Add minimal required fields if product_data is missing
              description: '',
              source_name: 'Unknown',
              currency: '$'
            } as SearchResult;

            return (
              <ProductCard
                key={favorite.id}
                product={productData}
                onSelect={() => setSelectedProduct(productData)}
              />
            );
          })}
        </div>
      )}

      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
        />
      )}
    </div>
  );
}
