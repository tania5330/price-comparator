import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import init_db, count_favorites, count_alerts, get_price_history
from .routes.search import router as search_router
from .routes.products import router as products_router
from .routes.favorites import router as favorites_router
from .routes.alerts import router as alerts_router
from .routes.ai import router as ai_router
from .routes.demo import router as demo_router
from .routes.ml import router as ml_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("Database initialized")
    yield

app = FastAPI(title="Price Comparator API", version="1.0.0", lifespan=lifespan)

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "https://price-comparator.onrender.com",
    "https://price-comparator-ml-lab.onrender.com",
]
extra_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# CORS - allow the Vite dev server and Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins + extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router, prefix="/api", tags=["Search"])
app.include_router(products_router, prefix="/api", tags=["Products"])
app.include_router(favorites_router, prefix="/api", tags=["Favorites"])
app.include_router(alerts_router, prefix="/api", tags=["Alerts"])
app.include_router(ai_router, prefix="/api", tags=["AI"])
app.include_router(demo_router, prefix="/api", tags=["Demo"])
app.include_router(ml_router, prefix="/api", tags=["ML"])


@app.get("/api/stats")
async def get_stats():
    fav_count = count_favorites()
    total_alerts, active_alerts = count_alerts()
    return {
        "favorites": fav_count,
        "alerts": total_alerts,
        "activeAlerts": active_alerts,
    }


@app.get("/api/price-history/{product_id}")
async def price_history(product_id: str):
    return get_price_history(product_id)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
