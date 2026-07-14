import { useState } from 'react';
import { X, ExternalLink, Heart, Bell, ShieldCheck, Truck, Store, Star, Printer, Package } from 'lucide-react';
import { SearchResult } from '../../types';
import { useFavorites } from '../../context/FavoritesContext';
import { useTheme } from '../../context/ThemeContext';
import { PriceHistoryChart } from './PriceHistoryChart';
import { AIPurchaseAdvisor } from './AIPurchaseAdvisor';

interface ProductModalProps {
  product: SearchResult;
  onClose: () => void;
}

export function ProductModal({ product, onClose }: ProductModalProps) {
  const { isFavorite, addFavorite, removeFavorite } = useFavorites();
  const { theme } = useTheme();
  // const { addAlert } = useAlerts(); // TODO: Implement alerts
  // const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);

  const isFav = isFavorite(product.id);
  const [imageError, setImageError] = useState(false);

  const handleToggleFavorite = () => {
    if (isFav) {
      removeFavorite(product.id);
    } else {
      addFavorite(product);
    }
  };

  const handleExportReport = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const productName = product.canonical_name || product.name;
    const currentPrice = product.price ? `$${product.price.toLocaleString()}` : 'Ver precio';
    const sourceName = product.source_name || 'Tienda';
    const ratingInfo = product.rating ? `${product.rating} ⭐ (${product.reviews_count} reseñas)` : 'Sin calificaciones';

    printWindow.document.write(`
      <html>
        <head>
          <title>Reporte de Compra IA - ${productName}</title>
          <style>
            body {
              font-family: 'Inter', system-ui, -apple-system, sans-serif;
              color: #1f2937;
              padding: 40px;
              max-width: 800px;
              margin: 0 auto;
            }
            .header {
              display: flex;
              align-items: center;
              justify-content: space-between;
              border-bottom: 2px solid #e5e7eb;
              padding-bottom: 20px;
              margin-bottom: 30px;
            }
            .logo {
              font-size: 24px;
              font-weight: 800;
              color: #2563eb;
            }
            .report-title {
              font-size: 14px;
              font-weight: 600;
              color: #6b7280;
              text-transform: uppercase;
              letter-spacing: 0.05em;
            }
            .product-container {
              display: flex;
              gap: 40px;
              margin-bottom: 30px;
            }
            .product-image {
              width: 200px;
              height: 200px;
              object-fit: contain;
              border: 1px solid #e5e7eb;
              border-radius: 16px;
              padding: 15px;
              background: #f9fafb;
            }
            .product-details {
              flex: 1;
            }
            .product-title {
              font-size: 22px;
              font-weight: 700;
              color: #111827;
              margin-top: 0;
              margin-bottom: 10px;
            }
            .store-tag {
              display: inline-block;
              background: #eff6ff;
              color: #2563eb;
              font-size: 12px;
              font-weight: 600;
              padding: 4px 12px;
              border-radius: 9999px;
              margin-bottom: 15px;
            }
            .price-box {
              background: #f3f4f6;
              padding: 15px 20px;
              border-radius: 16px;
              margin-bottom: 20px;
            }
            .current-price {
              font-size: 28px;
              font-weight: 800;
              color: #111827;
            }
            .rating-info {
              font-size: 14px;
              color: #4b5563;
              margin-top: 5px;
            }
            .ai-section {
              background: #f5f3ff;
              border: 1px solid #ddd6fe;
              border-radius: 16px;
              padding: 25px;
              margin-top: 30px;
            }
            .ai-header {
              font-weight: 700;
              color: #5b21b6;
              font-size: 16px;
              margin-bottom: 15px;
              display: flex;
              align-items: center;
              gap: 10px;
            }
            .ai-tips {
              margin-top: 15px;
              padding-left: 20px;
              margin-bottom: 0;
            }
            .ai-tips li {
              font-size: 14px;
              color: #4b5563;
              margin-bottom: 8px;
            }
            .footer {
              margin-top: 50px;
              border-top: 1px solid #e5e7eb;
              padding-top: 20px;
              text-align: center;
              font-size: 12px;
              color: #9ca3af;
            }
            @media print {
              body { padding: 0; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">PriceCompare</div>
            <div class="report-title">Reporte IA de Compra Inteligente</div>
          </div>
          
          <div class="product-container">
            <img src="${product.image}" class="product-image" onerror="this.style.display='none'" />
            <div class="product-details">
              <span class="store-tag">Ofrecido por ${sourceName}</span>
              <h1 class="product-title">${productName}</h1>
              <div class="price-box">
                <div class="current-price">${currentPrice}</div>
                <div class="rating-info">${ratingInfo}</div>
              </div>
            </div>
          </div>

          <div class="ai-section">
            <div class="ai-header">🔮 Análisis de Inteligencia Artificial (ChatGPT)</div>
            <div id="ai-verdict-target">
              <p style="font-size: 14px; color: #4b5563;">
                Cargando veredicto de compra y recomendaciones detalladas...
              </p>
            </div>
          </div>

          <div class="footer">
            Reporte generado por PriceCompare el ${new Date().toLocaleDateString()} a las ${new Date().toLocaleTimeString()}.
          </div>

          <script>
            if (window.opener) {
              // Find the parent's recommendation card text contents
              const parentCard = window.opener.document.querySelector('.border.rounded-2xl.p-5');
              if (parentCard) {
                const title = parentCard.querySelector('.tracking-wider')?.textContent || 'RECOMENDACIÓN';
                const desc = parentCard.querySelector('p.text-sm')?.textContent || '';
                const reason = parentCard.querySelector('p.text-xs')?.textContent || '';
                const tipsLi = Array.from(parentCard.querySelectorAll('ul li')).map(li => li.textContent);
                
                let tipsHtml = '';
                if (tipsLi.length > 0) {
                  tipsHtml = '<ul class="ai-tips">' + tipsLi.map(t => '<li>' + t + '</li>').join('') + '</ul>';
                }

                document.getElementById('ai-verdict-target').innerHTML = 
                  '<p style="color: #6d28d9; font-weight: 800; font-size: 16px; margin: 0 0 10px 0;">VEREDICTO: ' + title + '</p>' +
                  '<p style="font-weight: 650; margin: 0 0 8px 0; font-size: 15px;">' + desc + '</p>' +
                  '<p style="font-size: 14px; color: #374151; line-height: 1.5; margin: 0;">' + reason + '</p>' +
                  tipsHtml;
              }
            }
            
            window.onload = function() {
              setTimeout(function() {
                window.print();
              }, 500);
            };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className={`relative rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-200 ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
        <button
          onClick={onClose}
          className={`absolute top-4 right-4 p-2 backdrop-blur rounded-full transition-colors z-10 ${theme === 'dark' ? 'bg-gray-700/80 hover:bg-gray-700' : 'bg-white/80 hover:bg-gray-100'}`}
        >
          <X size={20} className={theme === 'dark' ? 'text-gray-300' : 'text-gray-500'} />
        </button>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
          {/* Image Section */}
          <div className={`relative p-8 flex items-center justify-center min-h-[300px] md:min-h-[500px] ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
            {product.image && !imageError ? (
              <img
                src={product.image}
                alt={product.name}
                onError={() => setImageError(true)}
                className="max-w-full max-h-[400px] object-contain mix-blend-multiply"
              />
            ) : (
              <Package className={theme === 'dark' ? 'text-gray-600' : 'text-gray-300'} size={80} />
            )}
            {product.old_price && (product.price || product.bestPrice) && (
              <div className="absolute top-6 left-6 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold shadow-lg">
                -{Math.round(((product.old_price - (product.price || product.bestPrice || 0)) / product.old_price) * 100)}%
              </div>
            )}
          </div>

          {/* Content Section */}
          <div className="p-8 flex flex-col h-full">
            <div className="flex-1">
              <div className="flex items-start justify-between gap-4 mb-2">
                <div className={`flex items-center gap-2 text-sm font-medium px-3 py-1 rounded-full ${theme === 'dark' ? 'text-blue-400 bg-blue-900/30' : 'text-blue-600 bg-blue-50'}`}>
                  <Store size={14} />
                  {product.source_name || 'Tienda'}
                </div>
                {product.rating && (
                  <div className={`flex items-center gap-1 px-3 py-1 rounded-full ${theme === 'dark' ? 'text-amber-400 bg-amber-900/30' : 'text-amber-500 bg-amber-50'}`}>
                    <span className="text-sm font-bold">{product.rating}</span>
                    <Star size={14} className="fill-amber-500" />
                    <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>({product.reviews_count})</span>
                  </div>
                )}
              </div>

              <h2 className={`text-2xl font-bold mb-4 leading-tight ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                {product.canonical_name || product.name}
              </h2>

              <div className="flex items-baseline gap-3 mb-6">
                <span className={`text-4xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  {(product.price !== undefined && product.price !== null && product.price > 0)
                    ? `${product.currency || '$'}${product.price.toLocaleString()}`
                    : "Ver precio"}
                </span>
                {product.old_price && (
                  <span className="text-lg text-gray-400 line-through">
                    ${product.old_price.toLocaleString()}
                  </span>
                )}
              </div>

              <div className="space-y-4 mb-8">
                <div className={`flex items-center gap-3 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                  <Truck size={20} className="text-green-600" />
                  <span>{product.delivery || 'Envío disponible'}</span>
                </div>
                <div className={`flex items-center gap-3 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                  <ShieldCheck size={20} className="text-blue-600" />
                  <span>Garantía de compra protegida</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-6">
                <button
                  onClick={() => window.open(product.product_link, '_blank')}
                  className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-3.5 rounded-xl font-semibold transition-all shadow-lg shadow-blue-600/20 hover:shadow-blue-600/30 hover:-translate-y-0.5"
                >
                  <ExternalLink size={20} />
                  Ver oferta
                </button>

                <button
                  onClick={handleExportReport}
                  className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white py-3.5 rounded-xl font-semibold transition-all shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/30 hover:-translate-y-0.5"
                >
                  <Printer size={20} />
                  Reporte IA
                </button>

                <button
                  onClick={handleToggleFavorite}
                  className={`flex items-center justify-center gap-2 py-3 rounded-xl font-medium transition-all border ${isFav
                    ? 'bg-red-50 border-red-200 text-red-600'
                    : `${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700' : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'}`
                    }`}
                >
                  <Heart size={20} className={isFav ? 'fill-red-600' : ''} />
                  {isFav ? 'Guardado' : 'Guardar'}
                </button>

                <button
                  onClick={() => window.alert('Funcionalidad de alertas próximamente')}
                  className={`flex items-center justify-center gap-2 py-3 rounded-xl font-medium transition-all border ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700' : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'}`}
                >
                  <Bell size={20} />
                  Crear alerta
                </button>
              </div>
            </div>

            {/* AI Purchase Advisor */}
            <div className={`border-t pt-6 mb-6 ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
              <AIPurchaseAdvisor
                productId={product.id}
                productName={product.canonical_name || product.name}
                onCloseModal={onClose}
              />
            </div>

            {/* Price History Chart */}
            <div className={`border-t pt-6 ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
              <PriceHistoryChart
                productId={product.id}
                productName={product.canonical_name || product.name}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

