import os
import secrets
import threading
from contextlib import contextmanager
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from .. import ml_model
from ..database import (
    get_price_history, get_product,
    get_experiments, get_experiment, get_best_model, save_best_model, save_experiment
)
from ..preprocessing import (
    handle_missing_values, remove_duplicates, remove_outliers,
    scale_features, add_time_features, add_lag_features, add_rolling_features
)
from ..statistical_tests import (
    mann_whitney_test, kolmogorov_smirnov_test, morgan_pitman_test,
    stability_analysis, friedman_test, nemenyi_posthoc_test
)


router = APIRouter()
_training_lock = threading.Lock()


@contextmanager
def _workload_guard(lock: threading.Lock, busy_message: str):
    acquired = lock.acquire(blocking=False)
    if not acquired:
        raise HTTPException(status_code=409, detail=busy_message)
    try:
        yield
    finally:
        lock.release()

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
    model_config = ConfigDict(protected_namespaces=(), extra="allow")

    product_id: Optional[str] = None
    dataset_records: Optional[List[Dict[str, Any]]] = None
    base_price: Optional[float] = 100
    days: int = 180
    product_name: str = "Producto X"
    model_name: str = "price_predictor"
    experiment_name: Optional[str] = None
    experiment_description: Optional[str] = None
    sequence_length: int = Field(default=7, ge=3, le=60)
    epochs: int = Field(default=10, ge=5, le=200)
    batch_size: int = Field(default=16, ge=1, le=128)
    validation_splits: int = Field(default=2, ge=2, le=5)
    stability_runs: int = Field(default=2, ge=1, le=20)
    model_types: List[str] = Field(default_factory=lambda: ["gru"])
    max_trials: int = Field(default=2, ge=1, le=12)
    hidden_units: int = Field(default=32, ge=8, le=256)
    num_layers: int = Field(default=1, ge=1, le=4)
    dropout: float = Field(default=0.15, ge=0.0, le=0.5)
    learning_rate: float = Field(default=0.001, gt=0)
    optimizer: str = "Adam"
    loss_function: str = "MSE"


class ValidateAndOptimizeRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), extra="allow")

    product_id: Optional[str] = None
    dataset_records: Optional[List[Dict[str, Any]]] = None
    base_price: Optional[float] = 100
    days: int = 180
    product_name: str = "Producto X"
    model_name: str = "price_predictor"
    experiment_name: Optional[str] = "EXP-001"
    sequence_length: int = Field(default=7, ge=3, le=60)
    epochs: int = Field(default=10, ge=5, le=200)
    batch_size: int = Field(default=16, ge=1, le=128)
    validation_splits: int = Field(default=5, ge=2, le=10)
    model_type: str = "gru"
    hidden_units: int = Field(default=32, ge=8, le=256)
    num_layers: int = Field(default=1, ge=1, le=4)
    dropout: float = Field(default=0.15, ge=0.0, le=0.5)
    learning_rate: float = Field(default=0.001, gt=0)
    optimizer: str = "Adam"
    loss_function: str = "mse"
    optimization_method: str = "grid"
    max_iterations: int = Field(default=25, ge=5, le=100)
    use_early_stopping: bool = True
    patience: int = Field(default=5, ge=2, le=20)
    retrain_automatically: bool = True


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
        "hidden_units": request.hidden_units,
        "num_layers": request.num_layers,
        "dropout": request.dropout,
        "learning_rate": request.learning_rate,
        "optimizer": request.optimizer,
        "loss_function": request.loss_function,
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
    with _workload_guard(
        _training_lock,
        "ML model training is already in progress. Try again after it finishes.",
    ):
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
                hidden_units=effective_request.hidden_units,
                num_layers=effective_request.num_layers,
                dropout=effective_request.dropout,
                learning_rate=effective_request.learning_rate,
                optimizer=effective_request.optimizer,
                loss_function=effective_request.loss_function,
            ), data_source

        try:
            result, data_source = await run_in_threadpool(train_suite)

            experiment_id = None
            try:
                experiment_id = save_experiment({
                    "created_at": result.get("created_at"),
                    "dataset_name": effective_request.experiment_name or effective_request.product_name,
                    "dataset_source": data_source,
                    "model_type": result.get("best_model", {}).get("model_type"),
                    "random_seed": result.get("best_model", {}).get("seed"),
                    "hyperparameters": _training_config(effective_request),
                    "rmse": result.get("metrics", {}).get("rmse"),
                    "mae": result.get("metrics", {}).get("mae"),
                    "r2": result.get("metrics", {}).get("r2"),
                    "loss": effective_request.loss_function,
                    "model_path": result.get("artifact_paths", {}).get("model_path"),
                    "history_path": result.get("artifact_paths", {}).get("history_path"),
                    "scaler_path": result.get("artifact_paths", {}).get("scaler_path"),
                    "metadata_path": result.get("artifact_paths", {}).get("metadata_path"),
                    "report_html_path": result.get("artifact_paths", {}).get("report_html"),
                    "report_pdf_path": result.get("artifact_paths", {}).get("report_pdf"),
                    "is_best": True,
                })
            except Exception:
                experiment_id = None

            return {
                "status": "success",
                "model_name": effective_request.model_name,
                "experiment_id": experiment_id,
                "best_model": result["best_model"],
                "best_architecture": result.get("best_architecture"),
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


@router.post("/ml/validate-and-optimize")
async def validate_and_optimize_model_endpoint(
    request: ValidateAndOptimizeRequest,
    training_key: str | None = Header(default=None, alias="X-ML-Training-Key"),
):
    if not _enabled("ML_TRAINING_ENABLED"):
        raise HTTPException(status_code=403, detail="ML training is disabled for this deployment.")
    configured_training_key = os.getenv("ML_TRAINING_KEY")
    if configured_training_key and (
        training_key is None or not secrets.compare_digest(training_key, configured_training_key)
    ):
        raise HTTPException(status_code=401, detail="Missing or invalid ML training key.")

    def validate_and_optimize() -> dict[str, Any]:
        if request.dataset_records is not None:
            df = pd.DataFrame(request.dataset_records)
        elif request.product_id:
            product = get_product(request.product_id) or {}
            product_name = product.get("name") or request.product_name
            base_price = product.get("price") or request.base_price
            history = get_price_history(request.product_id)
            df = ml_model.history_to_dataframe(history, product_name)
        else:
            df = ml_model.generate_historical_prices(
                base_price=request.base_price or 100,
                days=request.days,
                product_name=request.product_name,
            )
        return ml_model.validate_and_optimize_model(
            df=df,
            model_name=request.model_name,
            base_price=request.base_price,
            days=request.days,
            product_name=request.product_name,
            sequence_length=request.sequence_length,
            epochs=request.epochs,
            batch_size=request.batch_size,
            validation_splits=request.validation_splits,
            model_type=request.model_type,
            hidden_units=request.hidden_units,
            num_layers=request.num_layers,
            dropout=request.dropout,
            learning_rate=request.learning_rate,
            optimizer=request.optimizer,
            loss_function=request.loss_function,
            optimization_method=request.optimization_method,
            max_iterations=request.max_iterations,
            use_early_stopping=request.use_early_stopping,
            patience=request.patience,
            retrain_automatically=request.retrain_automatically,
            experiment_name=request.experiment_name or "EXP-001",
        )

    try:
        return await run_in_threadpool(validate_and_optimize)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al validar y optimizar el modelo: {str(exc)}")


class StatisticalValidationRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), extra="allow")
    training_result: Dict[str, Any]
    experiment_name: str = "EXP-001"


class PublishModelRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), extra="allow")
    model_name: str = "price_predictor_v2"
    new_model_name: str = "best_model"


@router.post("/ml/statistical-validation")
async def statistical_validation_endpoint(
    request: StatisticalValidationRequest,
    training_key: str | None = Header(default=None, alias="X-ML-Training-Key")
):
    try:
        validated_result = ml_model.run_statistical_validation(
            request.training_result,
            request.experiment_name
        )
        return validated_result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar validación estadística: {str(exc)}")


@router.get("/ml/model-history")
async def get_model_history():
    from .database import get_best_models_history
    try:
        history = get_best_models_history()
        return {"status": "success", "history": history}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener el historial: {str(exc)}")


