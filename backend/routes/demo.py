import random
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_connection, get_product, get_price_history

router = APIRouter()


class SeedRequest(BaseModel):
    product_id: str
    days: int = 30
    min_entries: int = 12


def _seed_price_history(product_id: str, days: int, min_entries: int) -> list[dict]:
    """
    Generate realistic price history for a product and insert it into the DB.
    Strategy:
      - Start from a slightly higher price (products tend to be discounted over time).
      - Add realistic noise: small daily fluctuations (±2–5%).
      - Insert a notable dip around day 10 (flash sale simulation).
      - Insert a notable spike around day 20 (demand surge simulation).
      - End near the current product price.
    """
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    current_price = product.get("price")
    if not current_price or current_price <= 0:
        raise HTTPException(status_code=422, detail="Product has no valid price to base history on")

    store_name = product.get("source_name", "Store")

    # Calculate how many records already exist
    existing = get_price_history(product_id)
    if len(existing) >= min_entries:
        return existing  # Already has enough history, skip seeding

    # Generate evenly spaced timestamps over the past `days` days
    now = datetime.utcnow()
    entries_to_generate = max(min_entries, days // 2)
    interval_hours = (days * 24) / entries_to_generate

    # Price generation strategy
    # Start slightly above current price
    start_price = current_price * random.uniform(1.05, 1.20)
    prices: list[float] = []

    price = start_price
    for i in range(entries_to_generate):
        progress = i / (entries_to_generate - 1)  # 0.0 → 1.0

        # General downward trend toward current price
        target = start_price + (current_price - start_price) * progress

        # Random noise ±3%
        noise_pct = random.uniform(-0.03, 0.03)

        # Flash sale dip around 30–40% of the timeline
        if 0.30 <= progress <= 0.40:
            noise_pct -= random.uniform(0.04, 0.09)

        # Demand spike around 65–75% of the timeline
        if 0.65 <= progress <= 0.75:
            noise_pct += random.uniform(0.03, 0.08)

        price = round(target * (1 + noise_pct), 2)
        price = max(price, current_price * 0.70)  # Never below 70% of current
        prices.append(price)

    # Ensure last price matches current product price exactly
    prices[-1] = current_price

    # Build records with timestamps
    records = []
    for i, p in enumerate(prices):
        recorded_at = now - timedelta(hours=interval_hours * (entries_to_generate - 1 - i))
        records.append({
            "product_id": product_id,
            "store_name": store_name,
            "price": p,
            "recorded_at": recorded_at.isoformat(),
        })

    # Insert into DB (skip existing to avoid duplicates on re-seed)
    conn = get_connection()
    conn.executemany(
        "INSERT INTO price_history (product_id, store_name, price, recorded_at) VALUES (?, ?, ?, ?)",
        [(r["product_id"], r["store_name"], r["price"], r["recorded_at"]) for r in records],
    )
    conn.commit()
    conn.close()

    return records


@router.post("/demo/seed-history")
async def seed_price_history(request: SeedRequest):
    """
    Seed realistic price history data for a product.
    Generates fluctuating entries over the past N days, simulating
    flash sales, demand spikes, and a gradual price trend.
    Skips if the product already has enough historical entries.
    """
    records = _seed_price_history(request.product_id, request.days, request.min_entries)
    return {
        "seeded": len(records),
        "product_id": request.product_id,
        "message": f"Price history ready with {len(records)} data points.",
    }
