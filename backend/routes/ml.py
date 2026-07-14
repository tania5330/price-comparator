from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import os

from .. import ml_model

router = APIRouter()

# ------------------------------
# Schemas Pydantic
# ------------------------------
class TrainModelRequest(BaseModel):
    base_price: float
    days: int = 180
    product_name: str = "Producto Genérico"
    model_name: str = "price_predictor"


class PredictRequest(BaseModel):
    model_name: str = "price_predictor"
    days_ahead: int = 7


# ------------------------------
# Endpoints
# ------------------------------
@router.post("/ml/train")
async def train_model(request: TrainModelRequest):
    """Entrena un modelo de predicción de precios"""
    try:
        df = ml_model.generate_historical_prices(
            base_price=request.base_price,
            days=request.days,
            product_name=request.product_name
        )
        result = ml_model.train_price_prediction_model(df, model_name=request.model_name)
        
        return {
            "status": "success",
            "model_name": request.model_name,
            "metrics": {
                "mae": result["metrics"]["mae"],
                "rmse": result["metrics"]["rmse"],
                "r2": result["metrics"]["r2"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al entrenar el modelo: {str(e)}")


@router.post("/ml/predict")
async def predict_prices(request: PredictRequest):
    """Predice precios futuros usando un modelo entrenado"""
    try:
        loaded = ml_model.load_model(request.model_name)
        if not loaded:
            # Si no hay modelo entrenado, entrenar uno con valores predeterminados
            df = ml_model.generate_historical_prices(base_price=100, days=180)
            result = ml_model.train_price_prediction_model(df, request.model_name)
            loaded = {"model": result["model"], "scaler": result["scaler"]}
            
        predictions = ml_model.predict_future_prices(
            loaded["model"],
            loaded["scaler"],
            days_ahead=request.days_ahead
        )
        
        return {
            "status": "success",
            "model_name": request.model_name,
            "predictions": predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al realizar la predicción: {str(e)}")


@router.get("/ml/models")
async def list_models():
    """Lista todos los modelos guardados"""
    try:
        model_dir = ml_model.MODEL_DIR
        if not os.path.exists(model_dir):
            return {"models": []}
        
        models = [
            f.replace(".joblib", "") 
            for f in os.listdir(model_dir) 
            if f.endswith(".joblib") and not f.endswith("_scaler.joblib")
        ]
        
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar modelos: {str(e)}")


@router.delete("/ml/models/{model_name}")
async def delete_model(model_name: str):
    """Elimina un modelo guardado"""
    try:
        model_path = os.path.join(ml_model.MODEL_DIR, f"{model_name}.joblib")
        scaler_path = os.path.join(ml_model.MODEL_DIR, f"{model_name}_scaler.joblib")
        
        if os.path.exists(model_path):
            os.remove(model_path)
        if os.path.exists(scaler_path):
            os.remove(scaler_path)
            
        return {"status": "success", "message": f"Modelo {model_name} eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el modelo: {str(e)}")
