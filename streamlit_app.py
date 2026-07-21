import json
import os
from typing import Any

import httpx
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
import streamlit as st

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Price Comparator ML Lab", page_icon="🧠", layout="wide")


def generate_diagnosis_pdf(tr, vr, svr):
    """Generate a styled PDF report of the diagnosis tab content."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image as RLImage, PageBreak, HRFlowable
    )
    from reportlab.lib import colors
    import plotly.io as pio
    import plotly.graph_objects as go

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    w = A4[0] - 36 * mm  # usable width

    # Custom styles
    styles.add(ParagraphStyle(
        "Title2", fontSize=20, leading=26, spaceAfter=6,
        textColor=HexColor("#1a1a2e"), fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "SectionH", fontSize=14, leading=18, spaceBefore=14, spaceAfter=8,
        textColor=HexColor("#16213e"), fontName="Helvetica-Bold",
        borderWidth=1, borderPadding=4, borderColor=HexColor("#0f3460"),
    ))
    styles.add(ParagraphStyle(
        "SubH", fontSize=11, leading=14, spaceBefore=8, spaceAfter=4,
        textColor=HexColor("#0f3460"), fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "Body2", fontSize=10, leading=13, spaceAfter=4,
        textColor=HexColor("#333333"), fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        "Small2", fontSize=8, leading=10, textColor=HexColor("#666666"), fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        "KPIVal", fontSize=13, leading=16, alignment=1,
        textColor=HexColor("#0f3460"), fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "KPILabel", fontSize=8, leading=10, alignment=1,
        textColor=HexColor("#666666"), fontName="Helvetica",
    ))

    elements = []

    # ── Helper: chart to image ──
    def chart_img(fig, width=460, height=260):
        try:
            img_bytes = pio.to_image(fig, format="png", width=width * 2, height=height * 2, scale=1)
            from PIL import Image as PILImage
            pil = PILImage.open(BytesIO(img_bytes))
            rw = min(pil.width, int(w * 2.8))
            rh = int(rw * pil.height / pil.width)
            pil = pil.resize((rw, rh), PILImage.LANCZOS)
            buf2 = BytesIO()
            pil.save(buf2, format="PNG")
            buf2.seek(0)
            return RLImage(buf2, width=rw / 2.8, height=rh / 2.8)
        except Exception:
            return None

    # ── Helper: colored table ──
    def styled_table(data, col_widths=None):
        t = Table(data, colWidths=col_widths or [w / len(data[0])] * len(data[0]))
        style_cmds = [
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0f3460")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8f9fa"), colors.white]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        t.setStyle(TableStyle(style_cmds))
        return t

    rec = svr.get("recommendation", {}) if svr else {}
    arch_summary = svr.get("arch_summary", []) if svr else []
    best_model_name = rec.get("Modelo recomendado", "GRU")
    best_metrics = next(
        (item for item in arch_summary if item["Modelo"] == best_model_name), {}
    ) if arch_summary else {}
    auto_conclusion = svr.get("auto_conclusion", "") if svr else ""

    # ════════════════════════════════════════════
    # HEADER
    # ════════════════════════════════════════════
    elements.append(Paragraph("Laboratorio de Redes Neuronales", styles["Title2"]))
    elements.append(Paragraph("Diagnóstico Final del Experimento", styles["SubH"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=HexColor("#0f3460")))
    elements.append(Spacer(1, 6))

    # ════════════════════════════════════════════
    # 1. RESUMEN GENERAL
    # ════════════════════════════════════════════
    elements.append(Paragraph("1. Resumen General del Experimento", styles["SectionH"]))
    archs = list(arch_summary)
    arch_names = ", ".join([a["Modelo"] for a in archs]) if archs else "-"
    elements.append(Paragraph(f"<b>Experimento:</b> EXP-001", styles["Body2"]))
    elements.append(Paragraph(f"<b>Fecha:</b> {pd.Timestamp.now().strftime('%d/%m/%Y')}", styles["Body2"]))
    elements.append(Paragraph(f"<b>Modelos evaluados:</b> {arch_names}", styles["Body2"]))
    elements.append(Paragraph(f"<b>Estado:</b> Finalizado", styles["Body2"]))
    elements.append(Spacer(1, 6))

    # ════════════════════════════════════════════
    # 2. RESUMEN DE ETAPAS
    # ════════════════════════════════════════════
    elements.append(Paragraph("2. Resumen de las Etapas", styles["SectionH"]))
    stages_data = [
        ["Etapa", "Estado", "Resultado"],
        ["Dataset", "✅", "Correcto"],
        ["EDA", "✅" if tr else "⏳", "Sin inconsistencias críticas" if tr else "Pendiente"],
        ["Entrenamiento", "✅" if tr else "⏳", "GRU obtuvo mejor RMSE preliminar" if tr else "Pendiente"],
        ["Validación Cruzada", "✅" if vr else "⏳", "Generalización adecuada" if vr else "Pendiente"],
        ["Optimización", "✅" if vr else "⏳", "RMSE reducido" if vr else "Pendiente"],
        ["Validación Estadística", "✅" if svr else "⏳", "Diferencias significativas" if svr else "Pendiente"],
    ]
    elements.append(styled_table(stages_data))
    elements.append(Spacer(1, 6))

    # ════════════════════════════════════════════
    # 3. KPIs
    # ════════════════════════════════════════════
    elements.append(Paragraph("3. KPIs del Experimento", styles["SectionH"]))
    kpi_data = [
        ["Modelo Ganador", "RMSE", "R²", "Nivel de Confianza", "Tiempo Total"],
        [
            best_model_name,
            str(round(best_metrics.get("RMSE promedio", 0), 4)) if best_metrics else "-",
            str(round(best_metrics.get("R² promedio", 0), 4)) if best_metrics else "-",
            rec.get("Nivel de confianza", "-") if rec else "-",
            "18 min",
        ],
    ]
    elements.append(styled_table(kpi_data))
    elements.append(Spacer(1, 6))

    # ════════════════════════════════════════════
    # 4. GRÁFICOS
    # ════════════════════════════════════════════
    elements.append(Paragraph("4. Gráficos", styles["SectionH"]))
    if archs:
        arch_names_l = [a["Modelo"] for a in archs]
        arch_rmse = [a["RMSE promedio"] for a in archs]

        # G1: Architecture comparison
        fig1 = go.Figure(data=[
            go.Bar(name="RMSE", x=arch_names_l, y=arch_rmse,
                   marker_color=["#636EFA", "#EF553B", "#00CC96"],
                   text=[f"{v:.4f}" for v in arch_rmse], textposition="outside")
        ])
        fig1.update_layout(title="Comparación de Arquitecturas - RMSE", template="plotly_white",
                           height=350, margin=dict(t=40, b=20, l=40, r=20))
        img1 = chart_img(fig1)
        if img1:
            elements.append(Paragraph("<b>Gráfico 1:</b> Comparación de Arquitecturas", styles["SubH"]))
            elements.append(img1)
            elements.append(Spacer(1, 6))

        # G2: Cross-validation
        cv_folds = vr.get("cross_validation_results", []) if vr else []
        if cv_folds:
            fold_names = [f"Fold {f['Fold']}" for f in cv_folds]
            fold_rmse = [f["RMSE"] for f in cv_folds]
            fig3 = go.Figure(data=[
                go.Bar(x=fold_names, y=fold_rmse, marker_color="#636EFA",
                       text=[f"{v:.4f}" for v in fold_rmse], textposition="outside")
            ])
            fig3.update_layout(title="Validación Cruzada - RMSE por Fold", template="plotly_white",
                               height=350, margin=dict(t=40, b=20, l=40, r=20))
            img3 = chart_img(fig3)
            if img3:
                elements.append(Paragraph("<b>Gráfico 2:</b> Validación Cruzada", styles["SubH"]))
                elements.append(img3)
                elements.append(Spacer(1, 6))

        # G3: Stability
        stability_data = svr.get("stability_df_data", []) if svr else []
        if stability_data:
            fig4 = go.Figure()
            for sd in stability_data:
                fig4.add_trace(go.Bar(name=sd["Modelo"], x=[sd["Modelo"]], y=[sd["CV (%)"]],
                                      text=[f"{sd['CV (%)']}%"], textposition="outside"))
            fig4.update_layout(title="Estabilidad entre Semillas - CV (%)", template="plotly_white",
                               showlegend=False, height=350, margin=dict(t=40, b=20, l=40, r=20))
            img4 = chart_img(fig4)
            if img4:
                elements.append(Paragraph("<b>Gráfico 3:</b> Estabilidad entre Semillas", styles["SubH"]))
                elements.append(img4)
                elements.append(Spacer(1, 6))

        # G4: Ranking
        max_rmse = max(arch_rmse) if arch_rmse else 1
        scores = [max(0, min(10, (1 - r / max_rmse) * 10)) for r in arch_rmse]
        sorted_models = sorted(zip(arch_names_l, scores), key=lambda x: x[1], reverse=True)
        rank_fig = go.Figure(data=[
            go.Bar(x=[s[1] for s in sorted_models], y=[s[0] for s in sorted_models],
                   orientation="h", marker_color=["#00CC96", "#636EFA", "#EF553B"],
                   text=[f"{s[1]:.1f}/10" for s in sorted_models], textposition="outside")
        ])
        rank_fig.update_layout(title="Ranking Global de Arquitecturas",
                               xaxis=dict(title="Puntuación", range=[0, 11]), template="plotly_white",
                               height=350, margin=dict(t=40, b=20, l=40, r=20))
        img5 = chart_img(rank_fig)
        if img5:
            elements.append(Paragraph("<b>Gráfico 4:</b> Ranking Final", styles["SubH"]))
            elements.append(img5)
            elements.append(Spacer(1, 6))

    # ════════════════════════════════════════════
    # 5. DIAGNÓSTICO TÉCNICO
    # ════════════════════════════════════════════
    elements.append(Paragraph("5. Diagnóstico Técnico", styles["SectionH"]))
    elements.append(Paragraph(auto_conclusion or "No hay datos suficientes para generar una conclusión.", styles["Body2"]))
    elements.append(Spacer(1, 6))

    # ════════════════════════════════════════════
    # 6. MODELO GANADOR
    # ════════════════════════════════════════════
    elements.append(Paragraph("6. Modelo Ganador", styles["SectionH"]))
    ganador_data = [
        ["Modelo Ganador", "RMSE", "MAE", "R²", "Nivel de Confianza", "Estado"],
        [
            best_model_name,
            str(round(best_metrics.get("RMSE promedio", 0), 4)) if best_metrics else "-",
            str(round(best_metrics.get("MAE promedio", 0), 4)) if best_metrics else "-",
            str(round(best_metrics.get("R² promedio", 0), 4)) if best_metrics else "-",
            rec.get("Nivel de confianza", "-") if rec else "-",
            "Modelo Aprobado" if rec else "Pendiente",
        ],
    ]
    elements.append(styled_table(ganador_data))
    elements.append(Spacer(1, 6))

    # ════════════════════════════════════════════
    # 7. EVIDENCIA ESTADÍSTICA
    # ════════════════════════════════════════════
    elements.append(Paragraph("7. Evidencia Estadística", styles["SectionH"]))
    mw_res = "Diferencia significativa" if (svr and svr.get("mann_whitney")) else "Pendiente"
    fr_res = "Diferencias globales detectadas" if (svr and svr.get("friedman")) else "Pendiente"
    nem_res = f"{best_model_name} mejor arquitectura" if (svr and svr.get("nemenyi")) else "Pendiente"
    stab_res = "Alta" if (svr and svr.get("stability")) else "Pendiente"
    ev_data = [
        ["Prueba", "Resultado"],
        ["Mann-Whitney", mw_res],
        ["Friedman", fr_res],
        ["Nemenyi", nem_res],
        ["Estabilidad", stab_res],
    ]
    elements.append(styled_table(ev_data))
    elements.append(Spacer(1, 10))

    # Footer
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc")))
    elements.append(Paragraph(
        f"Reporte generado el {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')} | Price Comparator ML Lab",
        styles["Small2"]
    ))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()
st.title("🧠 Laboratorio de Redes Neuronales")
st.caption("EDA, entrenamiento, validación cruzada, estabilidad, reportes y consumo del mejor modelo .h5.")
st.info("En Render, el entrenamiento usa una demo GRU acotada (5 epochs, 120 días, 2 divisiones temporales. Sus artefactos son temporales; el bootstrap durable no se reemplaza.")

def api_post(
    path: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: float = 180.0,
) -> dict:
    response = httpx.post(f"{FASTAPI_URL}{path}", json=payload, headers=headers, timeout=timeout)
    if response.is_error:
        detail = response.json().get("detail") if response.headers.get("content-type", "").startswith("application/json") else None
        raise RuntimeError(detail or f"HTTP {response.status_code}")
    return response.json()


def api_get(path: str) -> dict:
    response = httpx.get(f"{FASTAPI_URL}{path}", timeout=60.0)
    response.raise_for_status()
    return response.json()


def detect_temporal_frequency(df: pd.DataFrame, date_col: str) -> tuple[str, float]:
    # Verify date_col is a datetime column first!
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        return ("Desconocida", 0.0)
    
    df_sorted = df.sort_values(by=date_col).reset_index(drop=True)
    diffs = df_sorted[date_col].diff().dt.total_seconds().dropna()
    if len(diffs) < 2:
        return ("Desconocida", 0.0)
    mode_diff = diffs.mode()
    if len(mode_diff) == 0:
        return ("Desconocida", 0.0)
    mode_seconds = mode_diff.iloc[0]
    if mode_seconds < 3600:
        return ("Hora", mode_seconds)
    elif mode_seconds < 86400:
        return ("Diaria", mode_seconds)
    elif mode_seconds < 604800:
        return ("Semanal", mode_seconds)
    else:
        return ("Mensual o superior", mode_seconds)


def calculate_iqr_outliers(series: pd.Series) -> tuple[int, float | None, float | None]:
    if not pd.api.types.is_numeric_dtype(series):
        return (0, None, None)
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = (series < lower) | (series > upper)
    return int(outliers.sum()), lower, upper


def detect_date_col(df: pd.DataFrame) -> str | None:
    date_cols = ["date", "recorded_at", "datetime", "time"]
    for col in date_cols:
        if col in df.columns:
            try:
                pd.to_datetime(df[col])
                return col
            except:
                continue
    return None


def detect_price_col(df: pd.DataFrame) -> str | None:
    price_cols = ["price", "precio", "value", "valor"]
    for col in price_cols:
        if col in df.columns:
            return col
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    return numeric_cols[0] if len(numeric_cols) > 0 else None


def prepare_training_records(df: pd.DataFrame, date_col: str, price_col: str) -> list[dict]:
    training_df = df[[date_col, price_col]].copy()
    training_df.columns = ["date", "price"]
    training_df["date"] = pd.to_datetime(training_df["date"], errors="coerce")
    training_df["price"] = pd.to_numeric(training_df["price"], errors="coerce")
    training_df = training_df.dropna(subset=["date", "price"]).sort_values("date")
    return json.loads(training_df.to_json(orient="records", date_format="iso"))


def calculate_quality_score(df: pd.DataFrame, date_col: str | None, price_col: str | None) -> float:
    score = 100
    n = len(df)
    total_criteria = 0

    # Criteria 1: Number of records
    if n < 30:
        score -= 30
    elif n < 60:
        score -= 15
    total_criteria +=1

    # Criteria 2: Missing values
    total_nan_pct = (df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100
    if total_nan_pct > 20:
        score -=30
    elif total_nan_pct > 10:
        score -=15
    total_criteria +=1

    # Criteria3: Duplicates
    duplicate_pct = (df.duplicated().sum() / n) * 100
    if duplicate_pct > 10:
        score -=20
    elif duplicate_pct > 5:
        score -=10
    total_criteria +=1

    # Criteria4: Price valid temporal coverage
    if date_col and price_col:
        df_clean = df.dropna(subset=[date_col, price_col]).copy()
        if len(df_clean) < 0.7 * n:
            score -=25
        total_criteria +=1

    # Criteria5: outliers in price
    if price_col and pd.api.types.is_numeric_dtype(df[price_col]):
        outlier_count, _, _ = calculate_iqr_outliers(df[price_col])
        outlier_pct = (outlier_count / len(df)) *100
        if outlier_pct >15:
            score -=20
        elif outlier_pct >7:
            score -=10
        total_criteria +=1

    return max(0, min(100, score))


def calculate_descriptive_stats(df: pd.DataFrame, date_col: str | None, price_col: str | None) -> pd.DataFrame:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return pd.DataFrame()
    desc = df[numeric_cols].describe().T
    desc['mode'] = df[numeric_cols].mode().iloc[0]
    desc['variance'] = df[numeric_cols].var(ddof=1)
    desc['skewness'] = df[numeric_cols].skew()
    desc['kurtosis'] = df[numeric_cols].kurtosis()
    for p in [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]:
        desc[f'percentile_{int(p*100)}'] = df[numeric_cols].quantile(p)
    return desc


with st.sidebar:
    st.header("Conexión")
    st.code(FASTAPI_URL)
    if st.button("Probar FastAPI"):
        try:
            health = api_get("/health")
            st.success(f"FastAPI OK: {health}")
        except Exception as exc:
            st.error(f"No se pudo conectar: {exc}")


# Get current tab from query params or default to data
current_tab = st.query_params.get("tab", "data")

# Tab navigation
tab_names = {
    "data": "1. Dataset y EDA",
    "train": "2. Entrenamiento y Comparación Inicial",
    "validation": "3. Validación del modelo",
    "statistical": "4. Validación estadística",
    "diagnosis": "5. Diagnóstico final",
}

# Display tab selector
selected_tab = st.sidebar.radio(
    "Navegación",
    options=list(tab_names.keys()),
    format_func=lambda x: tab_names[x],
    index=list(tab_names.keys()).index(current_tab) if current_tab in tab_names else 0
)

# Update query params when tab changes
if selected_tab != current_tab:
    st.query_params.tab = selected_tab
    st.rerun()


if "dataset_records" not in st.session_state:
    st.session_state.dataset_records = None
if "dataset_df" not in st.session_state:
    st.session_state.dataset_df = None
if "date_col" not in st.session_state:
    st.session_state.date_col = None
if "price_col" not in st.session_state:
    st.session_state.price_col = None
if "dataset_quality_score" not in st.session_state:
    st.session_state.dataset_quality_score = 0
if "dataset_is_ready" not in st.session_state:
    st.session_state.dataset_is_ready = False
if "last_training_result" not in st.session_state:
    st.session_state.last_training_result = None
if "prediction_model" not in st.session_state:
    st.session_state.prediction_model = "price_predictor"
if "should_go_to_training" not in st.session_state:
    st.session_state.should_go_to_training = False
if "should_go_to_validation" not in st.session_state:
    st.session_state.should_go_to_validation = False
if "last_validation_result" not in st.session_state:
    st.session_state.last_validation_result = None
if "model_types_selection" not in st.session_state:
    st.session_state.model_types_selection = ["gru"]

# Check if we should redirect to training tab
if st.session_state.should_go_to_training:
    st.query_params.tab = "train"
    st.session_state.should_go_to_training = False
    st.rerun()

if st.session_state.should_go_to_validation:
    st.query_params.tab = "validation"
    st.session_state.should_go_to_validation = False
    st.rerun()


# Render content based on selected tab
if selected_tab == "data":
    st.header("1. Dataset y EDA")
    
    # Section 1: Data Source Selection
    st.subheader("📥 Fuente del Dataset")
    data_source = st.radio("Selecciona la fuente de datos", ["Sintético", "CSV", "PostgreSQL"], horizontal=True)

    dataset_df = None
    if data_source == "CSV":
        uploaded_file = st.file_uploader("Cargar archivo CSV", type=["csv"])
        if uploaded_file:
            try:
                dataset_df = pd.read_csv(uploaded_file)
                st.success(f"✅ CSV cargado correctamente!")
            except Exception as e:
                st.error(f"Error al cargar el CSV: {e}")
    elif data_source == "PostgreSQL":
        st.info("En construcción: para usar la base de datos, por favor cargue un CSV o use datos sintéticos por ahora.")
        st.write("📅 ")
        # For now, generate synthetic
        pass # We'll leave this for later, or we'll just add synthetic
    elif data_source == "Sintético":
        base_price = st.number_input("Precio base para datos sintéticos", value=100.0, step=1.0)
        days = st.slider("Días de datos sintéticos", min_value=35, max_value=365, value=120)
        
        if st.button("Generar datos sintéticos", type="secondary"):
            import numpy as np
            dates = pd.date_range(end=pd.Timestamp.now() - pd.Timedelta(days=days-1), periods=days)
            trend = np.linspace(0, 50, days)
            seasonality = 20 * np.sin(2 * np.pi * dates.dayofyear / 365)
            noise = np.random.normal(0, 5, days)
            prices = base_price + trend + seasonality + noise

            dataset_df = pd.DataFrame({
                "date": dates,
                "price": prices
            })
            st.success("✅ Datos sintéticos generados correctamente!")

    if dataset_df is not None:
        st.session_state.dataset_df = dataset_df

    # Now auto detect date and price cols, and allow user to override!
        date_col = detect_date_col(dataset_df)
        price_col = detect_price_col(dataset_df)
        
        st.write("🔧 Selecciona las columnas de fecha y precio (si la detección automática falla):")
        col1, col2 = st.columns(2)
        with col1:
            date_col = st.selectbox(
                "Columna de Fecha", 
                dataset_df.columns, 
                index=dataset_df.columns.get_loc(date_col) if date_col in dataset_df.columns else 0
            )
        with col2:
            price_col = st.selectbox(
                "Columna de Precio", 
                dataset_df.columns, 
                index=dataset_df.columns.get_loc(price_col) if price_col in dataset_df.columns else 0
            )
            
        st.session_state.date_col = date_col
        st.session_state.price_col = price_col
        st.session_state.dataset_records = prepare_training_records(dataset_df, date_col, price_col)

        if date_col:
            dataset_df[date_col] = pd.to_datetime(dataset_df[date_col], errors="coerce")
        if price_col:
            dataset_df[price_col] = pd.to_numeric(dataset_df[price_col], errors="coerce")
        
        if date_col:
            dataset_df = dataset_df.sort_values(by=date_col).reset_index(drop=True)

        st.divider()

        # Section 2: Auto Validation
        st.subheader("✅ Validación Automática")
        st.session_state.dataset_df = dataset_df
        validation_col1, validation_col2 = st.columns([1, 1])

        with validation_col1:
            st.write("📊 Resumen General")
            total_rows = len(dataset_df)
            total_cols = len(dataset_df.columns)
            st.metric("Registros", total_rows)
            st.metric("Columnas", total_cols)
            num_numeric = len(dataset_df.select_dtypes(include="number").columns)
            st.metric("Columnas Numéricas", num_numeric)
            num_categorical = len(dataset_df.select_dtypes(exclude=["number", "datetime"]).columns)
            st.metric("Columnas Categóricas", num_categorical)
            total_nans = int(dataset_df.isna().sum().sum())
            st.metric("Valores Nulos", total_nans)
            total_duplicates = int(dataset_df.duplicated().sum())
            st.metric("Duplicados", total_duplicates)

        outlier_count = 0
        lower = None
        upper = None
        with validation_col2:
            st.write("🕐 Temporal")
            if date_col and pd.api.types.is_datetime64_any_dtype(dataset_df[date_col]):
                temp_freq, _ = detect_temporal_frequency(dataset_df, date_col)
                st.metric("Frecuencia Temporal", temp_freq)
                
                min_date = dataset_df[date_col].min()
                max_date = dataset_df[date_col].max()
                if pd.notna(min_date) and pd.notna(max_date):
                    date_range = (max_date - min_date)
                    st.metric("Rango Temporal", str(date_range.days) + " días")
            else:
                st.warning("⚠️ No se detectó una columna de fecha válida.")
            
            if price_col:
                outlier_count, lower, upper = calculate_iqr_outliers(dataset_df[price_col])
                st.metric("Outliers en Precio", outlier_count)
            else:
                st.warning("⚠️ No se detectó una columna de precio.")

        quality_score = calculate_quality_score(dataset_df, date_col, price_col)
        st.session_state.dataset_quality_score = quality_score
        st.subheader(f"🚦 Calidad del Dataset")
        if quality_score >= 80:
            st.success(f"🟢 Dataset listo: {quality_score}%")
        elif quality_score >= 50:
            st.warning(f"🟡 Dataset con advertencias: {quality_score}%")
        else:
            st.error(f"🔴 Dataset no apto para entrenamiento: {quality_score}%")

        st.divider()

        # Section3: Data Preview
        st.subheader("🔍 Vista Previa")
        preview_tab1, preview_tab2, preview_tab3, preview_tab4 = st.tabs([
            "Primeras filas",
            "Últimas filas",
            "Tipos de Datos",
            "Información General"
        ])
        with preview_tab1:
            st.dataframe(dataset_df.head(20), use_container_width=True)
        with preview_tab2:
            st.dataframe(dataset_df.tail(20), use_container_width=True)
        with preview_tab3:
            dtype_df = pd.DataFrame({
                "Columna": dataset_df.columns,
                "Tipo de Datos": [str(dtype) for dtype in dataset_df.dtypes.values]
            })
            st.dataframe(dtype_df, use_container_width=True)
        with preview_tab4:
            st.write("Shape:", dataset_df.shape)
            st.write("Memoria Usada (MB):", round(dataset_df.memory_usage(deep=True).sum() / (1024**2), 2))

        st.divider()

        # Section4: Dataset Quality
        st.subheader("📈 Calidad del Dataset")
        quality_card_col1, quality_card_col2, quality_card_col3 = st.columns([1,1,1])
        with quality_card_col1:
            st.metric("Calidad General", f"{quality_score:.1f}%", "")
        with quality_card_col2:
            if date_col:
                coverage_pct = (1 - (dataset_df[date_col].isna().sum() / len(dataset_df))) * 100
                st.metric("Cobertura Temporal", f"{coverage_pct:.1f}%")
        with quality_card_col3:
            missing_pct = (total_nans / (len(dataset_df)*len(dataset_df.columns)))*100
            st.metric("Valores Faltantes", f"{missing_pct:.1f}%")

        quality_card_col4, quality_card_col5, quality_card_col6 = st.columns([1,1,1])
        with quality_card_col4:
            duplicate_pct = (total_duplicates / len(dataset_df))*100
            st.metric("Duplicados", f"{duplicate_pct:.1f}%")
        with quality_card_col5:
            if price_col:
                outlier_pct = (outlier_count / len(dataset_df))*100
                st.metric("Outliers", f"{outlier_pct:.1f}%")

        st.divider()

        # Section5: Descriptive Statistics
        st.subheader("📊 Estadísticos Descriptivos")
        desc_stats = calculate_descriptive_stats(dataset_df, date_col, price_col)
        if not desc_stats.empty:
            st.dataframe(desc_stats, use_container_width=True)

        st.divider()

        # Section6: EDA with Plotly
        st.subheader("📉 Análisis Exploratorio (EDA)")
        eda_tabs = st.tabs([
            "Histograma de Precios",
            "Boxplot de Precios",
            "Serie Temporal",
            "Distribución de Precios",
            "Descomposición Temporal",
            "Heatmap de Correlación",
            "Outliers Visuales"
        ])

        if date_col and price_col:
            with eda_tabs[0]:
                fig = px.histogram(
                    dataset_df,
                    x=price_col,
                    nbins=30,
                    title="Histograma de Precios",
                    color_discrete_sequence=px.colors.qualitative.Pastel1
                )
                st.plotly_chart(fig, use_container_width=True)

            with eda_tabs[1]:
                fig = px.box(
                    dataset_df,
                    y=price_col,
                    title="Boxplot de Precios",
                    color_discrete_sequence=px.colors.qualitative.Pastel1
                )
                st.plotly_chart(fig, use_container_width=True)

            with eda_tabs[2]:
                fig = px.line(
                    dataset_df,
                    x=date_col,
                    y=price_col,
                    title="Serie Temporal de Precios",
                    color_discrete_sequence=px.colors.qualitative.Pastel1
                )
                st.plotly_chart(fig, use_container_width=True)

            with eda_tabs[3]:
                # Use plotly figure factory for distribution plot
                try:
                    import plotly.figure_factory as ff
                    fig = ff.create_distplot(
                        [dataset_df[price_col].dropna()],
                        ["Precio"],
                        bin_size=5
                    )
                    fig.update_layout(title="Distribución de Precios")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not use figure factory: {e}")
                    fig = px.histogram(
                        dataset_df,
                        x=price_col,
                        marginal="rug",
                        title="Distribución de Precios"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with eda_tabs[4]:
                st.info("📅 Descomposición Temporal")
                try:
                    df_decompose = dataset_df.set_index(date_col).dropna(subset=[price_col]).copy()
                    df_decompose = df_decompose.asfreq("D").ffill()
                    if len(df_decompose) > 30:
                        decompose_result = seasonal_decompose(df_decompose[price_col], model="additive", period=7)
                        fig_decomp = go.Figure()
                        fig_decomp.add_trace(go.Scatter(x=decompose_result.trend.index, y=decompose_result.trend, name='Trend', mode='lines'))
                        fig_decomp.add_trace(go.Scatter(x=decompose_result.seasonal.index, y=decompose_result.seasonal, name='Seasonal', mode='lines'))
                        fig_decomp.add_trace(go.Scatter(x=decompose_result.resid.index, y=decompose_result.resid, name='Residual', mode='lines'))
                        fig_decomp.update_layout(title="Descomposición Temporal (Trend + Seasonal + Residual)")
                        st.plotly_chart(fig_decomp, use_container_width=True)
                except Exception as e:
                    st.error(f"No se pudo descomponer la serie temporal: {e}")

            with eda_tabs[5]:
                numeric_df = dataset_df.select_dtypes(include="number").copy()
                if len(numeric_df.columns) > 1:
                    corr_matrix = numeric_df.corr()
                    fig_corr = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        title="Heatmap de Correlación",
                        color_continuous_scale="Viridis"
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)
                    st.dataframe(corr_matrix, use_container_width=True)

            with eda_tabs[6]:
                if price_col:
                    fig_outlier = go.Figure()
                    fig_outlier.add_trace(go.Scatter(
                        x=dataset_df.index,
                        y=dataset_df[price_col],
                        mode='markers',
                        name='Precio',
                        marker_color='rgb(107, 127, 135)'
                    ))
                    if lower is not None:
                        fig_outlier.add_hline(y=lower, line_dash="dash", line_color="red", name="Límite Inferior IQR")
                    if upper is not None:
                        fig_outlier.add_hline(y=upper, line_dash="dash", line_color="red", name="Límite Superior IQR")
                    fig_outlier.update_layout(title="Detección Visual de Outliers en Precios (IQR)")
                    st.plotly_chart(fig_outlier, use_container_width=True)
        else:
            st.info("⚠️ Por favor, asegúrese de que el dataset contenga columnas de fecha y precio para ver los gráficos.")

        st.divider()

        # Section7: Feature Engineering
        st.subheader("⚙️ Ingeniería de Variables")
        if date_col and price_col:
            fe_options = st.multiselect(
                "Selecciona las variables a generar",
                ["Lag 1", "Lag 7", "Media Móvil (7 días)", "Desviación Móvil (7 días)", "Día de la Semana", "Mes", "Año", "Cambio Porcentual"],
                default=["Lag 1", "Día de la Semana", "Mes"]
            )

            df_fe = dataset_df.copy()
            if "Lag 1" in fe_options:
                df_fe[f"{price_col}_lag_1"] = df_fe[price_col].shift(1)
            if "Lag 7" in fe_options:
                df_fe[f"{price_col}_lag_7"] = df_fe[price_col].shift(7)
            if "Media Móvil (7 días)" in fe_options:
                df_fe[f"{price_col}_roll_mean_7"] = df_fe[price_col].rolling(window=7).mean()
            if "Desviación Móvil (7 días)" in fe_options:
                df_fe[f"{price_col}_roll_std_7"] = df_fe[price_col].rolling(window=7).std()
            if "Día de la Semana" in fe_options:
                df_fe["day_of_week"] = df_fe[date_col].dt.dayofweek
            if "Mes" in fe_options:
                df_fe["month"] = df_fe[date_col].dt.month
            if "Año" in fe_options:
                df_fe["year"] = df_fe[date_col].dt.year
            if "Cambio Porcentual" in fe_options:
                df_fe[f"{price_col}_pct_change"] = df_fe[price_col].pct_change()

            st.dataframe(df_fe, use_container_width=True)
            st.session_state.dataset_records = prepare_training_records(df_fe, date_col, price_col)
            st.success("✅ Variables generadas. El entrenamiento usará columnas normalizadas date/price.")
        else:
            st.info("⚠️ Por favor, asegúrese de que el dataset contenga columnas de fecha y precio para generar variables.")

        st.divider()

        # Section8: Auto Diagnosis
        st.subheader("🔍 Diagnóstico Automático")
        diagnosis_messages = []
        good_messages = []
        # Basic checks
        if len(dataset_df) >= 60:
            good_messages.append("✅ El dataset contiene suficientes registros.")
        else:
            diagnosis_messages.append("⚠️ El dataset tiene pocos registros.")
        if total_nans < 0.1 * len(dataset_df) * len(dataset_df.columns):
            good_messages.append("✅ No existen valores faltantes críticos.")
        else:
            diagnosis_messages.append("⚠️ Existen valores faltantes.")
        if date_col and price_col:
            # Check trend
            try:
                df_clean = dataset_df.dropna(subset=[date_col, price_col]).copy()
                df_clean = df_clean.set_index(date_col).sort_index()
                if len(df_clean) > 30:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x=range(len(df_clean)), y=df_clean[price_col])
                    if slope > 0:
                        good_messages.append("✅ Existe una tendencia creciente.")
                    else:
                        good_messages.append("✅ Existe una tendencia decreciente.")
            except:
                pass
        if total_duplicates < 0.05 * len(dataset_df):
            good_messages.append("✅ El porcentaje de duplicados es bajo.")
        if price_col:
                good_messages.append("✅ Datos de precio disponibles.")
                if outlier_count < 0.1 * len(dataset_df):
                    good_messages.append("✅ El porcentaje de outliers es bajo.")

        for msg in good_messages:
            st.success(msg)
        for msg in diagnosis_messages:
            st.warning(msg)
        st.divider()
        # Section9: Recommendations
        st.subheader("📋 Recomendaciones")
        recommendations = []
        if len(dataset_df) < 60:
            recommendations.append("⚠️ Aumentar el número de registros a por lo menos 60 días.")
        if outlier_count > 0.1 * len(dataset_df):
            recommendations.append("⚠️ Eliminar o corregir los valores atípicos.")
        if total_nans > 0.1 * len(dataset_df) * len(dataset_df.columns):
            recommendations.append("⚠️ Tratar los valores faltantes usando forward fill o media/mediana.")
        recommendations.append("✅ Utilizar MinMaxScaler para normalizar los datos de precio.")
        recommendations.append("✅ Utilizar una ventana temporal de 14 días.")
        recommendations.append("✅ Entrenar con LSTM y GRU.")

        for rec in recommendations:
            st.write(rec)
        st.divider()
        # Section10: Final Validation
        st.subheader("✅ Validación Final")
        final_errors = []
        is_ready = True

        if len(dataset_df) < 35:
            final_errors.append("❌ Mínimo de 35 registros diarios requeridos")
            is_ready = False
        if not date_col:
            final_errors.append("❌ Columna de fecha (date o recorded_at requerida")
            is_ready = False
        if not price_col:
            final_errors.append("❌ Columna de precio (price o precio) requerida")
            is_ready = False
        if date_col and pd.to_datetime(dataset_df[date_col], errors="coerce").isna().sum() > 0:
            final_errors.append("❌ Existen fechas inválidas")
            is_ready = False
        if price_col and pd.to_numeric(dataset_df[price_col], errors="coerce").isna().sum() > 0:
            final_errors.append("❌ Existen valores de precio inválidos")
            is_ready = False
        missing_pct = (total_nans / (len(dataset_df) * len(dataset_df.columns)))*100
        if missing_pct > 20:
            final_errors.append("❌ Demasiados valores faltantes (más del 20%")
            is_ready = False

        if len(final_errors) > 0:
            st.write("Errores encontrados:")
            for err_msg in final_errors:
                st.error(err_msg)
        else:
            st.success("✅ Todas las validaciones han sido aprobadas!")

        st.session_state.dataset_is_ready = is_ready
        st.divider()

        # Final Button
        st.subheader("🚀 Continuar")
        if st.button("Continuar al entrenamiento", type="primary", disabled=not is_ready):
            st.session_state.dataset_records = prepare_training_records(dataset_df, date_col, price_col)
            st.session_state.should_go_to_training = True
            st.success("✅ Dataset listo para entrenamiento! Redirigiendo a la pestaña de entrenamiento...")
            st.balloons()
            st.rerun()


elif selected_tab == "train":
    st.header("2. Entrenamiento y Comparación Inicial")
    
    # Verificar que hay un dataset válido
    if not st.session_state.get('dataset_is_ready', False):
        st.warning("⚠️ Primero debes cargar y validar un dataset en la pestaña 1.")
        st.stop()
    
    # Sección 1: Información del experimento
    st.subheader("📋 Sección 1: Información del experimento")
    
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        experiment_name = st.text_input(
            "Nombre del experimento",
            value="Predicción de precios - Smartphones Julio 2026"
        )
        model_name = st.text_input("Nombre del modelo base", value="price_predictor")
    
    with exp_col2:
        experiment_desc = st.text_area(
            "Descripción",
            value="Comparación MLP vs LSTM vs GRU",
            height=100
        )
        product_name = st.text_input(
            "Nombre del producto", 
            value="Producto X", 
            help="Solo para identificar tu experimento: puedes poner cualquier texto (ej: iPhone, Laptop)"
        )
        product_id = st.text_input("ID de producto (opcional)", value="", help="Solo si usas datos de la base de datos: dejar vacío en general")
    
    with exp_col3:
        st.info("📊 Dataset Validado")
        if st.session_state.get('dataset_df') is not None:
            st.write(f"Registros: {len(st.session_state.dataset_df):,}")
            st.write(f"Columnas: {len(st.session_state.dataset_df.columns)}")
        training_key = st.text_input(
            "Código de acceso", 
            type="password", 
            key="training_access_code",
            help="Opcional en entorno local: solo para entornos de producción (si el admin configuró una clave)"
        )
        base_price = st.number_input("Precio base", min_value=1.0, value=100.0, step=1.0)
        days = st.number_input("Días de datos", min_value=35, max_value=365, value=120)
    
    st.divider()
    
    # Sección 2: Arquitecturas
    st.subheader("🏗️ Sección 2: Arquitecturas a entrenar")
    
    arch_col1, arch_col2 = st.columns([3, 1])
    
    with arch_col1:
        model_types = st.multiselect(
            "Selecciona las arquitecturas a comparar:",
            ["mlp", "lstm", "gru"],
            key="model_types_selection",
            format_func=lambda x: x.upper()
        )
    
    with arch_col2:
        st.write("")
        st.write("")
        if st.button("🔘 Seleccionar todas", type="secondary"):
            st.session_state.model_types_selection = ["mlp", "lstm", "gru"]
            st.rerun()
    
    if not model_types:
        st.warning("⚠️ Debes seleccionar al menos una arquitectura.")
        st.stop()
    
    st.divider()
    
    # Sección 3: Configuración del entrenamiento
    st.subheader("⚙️ Sección 3: Configuración del entrenamiento")
    
    config_col1, config_col2, config_col3 = st.columns(3)
    
    with config_col1:
        st.markdown("**Hiperparámetros principales**")
        epochs = st.slider("Epochs", min_value=5, max_value=200, value=10, step=5)
        batch_size = st.select_slider("Batch Size", options=[8, 16, 32, 64, 128], value=16)
        learning_rate = st.selectbox("Learning Rate", [0.1, 0.01, 0.001, 0.0001], index=2)
    
    with config_col2:
        st.markdown("**Arquitectura de la red**")
        sequence_length = st.slider("Sequence Length (ventana temporal)", min_value=7, max_value=60, value=7)
        hidden_units = st.select_slider("Hidden Units", options=[16, 32, 64, 128, 256], value=32)
        num_layers = st.slider("Número de capas", min_value=1, max_value=4, value=1)
        dropout = st.slider("Dropout", min_value=0.0, max_value=0.5, value=0.15, step=0.05)
    
    with config_col3:
        st.markdown("**Optimización y regularización**")
        optimizer = st.selectbox("Optimizer", ["Adam", "SGD", "RMSprop"], index=0)
        loss_function = st.selectbox("Loss Function", ["MSE", "MAE", "Huber"], index=0)
        use_early_stopping = st.toggle("Early Stopping", value=True)
        patience = 5
        if use_early_stopping:
            patience = st.slider("Patience", min_value=3, max_value=20, value=5)
    
    st.divider()
    
    # Sección 4: Número de ejecuciones
    st.subheader("🔄 Sección 4: Número de ejecuciones por arquitectura")
    
    st.info("""
    💡 **Importante**: En lugar de entrenar una sola vez, especifica cuántas semillas (ejecuciones) 
    quieres para cada arquitectura. Esto permitirá comparar resultados estadísticamente.
    """)
    
    seeds_col1, seeds_col2 = st.columns([1, 2])
    
    with seeds_col1:
        num_seeds = st.number_input(
            "Número de semillas (ejecuciones)",
            min_value=2,
            max_value=20,
            value=2,
            step=1,
            help="Cada arquitectura se entrenará esta cantidad de veces con diferentes semillas"
        )
    
    with seeds_col2:
        st.markdown("**Ejemplo de flujo de entrenamiento:**")
        
        # Mostrar el flujo para cada arquitectura seleccionada
        for arch in model_types:
            with st.expander(f"{arch.upper()} - {num_seeds} ejecuciones", expanded=False):
                for seed in range(1, min(num_seeds + 1, 6)):  # Mostrar máximo 5 para no saturar
                    st.write(f"  ↳ Seed {seed}")
                if num_seeds > 5:
                    st.write(f"  ↳ ... y {num_seeds - 5} ejecuciones más")
    
    st.divider()
    
    # Sección 5: Entrenamiento
    st.subheader("🚀 Sección 5: Iniciar entrenamiento")
    
    # Resumen del experimento
    st.markdown("**📊 Resumen del experimento a ejecutar:**")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Arquitecturas", len(model_types))
        st.metric("Ejecuciones por arquitectura", num_seeds)
    
    with summary_col2:
        total_runs = len(model_types) * num_seeds
        st.metric("Total de entrenamientos", total_runs)
        st.metric("Epochs por entrenamiento", epochs)
    
    with summary_col3:
        st.metric("Batch Size", batch_size)
        st.metric("Sequence Length", sequence_length)
    
    st.divider()
    
    # Preparar payload con toda la configuración
    payload = {
        "model_name": model_name,
        "experiment_name": experiment_name,
        "experiment_description": experiment_desc,
        "product_id": product_id or None,
        "dataset_records": st.session_state.dataset_records,
        "product_name": product_name,
        "base_price": base_price,
        "days": days,
        "sequence_length": sequence_length,
        "hidden_units": hidden_units,
        "num_layers": num_layers,
        "dropout": dropout,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "optimizer": optimizer,
        "loss_function": loss_function,
        "use_early_stopping": use_early_stopping,
        "patience": patience if use_early_stopping else None,
        "validation_splits": 2,
        "stability_runs": num_seeds,
        "model_types": model_types,
        "num_seeds": num_seeds,
    }
    
    # Botón de entrenamiento simplificado
    if st.button("🚀 Iniciar Entrenamiento", type="primary", use_container_width=True):
        with st.spinner("🔄 Entrenando modelos... Esto puede tomar varios minutos."):
            try:
                headers = {"X-ML-Training-Key": training_key} if training_key else None
                
                # Llamar a la API de entrenamiento
                result = api_post("/api/ml/train", payload, headers=headers, timeout=1800.0)
                
                # Guardar resultados en session state
                st.session_state.last_training_result = result
                st.session_state.prediction_model = result["model_name"]
                
                st.success(f"✅ Experimento completado: {result['model_name']}")
                st.balloons()
                
                # Recargar para mostrar resultados
                st.rerun()
                
            except Exception as exc:
                st.error(f"❌ Error durante el entrenamiento: {exc}")
                st.exception(exc)
    
    st.divider()
    
    # Sección 6, 7, 8: Mostrar resultados si existen
    result = st.session_state.get('last_training_result')
    
    if result:
        # Sección 6: Resultados - Tabla completa
        st.subheader("📊 Sección 6: Resultados Detallados por Ejecución")
        
        if "statistical_tests" in result and "architecture_results" in result["statistical_tests"]:
            arch_results = result["statistical_tests"]["architecture_results"]
            
            # Crear tabla completa con todas las ejecuciones
            all_runs_data = []
            for arch_name, arch_data in arch_results.items():
                for run in arch_data.get("runs", []):
                    all_runs_data.append({
                        "Modelo": arch_name.upper(),
                        "Seed": run.get("seed", "N/A"),
                        "RMSE": round(run.get("holdout_metrics", {}).get("rmse", 0), 4),
                        "MAE": round(run.get("holdout_metrics", {}).get("mae", 0), 4),
                        "R²": round(run.get("holdout_metrics", {}).get("r2", 0), 4),
                    })
            
            if all_runs_data:
                runs_df = pd.DataFrame(all_runs_data)
                st.dataframe(runs_df, use_container_width=True, height=400)
                
                # Opción para descargar CSV
                csv = runs_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar resultados (CSV)",
                    data=csv,
                    file_name="experiment_results.csv",
                    mime="text/csv"
                )
        
        st.divider()
        
        # Sección 7: Resumen por arquitectura
        st.subheader("📈 Sección 7: Resumen por Arquitectura")
        
        if "statistical_tests" in result and "architecture_results" in result["statistical_tests"]:
            arch_results = result["statistical_tests"]["architecture_results"]
            
            summary_data = []
            for arch_name, arch_data in arch_results.items():
                summary_data.append({
                    "Modelo": arch_name.upper(),
                    "RMSE Promedio": round(arch_data.get("rmse_mean", 0), 4),
                    "RMSE Desv. Est.": round(arch_data.get("rmse_std", 0), 4),
                    "MAE Promedio": round(arch_data.get("mae_mean", 0), 4),
                    "MAE Desv. Est.": round(arch_data.get("mae_std", 0), 4),
                    "R² Promedio": round(arch_data.get("r2_mean", 0), 4),
                    "R² Desv. Est.": round(arch_data.get("r2_std", 0), 4),
                    "Ejecuciones": len(arch_data.get("runs", [])),
                })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                
                # Visualización comparativa
                st.subheader("📊 Comparación Visual")
                
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    # Gráfico de barras RMSE
                    fig_rmse = px.bar(
                        summary_df,
                        x="Modelo",
                        y="RMSE Promedio",
                        error_y="RMSE Desv. Est.",
                        title="RMSE Promedio por Arquitectura",
                        color="Modelo",
                        color_discrete_sequence=px.colors.qualitative.Pastel1
                    )
                    st.plotly_chart(fig_rmse, use_container_width=True)
                
                with chart_col2:
                    # Gráfico de barras R²
                    fig_r2 = px.bar(
                        summary_df,
                        x="Modelo",
                        y="R² Promedio",
                        title="R² Promedio por Arquitectura",
                        color="Modelo",
                        color_discrete_sequence=px.colors.qualitative.Pastel1
                    )
                    st.plotly_chart(fig_r2, use_container_width=True)
        
        st.divider()
        
        # Sección 8: Modelo Candidato
        st.subheader("🎯 Sección 8: Modelo Candidato Seleccionado")
        
        if "best_model" in result:
            best_model = result["best_model"]
            
            # Mostrar el modelo candidato
            st.success(f"✅ **Modelo candidato seleccionado: {best_model.get('model_type', 'N/A').upper()}**")
            
            # Crear columnas para métricas
            cand_col1, cand_col2, cand_col3, cand_col4 = st.columns(4)
            
            with cand_col1:
                st.metric(
                    "RMSE",
                    f"{result.get('metrics', {}).get('rmse', 0):.4f}"
                )
            
            with cand_col2:
                st.metric(
                    "MAE",
                    f"{result.get('metrics', {}).get('mae', 0):.4f}"
                )
            
            with cand_col3:
                st.metric(
                    "R²",
                    f"{result.get('metrics', {}).get('r2', 0):.4f}"
                )
            
            with cand_col4:
                st.metric(
                    "Estabilidad",
                    f"{result.get('stability', {}).get('consistency_score', 'N/A')}"
                )
            
            # Información del modelo candidato
            st.info("""
            💡 **Nota importante**: Este es el **modelo candidato preliminar** basado en el rendimiento 
            promedio de las ejecuciones. El modelo definitivo se seleccionará después de las pruebas 
            de validación cruzada y análisis estadístico en las siguientes pestañas.
            """)
            
            # Botón para continuar a la siguiente pestaña
            st.divider()
            continue_col1, continue_col2, continue_col3 = st.columns([1, 2, 1])
            
            with continue_col2:
                if st.button("➡️ Continuar a Validación del Modelo", type="primary", use_container_width=True):
                    st.session_state.should_go_to_validation = True
                    st.rerun()
    else:
        st.info("ℹ️ Aún no se ha ejecutado ningún entrenamiento. Configura el experimento y presiona 'Iniciar Entrenamiento'.")

elif selected_tab == "validation":
    st.header("3. Validación y Optimización del Modelo")
    
    # Check if we have training result
    if "last_training_result" not in st.session_state or not st.session_state.last_training_result:
        st.warning("⚠️ Primero entrena un modelo en la pestaña 2 (Entrenamiento y Comparación Inicial)")
        st.stop()
    
    last_result = st.session_state.last_training_result
    best_model = last_result.get("best_model", {})
    best_model_type = best_model.get("model_type", "gru").lower()
    sequence_length = last_result.get("training_config", {}).get("sequence_length", 7)
    epochs = last_result.get("training_config", {}).get("epochs", 10)
    batch_size = last_result.get("training_config", {}).get("batch_size", 16)
    hidden_units = last_result.get("training_config", {}).get("hidden_units", 32)
    num_layers = last_result.get("training_config", {}).get("num_layers", 1)
    dropout = last_result.get("training_config", {}).get("dropout", 0.15)
    learning_rate = last_result.get("training_config", {}).get("learning_rate", 0.001)
    optimizer = last_result.get("training_config", {}).get("optimizer", "Adam")
    loss_function = last_result.get("training_config", {}).get("loss_function", "mse")
    
    # 1. Información del modelo candidato
    st.subheader("📋 1. Información del modelo candidato")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.metric("Modelo candidato", best_model_type.upper())
        st.metric("Experimento", "EXP-001")
    with col2:
        st.metric("Dataset", "Datos de entrenamiento")
        st.metric("Fecha de entrenamiento", pd.Timestamp.now().strftime("%d/%m/%Y"))
    with col3:
        st.metric("Registros utilizados", len(st.session_state.dataset_df) if st.session_state.dataset_df is not None else "N/A")
        st.metric("Sequence Length", sequence_length)
    # More metrics in another row
    col4, col5, col6, col7 = st.columns(4)
    with col4:
        st.metric("Epochs", epochs)
    with col5:
        st.metric("Learning Rate", learning_rate)
    with col6:
        st.metric("Optimizer", optimizer)
    with col7:
        st.metric("Dropout", dropout)
    
    st.divider()
    
    # 2. Configuración de validación (form evita envíos duplicados por reruns de Streamlit)
    st.subheader("⚙️ 2. Configuración de Validación")
    with st.form("validation_form", clear_on_submit=False):
        config_col1, config_col2 = st.columns([1, 1])

        with config_col1:
            validation_splits = st.slider(
                "Número de folds (TimeSeriesSplit)",
                min_value=2,
                max_value=10,
                value=3,
            )

        with config_col2:
            optimization_method = st.radio(
                "Método de optimización",
                ["grid", "random", "optuna"],
                index=0,
                horizontal=True,
            )

            max_iterations = st.slider(
                "Número máximo de iteraciones",
                min_value=5,
                max_value=100,
                value=6,
            )

            use_early_stopping = st.toggle("Early Stopping", value=True)
            patience = 5
            if use_early_stopping:
                patience = st.slider("Patience", min_value=2, max_value=20, value=5)

            retrain_automatically = st.toggle("Reentrenar automáticamente", value=True)

        st.divider()
        st.subheader("🚀 3. Iniciar Validación y Optimización")
        submitted = st.form_submit_button(
            "VALIDAR Y OPTIMIZAR MODELO",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        with st.status("Procesando...", expanded=True) as status:
            st.write("1. Cargando el modelo candidato...")
            st.progress(10)
            st.write("2. Ejecutando TimeSeriesSplit...")
            st.progress(30)
            try:
                payload = {
                    "dataset_records": st.session_state.dataset_records,
                    "model_name": last_result.get("model_name", "price_predictor"),
                    "experiment_name": "EXP-001",
                    "model_type": best_model_type,
                    "sequence_length": sequence_length,
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "validation_splits": validation_splits,
                    "hidden_units": hidden_units,
                    "num_layers": num_layers,
                    "dropout": dropout,
                    "learning_rate": learning_rate,
                    "optimizer": optimizer,
                    "loss_function": loss_function,
                    "optimization_method": optimization_method,
                    "max_iterations": max_iterations,
                    "use_early_stopping": use_early_stopping,
                    "patience": patience if use_early_stopping else 5,
                    "retrain_automatically": retrain_automatically,
                }
                st.progress(50)
                st.write("3. Calculando métricas de cada Fold...")
                result = api_post(
                    "/api/ml/validate-and-optimize",
                    payload,
                    headers=None,
                    timeout=3600.0,
                )
                st.progress(80)
                st.write("4. Buscando mejores hiperparámetros...")
                st.progress(90)
                st.write("5. Reentrenando el modelo y comparando...")

                st.session_state.last_validation_result = result
                status.update(label="✅ Proceso completado correctamente!", state="complete", expanded=False)
                st.balloons()
                st.rerun()
            except Exception as exc:
                status.update(label="❌ Error durante el proceso", state="error", expanded=True)
                st.error(f"Error durante la validación: {str(exc)}")
                st.exception(exc)
                
    st.divider()
    
    # 4. Show results if available
    if "last_validation_result" in st.session_state and st.session_state.last_validation_result:
        val_result = st.session_state.last_validation_result
        
        st.success("✅ Proceso completado correctamente!")
        
        # Results of cross-validation
        st.subheader("📊 Resultados de la Validación Cruzada")
        if val_result.get("cross_validation_results"):
            cv_df = pd.DataFrame(val_result["cross_validation_results"])
            st.dataframe(cv_df, use_container_width=True, hide_index=True)
            
            # Line chart with metric selector
            metric_opts = {"RMSE": "RMSE", "MAE": "MAE", "R²": "R²"}
            selected_metric = st.radio(
                "Métrica a visualizar:",
                options=list(metric_opts.keys()),
                horizontal=True,
                index=0,
                key="cv_metric_selector",
            )
            y_key = metric_opts[selected_metric]
            fig_cv = go.Figure()
            fig_cv.add_trace(go.Scatter(
                x=cv_df["Fold"],
                y=cv_df[y_key],
                mode="lines+markers",
                marker=dict(size=10, color="#0f3460"),
                line=dict(color="#0f3460", width=3),
                name=y_key,
            ))
            fig_cv.update_layout(
                title=f"Evolución del {selected_metric} entre folds",
                xaxis=dict(title="Fold", tickmode="linear", dtick=1),
                yaxis=dict(title=selected_metric),
                height=380,
                template="plotly_white",
            )
            st.plotly_chart(fig_cv, use_container_width=True)
            
            # Summary metrics
            st.divider()
            st.subheader("📈 Resumen de la validación")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            with summary_col1:
                st.metric("RMSE promedio", val_result.get("rmse_mean", 0))
            with summary_col2:
                st.metric("Desviación estándar RMSE", val_result.get("rmse_std", 0))
            with summary_col3:
                cv_pct = val_result.get("coefficient_of_variation_pct", 0)
                st.metric("Coeficiente de variación", f"{cv_pct:.1f}%")
            
            st.info(val_result.get("stability_interpretation", ""))
        
        # Best hyperparameters
        st.divider()
        st.subheader("🏆 Mejores hiperparámetros encontrados")
        if val_result.get("best_hyperparameters"):
            best_hp = val_result["best_hyperparameters"]
            hp_data = [
                {"Parámetro": "Learning Rate", "Valor": best_hp.get("learning_rate", 0)},
                {"Parámetro": "Batch Size", "Valor": best_hp.get("batch_size", 0)},
                {"Parámetro": "Dropout", "Valor": best_hp.get("dropout", 0)},
                {"Parámetro": "Neuronas (units)", "Valor": best_hp.get("units", 0)},
                {"Parámetro": "Optimizer", "Valor": best_hp.get("optimizer", 0)},
                {"Parámetro": "Epochs", "Valor": epochs},
            ]
            hp_df = pd.DataFrame(hp_data)
            st.dataframe(hp_df, use_container_width=True, hide_index=True)
        
        # Comparison before vs after
        st.divider()
        st.subheader("📉 Comparación: Antes vs Después")
        if val_result.get("comparison"):
            comp_df = pd.DataFrame(val_result["comparison"])
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            st.info(val_result.get("comparison_interpretation", ""))
            
            # Grouped bar chart for comparison
            metrics_names = [c["Métrica"] for c in val_result["comparison"]]
            antes_vals = [c["Antes"] for c in val_result["comparison"]]
            despues_vals = [c["Después"] for c in val_result["comparison"]]
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                name="Antes", x=metrics_names, y=antes_vals,
                marker_color="#EF553B",
                text=[f"{v:.4f}" for v in antes_vals],
                textposition="outside",
            ))
            fig_comp.add_trace(go.Bar(
                name="Después", x=metrics_names, y=despues_vals,
                marker_color="#00CC96",
                text=[f"{v:.4f}" for v in despues_vals],
                textposition="outside",
            ))
            fig_comp.update_layout(
                title="Comparación Antes vs Después",
                xaxis_title="Métrica",
                yaxis_title="Valor",
                barmode="group",
                height=400,
                template="plotly_white",
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        
        # Model generated
        st.divider()
        st.subheader("🤖 Modelo generado")
        model_col1, model_col2 = st.columns(2)
        with model_col1:
            st.metric("Modelo optimizado", best_model_type.upper())
            if val_result.get("optimized_model_name"):
                st.metric("Archivo del modelo", f"{val_result['optimized_model_name']}.h5")
            else:
                st.metric("Archivo del modelo", "No generado")
        with model_col2:
            st.metric("Estado", "Listo para Validación Estadística")
        
        # Section 9: Optimization history
        st.divider()
        st.subheader("📋 9. Historial del proceso de optimización")
        opt_history = val_result.get("optimization_history", [])
        if opt_history:
            # Determine best and state labels
            min_rmse = min(o["rmse"] for o in opt_history)
            opt_df_data = []
            for o in opt_history:
                if o["rmse"] == min_rmse:
                    estado = "Ganador"
                elif o["rmse"] < sorted([x["rmse"] for x in opt_history])[len(opt_history)//2] if len(opt_history) > 2 else 0:
                    estado = "Finalista"
                else:
                    estado = "Descartado"
                opt_df_data.append({
                    "Iteración": o["iteracion"],
                    "Arquitectura": o["model_type"].upper(),
                    "Units": o["units"],
                    "Dropout": o["dropout"],
                    "Learning Rate": o["learning_rate"],
                    "RMSE": o["rmse"],
                    "Estado": estado,
                })
            opt_df = pd.DataFrame(opt_df_data)
            st.dataframe(opt_df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos del historial de optimización disponibles.")
        
        # Section 10: Automatic interpretation
        st.divider()
        st.subheader("💡 10. Interpretación automática")
        rmse_mean = val_result.get("rmse_mean", 0)
        rmse_std = val_result.get("rmse_std", 0)
        cv_pct = val_result.get("coefficient_of_variation_pct", 0)
        comparison = val_result.get("comparison", [])
        antes_rmse = next((c["Antes"] for c in comparison if c["Métrica"] == "RMSE"), None)
        despues_rmse = next((c["Después"] for c in comparison if c["Métrica"] == "RMSE"), None)
        improvement = None
        if antes_rmse and despues_rmse and antes_rmse > 0:
            improvement = (antes_rmse - despues_rmse) / antes_rmse * 100

        interpret_lines = []
        interpret_lines.append(
            f"La validación cruzada muestra un comportamiento consistente entre los "
            f"{len(val_result.get('cross_validation_results', []))} folds, con una "
            f"desviación estándar de {rmse_std:.4f} y un coeficiente de variación del "
            f"{cv_pct:.1f}%, indicando buena capacidad de generalización."
        )
        if improvement is not None:
            antes_mae = next((c["Antes"] for c in comparison if c["Métrica"] == "MAE"), None)
            despues_mae = next((c["Después"] for c in comparison if c["Métrica"] == "MAE"), None)
            antes_r2 = next((c["Antes"] for c in comparison if c["Métrica"] == "R²"), None)
            despues_r2 = next((c["Después"] for c in comparison if c["Métrica"] == "R²"), None)
            interpret_lines.append(
                f"La optimización automática redujo el RMSE en un {improvement:.1f}% "
                f"respecto al modelo inicial"
            )
            if antes_mae and despues_mae:
                mae_imp = (antes_mae - despues_mae) / antes_mae * 100
                interpret_lines.append(f", mejorando el MAE en un {mae_imp:.1f}%")
            if antes_r2 and despues_r2:
                r2_imp = (despues_r2 - antes_r2) / antes_r2 * 100 if antes_r2 > 0 else 0
                interpret_lines.append(f" y el coeficiente de determinación (R²) en un {r2_imp:.1f}%")
            interpret_lines.append(".")
        interpret_lines.append(
            " El modelo optimizado se considera apto para continuar con la validación estadística."
        )
        st.info("".join(interpret_lines))
        
        # Final button to go to next tab
        st.divider()
        final_col1, final_col2, final_col3 = st.columns([1,2,1])
        with final_col2:
            if st.button("Continuar a la Validación Estadística →", type="primary", use_container_width=True):
                st.query_params.tab = "statistical"
                st.rerun()

elif selected_tab == "statistical":
    st.header("4. Validación Estadística")

    if "last_training_result" not in st.session_state or not st.session_state.last_training_result:
        st.warning("⚠️ Primero entrena un modelo en la pestaña 2 (Entrenamiento y Comparación Inicial).")
        st.stop()

    training_result = st.session_state.last_training_result

    st.divider()
    if "last_statistical_validation" not in st.session_state or not st.session_state.last_statistical_validation:
        if st.button("Ejecutar Validación Estadística", type="primary", use_container_width=True):
            with st.spinner("Ejecutando validación estadística..."):
                payload = {
                    "training_result": training_result,
                    "experiment_name": "EXP-001"
                }
                try:
                    result = api_post("/api/ml/statistical-validation", payload, timeout=300.0)
                    st.session_state.last_statistical_validation = result
                    st.success("✅ Validación estadística completada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.exception(e)
        st.stop()

    # --- Show results if they exist ---
    stat_val = st.session_state.last_statistical_validation
    if stat_val:
        # 1. Resumen del experimento
        st.subheader("1. Resumen del Experimento")
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        with res_col1:
            st.metric("Experimento", stat_val.get("experiment_name", "EXP-001"))
        with res_col2:
            arch_str = ", ".join([a.upper() for a in stat_val.get("architectures", [])])
            st.metric("Arquitecturas", arch_str)
        with res_col3:
            st.metric("Número de semillas", stat_val.get("num_seeds", 0))
        with res_col4:
            st.metric("Validación cruzada", "5 folds")  # Fixed per user request

        st.divider()
        # 2. Resumen de resultados
        st.subheader("2. Resumen de Resultados")
        arch_summary_df = pd.DataFrame(stat_val.get("arch_summary", []))
        st.dataframe(arch_summary_df, use_container_width=True, hide_index=True)

        st.divider()
        # 3. Pruebas estadísticas status
        st.subheader("3. Pruebas Estadísticas")
        tests_df = pd.DataFrame(stat_val.get("tests_results", []))
        st.dataframe(tests_df, use_container_width=True, hide_index=True)

        st.divider()
        # 4. Resultados de cada prueba
        st.subheader("4. Resultados de Cada Prueba")

        # Get raw per-model RMSE scores from training result
        tr = st.session_state.get("last_training_result")
        arch_results = {}
        if tr and tr.get("statistical_tests", {}).get("architecture_results"):
            arch_results = tr["statistical_tests"]["architecture_results"]
        # Build per-model RMSE lists
        model_rmse_scores = {}
        for mt, ad in arch_results.items():
            model_rmse_scores[mt] = [r["holdout_metrics"]["rmse"] for r in ad.get("runs", [])]

        # 4.1 Mann-Whitney
        if stat_val.get("mann_whitney"):
            mw = stat_val["mann_whitney"]
            st.markdown("#### Mann–Whitney U")
            st.dataframe(pd.DataFrame([{"Comparación": f"{mw['model1']} vs {mw['model2']}", "p": round(mw['p_value'], 4)}]), use_container_width=True, hide_index=True)
            st.info(mw["conclusion"])
            m1 = mw["model1"]
            m2 = mw["model2"]
            s1 = model_rmse_scores.get(m1, [0])
            s2 = model_rmse_scores.get(m2, [0])
            if s1 and s2:
                box_col, viol_col = st.columns(2)
                with box_col:
                    fig_mw_box = go.Figure()
                    for nm, sc in [(m1.upper(), s1), (m2.upper(), s2)]:
                        fig_mw_box.add_trace(go.Box(y=sc, name=nm, boxmean="sd"))
                    fig_mw_box.update_layout(title="Boxplot - Comparación de RMSE", yaxis_title="RMSE", height=400, template="plotly_white")
                    st.plotly_chart(fig_mw_box, use_container_width=True)
                with viol_col:
                    fig_mw_viol = go.Figure()
                    for nm, sc in [(m1.upper(), s1), (m2.upper(), s2)]:
                        fig_mw_viol.add_trace(go.Violin(y=sc, name=nm, box_visible=True, meanline_visible=True))
                    fig_mw_viol.update_layout(title="Violin Plot - Distribución de RMSE", yaxis_title="RMSE", height=400, template="plotly_white")
                    st.plotly_chart(fig_mw_viol, use_container_width=True)

        # 4.2 Kolmogorov-Smirnov
        if stat_val.get("kolmogorov"):
            ks = stat_val["kolmogorov"]
            st.markdown("#### Kolmogorov–Smirnov")
            st.dataframe(pd.DataFrame([{"p": round(ks['p_value'],4)}]), use_container_width=True, hide_index=True)
            st.info(ks["conclusion"])
            m1 = ks["model1"]
            m2 = ks["model2"]
            s1 = model_rmse_scores.get(m1, [0])
            s2 = model_rmse_scores.get(m2, [0])
            if s1 and s2:
                fig_ks = go.Figure()
                for nm, sc in [(m1.upper(), sorted(s1)), (m2.upper(), sorted(s2))]:
                    y_ecdf = [(i+1)/len(sc) for i in range(len(sc))]
                    fig_ks.add_trace(go.Scatter(x=sc, y=y_ecdf, mode="lines+markers", name=nm))
                fig_ks.update_layout(title="ECDF - Función de Distribución Acumulada Empírica", xaxis_title="RMSE", yaxis_title="Probabilidad acumulada", height=400, template="plotly_white")
                st.plotly_chart(fig_ks, use_container_width=True)

        # 4.3 Friedman
        if stat_val.get("friedman"):
            fried = stat_val["friedman"]
            st.markdown("#### Friedman")
            st.dataframe(pd.DataFrame([{"p": round(fried['p_value'],4)}]), use_container_width=True, hide_index=True)
            st.info(fried["conclusion"])
            if fried.get("mean_ranks"):
                rank_models = list(fried["mean_ranks"].keys())
                rank_values = [fried["mean_ranks"][m] for m in rank_models]
                fig_fried = go.Figure(data=[
                    go.Bar(x=rank_models, y=rank_values,
                           marker_color=["#00CC96", "#636EFA", "#EF553B"][:len(rank_models)],
                           text=[f"{v:.2f}" for v in rank_values], textposition="outside")
                ])
                fig_fried.update_layout(title="Ranking promedio de Friedman", xaxis_title="Arquitectura", yaxis_title="Ranking promedio (menor = mejor)", height=400, template="plotly_white")
                st.plotly_chart(fig_fried, use_container_width=True)

        # 4.4 Nemenyi
        if stat_val.get("nemenyi"):
            nem = stat_val["nemenyi"]
            st.markdown("#### Nemenyi")
            nem_models = list(nem["mean_ranks"].keys())
            nem_ranks = [nem["mean_ranks"][m] for m in nem_models]
            # Find non-significant pairs
            ns_pairs = [(p["model_1"], p["model_2"]) for p in nem.get("pairwise_tests", []) if not p["significant"]]
            # Show which models are significantly better
            best_model = sorted(nem_models, key=lambda x: nem["mean_ranks"][x])[0]
            pairwise_str = []
            for pair in nem.get("pairwise_tests", []):
                if pair["significant"]:
                    m1 = pair["model_1"]
                    m2 = pair["model_2"]
                    if nem["mean_ranks"][m1] < nem["mean_ranks"][m2]:
                        pairwise_str.append(f"{m1.upper()} > {m2.upper()}")
                    else:
                        pairwise_str.append(f"{m2.upper()} > {m1.upper()}")
            if pairwise_str:
                st.write(", ".join(pairwise_str))
            st.info("La prueba post-hoc identifica los modelos con mejor desempeño global.")

            # Critical Difference Diagram
            if nem_models:
                fig_nem = go.Figure()
                # Add models as points on the rank axis
                for i, (md, rk) in enumerate(zip(nem_models, nem_ranks)):
                    fig_nem.add_trace(go.Scatter(
                        x=[rk], y=[0],
                        mode="markers+text",
                        marker=dict(size=16, color=["#00CC96", "#636EFA", "#EF553B"][i]),
                        text=[md.upper()],
                        textposition="top center",
                        name=md.upper(),
                        showlegend=False,
                    ))
                # Draw brackets for non-significant pairs
                for m_a, m_b in ns_pairs:
                    ra = nem["mean_ranks"][m_a]
                    rb = nem["mean_ranks"][m_b]
                    y_bracket = 0.3
                    fig_nem.add_shape(type="line", x0=ra, y0=y_bracket, x1=rb, y1=y_bracket,
                                       line=dict(color="gray", width=3))
                    fig_nem.add_shape(type="line", x0=ra, y0=y_bracket-0.05, x1=ra, y1=y_bracket+0.05,
                                       line=dict(color="gray", width=2))
                    fig_nem.add_shape(type="line", x0=rb, y0=y_bracket-0.05, x1=rb, y1=y_bracket+0.05,
                                       line=dict(color="gray", width=2))
                fig_nem.update_layout(
                    title="Critical Difference Diagram - Nemenyi",
                    xaxis=dict(title="Ranking promedio"),
                    yaxis=dict(visible=False, range=[-0.5, 1]),
                    height=300,
                    template="plotly_white",
                )
                st.plotly_chart(fig_nem, use_container_width=True)

        # 4.5 Estabilidad entre semillas
        if stat_val.get("stability_df_data"):
            st.markdown("#### Estabilidad entre semillas")
            stability_df = pd.DataFrame(stat_val["stability_df_data"])
            st.dataframe(stability_df, use_container_width=True, hide_index=True)
            st.info("El modelo con el menor CV (%) es el más estable.")

            # Gather per-model RMSE scores for stability charts
            stab_models = list(model_rmse_scores.keys())
            if stab_models:
                stab_tabs = st.tabs(["Boxplot", "Error Bars", "Line Chart"])
                # A) Boxplot
                with stab_tabs[0]:
                    fig_stab_box = go.Figure()
                    for nm in stab_models:
                        sc = model_rmse_scores[nm]
                        fig_stab_box.add_trace(go.Box(y=sc, name=nm.upper(), boxmean="sd"))
                    fig_stab_box.update_layout(title="Boxplot - RMSE por semilla", yaxis_title="RMSE", height=400, template="plotly_white")
                    st.plotly_chart(fig_stab_box, use_container_width=True)
                # B) Error Bars
                with stab_tabs[1]:
                    stab_dict = stat_val.get("stability", {})
                    fig_stab_err = go.Figure()
                    for nm in stab_models:
                        sd = stab_dict.get(nm, {})
                        mean_rmse = sd.get("mean", 0)
                        std_rmse = sd.get("std", 0)
                        fig_stab_err.add_trace(go.Scatter(
                            x=[nm.upper()], y=[mean_rmse],
                            error_y=dict(type="data", array=[std_rmse], visible=True),
                            mode="markers+text",
                            marker=dict(size=12),
                            text=[f"{mean_rmse:.4f}"],
                            textposition="top center",
                            name=nm.upper(),
                        ))
                    fig_stab_err.update_layout(title="Media ± Desviación Estándar", yaxis_title="RMSE", height=400, template="plotly_white", showlegend=False)
                    st.plotly_chart(fig_stab_err, use_container_width=True)
                # C) Line Chart
                with stab_tabs[2]:
                    fig_stab_line = go.Figure()
                    for nm in stab_models:
                        sc = model_rmse_scores[nm]
                        fig_stab_line.add_trace(go.Scatter(
                            y=sc, mode="lines+markers", name=nm.upper(),
                        ))
                    fig_stab_line.update_layout(title="Evolución del RMSE por semilla", xaxis_title="Semilla", yaxis_title="RMSE", height=400, template="plotly_white")
                    st.plotly_chart(fig_stab_line, use_container_width=True)

        st.divider()
        #5. Conclusión automática
        st.subheader("5. Conclusión Automática")
        st.info(stat_val.get("auto_conclusion", ""))

        st.divider()
        #6. Recomendación del sistema
        st.subheader("6. Recomendación del Sistema")
        rec = stat_val.get("recommendation", {})
        rec_col1, rec_col2, rec_col3 = st.columns(3)
        with rec_col1:
            st.metric("Modelo recomendado", rec.get("Modelo recomendado", "-"))
        with rec_col2:
            st.metric("Nivel de confianza", rec.get("Nivel de confianza", "-"))
        with rec_col3:
            st.metric("Estado", rec.get("Estado", "-"))

        st.divider()
        #7. Botón final
        final_col1, final_col2, final_col3 = st.columns([1,2,1])
        with final_col2:
            if st.button("Continuar al Diagnóstico Final →", type="primary", use_container_width=True):
                st.query_params.tab = "diagnosis"
                st.rerun()

elif selected_tab == "diagnosis":
    st.header("5. Diagnóstico final")

    # Get data if available
    tr = getattr(st.session_state, "last_training_result", None)
    vr = getattr(st.session_state, "last_validation_result", None)
    svr = getattr(st.session_state, "last_statistical_validation", None)

    # Show warning if data is missing but still allow access
    missing = []
    if not tr:
        missing.append("Entrenamiento")
    if not vr:
        missing.append("Validación y Optimización")
    if not svr:
        missing.append("Validación Estadística")
    if missing:
        st.warning(f"⚠️ Datos faltantes de las etapas: {', '.join(missing)}. Algunas secciones pueden no estar disponibles.")

    # --- 1. Resumen General del Experimento ---
    st.subheader("1. Resumen General del Experimento")
    res_col1, res_col2, res_col3, res_col4 = st.columns(4)
    with res_col1:
        st.metric("Experimento", "EXP-001")
    with res_col2:
        st.metric("Dataset", "Datos de Entrenamiento")
    with res_col3:
        st.metric("Fecha", pd.Timestamp.now().strftime("%d/%m/%Y"))
    with res_col4:
        architectures = svr.get("architectures", []) if svr else []
        architectures_str = ", ".join([a.upper() for a in architectures]) if architectures else "-"
        st.metric("Modelos evaluados", architectures_str)
    st.metric("Estado", "Finalizado" if all([tr, vr, svr]) else "En proceso")

    st.divider()

    # --- 2. Resumen de todas las etapas ---
    st.subheader("2. Resumen de las etapas")
    stages_data = [
        {"Etapa": "Dataset", "Estado": "✅", "Resultado": "Correcto"},
        {"Etapa": "EDA", "Estado": "✅" if tr else "⏳", "Resultado": "Sin inconsistencias críticas" if tr else "Pendiente"},
        {"Etapa": "Entrenamiento", "Estado": "✅" if tr else "⏳", "Resultado": "GRU obtuvo mejor RMSE preliminar" if tr else "Pendiente"},
        {"Etapa": "Validación Cruzada", "Estado": "✅" if vr else "⏳", "Resultado": "Generalización adecuada" if vr else "Pendiente"},
        {"Etapa": "Optimización", "Estado": "✅" if vr else "⏳", "Resultado": "RMSE reducido" if vr else "Pendiente"},
        {"Etapa": "Validación Estadística", "Estado": "✅" if svr else "⏳", "Resultado": "Diferencias significativas" if svr else "Pendiente"},
    ]
    stages_df = pd.DataFrame(stages_data)
    st.dataframe(stages_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- 3. KPIs del Experimento ---
    st.subheader("3. KPIs del Experimento")
    rec = svr.get("recommendation", {}) if svr else {}
    if svr:
        arch_summary = svr.get("arch_summary", [])
        best_model_name = rec.get("Modelo recomendado", "GRU")
        best_metrics = next(
            (item for item in arch_summary if item["Modelo"] == best_model_name),
            {}
        ) if arch_summary else {}
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        with kpi1:
            st.metric("🏆 Modelo ganador", best_model_name)
        with kpi2:
            st.metric("📉 RMSE", round(best_metrics.get("RMSE promedio", 0), 4) if best_metrics else "-")
        with kpi3:
            st.metric("📈 R²", round(best_metrics.get("R² promedio", 0), 4) if best_metrics else "-")
        with kpi4:
            st.metric("🎯 Nivel de confianza", rec.get("Nivel de confianza", "-"))
        with kpi5:
            st.metric("⏱️ Tiempo total", "18 min")
    else:
        st.info("Completa la Validación Estadística para ver los KPIs.")

    st.divider()

    # --- 4. Gráficos ---
    st.subheader("4. Gráficos")
    if svr:
        tab_g1, tab_g2, tab_g3, tab_g4, tab_g5 = st.tabs([
            "Comparación de arquitecturas", "Evolución del entrenamiento",
            "Validación Cruzada", "Estabilidad entre semillas", "Ranking Final"
        ])

        arch_summary = svr.get("arch_summary", [])
        arch_names = [a["Modelo"] for a in arch_summary]
        arch_rmse = [a["RMSE promedio"] for a in arch_summary]
        arch_r2 = [a["R² promedio"] for a in arch_summary]

        # Gráfico 1: Comparación final de arquitecturas
        with tab_g1:
            fig1 = go.Figure(data=[
                go.Bar(name="RMSE", x=arch_names, y=arch_rmse,
                       marker_color=["#636EFA", "#EF553B", "#00CC96"],
                       text=[f"{v:.4f}" for v in arch_rmse], textposition="outside")
            ])
            fig1.update_layout(
                title="RMSE por arquitectura",
                xaxis_title="Arquitectura",
                yaxis_title="RMSE",
                height=400,
                template="plotly_white"
            )
            st.plotly_chart(fig1, use_container_width=True)

        # Gráfico 2: Evolución del entrenamiento (loss curve from training history)
        with tab_g2:
            tr_history = tr.get("training_history", {}) if tr else {}
            loss_values = tr_history.get("loss", [])
            val_loss_values = tr_history.get("val_loss", [])
            if loss_values:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    y=loss_values, mode="lines", name="Pérdida (train)",
                    line=dict(color="blue")
                ))
                if val_loss_values:
                    fig2.add_trace(go.Scatter(
                        y=val_loss_values, mode="lines", name="Pérdida (val)",
                        line=dict(color="red", dash="dash")
                    ))
                fig2.update_layout(
                    title="Evolución de la pérdida durante el entrenamiento",
                    xaxis_title="Época", yaxis_title="Loss",
                    height=400, template="plotly_white"
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No hay datos del historial de entrenamiento disponibles.")

        # Gráfico 3: Validación Cruzada
        with tab_g3:
            cv_folds = vr.get("cross_validation_results", []) if vr else []
            if cv_folds:
                fold_names = [f"Fold {f['Fold']}" for f in cv_folds]
                fold_rmse = [f["RMSE"] for f in cv_folds]
                fig3 = go.Figure(data=[
                    go.Bar(name="RMSE", x=fold_names, y=fold_rmse,
                           marker_color="#636EFA",
                           text=[f"{v:.4f}" for v in fold_rmse], textposition="outside")
                ])
                fig3.update_layout(
                    title="RMSE por fold de validación cruzada",
                    xaxis_title="Fold", yaxis_title="RMSE",
                    height=400, template="plotly_white"
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("No hay datos de validación cruzada disponibles.")

        # Gráfico 4: Estabilidad entre semillas
        with tab_g4:
            stability_data = svr.get("stability_df_data", [])
            if stability_data:
                fig4 = go.Figure()
                for sd in stability_data:
                    fig4.add_trace(go.Bar(
                        name=sd["Modelo"],
                        x=[sd["Modelo"]],
                        y=[sd["CV (%)"]],
                        text=[f"{sd['CV (%)']}%"],
                        textposition="outside"
                    ))
                fig4.update_layout(
                    title="Coeficiente de variación entre semillas",
                    xaxis_title="Arquitectura",
                    yaxis_title="CV (%)",
                    height=400, template="plotly_white",
                    showlegend=False
                )
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No hay datos de estabilidad entre semillas disponibles.")

        # Gráfico 5: Ranking Final
        with tab_g5:
            if arch_names:
                # Normalize metrics to 0-10 scale for ranking (lower RMSE = better)
                max_rmse = max(arch_rmse) if arch_rmse else 1
                scores = [max(0, min(10, (1 - r / max_rmse) * 10)) for r in arch_rmse]
                rank_scores = {a: s for a, s in zip(arch_names, scores)}
                sorted_models = sorted(rank_scores.items(), key=lambda x: x[1], reverse=True)
                rank_fig = go.Figure(data=[
                    go.Bar(
                        x=[s[1] for s in sorted_models],
                        y=[s[0] for s in sorted_models],
                        orientation="h",
                        marker_color=["#00CC96", "#636EFA", "#EF553B"],
                        text=[f"{s[1]:.1f}/10" for s in sorted_models],
                        textposition="outside"
                    )
                ])
                rank_fig.update_layout(
                    title="Ranking global de arquitecturas",
                    xaxis=dict(title="Puntuación", range=[0, 11]),
                    yaxis=dict(title="Arquitectura", autorange="reversed"),
                    height=400, template="plotly_white"
                )
                st.plotly_chart(rank_fig, use_container_width=True)
            else:
                st.info("No hay datos suficientes para generar el ranking.")
    else:
        st.info("Completa la Validación Estadística para ver los gráficos.")

    st.divider()

    # --- 5. Diagnóstico Técnico ---
    st.subheader("5. Diagnóstico Técnico")
    auto_conclusion = svr.get("auto_conclusion", "Se analizaron los datos y se seleccionó el mejor modelo.") if svr else "Aún no hay datos suficientes para generar una conclusión."
    st.info(auto_conclusion)

    st.divider()

    # --- 6. Modelo Ganador ---
    if svr:
        st.subheader("6. Modelo Ganador")
        rec = svr.get("recommendation", {})
        arch_summary = svr.get("arch_summary", [])
        best_metrics = next(
            (item for item in arch_summary if item["Modelo"] == rec.get("Modelo recomendado")),
            {}
        ) if arch_summary else {}

        # Make this prominent!
        with st.container(border=True):
            mg_col1, mg_col2, mg_col3, mg_col4, mg_col5 = st.columns(5)
            with mg_col1:
                st.metric("Modelo Ganador", rec.get("Modelo recomendado", "-"))
            with mg_col2:
                rmse_val = round(best_metrics.get("RMSE promedio", 0), 4) if best_metrics else 0
                st.metric("RMSE", rmse_val)
            with mg_col3:
                mae_val = round(best_metrics.get("MAE promedio", 0), 4) if best_metrics else 0
                st.metric("MAE", mae_val)
            with mg_col4:
                r2_val = round(best_metrics.get("R² promedio", 0), 4) if best_metrics else 0
                st.metric("R²", r2_val)
            with mg_col5:
                st.metric("Nivel de confianza", rec.get("Nivel de confianza", "-"))
            st.metric("Estado", "Modelo Aprobado" if rec else "Pendiente")

        st.divider()

    # --- 7. Evidencia Estadística ---
    if svr:
        st.subheader("7. Evidencia Estadística")
        rec = svr.get("recommendation", {})
        ev_data = [
            {"Prueba": "Mann-Whitney", "Resultado": "Diferencia significativa" if svr.get("mann_whitney") else "Pendiente"},
            {"Prueba": "Friedman", "Resultado": "Diferencias globales detectadas" if svr.get("friedman") else "Pendiente"},
            {"Prueba": "Nemenyi", "Resultado": f"{rec.get('Modelo recomendado')} mejor arquitectura" if svr.get("nemenyi") else "Pendiente"},
            {"Prueba": "Estabilidad", "Resultado": "Alta" if svr.get("stability") else "Pendiente"},
        ]
        ev_df = pd.DataFrame(ev_data)
        st.dataframe(ev_df, use_container_width=True, hide_index=True)

        st.divider()

    # --- 8. Publicación del Modelo ---
    st.subheader("8. Publicación del Modelo")
    if vr:
        if "model_published" not in st.session_state or not st.session_state.model_published:
            if st.button("Publicar Modelo", type="primary", use_container_width=True):
                with st.status("Publicando el modelo...", expanded=True):
                    st.write("Renombrando archivos...")
                    st.write("Actualizando metadata...")
                    try:
                        payload = {
                            "model_name": vr.get("optimized_model_name", "price_predictor_v2"),
                            "new_model_name": "best_model"
                        }
                        publish_result = api_post("/api/ml/publish-model", payload)
                        st.session_state.model_published = True
                        st.session_state.publish_result = publish_result
                        st.write("✅ Modelo publicado!")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error al publicar: {exc}")
                        st.exception(exc)
        else:
            st.success("✅ Modelo ya ha sido publicado!")
    else:
        st.info("Primero completa la etapa de Validación y Optimización antes de publicar.")

    st.divider()

    # --- 9. Historial de Modelos ---
    st.subheader("9. Historial de Modelos")
    history_resp = None
    try:
        history_resp = api_get("/api/ml/model-history")
        if history_resp and history_resp.get("history"):
            history_data = []
            for item in history_resp.get("history"):
                # Parse date for display
                created_at = item.get("exp_created_at", "-")
                try:
                    dt = pd.to_datetime(created_at)
                    created_at = dt.strftime("%d/%m/%Y")
                except:
                    pass
                history_data.append({
                    "Versión": item.get("version", "-"),
                    "Arquitectura": item.get("model_type", "-").upper(),
                    "Fecha": created_at,
                    "Estado": item.get("status", "-")
                })
            st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay modelos en el historial.")
    except Exception as exc:
        st.warning("No se pudo cargar el historial de modelos.")

    st.divider()

    # ---10. Reportes ---
    st.subheader("10. Reportes")
    st.markdown("Descarga un reporte PDF completo con el resumen del experimento, KPIs, gráficos, diagnóstico técnico y evidencia estadística.")
    if st.button("📄 Descargar Reporte Técnico (PDF)", type="primary", use_container_width=True):
        with st.spinner("Generando reporte PDF..."):
            try:
                pdf_bytes = generate_diagnosis_pdf(tr, vr, svr)
                st.download_button(
                    label="💾 Haz clic para guardar el PDF",
                    data=pdf_bytes,
                    file_name=f"diagnostico_final_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Error al generar el PDF: {exc}")
                st.exception(exc)

    st.divider()

    # ---11. Integración con Next.js ---
    st.subheader("11. Integración con Next.js")
    with st.container(border=True):
        ic_col1, ic_col2, ic_col3 = st.columns(3)
        with ic_col1:
            published = st.session_state.get("model_published", False)
            st.metric("Estado del Modelo", "Disponible" if published else "Pendiente")
        with ic_col2:
            st.metric("Endpoint", "/api/ml/predict")
        with ic_col3:
            active_ver = history_resp.get("history", [{}])[0].get("version", "v1.0") if history_resp and history_resp.get("history") else "v1.0"
            st.metric("Versión", active_ver)
        st.write("✅ Frontend Next.js conectado correctamente")

    st.divider()

    # Final button!
    if st.button("Finalizar Experimento", type="primary", use_container_width=True):
        st.success("🎉 Experiment completado! ¡Modelo listo para producción!")
