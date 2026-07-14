import { useState } from 'react';
import { Brain, TrendingUp, Database, BarChart3, Calendar } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { ApiService } from '../services/api';

export const MLPricePredictor = () => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [trainingLoading, setTrainingLoading] = useState(false);
  const [basePrice, setBasePrice] = useState(100);
  const [days, setDays] = useState(180);
  const [productName, setProductName] = useState('Producto X');
  const [modelName, setModelName] = useState('price_predictor');
  const [daysAhead, setDaysAhead] = useState(7);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const trainModel = async () => {
    setTrainingLoading(true);
    setError(null);
    try {
      const data = await ApiService.trainPriceModel({
        base_price: basePrice,
        days: days,
        product_name: productName,
        model_name: modelName
      });
      setMetrics(data.metrics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al entrenar el modelo');
    } finally {
      setTrainingLoading(false);
    }
  };

  const predictPrices = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ApiService.predictPrices({
        model_name: modelName,
        days_ahead: daysAhead
      });
      setPredictions(data.predictions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al realizar la predicción');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`p-6 transition-colors duration-300 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className={`p-3 rounded-xl ${theme === "dark" ? "bg-purple-900/30 text-purple-400" : "bg-purple-100 text-purple-600"}`}>
            <Brain size={32} />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Predicción de Precios</h1>
            <p className={theme === "dark" ? "text-gray-400" : "text-gray-600"}>
              Usa Machine Learning para predecir precios futuros
            </p>
          </div>
        </div>

        {error && (
          <div className={`mb-6 p-4 rounded-lg border ${theme === "dark" ? "bg-red-900/20 text-red-300 border-red-800" : "bg-red-50 text-red-600 border-red-200"}`}>
            {error}
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Columna 1: Entrenamiento */}
          <div className={`p-6 rounded-2xl border ${theme === "dark" ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200"}`}>
            <div className="flex items-center gap-2 mb-6">
              <Database className={theme === "dark" ? "text-blue-400" : "text-blue-500"} />
              <h2 className="text-xl font-semibold">Entrenar Modelo</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-gray-300" : "text-gray-700"}`}>
                  Precio Base del Producto
                </label>
                <input
                  type="number"
                  value={basePrice}
                  onChange={(e) => setBasePrice(Number(e.target.value))}
                  className={`w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all ${theme === "dark" ? "bg-gray-700 border-gray-600 text-white" : "bg-gray-50 border-gray-300 text-gray-900"}`}
                  min={1}
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-gray-300" : "text-gray-700"}`}>
                  Días de Datos Históricos: {days}
                </label>
                <input
                  type="range"
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                  min={30}
                  max={365}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-gray-300" : "text-gray-700"}`}>
                  Nombre del Producto
                </label>
                <input
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  className={`w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all ${theme === "dark" ? "bg-gray-700 border-gray-600 text-white" : "bg-gray-50 border-gray-300 text-gray-900"}`}
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-gray-300" : "text-gray-700"}`}>
                  Nombre del Modelo
                </label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className={`w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all ${theme === "dark" ? "bg-gray-700 border-gray-600 text-white" : "bg-gray-50 border-gray-300 text-gray-900"}`}
                />
              </div>

              <button
                onClick={trainModel}
                disabled={trainingLoading}
                className={`w-full py-3 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${
                  trainingLoading
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700 text-white"
                }`}
              >
                {trainingLoading ? "Entrenando..." : "Entrenar Modelo"}
              </button>
            </div>

            {metrics && (
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <h3 className={`font-semibold mb-4 ${theme === "dark" ? "text-gray-200" : "text-gray-800"}`}>Métricas del Modelo</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className={`p-3 rounded-lg ${theme === "dark" ? "bg-gray-700" : "bg-gray-100"}`}>
                    <p className={`text-xs ${theme === "dark" ? "text-gray-400" : "text-gray-500"}`}>MAE</p>
                    <p className="text-lg font-bold">${metrics.mae.toFixed(2)}</p>
                  </div>
                  <div className={`p-3 rounded-lg ${theme === "dark" ? "bg-gray-700" : "bg-gray-100"}`}>
                    <p className={`text-xs ${theme === "dark" ? "text-gray-400" : "text-gray-500"}`}>RMSE</p>
                    <p className="text-lg font-bold">${metrics.rmse.toFixed(2)}</p>
                  </div>
                  <div className={`p-3 rounded-lg ${theme === "dark" ? "bg-gray-700" : "bg-gray-100"}`}>
                    <p className={`text-xs ${theme === "dark" ? "text-gray-400" : "text-gray-500"}`}>R²</p>
                    <p className="text-lg font-bold">{metrics.r2.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Columna 2: Predicción */}
          <div className={`p-6 rounded-2xl border ${theme === "dark" ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200"}`}>
            <div className="flex items-center gap-2 mb-6">
              <TrendingUp className={theme === "dark" ? "text-green-400" : "text-green-500"} />
              <h2 className="text-xl font-semibold">Predicción de Precios</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-gray-300" : "text-gray-700"}`}>
                  Días a Predecir: {daysAhead}
                </label>
                <input
                  type="range"
                  value={daysAhead}
                  onChange={(e) => setDaysAhead(Number(e.target.value))}
                  min={1}
                  max={30}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
              </div>

              <button
                onClick={predictPrices}
                disabled={loading}
                className={`w-full py-3 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${
                  loading
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-green-600 hover:bg-green-700 text-white"
                }`}
              >
                {loading ? "Prediciendo..." : "Predecir Precios"}
              </button>
            </div>

            {predictions.length > 0 && (
              <div className="mt-6">
                <h3 className={`font-semibold mb-4 ${theme === "dark" ? "text-gray-200" : "text-gray-800"}`}>
                  Predicciones
                </h3>
                <div className={`rounded-lg overflow-hidden border ${theme === "dark" ? "border-gray-700" : "border-gray-200"}`}>
                  <table className="w-full">
                    <thead className={theme === "dark" ? "bg-gray-700" : "bg-gray-50"}>
                      <tr>
                        <th className={`px-4 py-2 text-left text-sm font-semibold ${theme === "dark" ? "text-gray-200" : "text-gray-700"}`}>
                          <Calendar size={16} className="inline mr-2" />
                          Fecha
                        </th>
                        <th className={`px-4 py-2 text-right text-sm font-semibold ${theme === "dark" ? "text-gray-200" : "text-gray-700"}`}>
                          <BarChart3 size={16} className="inline mr-2" />
                          Precio Predicho
                        </th>
                      </tr>
                    </thead>
                    <tbody className={theme === "dark" ? "divide-gray-700" : "divide-gray-200"}>
                      {predictions.map((pred, index) => (
                        <tr key={index} className={theme === "dark" ? "bg-gray-800" : "bg-white"}>
                          <td className={`px-4 py-3 text-sm ${theme === "dark" ? "text-gray-300" : "text-gray-700"}`}>
                            {pred.date}
                          </td>
                          <td className={`px-4 py-3 text-sm text-right font-semibold ${theme === "dark" ? "text-gray-200" : "text-gray-900"}`}>
                            ${pred.predicted_price.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
