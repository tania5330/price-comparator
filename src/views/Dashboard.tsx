import { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, CheckCircle, Heart, Sparkles, ArrowRight, Tag } from 'lucide-react';
import { Badge } from '../components/Common/Badge';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { ApiService } from '../services/api';
import { ProductModal } from '../components/Product/ProductModal';
import { SearchResult } from '../types';

function DashboardProductImage({ src, alt }: { src?: string; alt: string }) {
  const [imageError, setImageError] = useState(false);

  if (src && !imageError) {
    return (
      <img
        src={src}
        alt={alt}
        onError={() => setImageError(true)}
        className="max-w-full max-h-full object-contain"
      />
    );
  }
  return <Tag className="text-gray-300" size={24} />;
}

interface Opportunity {
  id: string;
  name: string;
  image?: string;
  price: number;
  old_price?: number;
  source_name?: string;
  rating?: number;
  reviews_count?: number;
  product_link: string;
  saving_pct: number;
  avg_price: number;
  min_price: number;
}

export function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    favorites: 0,
    alerts: 0,
    activeAlerts: 0,
  });
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<SearchResult | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statsData, oppsData] = await Promise.all([
        ApiService.getStats(),
        ApiService.getProductOpportunities()
      ]);

      setStats({
        favorites: statsData.favorites || 0,
        alerts: statsData.alerts || 0,
        activeAlerts: statsData.activeAlerts || 0,
      });

      setOpportunities(oppsData || []);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectProduct = (opp: Opportunity) => {
    // Map Opportunity shape to SearchResult shape for the ProductModal
    const searchResult: SearchResult = {
      id: opp.id,
      name: opp.name,
      image: opp.image || '',
      description: '',
      product_link: opp.product_link,
      source_name: opp.source_name || 'Desconocido',
      price: opp.price,
      old_price: opp.old_price,
      currency: '$',
      rating: opp.rating,
      reviews_count: opp.reviews_count,
      scraped_at: new Date().toISOString(),
      bestPrice: opp.price,
      availability: 'in_stock'
    };
    setSelectedProduct(searchResult);
  };

  if (isLoading) {
    return <div className="h-64 flex items-center justify-center"><LoadingSpinner /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Visión general del sistema de comparación de precios e Inteligencia Artificial
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Sistema</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">Activo</p>
            </div>
            <div className="p-3 bg-green-50 text-green-600 rounded-xl border border-green-100">
              <CheckCircle size={22} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-4 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-ping"></span>
            Conectado al backend local
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Favoritos</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.favorites}</p>
            </div>
            <div className="p-3 bg-pink-50 text-pink-600 rounded-xl border border-pink-100">
              <Heart size={22} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-4">
            Productos guardados en tu lista
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Alertas Totales</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.alerts}</p>
            </div>
            <div className="p-3 bg-amber-50 text-amber-600 rounded-xl border border-amber-100">
              <TrendingUp size={22} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-4">
            Monitoreando variaciones de precio
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 font-medium">Alertas Activas</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.activeAlerts}</p>
            </div>
            <div className="p-3 bg-red-50 text-red-600 rounded-xl border border-red-100">
              <AlertCircle size={22} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-4">
            Notificaciones de Telegram habilitadas
          </p>
        </div>
      </div>

      {/* Main Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left/Middle: Opportunities of the Day */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5 border-b pb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="text-indigo-600 animate-pulse" size={20} />
              <h2 className="text-lg font-bold text-gray-900">Oportunidades del Día (Mejores Descuentos)</h2>
            </div>
            <span className="text-xs text-gray-500 font-medium">Análisis de Promedio Histórico</span>
          </div>

          {opportunities.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center text-center p-6 border border-dashed border-gray-200 rounded-2xl">
              <Tag size={40} className="text-gray-300 mb-2" />
              <p className="text-gray-500 font-medium text-sm">No se encontraron ofertas significativas todavía.</p>
              <p className="text-gray-400 text-xs mt-1">Buscá y abrí productos nuevos para recopilar historial y detectar oportunidades.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {opportunities.map((opp) => (
                <div
                  key={opp.id}
                  onClick={() => handleSelectProduct(opp)}
                  className="group bg-gray-50/50 hover:bg-indigo-50/30 border border-gray-150 hover:border-indigo-200 rounded-2xl p-4 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-sm hover:shadow-md"
                >
                  <div className="flex gap-3">
                    <div className="w-16 h-16 bg-white rounded-xl flex-shrink-0 flex items-center justify-center p-2 border border-gray-100">
                      <DashboardProductImage src={opp.image} alt={opp.name} />
                    </div>
                    <div className="min-w-0">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                        {opp.source_name}
                      </span>
                      <h3 className="font-semibold text-gray-900 text-sm mt-1 truncate group-hover:text-indigo-950">
                        {opp.name}
                      </h3>
                      <div className="flex items-center gap-1.5 mt-1.5">
                        <span className="font-bold text-gray-950 text-base">${opp.price.toLocaleString()}</span>
                        <span className="text-xs text-gray-400 line-through">${opp.avg_price.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg">
                      {opp.saving_pct}% de ahorro
                    </span>
                    <span className="text-xs font-semibold text-indigo-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                      Ver oferta <ArrowRight size={12} />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Panel: How to Start / Tips */}
        <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl p-6 border border-blue-200 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-xl font-bold text-indigo-950 mb-3 flex items-center gap-2">
              Comenzá a buscar
            </h2>
            <p className="text-gray-700 text-sm leading-relaxed mb-4">
              Usá la barra de búsqueda en la parte superior para encontrar y comparar precios de productos en múltiples tiendas.
            </p>
            <p className="text-gray-700 text-sm leading-relaxed mb-6">
              Al abrir el detalle de cualquier producto, la IA analizará el historial y te dará consejos de conveniencia instantáneos.
            </p>
          </div>
          <div>
            <Badge variant="info">Listo para usar</Badge>
          </div>
        </div>
      </div>

      {/* Selected Product Modal rendering */}
      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
        />
      )}
    </div>
  );
}
