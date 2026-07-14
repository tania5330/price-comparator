import { useEffect, useState } from 'react';
import { ApiService } from '../../services/api';
import { Sparkles, TrendingDown, AlertTriangle, Play, HelpCircle } from 'lucide-react';

interface AIPurchaseAdvisorProps {
  productId: string;
  productName: string;
  onCloseModal?: () => void;
}

interface AdviceData {
  verdict: 'BUY' | 'WAIT' | 'HOLD';
  reason: string;
  tips: string[];
}

export function AIPurchaseAdvisor({ productId, productName, onCloseModal }: AIPurchaseAdvisorProps) {
  const [advice, setAdvice] = useState<AdviceData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAdvice() {
      try {
        setIsLoading(true);
        setError(null);
        // Seed first to make sure history exists for analysis
        await ApiService.seedPriceHistory(productId);
        const data = await ApiService.getAIPurchaseAdvice(productId);
        setAdvice(data);
      } catch (err) {
        console.error('Error fetching AI purchase advice:', err);
        setError('No se pudo cargar la recomendación de la IA.');
      } finally {
        setIsLoading(false);
      }
    }

    if (productId) {
      fetchAdvice();
    }
  }, [productId]);

  const handleOpenChat = () => {
    if (onCloseModal) {
      onCloseModal();
    }
    // Dispatch custom event to switch view and pass product context
    window.dispatchEvent(
      new CustomEvent('open-ai-chat', {
        detail: { productId, productName },
      })
    );
  };

  if (isLoading) {
    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-5 animate-pulse">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="text-blue-500 animate-spin" size={18} />
          <div className="h-4 w-48 bg-blue-200 rounded"></div>
        </div>
        <div className="space-y-2">
          <div className="h-3 w-full bg-blue-100 rounded"></div>
          <div className="h-3 w-5/6 bg-blue-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !advice) {
    return null; // Fallback silently or show basic error
  }

  const { verdict, reason, tips } = advice;

  const verdictStyles = {
    BUY: {
      bg: 'bg-emerald-50 border-emerald-200',
      badge: 'bg-emerald-500 text-white',
      text: 'text-emerald-800',
      icon: TrendingDown,
      label: 'COMPRAR AHORA',
      desc: 'El precio es excelente comparado con el promedio histórico.',
    },
    WAIT: {
      bg: 'bg-amber-50 border-amber-200',
      badge: 'bg-amber-500 text-white',
      text: 'text-amber-800',
      icon: AlertTriangle,
      label: 'CONVIENE ESPERAR',
      desc: 'El precio actual está inflado. Los datos sugieren una baja pronto.',
    },
    HOLD: {
      bg: 'bg-slate-50 border-slate-200',
      badge: 'bg-slate-500 text-white',
      text: 'text-slate-800',
      icon: HelpCircle,
      label: 'PRECIO ESTABLE',
      desc: 'Está en su precio normal. Comprá solo si lo necesitás ya.',
    },
  }[verdict];

  const VerdictIcon = verdictStyles.icon;

  return (
    <div className={`border rounded-2xl p-5 ${verdictStyles.bg} transition-all shadow-sm`}>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="text-indigo-600 animate-pulse" size={18} />
          <span className="font-bold text-gray-800 text-sm tracking-wide">RECOMENDACIÓN IA</span>
        </div>
        <span className={`text-xs font-black px-3 py-1 rounded-full ${verdictStyles.badge} tracking-wider`}>
          {verdictStyles.label}
        </span>
      </div>

      <div className="flex gap-3 items-start mb-4">
        <div className={`p-2 rounded-xl bg-white shadow-sm border ${verdictStyles.text}`}>
          <VerdictIcon size={20} />
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-900 leading-snug">{verdictStyles.desc}</p>
          <p className="text-xs text-gray-600 mt-1">{reason}</p>
        </div>
      </div>

      {tips && tips.length > 0 && (
        <div className="border-t border-gray-200/55 pt-3 mt-3">
          <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Sugerencias del Asistente</h4>
          <ul className="space-y-1.5">
            {tips.map((tip, idx) => (
              <li key={idx} className="text-xs text-gray-600 flex items-start gap-1.5">
                <span className="text-indigo-500 font-bold">•</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={handleOpenChat}
        className="w-full mt-4 flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold py-2.5 rounded-xl transition-all shadow-md shadow-indigo-600/10 hover:shadow-indigo-600/20"
      >
        <Play size={14} className="fill-white" />
        Preguntar al Asistente sobre este producto
      </button>
    </div>
  );
}
