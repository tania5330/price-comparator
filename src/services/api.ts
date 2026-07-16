import { ENV } from '../config/env';
import {
  Favorite,
  MLModelSummary,
  MLPrediction,
  MLTrainingResult,
  PriceAlert,
  Product,
  ProductPrice,
  SearchResult
} from '../types';

const API = ENV.apiUrl;

export class ApiService {
  // --- Search ---
  static async searchProducts(payload: { query: string; location: string }): Promise<SearchResult[]> {
    const response = await fetch(`${API}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error('Search request failed');
    }

    const data = await response.json();
    return data.map((item: any) => ({
      id: item.id,
      name: item.canonical_name || item.name || 'Producto sin nombre',
      image: item.image,
      description: item.snippet || item.description,
      category: item.category,
      brand: item.brand,
      canonical_name: item.canonical_name,
      product_link: item.product_link,
      source_name: item.source_name,
      price: item.price,
      old_price: item.old_price,
      currency: item.currency,
      price_raw: item.price_raw,
      rating: item.rating,
      reviews_count: item.reviews_count,
      tag: item.tag,
      delivery: item.delivery,
      snippet: item.snippet,
      scraped_at: item.scraped_at,
      raw: item.raw,
      bestPrice: item.price,
      availability: item.delivery ? 'in_stock' : 'unknown',
    }));
  }

  // --- Products ---
  static async getProduct(productId: string): Promise<Product | null> {
    const response = await fetch(`${API}/api/products/${productId}`);
    if (response.status === 404) return null;
    if (!response.ok) throw new Error('Product request failed');
    return response.json();
  }

  static async getProductPrices(productId: string): Promise<ProductPrice[]> {
    const response = await fetch(`${API}/api/products/${productId}/prices`);
    if (!response.ok) throw new Error('Price request failed');
    const data = await response.json();
    return data.map((item: any) => ({
      store: item.store_name || 'Unknown',
      price: item.price,
      currency: '$',
      lastUpdated: item.recorded_at,
    }));
  }

  static async getProducts(filters?: {
    category?: string;
    brand?: string;
    minPrice?: number;
    maxPrice?: number;
  }): Promise<SearchResult[]> {
    const params = new URLSearchParams();
    if (filters?.category) params.append('category', filters.category);
    if (filters?.brand) params.append('brand', filters.brand);
    if (filters?.minPrice !== undefined) params.append('minPrice', String(filters.minPrice));
    if (filters?.maxPrice !== undefined) params.append('maxPrice', String(filters.maxPrice));

    const response = await fetch(`${API}/api/products?${params}`);
    if (!response.ok) throw new Error('Products request failed');
    return response.json();
  }

  static async getProductOpportunities(): Promise<any[]> {
    const response = await fetch(`${API}/api/products/opportunities`);
    if (!response.ok) return [];
    return response.json();
  }

  // --- Favorites ---

  static async getFavorites(): Promise<Favorite[]> {
    const response = await fetch(`${API}/api/favorites`);
    if (!response.ok) throw new Error('Favorites request failed');
    const data = await response.json();
    return data.map((item: any) => ({
      id: String(item.id),
      user_id: '',
      product_id: item.product_id,
      product_name: item.product_data?.name || 'Unknown',
      product_image: item.product_data?.image,
      current_price: item.product_data?.price || item.product_data?.bestPrice || 0,
      last_updated: item.created_at,
      created_at: item.created_at,
      product_data: item.product_data,
    }));
  }

  static async addFavorite(product: SearchResult): Promise<Favorite> {
    const response = await fetch(`${API}/api/favorites`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_id: product.id,
        product_data: product,
      }),
    });
    if (!response.ok) throw new Error('Add favorite failed');
    const data = await response.json();
    return {
      id: String(data.id),
      user_id: '',
      product_id: data.product_id,
      product_name: data.product_data?.name || product.name,
      product_image: data.product_data?.image || product.image,
      current_price: data.product_data?.price || data.product_data?.bestPrice || product.price || 0,
      last_updated: data.created_at,
      created_at: data.created_at,
      product_data: data.product_data,
    };
  }

  static async removeFavorite(productId: string): Promise<void> {
    const response = await fetch(`${API}/api/favorites/${productId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Remove favorite failed');
  }

  // --- Alerts ---
  static async getAlerts(): Promise<PriceAlert[]> {
    const response = await fetch(`${API}/api/alerts`);
    if (!response.ok) throw new Error('Alerts request failed');
    const data = await response.json();
    return data.map((item: any) => ({
      ...item,
      id: String(item.id),
      user_id: '',
      is_active: Boolean(item.is_active),
    }));
  }

  static async createAlert(alertData: {
    product_name: string;
    target_price: number;
    condition: string;
    product_id: string;
    current_price: number;
    is_active: boolean;
  }): Promise<PriceAlert> {
    const response = await fetch(`${API}/api/alerts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(alertData),
    });
    if (!response.ok) throw new Error('Create alert failed');
    const data = await response.json();
    return { ...data, id: String(data.id), user_id: '', is_active: Boolean(data.is_active) };
  }

  static async updateAlert(alertId: string, updates: { is_active?: boolean }): Promise<void> {
    const response = await fetch(`${API}/api/alerts/${alertId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!response.ok) throw new Error('Update alert failed');
  }

  static async deleteAlert(alertId: string): Promise<void> {
    const response = await fetch(`${API}/api/alerts/${alertId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Delete alert failed');
  }

  static async searchProductsForAlerts(query: string): Promise<any[]> {
    const response = await fetch(`${API}/api/alerts/search-products?q=${encodeURIComponent(query)}`);
    if (!response.ok) return [];
    return response.json();
  }

  // --- Stats ---
  static async getStats(): Promise<{ favorites: number; alerts: number; activeAlerts: number }> {
    const response = await fetch(`${API}/api/stats`);
    if (!response.ok) throw new Error('Stats request failed');
    return response.json();
  }

  // --- Price History ---
  static async getPriceHistory(productId: string): Promise<any[]> {
    const response = await fetch(`${API}/api/price-history/${productId}`);
    if (!response.ok) return [];
    return response.json();
  }

  // --- AI Features ---
  static async getAIPurchaseAdvice(productId: string): Promise<{
    verdict: 'BUY' | 'WAIT' | 'HOLD';
    reason: string;
    tips: string[];
  }> {
    const response = await fetch(`${API}/api/ai/advisor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId }),
    });
    if (!response.ok) throw new Error('AI advisor request failed');
    return response.json();
  }

