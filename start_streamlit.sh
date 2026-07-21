#!/bin/bash
# Script de inicio para Streamlit en Render
# Fuerza la extracción correcta de los archivos frontend de Streamlit

set -e

echo "=== Iniciando Streamlit Lab ==="

# Limpiar caché de Streamlit para evitar archivos estáticos obsoletos
echo "Limpiando caché de Streamlit..."
streamlit cache clear 2>/dev/null || true

# Forzar a Streamlit a extraer sus archivos frontend ejecutando un comando breve
echo "Extrayendo archivos frontend..."
timeout 5 streamlit hello 2>/dev/null || true

# Esperar un momento para que los archivos se escriban
sleep 1

# Iniciar la aplicación real
echo "Iniciando aplicación..."
exec streamlit run streamlit_app.py \
  --server.port "$PORT" \
  --server.address "0.0.0.0" \
  --server.headless=true \
  --server.enableStaticServing=true \
  --server.enableCORS=false \
  --server.fileWatcherType=none \
  --global.developmentMode=false \
  --browser.gatherUsageStats=false \
  --theme.base="light"
