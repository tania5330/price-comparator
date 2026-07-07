import { ExternalLink, TrendingDown, Clock } from 'lucide-react';
import { ProductPrice } from '../../types';
import { Badge } from '../Common/Badge';

interface PriceComparisonTableProps {
  prices: ProductPrice[];
  lastUpdated?: string;
}

export function PriceComparisonTable({ prices, lastUpdated }: PriceComparisonTableProps) {
  const sortedPrices = [...prices].sort((a, b) => a.price - b.price);
  const bestPrice = sortedPrices[0]?.price;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          Comparación de precios
        </h3>
        {lastUpdated && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock size={16} />
            <span>Actualizado {lastUpdated}</span>
          </div>
        )}
      </div>

      {sortedPrices.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <p className="text-gray-500">
            No hay información de precios disponible.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tienda
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Precio
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Envío
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entrega
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reputación
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acción
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sortedPrices.map((priceInfo, index) => (
                <tr
                  key={`${priceInfo.store}-${index}`}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        {priceInfo.store}
                      </span>
                      {priceInfo.price === bestPrice && (
                        <Badge variant="success">
                          <TrendingDown size={12} className="inline mr-1" />
                          Mejor precio
                        </Badge>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-lg font-bold text-gray-900">
                      {priceInfo.currency} {priceInfo.price.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-gray-600">
                      {priceInfo.shipping !== undefined
                        ? priceInfo.shipping === 0
                          ? 'Gratis'
                          : `${priceInfo.currency} ${priceInfo.shipping.toFixed(2)}`
                        : 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-gray-600">
                      {priceInfo.delivery || 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {priceInfo.reputation !== undefined ? (
                      <div className="flex items-center gap-1">
                        <div className="w-12 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${priceInfo.reputation}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600">
                          {priceInfo.reputation}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-gray-400">N/A</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {priceInfo.url ? (
                      <a
                        href={priceInfo.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                      >
                        Ir a la tienda
                        <ExternalLink size={14} />
                      </a>
                    ) : (
                      <span className="text-gray-400 text-sm">
                        No disponible
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
