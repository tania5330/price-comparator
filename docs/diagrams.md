# Diagramas del Sistema — Price Comparator ML Lab

---

## 1. Diagrama de Arquitectura (C4 — Nivel Contenedor)

```mermaid
C4Context
  title Arquitectura del Sistema — Price Comparator ML Lab

  Person(user, "Usuario", "Comprador que busca productos y compara precios")
  Person(data_scientist, "Científico de Datos", "Entrena y evalúa modelos de predicción")

  System_Boundary(system, "Price Comparator") {
    Container(react, "Frontend React", "Vite + React + TypeScript", "Interfaz de usuario para búsqueda, comparación y predicción de precios")
    Container(streamlit, "Streamlit Lab", "Python + Streamlit", "Laboratorio interactivo de ML: EDA, entrenamiento, validación y diagnóstico")
    Container(fastapi, "Backend FastAPI", "Python + FastAPI", "API REST: scraping, ML, IA, gestión de datos")
    ContainerDb(sqlite, "Base de Datos", "SQLite / PostgreSQL", "Productos, favoritos, alertas, experimentos, modelos")
    Container(ml_artifacts, "ML Artifacts", "Sistema de archivos", "Modelos .h5, scalers, métricas, reportes PDF/HTML")
  }

  System_Ext(openai, "OpenAI API", "GPT-4o-mini para asesor de compras y chat")
  System_Ext(dummyjson, "DummyJSON API", "Fuente de productos externa")
  System_Ext(fakestore, "FakeStore API", "Fuente de productos externa")
  System_Ext(google, "Google Shopping", "Scraping de precios")
  System_Ext(duckduckgo, "DuckDuckGo", "Scraping de productos")
  System_Ext(telegram, "Telegram API", "Notificaciones de alertas")

  Rel(user, react, "Busca, compara, analiza")
  Rel(user, streamlit, "Entrena, valida, diagnostica")
  Rel(data_scientist, streamlit, "Ejecuta experimentos ML")
  Rel(react, fastapi, "HTTP /api/*", "JSON")
  Rel(streamlit, fastapi, "HTTP /api/ml/*", "JSON")
  Rel(fastapi, sqlite, "CRUD", "SQL")
  Rel(fastapi, ml_artifacts, "Guarda/carga modelos", "H5/JSON/CSV")
  Rel(fastapi, openai, "HTTP POST", "JSON")
  Rel(fastapi, dummyjson, "HTTP GET", "Scraping")
  Rel(fastapi, fakestore, "HTTP GET", "Scraping")
  Rel(fastapi, google, "HTTP GET", "Scraping HTML")
  Rel(fastapi, duckduckgo, "HTTP GET", "Scraping HTML")
  Rel(fastapi, telegram, "HTTP POST", "Notificaciones")
  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

---

## 2. Diagrama de Componentes

```mermaid
graph TB
  subgraph Frontend["Frontend React (Vite + TS)"]
    App["App.tsx<br/>Router principal"]
    Sidebar["Sidebar<br/>Navegación"]
    Header["Header<br/>Búsqueda + Tema"]

    subgraph Views["Vistas"]
      DV["Dashboard<br/>Estadísticas"]
      SR["SearchResults<br/>Resultados búsqueda"]
      PC["ProductComparison<br/>Comparativa"]
      FV["Favorites<br/>Favoritos"]
      AV["Alerts<br/>Alertas"]
      AA["AIAssistant<br/>Chat con GPT"]
      MLP["MLPricePredictor<br/>Predicción precios"]
    end

    subgraph Components["Componentes"]
      ProductCard["ProductCard"]
      ProductModal["ProductModal"]
      PriceHistoryChart["PriceHistoryChart"]
      PriceComparisonTable["PriceComparisonTable"]
      AIPurchaseAdvisor["AIPurchaseAdvisor"]
      SearchFilters["SearchFilters"]
      Badge["Badge"]
      LoadingSpinner["LoadingSpinner"]
    end

    subgraph Context["Context Providers"]
      SearchCtx["SearchContext"]
      FavoritesCtx["FavoritesContext"]
      ThemeCtx["ThemeContext"]
      I18nCtx["I18nContext"]
    end

    API["ApiService<br/>src/services/api.ts"]
    AIFloatingChat["AIFloatingChat<br/>Chat persistente"]
  end

  subgraph StreamlitLab["Streamlit Lab"]
    StApp["streamlit_app.py<br/>6 pestañas"]
    Tab1["1. Dataset & EDA"]
    Tab2["2. Entrenamiento"]
    Tab3["3. Validación y Optimización"]
    Tab4["4. Validación Estadística"]
    Tab5["5. Diagnóstico Final"]
    Tab6["6. Predicción"]
  end

  subgraph Backend["Backend FastAPI"]
    Main["main.py<br/>App + CORS + Routers"]

    subgraph Routes["Routers /api/*"]
      RSearch["search.py<br/>Scraping multi-fuente"]
      RProducts["products.py<br/>CRUD productos"]
      RFavorites["favorites.py<br/>Favoritos"]
      RAlerts["alerts.py<br/>Alertas"]
      RAi["ai.py<br/>OpenAI asesor"]
      RDemo["demo.py<br/>Seed sintético"]
      RMl["ml.py<br/>ML Pipeline Endpoints"]
    end

    subgraph ML["Módulo ML"]
      MLModel["ml_model.py<br/>~1657 líneas"]
      Stats["statistical_tests.py<br/>Tests estadísticos"]
      Preproc["preprocessing.py<br/>Feature engineering"]
    end

    DB["database.py<br/>SQLite/PostgreSQL"]
    Scraper["scraper.py<br/>4 fuentes paralelas"]
  end

  App --> Sidebar
  App --> Header
  App --> Views
  Views --> Components
  App --> Context
  Views --> API
  MLP --> API

  StApp --> Tab1 & Tab2 & Tab3 & Tab4 & Tab5 & Tab6
  Tab2 --> RMl
  Tab3 --> RMl
  Tab4 --> RMl
  Tab5 --> RMl
  Tab6 --> RMl

  RMl --> MLModel
  MLModel --> Stats
  MLModel --> Preproc
  Main --> Routes
  Main --> DB
  Main --> Scraper
