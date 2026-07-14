import { useState, useEffect } from 'react';
import { Bell, Pause, Play, Trash2, Plus, Send } from 'lucide-react';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { Badge } from '../components/Common/Badge';
import { PriceAlert } from '../types';
import { ApiService } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { useI18n } from '../context/I18nContext';

export function Alerts() {
  const { theme } = useTheme();
  const { t } = useI18n();
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
      window.alert(t('createAlertError'));
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
    if (!window.confirm(t('deleteConfirm'))) return;
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
      window.alert(t('telegramCredentialsError'));
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
        window.alert(t('telegramSuccess'));
      } else {
        const errData = await response.json();
        console.error('Error al enviar notificación Telegram:', errData);
        window.alert(`${t('telegramError')} ${errData.description || 'Código incorrecto'}`);
      }
    } catch (error) {
      console.error('Error sending telegram message:', error);
      window.alert(t('telegramNetworkError'));
    }
  };


  const getConditionText = (condition: string, targetPrice: number) => {
    const conditionMap: Record<string, string> = {
      below: `${t('belowConditionText')} $${targetPrice.toFixed(2)}`,
      above: `${t('aboveConditionText')} $${targetPrice.toFixed(2)}`,
      equals: `${t('equalsConditionText')} $${targetPrice.toFixed(2)}`,
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
          <h1 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {t('alertsTitle')}
          </h1>
          <p className={`mt-1 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            {t('alertsSubtitle')}
          </p>
        </div>

        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} />
          <span>{t('newAlert')}</span>
        </button>
      </div>

      {showCreateForm && (
        <div className={`rounded-lg border p-6 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <h3 className={`text-lg font-semibold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {t('createAlertTitle')}
          </h3>

          <form onSubmit={handleCreateAlert} className="space-y-4">
            <div className="relative">
              <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                {t('productFieldLabel')}
              </label>
              <input
                type="text"
                required
                value={newAlert.product_name}
                onChange={(e) => handleSearchProduct(e.target.value)}
                placeholder={t('productPlaceholder')}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                autoComplete="off"
              />
              {suggestions.length > 0 && (
                <div className={`absolute z-10 w-full mt-1 border rounded-lg shadow-lg max-h-60 overflow-auto ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  {suggestions.map((product, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => handleSelectProduct(product)}
                      className={`w-full text-left px-4 py-2 text-sm transition-colors flex justify-between items-center ${theme === 'dark' ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-50 text-gray-700'}`}
                    >
                      <span>{product.canonical_name || product.name}</span>
                      {product.price && (
                        <span className={theme === 'dark' ? 'text-gray-400 text-xs' : 'text-gray-500 text-xs'}>
                          ${product.price}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                  {t('conditionFieldLabel')}
                </label>
                <select
                  value={newAlert.condition}
                  onChange={(e) => setNewAlert({ ...newAlert, condition: e.target.value })}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                >
                  <option value="below">{t('conditionBelow')}</option>
                  <option value="above">{t('conditionAbove')}</option>
                  <option value="equals">{t('conditionEquals')}</option>
                </select>
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                  {t('targetPriceLabel')}
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={newAlert.target_price}
                  onChange={(e) => setNewAlert({ ...newAlert, target_price: e.target.value })}
                  placeholder="0.00"
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                {t('createAlertBtn')}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className={`px-4 py-2 border rounded-lg transition-colors ${theme === 'dark' ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`}
              >
                {t('cancelBtn')}
              </button>
            </div>
          </form>
        </div>
      )}

      {alerts.length === 0 ? (
        <div className={`rounded-lg border p-12 text-center ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <Bell className={`mx-auto mb-4 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`} size={48} />
          <h3 className={`text-lg font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {t('noAlertsTitle')}
          </h3>
          <p className={`mb-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            {t('noAlertsDesc')}
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={20} />
            <span>{t('createFirstAlertBtn')}</span>
          </button>
        </div>
      ) : (
        <div className={`rounded-lg border overflow-hidden ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <table className="w-full">
            <thead className={`border-b ${theme === 'dark' ? 'bg-gray-900 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
              <tr>
                <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  {t('productColumn')}
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  {t('conditionColumn')}
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  {t('statusColumn')}
                </th>
                <th className={`px-6 py-3 text-right text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  {t('actionsColumn')}
                </th>
              </tr>
            </thead>
            <tbody className={`divide-y ${theme === 'dark' ? 'divide-gray-700' : 'divide-gray-200'}`}>
              {alerts.map((alert) => {
                const conditionMet = isConditionMet(alert);
                return (
                  <tr
                    key={alert.id}
                    className={`transition-colors ${conditionMet ? (theme === 'dark' ? 'bg-green-900/20 hover:bg-green-900/30' : 'bg-green-50 hover:bg-green-100') : (theme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-50')}`}
                  >
                    <td className="px-6 py-4">
                      <span className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {alert.product_name}
                      </span>
                    </td>
                    <td className={`px-6 py-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      {getConditionText(alert.condition, alert.target_price)}
                    </td>
                    <td className="px-6 py-4">
                      {conditionMet ? (
                        <Badge variant="success">{t('conditionMetBadge')}</Badge>
                      ) : alert.is_active ? (
                        <Badge variant="info">{t('activeBadge')}</Badge>
                      ) : (
                        <Badge variant="warning">{t('pausedBadge')}</Badge>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => sendTelegramNotification(alert)}
                          className={`p-2 rounded-lg transition-colors ${theme === 'dark' ? 'text-blue-400 hover:bg-blue-900/20' : 'text-blue-600 hover:bg-blue-50'}`}
                          title={t('testNotificationTitle')}
                        >
                          <Send size={18} />
                        </button>
                        <button
                          onClick={() => handleToggleActive(alert.id, alert.is_active)}
                          className={`p-2 rounded-lg transition-colors ${theme === 'dark' ? 'text-gray-400 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'}`}
                          title={alert.is_active ? t('pauseTitle') : t('activateTitle')}
                        >
                          {alert.is_active ? (
                            <Pause size={18} />
                          ) : (
                            <Play size={18} />
                          )}
                        </button>
                        <button
                          onClick={() => handleDelete(alert.id)}
                          className={`p-2 rounded-lg transition-colors ${theme === 'dark' ? 'text-red-400 hover:bg-red-900/20' : 'text-red-600 hover:bg-red-50'}`}
                          title={t('deleteTitle')}
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
