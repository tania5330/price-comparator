import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Rutas para guardar modelos y datos
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_models")
os.makedirs(MODEL_DIR, exist_ok=True)

# ------------------------------
# 1. Generador de datos históricos sintéticos
# ------------------------------
def generate_historical_prices(
    base_price: float, 
    days: int = 90, 
    product_name: str = "Producto Genérico"
) -> pd.DataFrame:
    """
    Genera datos históricos sintéticos de precios para simular fluctuaciones
    Incluye tendencias, estacionalidad y ruido.
    """
    # Generar fechas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    
    # Crear características
    n = len(dates)
    day_of_week = dates.dayofweek  # 0=Lunes, 6=Domingo
    day_of_month = dates.day
    month = dates.month
    trend = np.linspace(0, base_price * 0.1, n)  # Tendencia leve al alza
    seasonality = 10 * np.sin(2 * np.pi * day_of_week / 7)  # Efecto semanal
    noise = np.random.normal(0, base_price * 0.05, n)  # Ruido aleatorio
    
    # Precio final con fluctuaciones
    prices = base_price + trend + seasonality + noise
    prices = np.clip(prices, base_price * 0.7, base_price * 1.3)
    
    # Crear DataFrame
    df = pd.DataFrame({
        "date": dates,
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "month": month,
        "price": prices
    })
    
    return df


# ------------------------------
# 2. Entrenamiento del modelo
# ------------------------------
def train_price_prediction_model(
    df: pd.DataFrame, 
    model_name: str = "price_predictor"
) -> Dict:
    """
    Entrena un modelo de regresión lineal para predecir precios futuros
    """
    # Preparar datos
    X = df[["day_of_week", "day_of_month", "month"]]
    y = df["price"]
    
    # Dividir datos
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Escalar características
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Entrenar modelo (Linear Regression como base; puedes cambiar a NN)
    model = LinearRegression()
    model.fit(X_train_scaled, y_train)
    
    # Evaluar modelo
    y_pred = model.predict(X_test_scaled)
    metrics = {
        "mae": mean_absolute_error(y_test, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
        "r2": model.score(X_test_scaled, y_test)
    }
    
    # Guardar modelo y scaler
    model_path = os.path.join(MODEL_DIR, f"{model_name}.joblib")
    scaler_path = os.path.join(MODEL_DIR, f"{model_name}_scaler.joblib")
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    return {
        "model_path": model_path,
        "scaler_path": scaler_path,
        "metrics": metrics,
        "model": model,
        "scaler": scaler
    }


# ------------------------------
# 3. Cargar modelo entrenado
# ------------------------------
def load_model(model_name: str = "price_predictor") -> Optional[Dict]:
    """
    Carga un modelo y scaler previamente entrenados
    """
    try:
        model_path = os.path.join(MODEL_DIR, f"{model_name}.joblib")
        scaler_path = os.path.join(MODEL_DIR, f"{model_name}_scaler.joblib")
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            return {"model": model, "scaler": scaler}
        return None
    except Exception as e:
        print(f"Error al cargar el modelo: {e}")
        return None


# ------------------------------
# 4. Predicción de precios futuros
# ------------------------------
def predict_future_prices(
    model, 
    scaler, 
    days_ahead: int = 7
) -> List[Dict]:
    """
    Predice precios para los próximos 'days_ahead' días
    """
    # Generar fechas futuras
    future_dates = pd.date_range(
        start=datetime.now() + timedelta(days=1), 
        periods=days_ahead, 
        freq="D"
    )
    
    # Preparar características
    X_future = pd.DataFrame({
        "day_of_week": future_dates.dayofweek,
        "day_of_month": future_dates.day,
        "month": future_dates.month
    })
    
    # Escalar y predecir
    X_future_scaled = scaler.transform(X_future)
    predicted_prices = model.predict(X_future_scaled)
    
    # Formatear resultados
    predictions = []
    for i, date in enumerate(future_dates):
        predictions.append({
            "date": date.strftime("%Y-%m-%d"),
            "predicted_price": round(float(predicted_prices[i]), 2)
        })
    
    return predictions


# ------------------------------
# 5. Función principal de ejemplo
# ------------------------------
def main():
    # Ejemplo de uso
    print("Generando datos históricos...")
    df = generate_historical_prices(base_price=50, days=180, product_name="Audífonos")
    
    print("Entrenando modelo...")
    result = train_price_prediction_model(df)
    
    print("Métricas del modelo:")
    print(f"  MAE: ${result['metrics']['mae']:.2f}")
    print(f"  RMSE: ${result['metrics']['rmse']:.2f}")
    print(f"  R²: {result['metrics']['r2']:.2f}")
    
    print("\nPrediciendo precios para la próxima semana:")
    preds = predict_future_prices(result["model"], result["scaler"], days_ahead=7)
    for pred in preds:
        print(f"  {pred['date']}: ${pred['predicted_price']:.2f}")


if __name__ == "__main__":
    main()
