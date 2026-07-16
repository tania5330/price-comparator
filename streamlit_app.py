import json
import os
from typing import Any

import httpx
import pandas as pd
import streamlit as st


FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Price Comparator ML Lab", page_icon="🧠", layout="wide")
st.title("🧠 Laboratorio de Redes Neuronales")
st.caption("EDA, entrenamiento, validación cruzada, estabilidad, reportes y consumo del mejor modelo .h5.")
st.info("En Render, el entrenamiento usa una demo GRU acotada (5 epochs, 120 días, 2 divisiones temporales). Sus artefactos son temporales en almacenamiento efímero; el bootstrap permanece durable. El laboratorio local conserva EDA, CV y reportes académicos.")


def api_post(path: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict:
    response = httpx.post(f"{FASTAPI_URL}{path}", json=payload, headers=headers, timeout=180.0)
    if response.is_error:
        detail = response.json().get("detail") if response.headers.get("content-type", "").startswith("application/json") else None
        raise RuntimeError(detail or f"HTTP {response.status_code}")
    return response.json()


def api_get(path: str) -> dict:
    response = httpx.get(f"{FASTAPI_URL}{path}", timeout=60.0)
    response.raise_for_status()
    return response.json()


def local_eda(df: pd.DataFrame):
    st.subheader("EDA del dataset")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Filas", len(df))
    col_b.metric("Columnas", len(df.columns))
    col_c.metric("Nulos", int(df.isna().sum().sum()))

    st.write("Vista previa")
    st.dataframe(df.head(20), use_container_width=True)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        st.write("Resumen estadístico")
        st.dataframe(df[numeric_cols].describe(), use_container_width=True)

    if {"date", "price"}.issubset(df.columns):
        chart_df = df.copy()
        chart_df["date"] = pd.to_datetime(chart_df["date"], errors="coerce")
        chart_df["price"] = pd.to_numeric(chart_df["price"], errors="coerce")
        chart_df = chart_df.dropna(subset=["date", "price"]).sort_values("date")
        if not chart_df.empty:
            st.line_chart(chart_df, x="date", y="price")
    elif {"recorded_at", "price"}.issubset(df.columns):
        chart_df = df.rename(columns={"recorded_at": "date"}).copy()
        chart_df["date"] = pd.to_datetime(chart_df["date"], errors="coerce")
        chart_df["price"] = pd.to_numeric(chart_df["price"], errors="coerce")
        chart_df = chart_df.dropna(subset=["date", "price"]).sort_values("date")
        if not chart_df.empty:
            st.line_chart(chart_df, x="date", y="price")


with st.sidebar:
    st.header("Conexión")
    st.code(FASTAPI_URL)
    if st.button("Probar FastAPI"):
        try:
            health = api_get("/health")
            st.success(f"FastAPI OK: {health}")
        except Exception as exc:
            st.error(f"No se pudo conectar: {exc}")


tab_data, tab_train, tab_predict, tab_reports, tab_chat = st.tabs([
    "1. Dataset y EDA",
    "2. Entrenamiento",
    "3. Predicción",
    "4. Reportes",
    "5. Chatbot escrito",
])


if "dataset_records" not in st.session_state:
    st.session_state.dataset_records = None
if "last_training_result" not in st.session_state:
    st.session_state.last_training_result = None
if "prediction_model" not in st.session_state:
    st.session_state.prediction_model = "price_predictor"


with tab_data:
    st.header("Leer dataset")
    st.write("Subí un CSV con columnas `date` o `recorded_at` y `price`, o entrená desde el historial guardado en PostgreSQL.")
    uploaded_file = st.file_uploader("Dataset CSV", type=["csv"])
    if uploaded_file:
        dataset = pd.read_csv(uploaded_file)
        st.session_state.dataset_records = json.loads(dataset.to_json(orient="records"))
        local_eda(dataset)
    else:
        st.info("Sin CSV cargado: el entrenamiento puede usar `product_id` desde la base de datos o datos sintéticos de respaldo.")


with tab_train:
    st.header("Entrenamiento y selección de mejor modelo")
    col1, col2, col3 = st.columns(3)
    with col1:
        model_name = st.text_input("Nombre del modelo", value="price_predictor")
        product_id = st.text_input("ID de producto en DB", value="")
        product_name = st.text_input("Nombre del producto", value="Producto X")
        training_key = st.text_input("Código de acceso al entrenamiento", type="password", key="training_access_code")
    with col2:
        base_price = st.number_input("Precio base", min_value=1.0, value=100.0, step=1.0)
        days = st.slider("Días sintéticos de respaldo", 60, 365, 120)
        sequence_length = st.slider("Ventana temporal", 7, 30, 14)
    with col3:
        epochs = st.slider("Epochs", 5, 80, 5)
        max_trials = st.slider("Pruebas de hiperparámetros", 1, 8, 1)
        stability_runs = st.slider("Pruebas de estabilidad", 1, 5, 1)

    model_types = st.multiselect(
        "Arquitecturas neuronales",
        ["gru", "lstm", "mlp"],
        default=["gru"],
    )

    payload = {
        "model_name": model_name,
        "product_id": product_id or None,
        "dataset_records": st.session_state.dataset_records,
        "product_name": product_name,
        "base_price": base_price,
        "days": days,
        "sequence_length": sequence_length,
        "epochs": epochs,
        "batch_size": 8,
        "validation_splits": 2,
        "stability_runs": stability_runs,
        "model_types": model_types or ["gru"],
        "max_trials": max_trials,
    }

    if st.button("Entrenar demo GRU", type="primary"):
        with st.spinner("Entrenando demo GRU, validando y guardando .h5..."):
            try:
                headers = {"X-ML-Training-Key": training_key} if training_key else None
                result = api_post("/api/ml/train", payload, headers=headers)
                st.session_state.last_training_result = result
                st.session_state.prediction_model = result["model_name"]
                st.success(f"Modelo temporal entrenado: {result['model_name']}")
            except Exception as exc:
                st.error(f"Error de entrenamiento: {exc}")

    result = st.session_state.last_training_result
    if result:
        st.subheader("Resultado")
        metric_cols = st.columns(4)
        metric_cols[0].metric("Modelo ganador", result["best_model"]["model_type"].upper())
        metric_cols[1].metric("MAE", f"${result['metrics']['mae']:.2f}")
        metric_cols[2].metric("RMSE", f"${result['metrics']['rmse']:.2f}")
        metric_cols[3].metric("Estabilidad", result["stability"].get("consistency_score", "-"))

        st.write(f"Perfil efectivo: `{result.get('training_profile') or 'local'}`")
        st.json(result.get("training_config", {}))
        st.caption(f"Modelo publicado: {result['model_name']}. En Render este artefacto es temporal; el bootstrap durable no se reemplaza.")

        st.write("Baseline lineal")
        st.json(result["baseline"])
        st.write("Validación cruzada e hiperparámetros")
        st.dataframe(pd.DataFrame(result["cross_validation"]), use_container_width=True)
        st.write("Pruebas estadísticas robustas")
        st.json(result["statistical_tests"])
        st.write("EDA usada por FastAPI")
        st.json(result["eda"])


with tab_predict:
    st.header("Consumir mejor modelo .h5 desde FastAPI")
    pred_col1, pred_col2, pred_col3 = st.columns(3)
    with pred_col1:
        pred_model = st.text_input("Modelo para predicción", key="prediction_model")
    with pred_col2:
        pred_product_id = st.text_input("ID de producto para historial", value="")
    with pred_col3:
        days_ahead = st.slider("Días a predecir", 1, 30, 7)

    if st.button("Generar predicción"):
        try:
            prediction = api_post(
                "/api/ml/predict",
                {
                    "model_name": pred_model,
                    "product_id": pred_product_id or None,
                    "days_ahead": days_ahead,
                    "base_price": 100,
                },
            )
            pred_df = pd.DataFrame(prediction["predictions"])
            st.line_chart(pred_df, x="date", y=["lower_bound", "predicted_price", "upper_bound"])
            st.dataframe(pred_df, use_container_width=True)
        except Exception as exc:
            st.error(f"No se pudo predecir: {exc}")


with tab_reports:
    st.header("Modelos y reportes")
    try:
        models = api_get("/api/ml/models")["models"]
    except Exception:
        models = []

    if not models:
        st.info("Todavía no hay modelos entrenados.")
    else:
        model_names = [model["model_name"] for model in models]
        selected_model = st.selectbox("Modelo", model_names)
        st.dataframe(pd.DataFrame(models), use_container_width=True)
        if st.button("Cargar reporte técnico"):
            try:
                report = api_get(f"/api/ml/models/{selected_model}/report")
                st.markdown(report["report_markdown"])
            except Exception as exc:
                st.error(f"No se pudo cargar el reporte: {exc}")


with tab_chat:
    st.header("Chatbot escrito")
    st.write("El chatbot generativo se consume por FastAPI y usa `OPENAI_API_KEY` en el backend.")
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hola, soy tu asistente de compras. ¿Qué querés comparar?"}
        ]

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Escribí tu consulta")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        try:
            response = api_post("/api/ai/chat", {"messages": st.session_state.chat_messages})
            reply = response.get("reply", "No recibí respuesta.")
        except Exception as exc:
            reply = f"Error al consultar el chatbot: {exc}"
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()
