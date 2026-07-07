import { useState } from 'react';
import { Star } from 'lucide-react';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { useFavorites } from '../context/FavoritesContext';
import { ProductCard } from '../components/Product/ProductCard';
import { ProductModal } from '../components/Product/ProductModal';
import { SearchResult } from '../types';

export function Favorites() {
  const { favorites, isLoading } = useFavorites();
  const [selectedProduct, setSelectedProduct] = useState<SearchResult | null>(null);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Favoritos</h1>
          <p className="text-gray-600 mt-1">
            Gestiona tus productos favoritos
          </p>
        </div>
      </div>

      {favorites.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <Star className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No tienes favoritos
          </h3>
          <p className="text-gray-600 mb-4">
            Agrega productos a favoritos para guardarlos aquí
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
