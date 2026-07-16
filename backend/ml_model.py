import json
import math
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler


ARTIFACT_DIR = os.getenv(
    "ML_ARTIFACT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_models"),
)
MODEL_DIR = ARTIFACT_DIR
REPORT_DIR = os.path.join(ARTIFACT_DIR, "reports")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def _safe_name(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name.strip())
    return value or "price_predictor"


def _to_float(value: Any) -> float:
    return float(np.asarray(value).reshape(-1)[0])


def _metric_dict(y_true, y_pred) -> dict:
    rmse = math.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    return {
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "r2": round(float(r2_score(y_true, y_pred)), 4) if len(y_true) > 1 else 0.0,
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [_json_ready(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def _import_keras():
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers
    except Exception as exc:
        raise RuntimeError(
            "TensorFlow is required to train or load neural-network models. "
            "Install backend requirements before running this step."
        ) from exc
    return tf, keras, layers


def generate_historical_prices(
    base_price: float,
    days: int = 180,
    product_name: str = "Generic Product",
) -> pd.DataFrame:
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=max(days, 35), freq="D")
    n = len(dates)

    day_of_week = dates.dayofweek
    trend = np.linspace(0, base_price * 0.08, n)
    weekly = base_price * 0.035 * np.sin(2 * np.pi * day_of_week / 7)
    campaign = np.where((dates.day >= 25) | (dates.day <= 3), -base_price * 0.04, 0)
    noise = np.random.default_rng(42).normal(0, base_price * 0.035, n)

    prices = base_price + trend + weekly + campaign + noise
    prices = np.clip(prices, base_price * 0.65, base_price * 1.35)

    return pd.DataFrame({
        "date": dates,
        "product_name": product_name,
        "price": prices.round(2),
        "store_name": "Synthetic",
    })


def history_to_dataframe(history: list[dict], product_name: str = "Product") -> pd.DataFrame:
    if not history:
        return pd.DataFrame(columns=["date", "product_name", "price", "store_name"])

    rows = []
    for item in history:
        rows.append({
            "date": item.get("recorded_at") or item.get("date"),
            "product_name": product_name,
            "price": item.get("price"),
            "store_name": item.get("store_name") or "Unknown",
        })
    return pd.DataFrame(rows)


def normalize_price_dataframe(
    df: pd.DataFrame,
    base_price: float | None = None,
    days: int = 180,
    product_name: str = "Product",
    data_source: str = "synthetic_generator",
) -> pd.DataFrame:
    working = df.copy() if df is not None else pd.DataFrame()
    if "recorded_at" in working.columns and "date" not in working.columns:
        working["date"] = working["recorded_at"]

    if "date" not in working.columns or "price" not in working.columns:
        if data_source != "synthetic_generator":
            raise RuntimeError(f"{data_source} requires date (or recorded_at) and price columns with valid daily price records.")
        fallback_price = base_price or 100
        return generate_historical_prices(fallback_price, days=days, product_name=product_name)

    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working["price"] = pd.to_numeric(working["price"], errors="coerce")
    working = working.dropna(subset=["date", "price"])
    working = working[working["price"] > 0].sort_values("date")

    if working.empty:
        if data_source != "synthetic_generator":
            raise RuntimeError(f"{data_source} requires valid daily price records; synthetic data is not used for this source.")
        fallback_price = base_price or 100
        return generate_historical_prices(fallback_price, days=days, product_name=product_name)

    daily = (
        working.assign(date=working["date"].dt.floor("D"))
        .groupby("date", as_index=False)["price"]
        .mean()
        .sort_values("date")
    )

    if len(daily) < 35:
        if data_source != "synthetic_generator":
            raise RuntimeError(f"{data_source} requires at least 35 valid daily price records; synthetic data is not used for this source.")
        latest = float(daily["price"].iloc[-1]) if len(daily) else base_price or 100
        return generate_historical_prices(latest, days=max(days, 90), product_name=product_name)

    full_dates = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    daily = daily.set_index("date").reindex(full_dates)
    daily.index.name = "date"
    daily["price"] = daily["price"].interpolate().ffill().bfill()
    daily = daily.reset_index()
    daily["product_name"] = product_name
    daily["store_name"] = "Aggregated"
    return daily


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working = working.dropna(subset=["date", "price"]).sort_values("date")
    working["day_of_week"] = working["date"].dt.dayofweek / 6
    working["day_of_month"] = working["date"].dt.day / 31
    working["month"] = working["date"].dt.month / 12
    working["price_change"] = working["price"].pct_change().replace([np.inf, -np.inf], 0).fillna(0)
    working["rolling_mean_7"] = working["price"].rolling(7, min_periods=1).mean()
    return working


def compute_eda(df: pd.DataFrame) -> dict:
    prices = pd.to_numeric(df["price"], errors="coerce").dropna()
    q1 = prices.quantile(0.25) if not prices.empty else 0
    q3 = prices.quantile(0.75) if not prices.empty else 0
    iqr = q3 - q1
    outliers = prices[(prices < q1 - 1.5 * iqr) | (prices > q3 + 1.5 * iqr)]
    dates = pd.to_datetime(df["date"], errors="coerce").dropna()

    return {
        "rows": int(len(df)),
        "date_start": dates.min().date().isoformat() if not dates.empty else None,
        "date_end": dates.max().date().isoformat() if not dates.empty else None,
        "missing_values": {k: int(v) for k, v in df.isna().sum().to_dict().items()},
        "price": {
            "min": round(float(prices.min()), 4) if not prices.empty else 0,
            "max": round(float(prices.max()), 4) if not prices.empty else 0,
            "mean": round(float(prices.mean()), 4) if not prices.empty else 0,
            "median": round(float(prices.median()), 4) if not prices.empty else 0,
            "std": round(float(prices.std()), 4) if len(prices) > 1 else 0,
            "outliers_iqr": int(len(outliers)),
        },
    }


def _make_supervised(df: pd.DataFrame, sequence_length: int):
    feature_columns = [
        "price",
        "day_of_week",
        "day_of_month",
        "month",
        "price_change",
        "rolling_mean_7",
    ]
    featured = add_time_features(df)
    feature_values = featured[feature_columns].to_numpy(dtype=np.float32)
    target_values = featured["price"].to_numpy(dtype=np.float32)

    X, y = [], []
    for idx in range(sequence_length, len(featured)):
        X.append(feature_values[idx - sequence_length:idx])
        y.append(target_values[idx])

    return (
        np.asarray(X, dtype=np.float32),
        np.asarray(y, dtype=np.float32),
        featured, feature_columns,
    )


def _scale_sequences(scaler: StandardScaler, sequences: np.ndarray) -> np.ndarray:
    if len(sequences) == 0:
        return sequences.astype(np.float32)
    shape = sequences.shape
    return scaler.transform(sequences.reshape(-1, shape[-1])).reshape(shape).astype(np.float32)


def _scale_fold_data(X, y, train_idx, validation_idx) -> dict:
    feature_scaler = StandardScaler()
    target_scaler = StandardScaler()
    train_X = np.asarray(X[train_idx], dtype=np.float32)
    validation_X = np.asarray(X[validation_idx], dtype=np.float32)
    train_y = np.asarray(y[train_idx], dtype=np.float32)
    validation_y = np.asarray(y[validation_idx], dtype=np.float32)

    feature_scaler.fit(train_X.reshape(-1, train_X.shape[-1]))
    target_scaler.fit(train_y.reshape(-1, 1))
    return {
        "feature_scaler": feature_scaler,
        "target_scaler": target_scaler,
        "X_train": _scale_sequences(feature_scaler, train_X),
        "X_validation": _scale_sequences(feature_scaler, validation_X),
        "y_train": target_scaler.transform(train_y.reshape(-1, 1)).reshape(-1).astype(np.float32),
        "y_validation": target_scaler.transform(validation_y.reshape(-1, 1)).reshape(-1).astype(np.float32),
        "raw_y_validation": validation_y,
    }


def _build_neural_model(model_type: str, input_shape: tuple[int, int], params: dict):
    tf, keras, layers = _import_keras()
    tf.keras.utils.set_random_seed(int(params.get("seed", 42)))

    units = int(params.get("units", 32))
    dropout = float(params.get("dropout", 0.1))
    learning_rate = float(params.get("learning_rate", 0.001))

    inputs = keras.Input(shape=input_shape)
    if model_type == "mlp":
        x = layers.Flatten()(inputs)
        x = layers.Dense(units, activation="relu")(x)
        x = layers.Dropout(dropout)(x)
        x = layers.Dense(max(units // 2, 8), activation="relu")(x)
    elif model_type == "lstm":
        x = layers.LSTM(units, dropout=dropout)(inputs)
    else:
        x = layers.GRU(units, dropout=dropout)(inputs)

    outputs = layers.Dense(1)(x)
    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="mse",
        metrics=["mae"],
    )
    return model


def _candidate_grid(model_types: list[str], max_trials: int) -> list[dict]:
    grid = []
    for units in (24, 48):
        for learning_rate in (0.001, 0.0005):
            for model_type in model_types:
                grid.append({
                    "model_type": model_type,
                    "units": units,
                    "dropout": 0.15,
                    "learning_rate": learning_rate,
                    "seed": 42,
                })
    return grid[:max_trials]


def _inverse_target(target_scaler: StandardScaler, values) -> np.ndarray:
    return target_scaler.inverse_transform(np.asarray(values).reshape(-1, 1)).reshape(-1)


def _evaluate_linear_baseline(X, y, n_splits: int) -> dict:
    flat_X = X.reshape((X.shape[0], -1))
    splits = _time_splits(len(y), n_splits)
    fold_metrics = []
    for train_idx, test_idx in splits:
        model = LinearRegression()
        model.fit(flat_X[train_idx], y[train_idx])
        preds = model.predict(flat_X[test_idx])
        fold_metrics.append(_metric_dict(y[test_idx], preds))

    return {
        "model_type": "linear_baseline",
        "folds": fold_metrics,
        "mean_mae": round(float(np.mean([m["mae"] for m in fold_metrics])), 4),
        "mean_rmse": round(float(np.mean([m["rmse"] for m in fold_metrics])), 4),
    }


def _time_splits(sample_count: int, requested_splits: int):
    if sample_count < 8:
        split_at = max(1, int(sample_count * 0.75))
        return [(np.arange(0, split_at), np.arange(split_at, sample_count))]

    n_splits = min(max(2, requested_splits), max(2, sample_count // 8))
    return list(TimeSeriesSplit(n_splits=n_splits).split(np.arange(sample_count)))


def _cross_validate_candidate(
    candidate: dict,
    X,
    y,
    epochs: int,
    batch_size: int,
    requested_splits: int,
) -> dict:
    splits = _time_splits(len(y), requested_splits)
    fold_metrics = []

    for fold, (train_idx, test_idx) in enumerate(splits, start=1):
        scaled = _scale_fold_data(X, y, train_idx, test_idx)
        params = {**candidate, "seed": int(candidate.get("seed", 42)) + fold}
        model = _build_neural_model(candidate["model_type"], X.shape[1:], params)
        model.fit(
            scaled["X_train"],
            scaled["y_train"],
            epochs=epochs,
            batch_size=batch_size,
            verbose=0,
            validation_split=0.15 if len(train_idx) > 10 else 0,
        )
        preds = model.predict(scaled["X_validation"], verbose=0).reshape(-1)
        fold_metrics.append(_metric_dict(
            scaled["raw_y_validation"],
            _inverse_target(scaled["target_scaler"], preds),
        ))

    return {
        **candidate,
        "folds": fold_metrics,
        "mean_mae": round(float(np.mean([m["mae"] for m in fold_metrics])), 4),
        "mean_rmse": round(float(np.mean([m["rmse"] for m in fold_metrics])), 4),
        "std_rmse": round(float(np.std([m["rmse"] for m in fold_metrics])), 4),
    }


def _evaluate_holdout_candidate(candidate: dict, X, y, epochs: int, batch_size: int) -> tuple[dict, np.ndarray, np.ndarray]:
    split_at = max(1, int(len(y) * 0.8))
    train_idx = np.arange(0, split_at)
    test_idx = np.arange(split_at, len(y))
    if len(test_idx) == 0:
        test_idx = np.arange(len(y) - 1, len(y))
        train_idx = np.arange(0, len(y) - 1)
    scaled = _scale_fold_data(X, y, train_idx, test_idx)
    model = _build_neural_model(candidate["model_type"], X.shape[1:], candidate)
    model.fit(
        scaled["X_train"], scaled["y_train"], epochs=epochs, batch_size=batch_size,
        verbose=0, validation_split=0.15 if len(train_idx) > 10 else 0,
    )
    preds = model.predict(scaled["X_validation"], verbose=0).reshape(-1)
    actual = scaled["raw_y_validation"]
    predicted = _inverse_target(scaled["target_scaler"], preds)
    return _metric_dict(actual, predicted), actual, predicted


def _stability_tests(best_candidate: dict, X, y, epochs: int, batch_size: int, runs: int) -> dict:
    metrics = []
    for idx, seed in enumerate([11, 29, 47, 83, 101][:runs], start=1):
        params = {**best_candidate, "seed": seed}
        model = _build_neural_model(best_candidate["model_type"], X.shape[1:], params)
        split_at = max(1, int(len(y) * 0.8))
        scaled = _scale_fold_data(X, y, np.arange(0, split_at), np.arange(split_at, len(y)))
        model.fit(
            scaled["X_train"],
            scaled["y_train"],
            epochs=max(5, epochs // 2),
            batch_size=batch_size,
            verbose=0,
            validation_split=0.15 if split_at > 10 else 0,
        )
        preds = model.predict(scaled["X_validation"], verbose=0).reshape(-1)
        actual = scaled["raw_y_validation"]
        predicted = _inverse_target(scaled["target_scaler"], preds)
        metrics.append({"run": idx, "seed": seed, **_metric_dict(actual, predicted)})

    return {
        "runs": metrics,
        "mae_mean": round(float(np.mean([m["mae"] for m in metrics])), 4),
        "mae_std": round(float(np.std([m["mae"] for m in metrics])), 4),
        "rmse_mean": round(float(np.mean([m["rmse"] for m in metrics])), 4),
        "rmse_std": round(float(np.std([m["rmse"] for m in metrics])), 4),
        "consistency_score": round(float(1 / (1 + np.std([m["rmse"] for m in metrics]))), 4),
    }


def _statistical_tests(actual: np.ndarray, predicted: np.ndarray) -> dict:
    residuals = actual - predicted
    abs_residuals = np.abs(residuals)
    residual_std = float(np.std(residuals)) if len(residuals) else 0.0
    residual_mean = float(np.mean(residuals)) if len(residuals) else 0.0
    ci_margin = 1.96 * residual_std / math.sqrt(max(len(residuals), 1))
    median_abs_error = float(np.median(abs_residuals)) if len(abs_residuals) else 0.0
    robust_threshold = median_abs_error * 3 if median_abs_error else residual_std * 2
    outlier_count = int(np.sum(abs_residuals > robust_threshold)) if robust_threshold else 0

    return {
        "residual_mean": round(residual_mean, 4),
        "residual_std": round(residual_std, 4),
        "residual_mean_95ci": [
            round(residual_mean - ci_margin, 4),
            round(residual_mean + ci_margin, 4),
        ],
        "median_absolute_error": round(median_abs_error, 4),
        "robust_outlier_residuals": outlier_count,
        "positive_residual_ratio": round(float(np.mean(residuals > 0)), 4) if len(residuals) else 0,
    }


def _write_report(model_name: str, payload: dict) -> tuple[str, str]:
    report_md = os.path.join(REPORT_DIR, f"{model_name}_report.md")
    report_html = os.path.join(REPORT_DIR, f"{model_name}_report.html")

    lines = [
        f"# Neural Price Forecast Report: {model_name}",
        "",
        f"- Created at: {payload['created_at']}",
        f"- Data source: {payload['data_source']}",
        f"- Best model: {payload['best_model']['model_type']}",
        f"- Holdout MAE: {payload['metrics']['mae']}",
        f"- Holdout RMSE: {payload['metrics']['rmse']}",
        f"- Stability score: {payload['stability']['consistency_score']}",
        "",
        "## EDA",
        "```json",
        json.dumps(payload["eda"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Cross Validation",
        "```json",
        json.dumps(payload["cross_validation"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Statistical Robustness",
        "```json",
        json.dumps(payload["statistical_tests"], indent=2, ensure_ascii=False),
        "```",
    ]
    content = "\n".join(lines)
    with open(report_md, "w", encoding="utf-8") as handle:
        handle.write(content)
    with open(report_html, "w", encoding="utf-8") as handle:
        handle.write(
            "<html><body><pre>"
            + content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            + "</pre></body></html>"
        )
    return report_md, report_html


def _artifact_reference(path: str) -> str:
    normalized = path.replace("\\", "/")
    filename = normalized.rsplit("/", 1)[-1]
    is_windows_absolute = len(normalized) > 2 and normalized[1] == ":" and normalized[2] == "/"

    if is_windows_absolute and os.name != "nt":
        return filename

    if os.path.isabs(path):
        try:
            artifact_root = os.path.abspath(ARTIFACT_DIR)
            absolute_path = os.path.abspath(path)
            if os.path.commonpath([artifact_root, absolute_path]) == artifact_root:
                return os.path.relpath(absolute_path, artifact_root).replace("\\", "/")
        except ValueError:
            pass
        return filename

    if normalized == ".." or normalized.startswith("../") or "/../" in normalized:
        return filename
    return normalized


def _public_metadata(metadata: dict) -> dict:
    public = dict(metadata)
    artifact_paths = public.get("artifact_paths")
    if isinstance(artifact_paths, dict):
        public["artifact_paths"] = {
            key: _artifact_reference(value) if isinstance(value, str) else value
            for key, value in artifact_paths.items()
        }
    return public


def train_model_suite(
    df: pd.DataFrame,
    model_name: str = "price_predictor",
    base_price: float | None = None,
    days: int = 180,
    product_name: str = "Product",
    sequence_length: int = 14,
    epochs: int = 20,
    batch_size: int = 8,
    validation_splits: int = 3,
    stability_runs: int = 3,
    model_types: Optional[list[str]] = None,
    max_trials: int = 4,
    data_source: str = "direct_input",
) -> dict:
    safe_model_name = _safe_name(model_name)
    normalized = normalize_price_dataframe(
        df, base_price=base_price, days=days, product_name=product_name, data_source=data_source
    )
    eda = compute_eda(normalized)
    X, y, featured, feature_columns = _make_supervised(
        normalized,
        sequence_length=min(sequence_length, max(3, len(normalized) // 4)),
    )

    if len(y) < 5:
        if data_source != "synthetic_generator":
            raise RuntimeError(f"{data_source} does not contain enough samples after preprocessing for chronological evaluation.")
        normalized = generate_historical_prices(base_price or 100, days=max(days, 120), product_name=product_name)
        X, y, featured, feature_columns = _make_supervised(normalized, sequence_length=7)

    model_types = model_types or ["gru", "lstm", "mlp"]
    baseline = _evaluate_linear_baseline(X, y, validation_splits)
    candidates = _candidate_grid(model_types, max_trials=max_trials)
    cv_results = [
        _cross_validate_candidate(candidate, X, y, epochs, batch_size, validation_splits)
        for candidate in candidates
    ]
    best_candidate = min(cv_results, key=lambda item: item["mean_rmse"])

    metrics, actual, predicted = _evaluate_holdout_candidate(best_candidate, X, y, epochs, batch_size)
    stability = _stability_tests(best_candidate, X, y, epochs, batch_size, stability_runs)
    statistical_tests = _statistical_tests(actual, predicted)

    production = _scale_fold_data(X, y, np.arange(len(y)), np.arange(len(y)))
    production_model = _build_neural_model(best_candidate["model_type"], X.shape[1:], best_candidate)
    production_model.fit(
        production["X_train"], production["y_train"], epochs=epochs, batch_size=batch_size,
        verbose=0, validation_split=0.15 if len(y) > 12 else 0,
    )

    model_path = os.path.join(MODEL_DIR, f"{safe_model_name}.h5")
    scaler_path = os.path.join(MODEL_DIR, f"{safe_model_name}_scalers.joblib")
    metadata_path = os.path.join(MODEL_DIR, f"{safe_model_name}_metadata.json")
    metrics_path = os.path.join(MODEL_DIR, f"{safe_model_name}_metrics.json")

    production_model.save(model_path)
    joblib.dump(
        {
            "feature_scaler": production["feature_scaler"],
            "target_scaler": production["target_scaler"],
            "feature_columns": feature_columns,
            "sequence_length": X.shape[1],
        },
        scaler_path,
    )

    metadata = {
        "model_name": safe_model_name,
        "created_at": datetime.now().isoformat(),
        "product_name": product_name,
        "data_source": data_source,
        "data_points": int(len(normalized)),
        "best_model": best_candidate,
        "metrics": metrics,
        "baseline": baseline,
        "cross_validation": cv_results,
        "stability": stability,
        "statistical_tests": statistical_tests,
        "eda": eda,
        "artifact_paths": {
            "model_path": _artifact_reference(model_path),
            "scaler_path": _artifact_reference(scaler_path),
            "metadata_path": _artifact_reference(metadata_path),
            "metrics_path": _artifact_reference(metrics_path),
        },
        "residual_std": statistical_tests["residual_std"],
        "last_training_price": round(float(featured["price"].iloc[-1]), 4),
    }
    report_md, report_html = _write_report(safe_model_name, metadata)
    metadata["artifact_paths"]["report_md"] = _artifact_reference(report_md)
    metadata["artifact_paths"]["report_html"] = _artifact_reference(report_html)

    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(_json_ready(metadata), handle, indent=2, ensure_ascii=False)
    with open(metrics_path, "w", encoding="utf-8") as handle:
        json.dump(_json_ready({
            "metrics": metrics,
            "baseline": baseline,
            "stability": stability,
            "statistical_tests": statistical_tests,
        }), handle, indent=2, ensure_ascii=False)

    return _json_ready(_public_metadata(metadata))


def load_neural_artifacts(model_name: str = "price_predictor") -> dict | None:
    safe_model_name = _safe_name(model_name)
    model_path = os.path.join(MODEL_DIR, f"{safe_model_name}.h5")
    scaler_path = os.path.join(MODEL_DIR, f"{safe_model_name}_scalers.joblib")
    metadata_path = os.path.join(MODEL_DIR, f"{safe_model_name}_metadata.json")
    if not (os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(metadata_path)):
        return None

    tf, keras, layers = _import_keras()
    model = keras.models.load_model(model_path, compile=False)
    scalers = joblib.load(scaler_path)
    with open(metadata_path, "r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    return {"model": model, "scalers": scalers, "metadata": _public_metadata(metadata)}


def _future_feature_row(date: pd.Timestamp, price: float, prev_price: float) -> dict:
    price_change = (price - prev_price) / prev_price if prev_price else 0
    return {
        "price": price,
        "day_of_week": date.dayofweek / 6,
        "day_of_month": date.day / 31,
        "month": date.month / 12,
        "price_change": price_change,
        "rolling_mean_7": price,
    }


def predict_with_neural_model(
    model_name: str,
    df: pd.DataFrame,
    days_ahead: int = 7,
    base_price: float | None = None,
    product_name: str = "Product",
) -> list[dict]:
    loaded = load_neural_artifacts(model_name)
    if not loaded:
        raise FileNotFoundError(f"Model '{model_name}' was not trained yet.")

    model = loaded["model"]
    scalers = loaded["scalers"]
    metadata = loaded["metadata"]
    sequence_length = int(scalers["sequence_length"])
    feature_columns = scalers["feature_columns"]
    feature_scaler = scalers["feature_scaler"]
    target_scaler = scalers["target_scaler"]

    normalized = normalize_price_dataframe(df, base_price=base_price, days=120, product_name=product_name)
    featured = add_time_features(normalized)
    if len(featured) < sequence_length:
        normalized = generate_historical_prices(base_price or metadata.get("last_training_price", 100), days=120)
        featured = add_time_features(normalized)

    scaled_features = feature_scaler.transform(featured[feature_columns])
    sequence = scaled_features[-sequence_length:].copy()
    last_date = pd.to_datetime(featured["date"].iloc[-1])
    prev_price = float(featured["price"].iloc[-1])
    residual_std = float(metadata.get("residual_std", 0)) or float(metadata["metrics"].get("rmse", 0))
    confidence = max(0.45, min(0.98, 1 - (residual_std / max(prev_price, 1))))

    predictions = []
    for offset in range(1, days_ahead + 1):
        pred_scaled = model.predict(sequence.reshape(1, sequence_length, len(feature_columns)), verbose=0)
        predicted_price = max(0, _to_float(_inverse_target(target_scaler, pred_scaled)))
        future_date = last_date + timedelta(days=offset)
        lower = max(0, predicted_price - 1.96 * residual_std)
        upper = predicted_price + 1.96 * residual_std

        predictions.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "predicted_price": round(predicted_price, 2),
            "lower_bound": round(lower, 2),
            "upper_bound": round(upper, 2),
            "confidence": round(confidence, 3),
        })

        next_row = pd.DataFrame([_future_feature_row(future_date, predicted_price, prev_price)])
        next_scaled = feature_scaler.transform(next_row[feature_columns])[0]
        sequence = np.vstack([sequence[1:], next_scaled])
        prev_price = predicted_price

    return predictions


def list_model_artifacts() -> list[dict]:
    models = []
    for filename in os.listdir(MODEL_DIR):
        if not filename.endswith("_metadata.json"):
            continue
        path = os.path.join(MODEL_DIR, filename)
        with open(path, "r", encoding="utf-8") as handle:
            metadata = json.load(handle)
        models.append({
            "model_name": metadata.get("model_name", filename.replace("_metadata.json", "")),
            "model_type": metadata.get("best_model", {}).get("model_type"),
            "created_at": metadata.get("created_at"),
            "metrics": metadata.get("metrics"),
            "stability": metadata.get("stability"),
        })
    return sorted(models, key=lambda item: item.get("created_at") or "", reverse=True)


def delete_model_artifacts(model_name: str) -> int:
    safe_model_name = _safe_name(model_name)
    deleted = 0
    for suffix in [".h5", "_scalers.joblib", "_metadata.json", "_metrics.json"]:
        path = os.path.join(MODEL_DIR, f"{safe_model_name}{suffix}")
        if os.path.exists(path):
            os.remove(path)
            deleted += 1
    for suffix in ["_report.md", "_report.html"]:
        path = os.path.join(REPORT_DIR, f"{safe_model_name}{suffix}")
        if os.path.exists(path):
            os.remove(path)
            deleted += 1
    return deleted


def get_model_report(model_name: str) -> dict | None:
    safe_model_name = _safe_name(model_name)
    report_md = os.path.join(REPORT_DIR, f"{safe_model_name}_report.md")
    report_html = os.path.join(REPORT_DIR, f"{safe_model_name}_report.html")
    metadata_path = os.path.join(MODEL_DIR, f"{safe_model_name}_metadata.json")
    if not os.path.exists(metadata_path):
        return None
    with open(metadata_path, "r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    report_content = ""
    if os.path.exists(report_md):
        with open(report_md, "r", encoding="utf-8") as handle:
            report_content = handle.read()
    return {
        "metadata": _public_metadata(metadata),
        "report_markdown": report_content,
        "report_md_path": _artifact_reference(report_md) if os.path.exists(report_md) else None,
        "report_html_path": _artifact_reference(report_html) if os.path.exists(report_html) else None,
    }
