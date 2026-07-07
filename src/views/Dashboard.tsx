import { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, CheckCircle, Heart } from 'lucide-react';
import { Badge } from '../components/Common/Badge';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { ApiService } from '../services/api';

export function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    favorites: 0,
    alerts: 0,
    activeAlerts: 0,
  });

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await ApiService.getStats();
      setStats({
        favorites: data.favorites || 0,
        alerts: data.alerts || 0,
        activeAlerts: data.activeAlerts || 0,
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Visión general del sistema de comparación de precios
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Sistema</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">Activo</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={24} />
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Conectado al backend local
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Favoritos</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.favorites}</p>
            </div>
            <div className="p-3 bg-pink-100 rounded-lg">
              <Heart className="text-pink-600" size={24} />
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Productos guardados
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Alertas Totales</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.alerts}</p>
            </div>
            <div className="p-3 bg-amber-100 rounded-lg">
              <TrendingUp className="text-amber-600" size={24} />
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Monitoreando precios
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Alertas Activas</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.activeAlerts}</p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertCircle className="text-red-600" size={24} />
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Notificaciones habilitadas
          </p>
        </div>
      </div>

      <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-8 border border-blue-200">
        <div className="max-w-2xl">
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Comienza a buscar productos
          </h2>
          <p className="text-gray-700 mb-4">
            Utiliza la barra de búsqueda en la parte superior para encontrar y comparar precios de productos en múltiples tiendas.
          </p>
          <Badge variant="info">Listo para usar</Badge>
        </div>
      </div>
    </div>
  );
}