  static async sendAIChatMessage(
    messages: Array<{ role: 'user' | 'assistant'; content: string }>,
    productId?: string
  ): Promise<string> {
    const response = await fetch(`${API}/api/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, product_id: productId ?? null }),
    });
    if (!response.ok) throw new Error('AI chat request failed');
    const data = await response.json();
    return data.reply as string;
  }

  // --- Demo / Seeder ---
  static async seedPriceHistory(productId: string): Promise<void> {
    await fetch(`${API}/api/demo/seed-history`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, days: 30, min_entries: 12 }),
    });
  }

  // --- ML / Price Prediction ---
  static async trainPriceModel(payload: {
    product_id?: string;
    dataset_records?: Array<Record<string, unknown>>;
    base_price?: number;
    days?: number;
    product_name?: string;
    model_name: string;
    sequence_length?: number;
    epochs?: number;
    batch_size?: number;
    validation_splits?: number;
    stability_runs?: number;
    model_types?: string[];
    max_trials?: number;
  }): Promise<MLTrainingResult> {
    const response = await fetch(`${API}/api/ml/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error('Model training failed');
    return response.json();
  }

  static async predictPrices(payload: {
    model_name: string;
    product_id?: string;
    days_ahead: number;
    base_price?: number;
  }): Promise<{
    model_name: string;
    predictions: MLPrediction[];
  }> {
    const response = await fetch(`${API}/api/ml/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error('Price prediction failed');
    return response.json();
  }

  static async getModels(): Promise<{ models: MLModelSummary[] }> {
    const response = await fetch(`${API}/api/ml/models`);
    if (!response.ok) throw new Error('Get models failed');
    return response.json();
  }

  static async getModelReport(modelName: string): Promise<{
    metadata: Record<string, unknown>;
    report_markdown: string;
  }> {
    const response = await fetch(`${API}/api/ml/models/${encodeURIComponent(modelName)}/report`);
    if (!response.ok) throw new Error('Get model report failed');
    return response.json();
  }
}
