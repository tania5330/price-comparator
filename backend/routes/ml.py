import os
import secrets
import threading
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from .. import ml_model
from ..database import get_price_history, get_product


router = APIRouter()
_training_lock = threading.Lock()

_RENDER_DEMO_LIMITS = {
    "days": 120,
    "sequence_length": 14,
    "epochs": 5,
    "batch_size": 8,
    "validation_splits": 2,
    "stability_runs": 1,
    "model_types": ["gru"],
    "max_trials": 1,
}


def _enabled(setting: str, default: bool = True) -> bool:
    value = os.getenv(setting)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class TrainModelRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    product_id: Optional[str] = None
    dataset_records: Optional[List[Dict[str, Any]]] = None
    base_price: Optional[float] = 100
    days: int = 180
    product_name: str = "Producto X"
    model_name: str = "price_predictor"
    sequence_length: int = Field(default=14, ge=3, le=60)
    epochs: int = Field(default=20, ge=5, le=200)
    batch_size: int = Field(default=8, ge=1, le=128)
    validation_splits: int = Field(default=3, ge=2, le=5)
    stability_runs: int = Field(default=3, ge=1, le=5)
    model_types: List[str] = Field(default_factory=lambda: ["gru", "lstm", "mlp"])
    max_trials: int = Field(default=4, ge=1, le=12)


class PredictRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str = "price_predictor"
    product_id: Optional[str] = None
    days_ahead: int = Field(default=7, ge=1, le=30)
    base_price: Optional[float] = None


def _training_data_source(request: TrainModelRequest) -> str:
    if request.dataset_records is not None:
        return "uploaded_dataset"
    if request.product_id:
        return "database_price_history"
    return "synthetic_generator"


def _apply_training_profile(request: TrainModelRequest, profile: str | None) -> tuple[TrainModelRequest, str | None]:
    if not profile:
        return request, None
    if profile != "render_demo":
        raise RuntimeError(f"Unsupported ML training profile: {profile}")
    return request.model_copy(update=_RENDER_DEMO_LIMITS), profile


def _training_config(request: TrainModelRequest) -> dict[str, Any]:
    return {
        "days": request.days,
        "sequence_length": request.sequence_length,
        "epochs": request.epochs,
        "batch_size": request.batch_size,
        "validation_splits": request.validation_splits,
        "stability_runs": request.stability_runs,
        "model_types": request.model_types,
        "max_trials": request.max_trials,
    }


def _render_demo_model_name() -> str:
    return f"render_demo_{uuid.uuid4().hex}"


def _build_training_frame(request: TrainModelRequest) -> tuple[pd.DataFrame, str, float | None]:
    if request.dataset_records is not None:
        return pd.DataFrame(request.dataset_records), request.product_name, request.base_price

    if request.product_id:
        product = get_product(request.product_id) or {}
        product_name = product.get("name") or request.product_name
        base_price = product.get("price") or request.base_price
        history = get_price_history(request.product_id)
        return ml_model.history_to_dataframe(history, product_name), product_name, base_price

    return (
        ml_model.generate_historical_prices(
            base_price=request.base_price or 100,
            days=request.days,
            product_name=request.product_name,
        ),
        request.product_name,
        request.base_price,
    )


def _build_prediction_frame(request: PredictRequest) -> tuple[pd.DataFrame, str, float | None]:
    if request.product_id:
        product = get_product(request.product_id) or {}
        product_name = product.get("name") or "Product"
        base_price = product.get("price") or request.base_price
        history = get_price_history(request.product_id)
        return ml_model.history_to_dataframe(history, product_name), product_name, base_price

    base_price = request.base_price or 100
    return ml_model.generate_historical_prices(base_price=base_price), "Product", base_price


@router.post("/ml/train")
async def train_model(
    request: TrainModelRequest,
    training_key: str | None = Header(default=None, alias="X-ML-Training-Key"),
):
    if not _enabled("ML_TRAINING_ENABLED"):
        raise HTTPException(status_code=403, detail="ML training is disabled for this deployment.")
    training_profile = os.getenv("ML_TRAINING_PROFILE")
    configured_training_key = os.getenv("ML_TRAINING_KEY")
    if training_profile == "render_demo" and not configured_training_key:
        raise HTTPException(status_code=503, detail="ML training key is not configured for this deployment.")
    if configured_training_key and (
        training_key is None or not secrets.compare_digest(training_key, configured_training_key)
    ):
        raise HTTPException(status_code=401, detail="Missing or invalid ML training key.")
    if not _training_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="ML model training is already in progress. Try again after it finishes.")
    try:
        effective_request, profile = _apply_training_profile(request, training_profile)
        if profile == "render_demo":
            effective_request = effective_request.model_copy(update={"model_name": _render_demo_model_name()})

        def train_suite() -> tuple[dict[str, Any], str]:
            df, product_name, base_price = _build_training_frame(effective_request)
            data_source = _training_data_source(effective_request)
            return ml_model.train_model_suite(
                df=df,
                model_name=effective_request.model_name,
                base_price=base_price,
                days=effective_request.days,
                product_name=product_name,
                sequence_length=effective_request.sequence_length,
                epochs=effective_request.epochs,
                batch_size=effective_request.batch_size,
                validation_splits=effective_request.validation_splits,
                stability_runs=effective_request.stability_runs,
                model_types=effective_request.model_types,
                max_trials=effective_request.max_trials,
                data_source=data_source,
            ), data_source

        result, _ = await run_in_threadpool(train_suite)
        return {
            "status": "success",
            "model_name": effective_request.model_name,
            "best_model": result["best_model"],
            "metrics": result["metrics"],
            "baseline": result["baseline"],
            "cross_validation": result["cross_validation"],
            "stability": result["stability"],
            "statistical_tests": result["statistical_tests"],
            "eda": result["eda"],
            "data_source": result["data_source"],
            "artifact_paths": result["artifact_paths"],
            "training_profile": profile,
            "training_config": _training_config(effective_request),
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al entrenar el modelo: {str(exc)}")
    finally:
        _training_lock.release()


@router.post("/ml/predict")
async def predict_prices(request: PredictRequest):
    try:
        df, product_name, base_price = _build_prediction_frame(request)
        predictions = ml_model.predict_with_neural_model(
            model_name=request.model_name,
            df=df,
            days_ahead=request.days_ahead,
            base_price=base_price,
            product_name=product_name,
        )
        return {
            "status": "success",
            "model_name": request.model_name,
            "predictions": predictions,
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al realizar la predicción: {str(exc)}")


@router.get("/ml/models")
async def list_models():
    try:
        return {"models": ml_model.list_model_artifacts()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al listar modelos: {str(exc)}")


@router.get("/ml/models/{model_name}/report")
async def get_model_report(model_name: str):
    report = ml_model.get_model_report(model_name)
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return report


@router.delete("/ml/models/{model_name}")
async def delete_model(model_name: str):
    if not _enabled("ML_MODEL_DELETE_ENABLED"):
        raise HTTPException(status_code=403, detail="ML model deletion is disabled for this deployment.")
    try:
        deleted = ml_model.delete_model_artifacts(model_name)
        return {
            "status": "success",
            "message": f"Modelo {model_name} eliminado",
            "deleted_files": deleted,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el modelo: {str(exc)}")
