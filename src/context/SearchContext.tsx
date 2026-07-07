import { createContext, useContext, useState, ReactNode } from 'react';
import { SearchResult } from '../types';
import { ApiService } from '../services/api';

export interface FilterState {
    minPrice?: number;
    maxPrice?: number;
    source?: string;
    minRating?: number;
    delivery?: string;
    sortBy?: 'price_asc' | 'price_desc' | 'rating_desc' | 'discount_desc' | 'reviews_desc';
    groupBy?: 'none' | 'source';
}

interface SearchContextType {
    searchQuery: string;
    searchLocation: string;
    results: SearchResult[];
    filteredResults: SearchResult[];
    isLoading: boolean;
    error: string | null;
    filters: FilterState;
    performSearch: (query: string, location: string) => Promise<void>;
    setFilters: (filters: FilterState) => void;
    clearSearch: () => void;
}

const SearchContext = createContext<SearchContextType | undefined>(undefined);

export function SearchProvider({ children }: { children: ReactNode }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchLocation, setSearchLocation] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [filteredResults, setFilteredResults] = useState<SearchResult[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [filters, setFiltersState] = useState<FilterState>({ sortBy: 'price_asc', groupBy: 'none' });

    const applyFilters = (currentResults: SearchResult[], currentFilters: FilterState) => {
        let filtered = [...currentResults];
        const { minPrice, maxPrice, source, minRating, delivery, sortBy, groupBy } = currentFilters;

        // 1. Filtering
        if (source) {
            filtered = filtered.filter((p) =>
                p.source_name?.toLowerCase().includes(source.toLowerCase())
            );
        }

        if (minRating) {
            filtered = filtered.filter((p) =>
                (p.rating || 0) >= minRating
            );
        }

        if (delivery) {
            filtered = filtered.filter((p) =>
                p.delivery?.toLowerCase().includes(delivery.toLowerCase())
            );
        }

        if (minPrice !== undefined && !isNaN(minPrice)) {
            filtered = filtered.filter(
                (p) => (p.price || p.bestPrice || 0) >= minPrice
            );
        }

        if (maxPrice !== undefined && !isNaN(maxPrice)) {
            filtered = filtered.filter(
                (p) => (p.price || p.bestPrice || 0) <= maxPrice
            );
        }

        // 2. Sorting
        filtered.sort((a, b) => {
            // Primary Sort: Grouping
            if (groupBy === 'source') {
                const sourceA = a.source_name || '';
                const sourceB = b.source_name || '';
                const sourceCompare = sourceA.localeCompare(sourceB);
                if (sourceCompare !== 0) return sourceCompare;
            }

            // Secondary Sort: Selected Criteria
            const priceA = a.price || a.bestPrice || 0;
            const priceB = b.price || b.bestPrice || 0;
            const ratingA = a.rating || 0;
            const ratingB = b.rating || 0;
            const reviewsA = a.reviews_count || 0;
            const reviewsB = b.reviews_count || 0;

            switch (sortBy) {
                case 'price_asc':
                    return priceA - priceB;
                case 'price_desc':
                    return priceB - priceA;
                case 'rating_desc':
                    if (ratingB !== ratingA) return ratingB - ratingA;
                    return reviewsB - reviewsA; // Tie-break with reviews
                case 'reviews_desc':
                    return reviewsB - reviewsA;
                case 'discount_desc':
                    const discountA = a.old_price ? ((a.old_price - priceA) / a.old_price) : 0;
                    const discountB = b.old_price ? ((b.old_price - priceB) / b.old_price) : 0;
                    return discountB - discountA;
                default:
                    return 0;
            }
        });

        setFilteredResults(filtered);
    };

    const setFilters = (newFilters: FilterState) => {
        setFiltersState(newFilters);
        applyFilters(results, newFilters);
    };

    const performSearch = async (query: string, location: string) => {
        setSearchQuery(query);
        setSearchLocation(location);
        setIsLoading(true);
        setError(null);

        try {
            const data = await ApiService.searchProducts({ query, location });
            setResults(data);
            applyFilters(data, filters);
        } catch (err) {
            setError('Error al buscar productos. Por favor, intenta nuevamente.');
            console.error(err);
            setResults([]);
            setFilteredResults([]);
        } finally {
            setIsLoading(false);
        }
    };

    const clearSearch = () => {
        setSearchQuery('');
        setSearchLocation('');
        setResults([]);
        setFilteredResults([]);
        setError(null);
        setFiltersState({});
    };

    return (
        <SearchContext.Provider
            value={{
                searchQuery,
                searchLocation,
                results,
                filteredResults,
                isLoading,
                error,
                filters,
                performSearch,
                setFilters,
                clearSearch,
            }}
        >
            {children}
        </SearchContext.Provider>
    );
}

export function useSearch() {
    const context = useContext(SearchContext);
    if (context === undefined) {
        throw new Error('useSearch must be used within a SearchProvider');
    }
    return context;
}
