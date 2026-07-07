import { X, ExternalLink, Heart, Bell, ShieldCheck, Truck, Store, Star } from 'lucide-react';
import { SearchResult } from '../../types';
import { useFavorites } from '../../context/FavoritesContext';
import { PriceHistoryChart } from './PriceHistoryChart';

interface ProductModalProps {
    product: SearchResult;
    onClose: () => void;
}

export function ProductModal({ product, onClose }: ProductModalProps) {
    const { isFavorite, addFavorite, removeFavorite } = useFavorites();
    // const { addAlert } = useAlerts(); // TODO: Implement alerts
    // const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);

    const isFav = isFavorite(product.id);

    const handleToggleFavorite = () => {
        if (isFav) {
            removeFavorite(product.id);
        } else {
            addFavorite(product);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-200">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 bg-white/80 backdrop-blur rounded-full hover:bg-gray-100 transition-colors z-10"
                >
                    <X size={20} className="text-gray-500" />
                </button>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
                    {/* Image Section */}
                    <div className="relative bg-gray-50 p-8 flex items-center justify-center min-h-[300px] md:min-h-[500px]">
                        <img
                            src={product.image}
                            alt={product.name}
                            className="max-w-full max-h-[400px] object-contain mix-blend-multiply"
                        />
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
                                <div className="flex items-center gap-2 text-sm text-blue-600 font-medium bg-blue-50 px-3 py-1 rounded-full">
                                    <Store size={14} />
                                    {product.source_name || 'Tienda'}
                                </div>
                                {product.rating && (
                                    <div className="flex items-center gap-1 text-amber-500 bg-amber-50 px-3 py-1 rounded-full">
                                        <span className="text-sm font-bold">{product.rating}</span>
                                        <Star size={14} className="fill-amber-500" />
                                        <span className="text-xs text-gray-500">({product.reviews_count})</span>
                                    </div>
                                )}
                            </div>

                            <h2 className="text-2xl font-bold text-gray-900 mb-4 leading-tight">
                                {product.canonical_name || product.name}
                            </h2>

                            <div className="flex items-baseline gap-3 mb-6">
                                <span className="text-4xl font-bold text-gray-900">
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
                                <div className="flex items-center gap-3 text-gray-600">
                                    <Truck size={20} className="text-green-600" />
                                    <span>{product.delivery || 'Envío disponible'}</span>
                                </div>
                                <div className="flex items-center gap-3 text-gray-600">
                                    <ShieldCheck size={20} className="text-blue-600" />
                                    <span>Garantía de compra protegida</span>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3 mb-6">
                                <button
                                    onClick={() => window.open(product.product_link, '_blank')}
                                    className="col-span-2 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-3.5 rounded-xl font-semibold transition-all shadow-lg shadow-blue-600/20 hover:shadow-blue-600/30 hover:-translate-y-0.5"
                                >
                                    <ExternalLink size={20} />
                                    Ver oferta
                                </button>

                                <button
                                    onClick={handleToggleFavorite}
                                    className={`flex items-center justify-center gap-2 py-3 rounded-xl font-medium transition-all border ${isFav
                                        ? 'bg-red-50 border-red-200 text-red-600'
                                        : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                                        }`}
                                >
                                    <Heart size={20} className={isFav ? 'fill-red-600' : ''} />
                                    {isFav ? 'Guardado' : 'Guardar'}
                                </button>

                                <button
                                    onClick={() => window.alert('Funcionalidad de alertas próximamente')}
                                    className="flex items-center justify-center gap-2 bg-white border border-gray-200 text-gray-700 py-3 rounded-xl font-medium hover:bg-gray-50 transition-all"
                                >
                                    <Bell size={20} />
                                    Crear alerta
                                </button>
                            </div>
                        </div>

                        {/* Price History Chart */}
                        <div className="border-t pt-6">
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
