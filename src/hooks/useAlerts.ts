import { useState } from 'react';
import { ApiService } from '../services/api';
import { PriceAlert } from '../types';

export function useAlerts() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const addAlert = async (alert: Omit<PriceAlert, 'id' | 'created_at' | 'updated_at'>) => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await ApiService.createAlert({
                product_name: alert.product_name,
                target_price: alert.target_price,
                condition: alert.condition,
                product_id: alert.product_id,
                current_price: alert.current_price,
                is_active: alert.is_active,
            });
            return data;
        } catch (err: any) {
            console.error('Error adding alert:', err);
            setError(err.message);
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    return { addAlert, isLoading, error };
}
