import { useMemo, useState } from 'react';
import { useSearch } from '../context/SearchContext';
import { AlertCircle } from 'lucide-react';
import { SearchFilters } from '../components/Search/SearchFilters';
import { ProductCard } from '../components/Product/ProductCard';
import { ProductModal } from '../components/Product/ProductModal';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { SearchResult } from '../types';

export function SearchResults() {
  const {
    searchQuery,
    results,
    filteredResults,
    isLoading,
    error,
    filters,
    setFilters
  } = useSearch();

  const [selectedProduct, setSelectedProduct] = useState<SearchResult | null>(null);

  const availableSources = useMemo(() => {
    const sources = new Set(results.map(p => p.source_name).filter(Boolean));
    return Array.from(sources) as string[];
  }, [results]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Resultados de búsqueda
        </h1>
        <p className="text-gray-600 mt-1">
          {searchQuery && `Búsqueda: "${searchQuery}"`}
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="text-red-600" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <SearchFilters
            filters={filters}
            onFilterChange={setFilters}
            availableSources={availableSources}
          />
        </div>

        <div className="lg:col-span-3">
          {filteredResults.length > 0 ? (
            <div className="space-y-8">
              <p className="text-sm text-gray-600">
                {filteredResults.length} {filteredResults.length === 1 ? 'resultado' : 'resultados'}
              </p>

              {filters.groupBy === 'source' ? (
                // Grouped View
                Object.entries(
                  filteredResults.reduce((acc, product) => {
                    const source = product.source_name || 'Otros';
                    if (!acc[source]) acc[source] = [];
                    acc[source].push(product);
                    return acc;
                  }, {} as Record<string, SearchResult[]>)
                ).map(([source, products]) => (
                  <div key={source} className="space-y-4">
                    <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">
                      {source} <span className="text-sm font-normal text-gray-500">({products.length})</span>
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {products.map((product) => (
                        <ProductCard
                          key={product.id}
                          product={product}
                          onSelect={() => setSelectedProduct(product)}
                        />
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                // Standard Grid View
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {filteredResults.map((product) => (
                    <ProductCard
                      key={product.id}
                      product={product}
                      onSelect={() => setSelectedProduct(product)}
                    />
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <p className="text-gray-500">
                {searchQuery
                  ? 'No se encontraron productos con los criterios especificados.'
                  : 'Realiza una búsqueda para ver resultados.'}
              </p>
            </div>
          )}
        </div>
      </div>

      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
        />
      )}
    </div>
  );
}
