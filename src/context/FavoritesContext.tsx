import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Favorite, SearchResult } from '../types';
import { ApiService } from '../services/api';

interface FavoritesContextType {
    favorites: Favorite[];
    isLoading: boolean;
    addFavorite: (product: SearchResult) => Promise<void>;
    removeFavorite: (productId: string) => Promise<void>;
    isFavorite: (productId: string) => boolean;
}

const FavoritesContext = createContext<FavoritesContextType | undefined>(undefined);

export function FavoritesProvider({ children }: { children: ReactNode }) {
    const [favorites, setFavorites] = useState<Favorite[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadFavorites();
    }, []);

    const loadFavorites = async () => {
        try {
            const data = await ApiService.getFavorites();
            setFavorites(data);
        } catch (error) {
            console.error('Error loading favorites:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const addFavorite = async (product: SearchResult) => {
        try {
            const newFavorite = await ApiService.addFavorite(product);
            setFavorites([newFavorite, ...favorites]);
        } catch (error) {
            console.error('Error adding favorite:', error);
        }
    };

    const removeFavorite = async (productId: string) => {
        try {
            await ApiService.removeFavorite(productId);
            setFavorites(favorites.filter(f => f.product_id !== productId));
        } catch (error) {
            console.error('Error removing favorite:', error);
        }
    };

    const isFavorite = (productId: string) => {
        return favorites.some(f => f.product_id === productId);
    };

    return (
        <FavoritesContext.Provider
            value={{
                favorites,
                isLoading,
                addFavorite,
                removeFavorite,
                isFavorite,
            }}
        >
            {children}
        </FavoritesContext.Provider>
    );
}

export function useFavorites() {
    const context = useContext(FavoritesContext);
    if (context === undefined) {
        throw new Error('useFavorites must be used within a FavoritesProvider');
    }
    return context;
}
