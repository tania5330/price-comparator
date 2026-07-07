import { useEffect, useState } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';
import { ApiService } from '../../services/api';
import { LoadingSpinner } from '../Common/LoadingSpinner';

interface PriceHistoryChartProps {
    productId: string;
    productName: string;
}

interface ChartData {
    date: string;
    price: number;
    source: string;
}

export function PriceHistoryChart({ productId, productName }: PriceHistoryChartProps) {
    const [data, setData] = useState<ChartData[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchHistory() {
            try {
                setIsLoading(true);
                setError(null);

                const historyData = await ApiService.getPriceHistory(productId);

                const formattedData = (historyData || []).map((item: any) => ({
                    date: new Date(item.recorded_at).toLocaleDateString(),
                    timestamp: new Date(item.recorded_at).getTime(),
                    price: item.price,
                    source: item.store_name || 'Histórico'
                }));

                formattedData.sort((a: any, b: any) => a.timestamp - b.timestamp);
                setData(formattedData);
            } catch (err) {
                console.error('Error fetching price history:', err);
                setError('No se pudo cargar el historial de precios.');
            } finally {
                setIsLoading(false);
            }
        }

        if (productId) {
            fetchHistory();
        }
    }, [productId]);

    if (isLoading) return <div className="h-64 flex items-center justify-center"><LoadingSpinner /></div>;
    if (error) return <div className="text-red-500 text-sm">{error}</div>;
    if (data.length === 0) return <div className="text-gray-500 text-sm">No hay historial de precios disponible.</div>;

    return (
        <div className="w-full mt-4">
            <h3 className="text-lg font-semibold mb-2">Historial de Precios - {productName}</h3>
            <div className="w-full h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                        data={data}
                        margin={{
                            top: 5,
                            right: 30,
                            left: 20,
                            bottom: 5,
                        }}
                    >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            tick={{ fontSize: 12 }}
                            interval="preserveStartEnd"
                        />
                        <YAxis
                            tick={{ fontSize: 12 }}
                            tickFormatter={(value) => `$${value}`}
                        />
                        <Tooltip
                            formatter={(value: number) => [`$${value}`, 'Precio']}
                            labelStyle={{ color: '#374151' }}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="price"
                            stroke="#2563eb"
                            activeDot={{ r: 8 }}
                            name="Precio"
                            strokeWidth={2}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
