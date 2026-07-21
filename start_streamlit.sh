#!/bin/bash
# Script de inicio para Streamlit en Render

set -e

echo "=== Iniciando Streamlit Lab ==="

# Iniciar la aplicación real
exec streamlit run streamlit_app.py \
  --server.port "$PORT" \
  --server.address "0.0.0.0" \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false \
  --server.fileWatcherType=none \
  --global.developmentMode=false \
  --browser.gatherUsageStats=false \
  --theme.base="light"
