import { useState } from 'react';
import { Package, Star, Heart } from 'lucide-react';
import { SearchResult } from '../../types';
import { useFavorites } from '../../context/FavoritesContext';
import { useTheme } from '../../context/ThemeContext';

interface ProductCardProps {
  product: SearchResult;
  onSelect: (productId: string) => void;
}

export function ProductCard({ product, onSelect }: ProductCardProps) {
  const { isFavorite, addFavorite, removeFavorite } = useFavorites();
  const { theme } = useTheme();
  const isFav = isFavorite(product.id);
  const [imageError, setImageError] = useState(false);

  const handleToggleFavorite = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isFav) {
      removeFavorite(product.id);
    } else {
      addFavorite(product);
    }
  };

  return (
    <div
      onClick={() => onSelect(product.id)}
      className={`group rounded-xl border overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer flex flex-col h-full relative ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}
    >
      <div className={`aspect-square relative overflow-hidden ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
        {product.image && !imageError ? (
          <img
            src={product.image}
            alt={product.name}
            onError={() => setImageError(true)}
            className="w-full h-full object-contain mix-blend-multiply p-4 group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Package className={theme === 'dark' ? 'text-gray-600' : 'text-gray-300'} size={48} />
          </div>
        )}

        <button
          onClick={handleToggleFavorite}
          className="absolute top-3 right-3 p-2 bg-white/80 backdrop-blur-sm rounded-full shadow-sm hover:bg-white hover:scale-110 active:scale-90 transition-all duration-200 z-10 group/heart"
        >
          <Heart
            size={18}
            className={`${isFav ? "text-red-500 fill-current" : `${theme === 'dark' ? 'text-gray-500 group-hover/heart:text-red-400' : 'text-gray-400 group-hover/heart:text-red-400'}`} transition-colors duration-200`}
          />
        </button>
      </div>

      <div className="p-4 flex flex-col flex-1">
        <div className="mb-2">
          <div className="flex items-center gap-2 mb-1">
            {product.source_name && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${theme === 'dark' ? 'text-blue-400 bg-blue-900/30' : 'text-blue-600 bg-blue-50'}`}>
                {product.source_name}
              </span>
            )}
            {product.rating !== undefined && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full flex items-center gap-1 ${theme === 'dark' ? 'text-yellow-400 bg-yellow-900/30' : 'text-yellow-700 bg-yellow-50'}`}>
                <Star size={10} className="fill-current" />
                {product.rating}
              </span>
            )}
          </div>
          <h3 className={`font-semibold line-clamp-2 min-h-[2.5rem] group-hover:text-blue-600 transition-colors ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {product.name}
          </h3>
        </div>

        <div className={`mt-auto pt-3 border-t flex items-end justify-between ${theme === 'dark' ? 'border-gray-700' : 'border-gray-100'}`}>
          <div>
            {product.old_price && (
              <p className={`text-xs line-through ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                {product.currency || '$'}{product.old_price.toFixed(2)}
              </p>
            )}
            <p className="text-lg font-bold text-blue-600">
              {(product.price !== undefined && product.price !== null && product.price > 0)
                ? `${product.currency || '$'}${product.price.toFixed(2)}`
                : "Ver precio"}
            </p>
          </div>
          {product.delivery && (
            <span className={`text-xs font-medium px-2 py-1 rounded-md ${theme === 'dark' ? 'text-green-400 bg-green-900/30' : 'text-green-600 bg-green-50'}`}>
              {product.delivery}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
