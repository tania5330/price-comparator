import { useEffect, useState } from 'react';
import {
  BarChart3,
  Brain,
  Calendar,
  Database,
  FileText,
  LineChart as LineChartIcon,
  RefreshCcw,
  TrendingUp
} from 'lucide-react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import { useTheme } from '../context/ThemeContext';
import { ApiService } from '../services/api';
import { MLModelSummary, MLPrediction, MLTrainingResult } from '../types';

type TrainingResultWithProfile = MLTrainingResult & {
  training_profile?: string | null;
  training_config?: Record<string, number | string | string[]>;
};

export const MLPricePredictor = () => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [trainingLoading, setTrainingLoading] = useState(false);
  const [modelName, setModelName] = useState('price_predictor');
  const [trainingModelName, setTrainingModelName] = useState('price_predictor');
  const [productId, setProductId] = useState('');
  const [productName, setProductName] = useState('Producto X');
  const [basePrice, setBasePrice] = useState(100);
  const [days, setDays] = useState(120);
  const [sequenceLength, setSequenceLength] = useState(14);
  const [epochs, setEpochs] = useState(5);
  const [maxTrials, setMaxTrials] = useState(1);
  const [trainingKey, setTrainingKey] = useState('');
  const [daysAhead, setDaysAhead] = useState(7);
  const [predictions, setPredictions] = useState<MLPrediction[]>([]);
  const [trainingResult, setTrainingResult] = useState<TrainingResultWithProfile | null>(null);
  const [models, setModels] = useState<MLModelSummary[]>([]);
  const [report, setReport] = useState('');
  const [error, setError] = useState<string | null>(null);

  const panelClass = `p-5 rounded-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`;
  const inputClass = `w-full px-3 py-2 rounded-lg border focus:ring-2 focus:ring-indigo-500 focus:outline-none ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`;
  const mutedText = theme === 'dark' ? 'text-gray-400' : 'text-gray-600';

  const loadModels = async (preferredModel?: string) => {
    try {
      const data = await ApiService.getModels();
      setModels(data.models);
      setModelName((currentModel) => {
        const selectedModel = preferredModel ?? currentModel;
        return data.models.some((model) => model.model_name === selectedModel)
          ? selectedModel
          : data.models[0]?.model_name ?? currentModel
      });
    } catch {
      setModels([]);
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  const trainModel = async () => {
    setTrainingLoading(true);
    setError(null);
    setReport('');
    try {
      const data = await ApiService.trainPriceModel({
        model_name: trainingModelName,
        product_id: productId.trim() || undefined,
        product_name: productName,
        base_price: basePrice,
        days,
        sequence_length: sequenceLength,
        epochs,
        batch_size: 8,
        validation_splits: 2,
        stability_runs: 1,
        model_types: ['gru'],
        max_trials: maxTrials
      }, { trainingKey });
      setTrainingResult(data);
      setModelName(data.model_name);
      await loadModels(data.model_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al entrenar el modelo');
    } finally {
      setTrainingLoading(false);
      setTrainingKey('');
    }
  };

  const predictPrices = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ApiService.predictPrices({
        model_name: modelName,
        product_id: productId.trim() || undefined,
        base_price: basePrice,
        days_ahead: daysAhead
      });
      setPredictions(data.predictions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al realizar la predicción');
    } finally {
      setLoading(false);
    }
  };

  const loadReport = async () => {
    setError(null);
    try {
      const data = await ApiService.getModelReport(modelName);
      setReport(data.report_markdown);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el reporte');
    }
  };

  const formatMoney = (value?: number) => {
    if (value === undefined || Number.isNaN(value)) return '-';
    return `$${value.toFixed(2)}`;
  };

  return (
    <div className={`p-6 transition-colors duration-300 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${theme === 'dark' ? 'bg-indigo-900/30 text-indigo-300' : 'bg-indigo-100 text-indigo-700'}`}>
            <Brain size={30} />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Laboratorio de Predicción Neuronal</h1>
            <p className={mutedText}>
              Demo Render: GRU determinista y acotada. Sus artefactos son temporales en almacenamiento efímero; el bootstrap permanece durable. El laboratorio local conserva EDA, CV y reportes.
            </p>
          </div>
        </div>

        {error && (
          <div className={`p-4 rounded-lg border ${theme === 'dark' ? 'bg-red-900/20 text-red-300 border-red-800' : 'bg-red-50 text-red-600 border-red-200'}`}>
            {error}
          </div>
        )}

        <div className="grid xl:grid-cols-[420px_1fr] gap-6">
          <div className="space-y-6">
            <section className={panelClass}>
              <div className="flex items-center gap-2 mb-4">
                <Database size={20} className={theme === 'dark' ? 'text-blue-300' : 'text-blue-600'} />
                <h2 className="text-lg font-semibold">Dataset y Entrenamiento</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className={`block text-sm font-medium mb-2 ${mutedText}`}>ID de producto guardado</label>
                  <input
                    type="text"
                    value={productId}
                    onChange={(event) => setProductId(event.target.value)}
                    placeholder="Opcional: usa price_history si existe"
                    className={inputClass}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${mutedText}`}>Nombre del modelo a entrenar</label>
                    <input
                      type="text"
                      value={trainingModelName}
                      onChange={(event) => setTrainingModelName(event.target.value)}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${mutedText}`}>Producto</label>
                    <input
                      type="text"
                      value={productName}
                      onChange={(event) => setProductName(event.target.value)}
                      className={inputClass}
                    />
                  </div>
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-2 ${mutedText}`}>Código de acceso al entrenamiento</label>
                  <input
                    type="password"
                    value={trainingKey}
                    onChange={(event) => setTrainingKey(event.target.value)}
                    autoComplete="off"
                    className={inputClass}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${mutedText}`}>Precio base</label>
                    <input
                      type="number"
                      value={basePrice}
                      min={1}
                      onChange={(event) => setBasePrice(Number(event.target.value))}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${mutedText}`}>Días dataset: {days}</label>
                    <input
                      type="range"
                      min={60}
                      max={365}
                      value={days}
                      onChange={(event) => setDays(Number(event.target.value))}
                      className="w-full"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${mutedText}`}>Ventana: {sequenceLength}</label>
                    <input
                      type="range"
                      min={7}
                      max={30}
                      value={sequenceLength}
                      onChange={(event) => setSequenceLength(Number(event.target.value))}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${mutedText}`}>Epochs: {epochs}</label>
                    <input
                      type="range"
                      min={5}
                      max={60}
                      value={epochs}
                      onChange={(event) => setEpochs(Number(event.target.value))}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${mutedText}`}>Trials: {maxTrials}</label>
                    <input
                      type="range"
                      min={1}
                      max={6}
                      value={maxTrials}
                      onChange={(event) => setMaxTrials(Number(event.target.value))}
                      className="w-full"
                    />
                  </div>
                </div>

                <button
                  onClick={trainModel}
                  disabled={trainingLoading}
                  className="w-full py-3 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-500 text-white transition-colors"
                >
                  <RefreshCcw size={18} className={trainingLoading ? 'animate-spin' : ''} />
                  {trainingLoading ? 'Entrenando demo GRU...' : 'Entrenar demo GRU y seleccionar mejor .h5'}
                </button>
              </div>
            </section>

            <section className={panelClass}>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={20} className={theme === 'dark' ? 'text-green-300' : 'text-green-600'} />
                <h2 className="text-lg font-semibold">Predicción</h2>
              </div>
              <label className={`block text-sm font-medium mb-2 ${mutedText}`}>Días a predecir: {daysAhead}</label>
              <input
                type="range"
                min={1}
                max={30}
                value={daysAhead}
                onChange={(event) => setDaysAhead(Number(event.target.value))}
                className="w-full mb-4"
              />
              <button
                onClick={predictPrices}
                disabled={loading}
                className="w-full py-3 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-500 text-white transition-colors"
              >
                <LineChartIcon size={18} />
                {loading ? 'Prediciendo...' : 'Consumir mejor modelo .h5'}
              </button>
            </section>
          </div>

          <div className="space-y-6">
            {trainingResult && (
              <section className={panelClass}>
                <div className="flex items-center justify-between gap-3 mb-4">
                  <div>
                    <h2 className="text-xl font-semibold">Modelo ganador: {trainingResult.best_model.model_type?.toUpperCase()}</h2>
                    <p className={`text-sm ${mutedText}`}>Publicado como {trainingResult.model_name}. Comparado contra baseline lineal con validación temporal.</p>
                  </div>
                  <button
                    onClick={loadReport}
                    className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 border ${theme === 'dark' ? 'border-gray-600 hover:bg-gray-700' : 'border-gray-200 hover:bg-gray-50'}`}
                  >
                    <FileText size={16} />
                    Ver reporte
                  </button>
                </div>

                <div className="grid md:grid-cols-4 gap-3">
                  <MetricBox label="MAE" value={formatMoney(trainingResult.metrics.mae)} theme={theme} />
                  <MetricBox label="RMSE" value={formatMoney(trainingResult.metrics.rmse)} theme={theme} />
                  <MetricBox label="R2" value={trainingResult.metrics.r2?.toFixed(3) ?? '-'} theme={theme} />
                  <MetricBox
                    label="Estabilidad"
                    value={`${Number(trainingResult.stability.consistency_score ?? 0).toFixed(3)}`}
                    theme={theme}
                  />
                </div>

                <div className="grid md:grid-cols-4 gap-3 mt-4 text-sm">
                  <InfoBox title="Baseline lineal" body={`RMSE ${formatMoney(trainingResult.baseline.mean_rmse)} / MAE ${formatMoney(trainingResult.baseline.mean_mae)}`} theme={theme} />
                  <InfoBox title="Validación cruzada" body={`${trainingResult.cross_validation.length} configuraciones evaluadas con TimeSeriesSplit`} theme={theme} />
                  <InfoBox title="Pruebas estadísticas" body={`Std residuos: ${Number(trainingResult.statistical_tests.residual_std ?? 0).toFixed(3)}`} theme={theme} />
                  <InfoBox title="Perfil efectivo" body={`${trainingResult.training_profile ?? 'local'}: ${Object.entries(trainingResult.training_config ?? {}).map(([key, value]) => `${key}=${Array.isArray(value) ? value.join(',') : value}`).join(' · ') || 'sin límites'}`} theme={theme} />
                </div>
              </section>
            )}

            {predictions.length > 0 && (
              <section className={panelClass}>
                <h2 className="text-xl font-semibold mb-4">Forecast con intervalo de confianza</h2>
                <div className="h-[320px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={predictions}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis tickFormatter={(value) => `$${value}`} tick={{ fontSize: 12 }} />
                      <Tooltip formatter={(value: number) => [`$${Number(value).toFixed(2)}`, '']} />
                      <Legend />
                      <Line type="monotone" dataKey="upper_bound" name="Límite superior" stroke="#f59e0b" strokeDasharray="4 4" dot={false} />
                      <Line type="monotone" dataKey="predicted_price" name="Precio predicho" stroke="#16a34a" strokeWidth={3} />
                      <Line type="monotone" dataKey="lower_bound" name="Límite inferior" stroke="#f59e0b" strokeDasharray="4 4" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className={`mt-4 rounded-lg overflow-hidden border ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
                  <table className="w-full text-sm">
                    <thead className={theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'}>
                      <tr>
                        <th className="px-4 py-2 text-left"><Calendar size={15} className="inline mr-2" />Fecha</th>
                        <th className="px-4 py-2 text-right"><BarChart3 size={15} className="inline mr-2" />Predicción</th>
                        <th className="px-4 py-2 text-right">Rango</th>
                        <th className="px-4 py-2 text-right">Confianza</th>
                      </tr>
                    </thead>
                    <tbody className={theme === 'dark' ? 'divide-y divide-gray-700' : 'divide-y divide-gray-200'}>
                      {predictions.map((prediction) => (
                        <tr key={prediction.date}>
                          <td className="px-4 py-2">{prediction.date}</td>
                          <td className="px-4 py-2 text-right font-semibold">{formatMoney(prediction.predicted_price)}</td>
                          <td className="px-4 py-2 text-right">{formatMoney(prediction.lower_bound)} - {formatMoney(prediction.upper_bound)}</td>
                          <td className="px-4 py-2 text-right">{Math.round((prediction.confidence ?? 0) * 100)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            <section className={panelClass}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Modelos guardados</h2>
                <button
                  onClick={() => loadModels()}
                  className={`p-2 rounded-lg border ${theme === 'dark' ? 'border-gray-600 hover:bg-gray-700' : 'border-gray-200 hover:bg-gray-50'}`}
                  title="Actualizar"
                >
                  <RefreshCcw size={16} />
                </button>
              </div>
              {models.length === 0 ? (
                <p className={`text-sm ${mutedText}`}>Todavía no hay modelos `.h5` entrenados.</p>
              ) : (
                <div className="space-y-2">
                  {models.map((model) => (
                    <button
                      key={model.model_name}
                      onClick={() => setModelName(model.model_name)}
                      className={`w-full text-left p-3 rounded-lg border transition-colors ${theme === 'dark' ? 'border-gray-700 hover:bg-gray-700' : 'border-gray-200 hover:bg-gray-50'}`}
                    >
                      <div className="font-semibold">{model.model_name}</div>
                      <div className={`text-xs ${mutedText}`}>
                        {model.model_type?.toUpperCase()} · RMSE {model.metrics?.rmse ?? '-'} · estabilidad {model.stability?.consistency_score ?? '-'}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </section>

            {report && (
              <section className={panelClass}>
                <h2 className="text-lg font-semibold mb-3">Reporte técnico</h2>
                <pre className={`max-h-[360px] overflow-auto text-xs p-4 rounded-lg ${theme === 'dark' ? 'bg-gray-900 text-gray-200' : 'bg-gray-50 text-gray-800'}`}>
                  {report}
                </pre>
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

function MetricBox({ label, value, theme }: { label: string; value: string; theme: string }) {
  return (
    <div className={`p-3 rounded-lg ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-100'}`}>
      <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  );
}

function InfoBox({ title, body, theme }: { title: string; body: string; theme: string }) {
  return (
    <div className={`p-3 rounded-lg border ${theme === 'dark' ? 'border-gray-700 bg-gray-900/30' : 'border-gray-200 bg-gray-50'}`}>
      <p className="font-semibold">{title}</p>
      <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>{body}</p>
    </div>
  );
}
