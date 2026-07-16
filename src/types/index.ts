export interface Product {
  id: string;
  name: string;
  image?: string;
  description?: string;
  category?: string;
  brand?: string;
}

export interface ProductPrice {
  store: string;
  price: number;
  currency: string;
  shipping?: number;
  delivery?: string;
  reputation?: number;
  url?: string;
  lastUpdated?: string;
}

export interface SearchResult extends Product {
  search_id?: string;
  location_id?: string;
  provider_product_id?: string;
  canonical_name?: string;
  product_link?: string;
  source_name?: string;
  price?: number;
  old_price?: number;
  currency?: string;
  price_raw?: string;
  rating?: number | null;
  reviews_count?: number | null;
  tag?: string;
  delivery?: string;
  snippet?: string;
  scraped_at?: string;
  raw?: string;
  bestPrice?: number; // Mantener por compatibilidad si es necesario, o eliminar si ya no se usa
  priceCount?: number;
  availability?: string; // Mantener opcional o eliminar según uso
}

export interface Favorite {
  id: string;
  user_id: string;
  product_id: string;
  product_name: string;
  product_image?: string;
  current_price: number;
  last_updated: string;
  created_at: string;
  product_data?: SearchResult;
}

export interface PriceAlert {
  id: string;
  user_id: string;
  product_id: string;
  product_name: string;
  target_price: number;
  condition: 'below' | 'above' | 'equals';
  current_price: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SearchHistory {
  id: string;
  user_id?: string;
  search_query: string;
  result_count: number;
  created_at: string;
}

export interface PriceHistory {
  id: string;
  product_id: string;
  store_name: string;
  price: number;
  recorded_at: string;
}

export interface DashboardInsights {
  todayTrends: string[];
  mostSearched: SearchResult[];
  recentAlerts: PriceAlert[];
  systemStatus: {
    lastUpdate: string;
    connectedSources: number;
  };
}

export interface MLPrediction {
  date: string;
  predicted_price: number;
  lower_bound?: number;
  upper_bound?: number;
  confidence?: number;
}

export interface MLMetricSummary {
  mae: number;
  rmse: number;
  r2?: number;
}

export interface MLModelSummary {
  model_name: string;
  model_type?: string;
  created_at?: string;
  metrics?: MLMetricSummary;
  stability?: {
    consistency_score?: number;
    mae_mean?: number;
    mae_std?: number;
    rmse_mean?: number;
    rmse_std?: number;
  };
}

export interface MLTrainingResult {
  status: string;
  model_name: string;
  best_model: {
    model_type: string;
    units?: number;
    dropout?: number;
    learning_rate?: number;
    mean_mae?: number;
    mean_rmse?: number;
    std_rmse?: number;
  };
  metrics: MLMetricSummary;
  baseline: {
    model_type: string;
    mean_mae: number;
    mean_rmse: number;
  };
  cross_validation: Array<Record<string, unknown>>;
  stability: Record<string, unknown>;
  statistical_tests: Record<string, unknown>;
  eda: Record<string, unknown>;
  artifact_paths: Record<string, string>;
}
