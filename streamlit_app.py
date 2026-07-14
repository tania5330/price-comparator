import streamlit as st
import httpx
import os
import pandas as pd
from datetime import datetime

# Configuración de la API
FASTAPI_URL = "http://localhost:8000"

# Título de la app
st.set_page_config(page_title="Price Comparator - Streamlit", page_icon="💰")

st.title("💰 Comparador de Precios - Streamlit")

# Sidebar
st.sidebar.header("Opciones")

# Pestañas principales
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Búsqueda", "⭐ Favoritos", "🔔 Alertas", "🤖 AI Assistant", "📊 Predicción de Precios"])


# --- Pestaña 1: Búsqueda de productos
with tab1:
    st.header("Buscar productos")
    
    query = st.text_input("Nombre del producto")
    location = st.text_input("Ubicación (opcional)", placeholder="USA")

    if st.button("Buscar") and query:
        with st.spinner("Buscando productos..."):
            try:
                response = httpx.post(
                    f"{FASTAPI_URL}/api/search",
                    json={"query": query, "location": location}
                )
                results = response.json()

                if results:
                    st.subheader("Resultados de la búsqueda")
                    for product in results:
                        with st.container():
                            col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            if product.get("image"):
                                st.image(product["image"], width=150)
                            else:
                                st.markdown("📦")

                        with col2:
                            st.write(f"**{product.get('name', 'N/A')}**")
                            st.write(f"Precio: ${product.get('price', 'N/A')}")
                            st.write(f"Fuente: {product.get('source_name', 'N/A')}")
                            if product.get('old_price'):
                                st.write(f"Precio anterior: ~~${product['old_price']}~~")
                            if st.button(f"Ver detalles de {product.get('name')[:20]}...", key=f"view_{product.get('id')}"):
                                st.write(product)

            except Exception as e:
                st.error(f"Error al buscar productos: {str(e)}")


# --- Pestaña 2: Favoritos
with tab2:
    st.header("Tus productos favoritos")
    if st.button("Recargar favoritos"):
        try:
            response = httpx.get(f"{FASTAPI_URL}/api/favorites")
            favorites = response.json()
            if favorites:
                for fav in favorites:
                    st.subheader(fav.get("product_name", "N/A"))
                    st.write(f"ID: {fav.get('product_id')}")
                    st.write(f"Precio actual: ${fav.get('current_price', 'N/A')}")
            else:
                st.info("No tienes productos favoritos aún!")
        except Exception as e:
            st.error(f"Error al cargar favoritos: {str(e)}")


# --- Pestaña 3: Alertas
with tab3:
    st.header("Alertas de precio")

    # Crear nueva alerta
    st.subheader("Crear nueva alerta")
    with st.form("alert_form"):
        product_name = st.text_input("Nombre del producto")
        target_price = st.number_input("Precio objetivo", min_value=0.0, step=0.01)
        condition = st.selectbox("Condición", ["below", "above", "equals"])
        submit_alert = st.form_submit_button("Crear alerta")

    if submit_alert:
        try:
            response = httpx.post(
                f"{FASTAPI_URL}/api/alerts",
                json={
                    "product_name": product_name,
                    "target_price": target_price,
                    "condition": condition,
                    "is_active": True,
                    "current_price": 0
                }
            )
            if response.status_code == 200:
                st.success("Alerta creada exitosamente!")
            else:
                st.error(f"Error al crear alerta")
        except Exception as e:
            st.error(f"Error al crear alerta: {str(e)}")

    # Ver alertas existentes
    if st.button("Recargar alertas"):
        try:
            response = httpx.get(f"{FASTAPI_URL}/api/alerts")
            alerts = response.json()
            if alerts:
                for alert in alerts:
                    with st.expander(f"Alerta para {alert.get('product_name')}"):
                        st.write(f"Precio objetivo: ${alert.get('target_price')}")
                        st.write(f"Condición: {alert.get('condition')}")
                        st.write(f"Estado: {'Activa' if alert.get('is_active') else 'Pausada'}")
            else:
                st.info("No tienes alertas configuradas!")
        except Exception as e:
            st.error(f"Error al cargar alertas: {str(e)}")


