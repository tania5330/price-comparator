import { Package, Star, Heart } from 'lucide-react';
import { SearchResult } from '../../types';
import { useFavorites } from '../../context/FavoritesContext';

interface ProductCardProps {
  product: SearchResult;
  onSelect: (productId: string) => void;
}

export function ProductCard({ product, onSelect }: ProductCardProps) {
  const { isFavorite, addFavorite, removeFavorite } = useFavorites();
  const isFav = isFavorite(product.id);

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
      className="group bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer flex flex-col h-full relative"
    >
      <div className="aspect-square bg-gray-50 relative overflow-hidden">
        {product.image ? (
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-contain mix-blend-multiply p-4 group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Package className="text-gray-300" size={48} />
          </div>
        )}
        <button
          onClick={handleToggleFavorite}
          className="absolute top-3 right-3 p-2 bg-white/80 backdrop-blur-sm rounded-full shadow-sm hover:bg-white hover:scale-110 active:scale-90 transition-all duration-200 z-10 group/heart"
        >
          <Heart
            size={18}
            className={`${isFav ? "text-red-500 fill-current" : "text-gray-400 group-hover/heart:text-red-400"} transition-colors duration-200`}
          />
        </button>
      </div>

      <div className="p-4 flex flex-col flex-1">
        <div className="mb-2">
          <div className="flex items-center gap-2 mb-1">
            {product.source_name && (
              <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                {product.source_name}
              </span>
            )}
            {product.rating !== undefined && (
              <span className="text-xs font-medium text-yellow-700 bg-yellow-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Star size={10} className="fill-current" />
                {product.rating}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-gray-900 line-clamp-2 min-h-[2.5rem] group-hover:text-blue-600 transition-colors">
            {product.name}
          </h3>
        </div>

        <div className="mt-auto pt-3 border-t border-gray-100 flex items-end justify-between">
          <div>
            {product.old_price && (
              <p className="text-xs text-gray-500 line-through">
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
            <span className="text-xs text-green-600 font-medium bg-green-50 px-2 py-1 rounded-md">
              {product.delivery}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
