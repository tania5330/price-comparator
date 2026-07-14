import { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, CheckCircle, Heart, Sparkles, ArrowRight, Tag } from 'lucide-react';
import { Badge } from '../components/Common/Badge';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { ApiService } from '../services/api';
import { ProductModal } from '../components/Product/ProductModal';
import { SearchResult } from '../types';
import { useTheme } from '../context/ThemeContext';
import { useI18n } from '../context/I18nContext';

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
  const { theme } = useTheme();
  const { t } = useI18n();

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
        <h1 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{t('dashboardTitle')}</h1>
        <p className={`mt-1 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          {t('dashboardSubtitle')}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <div className={`p-6 rounded-2xl border shadow-sm flex flex-col justify-between transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{t('system')}</p>
              <p className={`text-2xl font-bold mt-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{t('active')}</p>
            </div>
            <div className="p-3 bg-green-50 text-green-600 rounded-xl border border-green-100">
              <CheckCircle size={22} />
            </div>
          </div>
          <p className={`text-xs mt-4 flex items-center gap-1 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
            <span className="w-2 h-2 rounded-full bg-green-500 animate-ping"></span>
            {t('connectedBackend')}
          </p>
        </div>

        <div className={`p-6 rounded-2xl border shadow-sm flex flex-col justify-between transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{t('statsFavorites')}</p>
              <p className={`text-2xl font-bold mt-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{stats.favorites}</p>
            </div>
            <div className="p-3 bg-pink-50 text-pink-600 rounded-xl border border-pink-100">
              <Heart size={22} />
            </div>
          </div>
          <p className={`text-xs mt-4 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
            {t('statsFavoritesDesc')}
          </p>
        </div>

        <div className={`p-6 rounded-2xl border shadow-sm flex flex-col justify-between transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{t('statsTotalAlerts')}</p>
              <p className={`text-2xl font-bold mt-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{stats.alerts}</p>
            </div>
            <div className="p-3 bg-amber-50 text-amber-600 rounded-xl border border-amber-100">
              <TrendingUp size={22} />
            </div>
          </div>
          <p className={`text-xs mt-4 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
            {t('statsTotalAlertsDesc')}
          </p>
        </div>

        <div className={`p-6 rounded-2xl border shadow-sm flex flex-col justify-between transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{t('statsActiveAlerts')}</p>
              <p className={`text-2xl font-bold mt-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{stats.activeAlerts}</p>
            </div>
            <div className="p-3 bg-red-50 text-red-600 rounded-xl border border-red-100">
              <AlertCircle size={22} />
            </div>
          </div>
          <p className={`text-xs mt-4 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
            {t('statsActiveAlertsDesc')}
          </p>
        </div>
      </div>

      {/* Main Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left/Middle: Opportunities of the Day */}
        <div className={`lg:col-span-2 rounded-2xl border p-6 shadow-sm transition-colors duration-300 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className={`flex items-center justify-between mb-5 border-b pb-4 ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center gap-2">
              <Sparkles className="text-indigo-600 animate-pulse" size={20} />
              <h2 className={`text-lg font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{t('opportunitiesTitle')}</h2>
            </div>
            <span className={`text-xs font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{t('opportunitiesSubtitle')}</span>
          </div>

          {opportunities.length === 0 ? (
            <div className={`h-64 flex flex-col items-center justify-center text-center p-6 border border-dashed rounded-2xl transition-colors duration-300 ${theme === 'dark' ? 'border-gray-600' : 'border-gray-200'}`}>
              <Tag size={40} className={`mb-2 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-300'}`} />
              <p className={`font-medium text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{t('noOpportunities')}</p>
              <p className={`text-xs mt-1 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>{t('noOpportunitiesHint')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {opportunities.map((opp) => (
                <div
                  key={opp.id}
                  onClick={() => handleSelectProduct(opp)}
                  className={`group rounded-2xl p-4 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-sm hover:shadow-md ${theme === 'dark' ? 'bg-gray-700/50 hover:bg-indigo-900/30 border border-gray-600 hover:border-indigo-700' : 'bg-gray-50/50 hover:bg-indigo-50/30 border border-gray-100 hover:border-indigo-200'}`}
                >
                  <div className="flex gap-3">
                    <div className={`w-16 h-16 rounded-xl flex-shrink-0 flex items-center justify-center p-2 border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'}`}>
                      <DashboardProductImage src={opp.image} alt={opp.name} />
                    </div>
                    <div className="min-w-0">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                        {opp.source_name}
                      </span>
                      <h3 className={`font-semibold text-sm mt-1 truncate group-hover:text-indigo-950 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {opp.name}
                      </h3>
                      <div className="flex items-center gap-1.5 mt-1.5">
                        <span className={`font-bold text-base ${theme === 'dark' ? 'text-white' : 'text-gray-950'}`}>${opp.price.toLocaleString()}</span>
                        <span className={`text-xs line-through ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>${opp.avg_price.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className={`mt-4 pt-3 border-t flex items-center justify-between ${theme === 'dark' ? 'border-gray-700' : 'border-gray-100'}`}>
                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg">
                      {opp.saving_pct}{t('savingPercent')}
                    </span>
                    <span className="text-xs font-semibold text-indigo-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                      {t('viewOffer')} <ArrowRight size={12} />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Panel: How to Start / Tips */}
        <div className={`rounded-2xl p-6 border shadow-sm flex flex-col justify-between transition-colors duration-300 ${theme === 'dark' ? 'bg-gradient-to-br from-indigo-950/50 to-gray-800 border-indigo-700' : 'bg-gradient-to-br from-blue-50 to-indigo-100 border-blue-200'}`}>
          <div>
            <h2 className={`text-xl font-bold mb-3 flex items-center gap-2 ${theme === 'dark' ? 'text-indigo-300' : 'text-indigo-950'}`}>
              {t('startSearchingTitle')}
            </h2>
            <p className={`text-sm leading-relaxed mb-4 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
              {t('startSearchingDesc1')}
            </p>
            <p className={`text-sm leading-relaxed mb-6 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
              {t('startSearchingDesc2')}
            </p>
          </div>
          <div>
            <Badge variant="info">{t('readyToUse')}</Badge>
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