@router.post("/ml/publish-model")
async def publish_model_endpoint(
    request: PublishModelRequest,
    training_key: str | None = Header(default=None, alias="X-ML-Training-Key")
):
    try:
        result = ml_model.publish_model(
            model_name=request.model_name,
            new_model_name=request.new_model_name
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al publicar el modelo: {str(exc)}")


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


# Nuevos endpoints para la mejora del proyecto
@router.get("/ml/experiments")
async def list_experiments():
    try:
        experiments = get_experiments()
        return {"status": "success", "experiments": experiments}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al listar experimentos: {str(exc)}")


@router.get("/ml/experiments/{experiment_id}")
async def get_experiment_details(experiment_id: str):
    try:
        exp = get_experiment(experiment_id)
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experimento {experiment_id} no encontrado")
        return {"status": "success", "experiment": exp}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener experimento: {str(exc)}")


@router.get("/ml/best-model")
async def get_best_endpoint():
    try:
        best = get_best_model()
        if best:
            return {"status": "success", "best_model": best}
        else:
            raise HTTPException(status_code=404, detail="No hay mejor modelo configurado aún")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al obtener mejor modelo: {str(exc)}")


# Preprocessing endpoints
class PreprocessingRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    dataset_records: List[Dict[str, Any]]
    missing_strategy: str = "ffill"
    remove_duplicates_flag: bool = True
    remove_outliers_flag: bool = False
    scaler_type: str = "minmax"
    add_time_features_flag: bool = True
    add_lag_features_flag: bool = True
    lag_features: List[int] = [1, 7, 14]
    add_rolling_features_flag: bool = True
    rolling_window: int = 7


@router.post("/ml/preprocess")
async def preprocess_data(req: PreprocessingRequest):
    try:
        df = pd.DataFrame(req.dataset_records)
        results = {}
        # Original stats
        results["original"] = {
            "shape": df.shape,
            "missing": df.isnull().sum().to_dict(),
            "duplicates": df.duplicated().sum(),
        }
        # Apply preprocessing
        if req.remove_duplicates_flag:
            df = remove_duplicates(df)
        df = handle_missing_values(df, req.missing_strategy)
        if req.remove_outliers_flag:
            df = remove_outliers(df)
        if req.add_time_features_flag and "date" in df.columns:
            df = add_time_features(df, "date")
        if req.add_lag_features_flag and "price" in df.columns:
            df = add_lag_features(df, "price", req.lag_features)
        if req.add_rolling_features_flag and "price" in df.columns:
            df = add_rolling_features(df, "price", req.rolling_window)
        # Scale
        scaled_df, _ = scale_features(df, scaler_type=req.scaler_type)
        results["processed"] = {
            "shape": scaled_df.shape,
            "columns": list(scaled_df.columns),
            "sample": scaled_df.head(10).to_dict(orient="records"),
        }
        return {"status": "success", "results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al preprocesar datos: {str(exc)}")


# Statistical tests endpoints
class StatisticalTestsRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_scores: Dict[str, List[float]]
    model_errors: Dict[str, List[float]]


@router.post("/ml/statistical-tests")
async def run_statistical_tests(req: StatisticalTestsRequest):
    try:
        results = {}
        model_names = list(req.model_scores.keys())

        if len(model_names) == 2:
            # Two models comparison
            results["mann_whitney"] = mann_whitney_test(
                req.model_scores[model_names[0]], req.model_scores[model_names[1]]
            )
            results["kolmogorov_smirnov"] = kolmogorov_smirnov_test(
                req.model_errors[model_names[0]], req.model_errors[model_names[1]]
            )
            results["morgan_pitman"] = morgan_pitman_test(
                req.model_errors[model_names[0]], req.model_errors[model_names[1]]
            )
        elif len(model_names) > 2:
            # Multiple models
            results["friedman"] = friedman_test(req.model_scores)
            if results["friedman"]["p_value"] < 0.05:
                results["nemenyi"] = nemenyi_posthoc_test(req.model_scores)

        # Stability analysis per model
        results["stability"] = {
            name: stability_analysis(scores)
            for name, scores in req.model_scores.items()
        }
        return {"status": "success", "results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar tests estadísticos: {str(exc)}")


# Endpoint for setting best model
class SetBestModelRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    experiment_id: str
    model_name: str
    model_type: str
    rmse: float
    mae: float
    mape: Optional[float] = None
    r2: float
    validation_status: str = "pending"


@router.post("/ml/set-best-model")
async def set_best_endpoint(req: SetBestModelRequest):
    try:
        save_best_model(req.experiment_id, req.model_dump())
        return {
            "status": "success",
            "message": "Mejor modelo actualizado",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al configurar mejor modelo: {str(exc)}")