# --- Pestaña 4: AI Assistant
with tab4:
    st.header("Asistente de compras AI")
    user_input = st.text_area("Pregunta lo que quieras sobre productos o precios")
    if st.button("Enviar"):
        with st.spinner("Pensando..."):
            try:
                response = httpx.post(
                    f"{FASTAPI_URL}/api/ai/chat",
                    json={"message": user_input}
                )
                ai_response = response.json()
                st.write(f"🤖: {ai_response.get('response', 'No hay respuesta disponible')}")
            except Exception as e:
            st.error(f"Error al comunicarse con el AI: {str(e)}")


# --- Pestaña 5: Predicción de Precios (ML)
with tab5:
    st.header("🤖 Predicción de Precios con Machine Learning")
    
    st.markdown("""
        Esta herramienta usa un modelo de ML para predecir precios futuros basados en datos históricos sintéticos.
    """)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Entrenar modelo")
        base_price = st.number_input("Precio base del producto", min_value=1, value=100, step=1)
        days = st.slider("Días de datos históricos", min_value=30, max_value=365, value=180)
        product_name = st.text_input("Nombre del producto", value="Producto X")
        model_name = st.text_input("Nombre del modelo", value="price_predictor")
        
        if st.button("Entrenar modelo"):
            with st.spinner("Entrenando modelo..."):
                try:
                    response = httpx.post(
                        f"{FASTAPI_URL}/api/ml/train",
                        json={
                            "base_price": base_price,
                            "days": days,
                            "product_name": product_name,
                            "model_name": model_name
                        }
                    )
                    result = response.json()
                    st.success(f"✅ Modelo entrenado exitosamente!")
                    st.metric("MAE", f"${result['metrics']['mae']:.2f}")
                    st.metric("RMSE", f"${result['metrics']['rmse']:.2f}")
                    st.metric("R²", f"{result['metrics']['r2']:.2f}")
                except Exception as e:
                    st.error(f"Error al entrenar el modelo: {str(e)}")

    with col2:
        st.subheader("Predecir precios")
        pred_model_name = st.text_input("Nombre del modelo para predicción", value="price_predictor")
        days_ahead = st.slider("Días a predecir", min_value=1, max_value=30, value=7)
        if st.button("Predecir"):
            with st.spinner("Realizando predicciones..."):
                try:
                    response = httpx.post(
                        f"{FASTAPI_URL}/api/ml/predict",
                        json={
                            "model_name": pred_model_name,
                            "days_ahead": days_ahead
                        }
                    )
                    result = response.json()
                    st.success("✅ Predicciones generadas!")
                    
                    # Mostrar tabla de predicciones
                    predictions = result['predictions']
                    
                    # Convertir a DataFrame para el gráfico
                    df_pred = pd.DataFrame(predictions)
                    df_pred['date'] = pd.to_datetime(df_pred['date'])
                    
                    st.line_chart(data=df_pred, x='date', y='predicted_price')
                    st.subheader("Predicciones detalladas")
                    st.write(predictions)
                    
                except Exception as e:
                    st.error(f"Error al realizar la predicción: {str(e)}")

    st.divider()
    st.subheader("Modelos guardados")
    if st.button("Ver modelos"):
        try:
            response = httpx.get(f"{FASTAPI_URL}/api/ml/models")
            models = response.json()
            if models['models']:
                st.write("Modelos disponibles:")
                for model in models['models']:
                    st.write(f"- {model}")
            else:
                st.info("No hay modelos guardados aún.")
        except Exception as e:
            st.error(f"Error al listar modelos: {str(e)}")


# --- Ver estadísticas
st.sidebar.subheader("Estadísticas generales")
if st.sidebar.button("Cargar estadísticas"):
    try:
        response = httpx.get(f"{FASTAPI_URL}/api/stats")
        stats = response.json()
        st.sidebar.metric("Productos favoritos", stats.get('favorites', 0))
        st.sidebar.metric("Total de alertas", stats.get('alerts', 0))
        st.sidebar.metric("Alertas activas", stats.get('activeAlerts', 0))
    except Exception as e:
        st.sidebar.error(f"Error al cargar estadísticas: {str(e)}")