```

---

## 3. Modelo de Datos (ER)

```mermaid
erDiagram
  products ||--o{ favorites : has
  products ||--o{ price_history : "price history"
  products ||--o{ alerts : "price alerts"
  experiments ||--|| best_models : "best model"

  products {
    string id PK "MD5(name+source)"
    string name "Nombre del producto"
    string canonical_name "Nombre normalizado"
    string image "URL imagen"
    string description "Descripción"
    string category "Categoría"
    string brand "Marca"
    string product_link "URL producto"
    string source_name "Tienda/fuente"
    float price "Precio actual"
    float old_price "Precio anterior"
    string currency "Moneda"
    float rating "Calificación"
    int reviews_count "Reseñas"
    string delivery "Info envío"
    datetime created_at "Fecha creación"
    string raw "JSON datos crudos"
  }

  favorites {
    int id PK "Autoincremental"
    string product_id FK "products.id"
    string product_data "JSON producto"
    datetime created_at "Fecha creación"
  }

  alerts {
    int id PK "Autoincremental"
    string product_id FK "products.id"
    string product_name "Nombre producto"
    float target_price "Precio objetivo"
    string condition "below|above|equals"
    float current_price "Precio actual"
    int is_active "0/1"
    datetime created_at "Fecha creación"
  }

  price_history {
    int id PK "Autoincremental"
    string product_id FK "products.id"
    string store_name "Nombre tienda"
    float price "Precio registrado"
    datetime recorded_at "Timestamp"
  }

  experiments {
    string id PK "UUID"
    datetime created_at "Fecha creación"
    string dataset_name "Nombre dataset"
    string model_type "GRU|LSTM|MLP"
    int random_seed "Semilla aleatoria"
    string hyperparameters "JSON"
    float rmse "RMSE"
    float mae "MAE"
    float mape "MAPE"
    float r2 "R²"
    float loss "Pérdida final"
    float training_time "Tiempo entrenamiento"
    string model_path "Ruta .h5"
    string scaler_path "Ruta scaler"
    string metadata_path "Ruta metadata"
    string report_html_path "Ruta reporte HTML"
    string report_pdf_path "Ruta reporte PDF"
    int is_best "0/1 flag"
  }

  best_models {
    int id PK "Autoincremental"
    string experiment_id FK "experiments.id"
    datetime created_at "Fecha creación"
    string model_name "Nombre modelo"
    string model_type "GRU|LSTM|MLP"
    float rmse "RMSE"
    float mae "MAE"
    float mape "MAPE"
    float r2 "R²"
    string validation_status "pending|approved"
  }

  search_history {
    int id PK "Autoincremental"
    string search_query "Consulta"
    int result_count "N° resultados"
    datetime created_at "Fecha creación"
  }
```

---

## 4. Diagrama de Secuencia — Entrenamiento de Modelo ML

```mermaid
sequenceDiagram
  actor DS as Científico de Datos
  participant St as Streamlit Lab<br/>(Pestaña 2)
  participant API as Backend API<br/>POST /api/ml/train
  participant ML as ML Engine<br/>ml_model.py
  participant Stats as statistical_tests.py
  participant FS as Sistema Archivos
  participant DB as Base de Datos

  DS->>St: 1. Configura hiperparámetros
  DS->>St: 2. Hace clic en "Entrenar Modelo"

  St->>API: POST /api/ml/train (payload)
  activate API

  API->>API: _workload_guard() — lock
  API->>API: _apply_training_profile()
  API->>API: _build_training_frame()

  alt dataset_records proporcionado
    API->>API: DataFrame directo
  else product_id proporcionado
    API->>DB: get_product(product_id)
    API->>DB: get_price_history(product_id)
    DB-->>API: datos del producto + historial
    API->>ML: history_to_dataframe()
  else sintético
    API->>ML: generate_historical_prices()
  end

  ML-->>API: DataFrame normalizado
  API->>ML: normalize_price_dataframe()
  API->>ML: compute_eda()
  API->>ML: _make_supervised()

  API->>ML: _evaluate_linear_baseline()
  ML-->>API: baseline metrics

  API->>ML: _candidate_grid(model_types, params)
  ML-->>API: lista de candidatos

  loop por cada candidato
    API->>ML: _cross_validate_candidate()
    activate ML
    ML->>ML: TimeSeriesSplit K-Folds
    loop por cada fold
      ML->>ML: _scale_fold_data()
      ML->>ML: _build_neural_model()
      ML->>ML: model.fit()
      ML->>ML: model.predict()
    end
    ML-->>API: fold_metrics + mean_rmse
    deactivate ML
  end

  API->>API: Selecciona best_candidate (min RMSE)

  loop por cada arquitectura (GRU, LSTM, MLP)
    API->>ML: _train_architecture_multiple_runs()
    ML->>ML: N runs con distintas seeds
    ML-->>API: architecture_results
  end

  API->>Stats: stability_analysis()
  API->>Stats: mann_whitney_test()
  API->>Stats: kolmogorov_smirnov_test()

  alt >= 3 modelos
    API->>Stats: friedman_test()
    alt p < 0.05
      API->>Stats: nemenyi_posthoc_test()
    end
  end

  API->>ML: Entrena modelo final (full data)
  API->>FS: Guarda .h5 + scalers + metadata
  API->>FS: Escribe reportes (.md, .html, .pdf)

  API->>DB: save_experiment()

  API-->>St: Resultado completo
  deactivate API

  St-->>DS: Muestra métricas, gráficos y tests
```

---

## 5. Diagrama de Secuencia — Predicción de Precios

```mermaid
sequenceDiagram
  actor User as Usuario
  participant FE as Frontend React<br/>MLPricePredictor
  participant API as Backend API<br/>POST /api/ml/predict
  participant FS as Sistema Archivos
  participant DB as Base de Datos

  User->>FE: 1. Ingresa producto y días a predecir
  User->>FE: 2. Hace clic en "Predecir"

  FE->>API: POST /api/ml/predict (model_name, product_id, days_ahead)
  activate API

  API->>FS: load_neural_artifacts(model_name)
  FS-->>API: model.h5 + scalers + metadata

  alt product_id proporcionado
    API->>DB: get_price_history(product_id)
    DB-->>API: price_history[]
    API->>API: history_to_dataframe()
  else sintético
    API->>API: generate_historical_prices()
  end

  API->>API: normalize_price_dataframe()
  API->>API: add_time_features()

  API->>API: feature_scaler.transform(X)
  API->>API: Tomar última secuencia (sequence_length)

  loop days_ahead veces
    API->>API: model.predict(sequence)
    API->>API: inverse_target(price)
    API->>API: Calcular intervalo confianza (±1.96 × residual_std)
    API->>API: Construir next_row con precio predicho
    API->>API: Shift sequence: [1:] + next_scaled
  end

  API-->>FE: [{date, price, lower, upper, confidence}]
  deactivate API

  FE->>FE: Renderizar gráfico forecast
  FE->>FE: Calcular interpretación automática
  FE-->>User: Muestra gráfico + tabla + interpretación
```

---

## 6. Diagrama de Secuencia — Validación y Optimización

```mermaid
sequenceDiagram
  actor DS as Científico de Datos
  participant St as Streamlit Lab<br/>(Pestaña 3)
  participant API as Backend API<br/>POST /api/ml/validate-and-optimize
  participant ML as ML Engine<br/>ml_model.py
  participant FS as Sistema Archivos

  DS->>St: 1. Configura folds, método de optimización
  DS->>St: 2. Hace clic en "VALIDAR Y OPTIMIZAR MODELO"

  St->>API: POST /api/ml/validate-and-optimize (payload)
  activate API

  API->>API: Construye dataframe
  API->>ML: normalize_price_dataframe()
  API->>ML: compute_eda()
  API->>ML: _make_supervised()

  API->>ML: _cross_validate_candidate(base_candidate)
  activate ML
  ML->>ML: TimeSeriesSplit K-Folds
  loop por cada fold
    ML->>ML: _scale_fold_data()
    ML->>ML: _build_neural_model()
    ML->>ML: model.fit() + EarlyStopping
    ML->>ML: model.predict()
  end
  ML-->>API: fold_metrics + mean_rmse
  deactivate ML

  API->>ML: _evaluate_holdout_candidate(base_candidate)
  ML-->>API: base_holdout_metrics

  Note over API,ML: Grid Search sobre {units, dropout, lr}

  loop por cada combinación de hiperparámetros
    API->>ML: _cross_validate_candidate(candidate)
    ML-->>API: candidate_metrics
  end

  API->>API: Selecciona best_candidate (min mean_rmse)

  opt retrain_automatically = True
    API->>ML: Re-entrena modelo con best params
    ML->>FS: Guarda candidate_model_v2.h5
    ML->>FS: Guarda scalers_v2
    API->>ML: _evaluate_holdout_candidate(best_params)
    ML-->>API: final_holdout_metrics
  end

  API->>API: Calcula CV%, genera interpretaciones
  API->>API: Compara Antes vs Después

  API->>FS: Guarda CSVs + JSON (validation/)

  API-->>St: metrics, best_params, comparison, optimization_history
  deactivate API

  St-->>DS: Muestra tabla CV, gráfico, comparación e interpretación
```

---

## 7. Diagrama de Estados — Ciclo de Vida del Experimento

```mermaid
stateDiagram-v2
  [*] --> DatasetConfig: Usuario selecciona/carga datos

  state DatasetConfig {
    [*] --> Synthetic: Generación sintética
    [*] --> Uploaded: Archivo subido
    [*] --> Database: Historial BD
  }

  DatasetConfig --> EDAAnalysis: Datos listos
  EDAAnalysis --> EDAComplete: EDA ejecutado

  state EDAComplete {
    [*] --> CheckQuality: Validar calidad
    CheckQuality --> ReadyForTraining: Sin inconsistencias críticas
    CheckQuality --> DatasetConfig: Inconsistencias detectadas
  }

  ReadyForTraining --> Training: Usuario inicia entrenamiento

  state Training {
    [*] --> GridSearch: Búsqueda de hiperparámetros
    GridSearch --> CrossValidation: Evaluación candidatos
    CrossValidation --> SelectBestArchitecture: Selección mejor modelo
    SelectBestArchitecture --> StatisticalTests: Pruebas estadísticas
    StatisticalTests --> SaveModel: Guardar artefactos
    SaveModel --> TrainingComplete: Experimento finalizado
  }

  Training --> TrainingComplete: Modelo entrenado + artefactos guardados

  state TrainingComplete {
    [*] --> HasResults: Métricas + gráficos + tests disponibles
  }

  TrainingComplete --> ValidationOptimization: Usuario inicia validación

  state ValidationOptimization {
    [*] --> TimeSeriesSplit: Validación cruzada
    TimeSeriesSplit --> HyperparameterSearch: Optimización grid
    HyperparameterSearch --> Retrain: Reentrenamiento con best params
    Retrain --> CompareBaseline: Comparación Antes vs Después
    CompareBaseline --> OptimizationComplete
  }

  ValidationOptimization --> StatisticalValidation: Usuario inicia validación estadística

  state StatisticalValidation {
    [*] --> ExtractMetrics: Extraer scores por arquitectura
    ExtractMetrics --> RunTests: Ejecutar tests
    state RunTests {
      MannWhitney --> Friedman: Si >= 3 modelos
      Friedman --> Nemenyi: Si p < 0.05
      KolmogorovSmirnov
      StabilityAnalysis
    }
    RunTests --> GenerateConclusion: Conclusión automática
    GenerateConclusion --> Recommendation: Recomendación + confianza
    Recommendation --> StatsComplete
  }

  StatisticalValidation --> Diagnosis: Consolidación de resultados

  state Diagnosis {
    [*] --> CompileResults: Integrar resultados
    CompileResults --> GenerateReport: Generar reporte PDF
    GenerateReport --> ReadyForPublish
  }

  ReadyForPublish --> Published: Usuario pulsa "Publicar Modelo"

  state Published {
    [*] --> CopyArtifacts: Renombrar best_model.h5
    CopyArtifacts --> UpdateDB: save_best_model()
    UpdateDB --> Active: Modelo disponible para predicción
  }

  Active --> [*]: Nuevo experimento comienza
```

---

## 8. Diagrama de Flujo de Datos — Pipeline ML

```mermaid
flowchart LR
  subgraph Input["Entrada de Datos"]
    DS["Dataset histórico<br/>(CSV / BD / Sintético)"]
  end

  subgraph Prep["Preparación"]
    Norm["Normalización<br/>- Interpolación<br/>- Relleno diario"]
    FE["Feature Engineering<br/>- Time features<br/>- Lag features<br/>- Rolling features"]
    Super["Supervisión<br/>Ventanas deslizantes"]
  end

  subgraph Train["Entrenamiento"]
    BL["Baseline<br/>Linear Regression"]
    GS["Grid Search<br/>GRU / LSTM / MLP"]
    CV["Cross-Validation<br/>TimeSeriesSplit"]
    AS["Arquitectura<br/>Multiple runs x seed"]
    TS["Tests Estadísticos<br/>M-W, KS, Friedman..."]
  end

  subgraph Val["Validación"]
    CV2["TimeSeriesSplit<br/>K-Folds"]
    HP["Optimización<br/>Hiperparámetros"]
    RC["Reentrenamiento<br/>Best params"]
    COMP["Comparación<br/>Antes vs Después"]
  end

  subgraph StatVal["Validación Estadística"]
    MW["Mann-Whitney U"]
    KS["Kolmogorov-Smirnov"]
    FR["Friedman"]
    NM["Nemenyi Post-hoc"]
    ST["Stability Analysis"]
  end

  subgraph Output["Salida"]
    MODEL["Modelo .h5"]
    SCALER["Scalers"]
    METRICS["Métricas JSON"]
    REPORTS["Reportes MD/HTML/PDF"]
    BEST["best_model.h5"]
  end

  DS --> Norm --> FE --> Super

  Super --> BL
  Super --> GS
  GS --> CV
  CV --> AS
  AS --> TS
  TS --> MODEL
  MODEL --> SCALER
  MODEL --> METRICS

  MODEL --> CV2
  CV2 --> HP
  HP --> RC
  RC --> COMP

  COMP --> MW
  COMP --> KS
  COMP --> FR
  FR --> NM
  COMP --> ST

  MW --> BEST
  KS --> BEST
  NM --> BEST
  ST --> BEST
  BEST --> REPORTS

  style Input fill:#e1f5fe
  style Prep fill:#fff3e0
  style Train fill:#e8f5e9
  style Val fill:#fce4ec
  style StatVal fill:#f3e5f5
  style Output fill:#e0f7fa
```

---

## 9. Diagrama de Despliegue

```mermaid
graph TB
  subgraph Browser["Navegador Web"]
    ReactApp["Frontend React<br/>Vite + React + TS<br/>Puerto :5173"]
    StreamlitApp["Streamlit Lab<br/>Python Streamlit<br/>Puerto :8501"]
  end

  subgraph Render["Render Cloud"]
    subgraph FrontendService["price-comparator"]
      Nginx["Nginx / Node<br/>Sirve build Vite"]
      ReactBuild["Static Files<br/>dist/"]
    end

    subgraph APIService["price-comparator-api"]
      Uvicorn["Uvicorn<br/>FastAPI<br/>Puerto :8000"]
      ML_Artifacts["ML Artifacts<br/>/opt/render/project/src/backend/ml_models/"]
      Reports["Reports<br/>/opt/render/project/src/backend/reports/"]
    end

    subgraph MLService["price-comparator-ml-lab"]
      StreamlitServer["Streamlit Server<br/>Puerto dinámico"]
    end

    subgraph Database["PostgreSQL 15"]
      PG["price_comparator_db"]
    end
  end

  subgraph ExternalAPIs["APIs Externas"]
    OpenAI["OpenAI API<br/>GPT-4o-mini"]
    DummyJSON["DummyJSON API"]
    FakeStore["FakeStore API"]
    Google["Google Shopping<br/>Scraping"]
    DuckDuckGo["DuckDuckGo<br/>Scraping"]
    Telegram["Telegram API"]
  end

  User1["Usuario Final"] --> ReactApp
  User2["Científico Datos"] --> StreamlitApp
  ReactApp -->|HTTP| Uvicorn
  StreamlitApp -->|HTTP| Uvicorn
  Uvicorn --> PG
  Uvicorn --> ML_Artifacts
  Uvicorn --> Reports
  Uvicorn --> OpenAI
  Uvicorn --> DummyJSON
  Uvicorn --> FakeStore
  Uvicorn --> Google
  Uvicorn --> DuckDuckGo
  Uvicorn --> Telegram

  ReactApp -.->|Desarrollo| Vite["Vite Dev Server<br/>localhost:5173"]
  StreamlitApp -.->|Desarrollo| LocalStreamlit["streamlit run<br/>localhost:8501"]
  Uvicorn -.->|Desarrollo| LocalUvicorn["uvicorn --reload<br/>localhost:8000"]
  LocalUvicorn -.-> SQLite["SQLite<br/>price_comparator.db"]
