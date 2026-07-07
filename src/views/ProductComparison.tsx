import { useState, useEffect } from 'react';
import { Star, Bell, ArrowLeft, Package } from 'lucide-react';
import { PriceComparisonTable } from '../components/Product/PriceComparisonTable';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { Badge } from '../components/Common/Badge';
import { ApiService } from '../services/api';
import { Product, ProductPrice } from '../types';

interface ProductComparisonProps {
  productId: string;
  onBack: () => void;
}

export function ProductComparison({ productId, onBack }: ProductComparisonProps) {
  const [product, setProduct] = useState<Product | null>(null);
  const [prices, setPrices] = useState<ProductPrice[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadProductData();
  }, [productId]);

  const loadProductData = async () => {
    setIsLoading(true);

    try {
      const [productData, pricesData] = await Promise.all([
        ApiService.getProduct(productId),
        ApiService.getProductPrices(productId),
      ]);

      setProduct(productData);
      setPrices(pricesData);
    } catch (error) {
      console.error('Error loading product data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!product) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
        <p className="text-gray-500">Producto no encontrado.</p>
        <button
          onClick={onBack}
          className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
        >
          Volver a resultados
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft size={20} />
        <span>Volver a resultados</span>
      </button>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex gap-6">
          <div className="w-48 h-48 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
            {product.image ? (
              <img
                src={product.image}
                alt={product.name}
                className="w-full h-full object-cover rounded-lg"
              />
            ) : (
              <Package className="text-gray-400" size={64} />
            )}
          </div>

          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {product.name}
            </h1>

            {product.description && (
              <p className="text-gray-600 mb-4">{product.description}</p>
            )}

            <div className="flex items-center gap-2 mb-4">
              {product.brand && <Badge variant="info">{product.brand}</Badge>}
              {product.category && (
                <Badge variant="info">{product.category}</Badge>
              )}
            </div>

            <div className="flex gap-3">
              <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <Star size={18} />
                <span>Agregar a favoritos</span>
              </button>

              <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <Bell size={18} />
                <span>Crear alerta</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <PriceComparisonTable prices={prices} lastUpdated="hace 5 min" />
    </div>
  );
}
