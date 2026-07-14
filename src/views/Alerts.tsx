import { useState, useEffect } from 'react';
import { Bell, Pause, Play, Trash2, Plus, Send } from 'lucide-react';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { Badge } from '../components/Common/Badge';
import { PriceAlert } from '../types';
import { ApiService } from '../services/api';

export function Alerts() {
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAlert, setNewAlert] = useState({
    product_name: '',
    target_price: '',
    condition: 'below',
    product_id: '',
  });

  // State for product search
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    setIsLoading(true);
    try {
      const data = await ApiService.getAlerts();
      setAlerts(data);
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchProduct = async (value: string) => {
    setNewAlert({ ...newAlert, product_name: value });
    setSelectedProduct(null);

    if (value.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const data = await ApiService.searchProductsForAlerts(value);
      setSuggestions(data || []);
    } catch (error) {
      console.error('Error searching products:', error);
    }
  };

  const handleSelectProduct = (product: any) => {
    setNewAlert({
      ...newAlert,
      product_name: product.canonical_name || product.name,
      product_id: product.id
    });
    setSelectedProduct(product);
    setSuggestions([]);

    if (product.price) {
      const currentPrice = product.price;
      setNewAlert(prev => ({
        ...prev,
        product_name: product.canonical_name || product.name,
        product_id: product.id,
        target_price: (currentPrice * 0.95).toFixed(2)
      }));
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const currentPrice = selectedProduct?.price || 0;

      const alertData = {
        product_name: newAlert.product_name,
        target_price: parseFloat(newAlert.target_price),
        condition: newAlert.condition,
        product_id: newAlert.product_id || 'manual-' + Date.now(),
        current_price: currentPrice,
        is_active: true,
      };

      const createdAlert = await ApiService.createAlert(alertData);
      setAlerts([createdAlert, ...alerts]);
      setShowCreateForm(false);
      setNewAlert({ product_name: '', target_price: '', condition: 'below', product_id: '' });
      setSelectedProduct(null);

      // Check if condition is met immediately
      const targetPrice = parseFloat(newAlert.target_price);
      let conditionMet = false;

      if (currentPrice > 0) {
        if (newAlert.condition === 'below' && currentPrice < targetPrice) conditionMet = true;
        if (newAlert.condition === 'above' && currentPrice > targetPrice) conditionMet = true;
        if (newAlert.condition === 'equals' && currentPrice === targetPrice) conditionMet = true;
      }

      if (conditionMet) {
        await sendTelegramNotification(createdAlert, selectedProduct?.product_link);
      }

    } catch (error) {
      console.error('Error creating alert:', error);
      window.alert('Error al crear la alerta');
    }
  };

  const handleToggleActive = async (id: string, currentStatus: boolean) => {
    try {
      await ApiService.updateAlert(id, { is_active: !currentStatus });
      setAlerts(alerts.map(a => a.id === id ? { ...a, is_active: !currentStatus } : a));
    } catch (error) {
      console.error('Error updating alert:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Estás seguro de eliminar esta alerta?')) return;
    try {
      await ApiService.deleteAlert(id);
      setAlerts(alerts.filter(a => a.id !== id));
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  const sendTelegramNotification = async (alertItem: PriceAlert, productLink?: string) => {
    const token = import.meta.env.VITE_TELEGRAM_BOT_TOKEN;
    const chatId = import.meta.env.VITE_TELEGRAM_CHAT_ID;

    if (!token || !chatId) {
      window.alert('Credenciales de Telegram no configuradas en .env (se necesitan VITE_TELEGRAM_BOT_TOKEN y VITE_TELEGRAM_CHAT_ID)');
      return;
    }

    let message = `🚨 *Alerta de Precio de Prueba*\n\nProducto: ${alertItem.product_name}\nPrecio Objetivo: $${alertItem.target_price}\nCondición: ${getConditionText(alertItem.condition, alertItem.target_price)}`;

    if (alertItem.current_price > 0) {
      message += `\nPrecio Actual: $${alertItem.current_price}`;
    }

    if (productLink) {
      message += `\n\n[Ver Producto](${productLink})`;
    }

    try {
      const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          chat_id: chatId,
          text: message,
          parse_mode: 'Markdown',
        }),
      });

      if (response.ok) {
        window.alert('¡Notificación enviada a Telegram con éxito! Revisa tu chat.');
      } else {
        const errData = await response.json();
        console.error('Error al enviar notificación Telegram:', errData);
        window.alert(`Error de Telegram: ${errData.description || 'Código incorrecto'}`);
      }
    } catch (error) {
      console.error('Error sending telegram message:', error);
      window.alert('Error de red al intentar conectarse con Telegram.');
    }
  };


  const getConditionText = (condition: string, targetPrice: number) => {
    const conditionMap: Record<string, string> = {
      below: `Menor a $${targetPrice.toFixed(2)}`,
      above: `Mayor a $${targetPrice.toFixed(2)}`,
      equals: `Igual a $${targetPrice.toFixed(2)}`,
    };
    return conditionMap[condition] || condition;
  };

  const isConditionMet = (alert: PriceAlert) => {
    if (!alert.is_active || alert.current_price <= 0) return false;

    const target = alert.target_price;
    const current = alert.current_price;

    if (alert.condition === 'below' && current < target) return true;
    if (alert.condition === 'above' && current > target) return true;
    if (alert.condition === 'equals' && current === target) return true;

    return false;
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alertas de precio</h1>
          <p className="text-gray-600 mt-1">
            Configura alertas para recibir notificaciones cuando los precios cambien
          </p>
        </div>

        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} />
          <span>Nueva alerta</span>
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Crear alerta de precio
          </h3>

          <form onSubmit={handleCreateAlert} className="space-y-4">
            <div className="relative">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Producto (Nombre)
              </label>
              <input
                type="text"
                required
                value={newAlert.product_name}
                onChange={(e) => handleSearchProduct(e.target.value)}
                placeholder="Ej: iPhone 15 Pro"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoComplete="off"
              />
              {suggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
                  {suggestions.map((product, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => handleSelectProduct(product)}
                      className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700 transition-colors flex justify-between items-center"
                    >
                      <span>{product.canonical_name || product.name}</span>
                      {product.price && (
                        <span className="text-gray-500 text-xs">${product.price}</span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Condición
                </label>
                <select
                  value={newAlert.condition}
                  onChange={(e) => setNewAlert({ ...newAlert, condition: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="below">Por debajo de</option>
                  <option value="above">Por encima de</option>
                  <option value="equals">Igual a</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Precio objetivo
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={newAlert.target_price}
                  onChange={(e) => setNewAlert({ ...newAlert, target_price: e.target.value })}
                  placeholder="0.00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Crear alerta
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {alerts.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <Bell className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No tienes alertas configuradas
          </h3>
          <p className="text-gray-600 mb-4">
            Crea alertas para recibir notificaciones cuando los precios cambien
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={20} />
            <span>Crear primera alerta</span>
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Producto
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Condición
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {alerts.map((alert) => {
                const conditionMet = isConditionMet(alert);
                return (
                  <tr
                    key={alert.id}
                    className={`transition-colors ${conditionMet ? 'bg-green-50 hover:bg-green-100' : 'hover:bg-gray-50'
                      }`}
                  >
                    <td className="px-6 py-4">
                      <span className="font-medium text-gray-900">
                        {alert.product_name}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {getConditionText(alert.condition, alert.target_price)}
                    </td>
                    <td className="px-6 py-4">
                      {conditionMet ? (
                        <Badge variant="success">Condición Cumplida</Badge>
                      ) : alert.is_active ? (
                        <Badge variant="info">Activa</Badge>
                      ) : (
                        <Badge variant="warning">Pausada</Badge>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => sendTelegramNotification(alert)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Probar notificación"
                        >
                          <Send size={18} />
                        </button>
                        <button
                          onClick={() => handleToggleActive(alert.id, alert.is_active)}
                          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                          title={alert.is_active ? 'Pausar' : 'Activar'}
                        >
                          {alert.is_active ? (
                            <Pause size={18} />
                          ) : (
                            <Play size={18} />
                          )}
                        </button>
                        <button
                          onClick={() => handleDelete(alert.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Eliminar"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
