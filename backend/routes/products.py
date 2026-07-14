from fastapi import APIRouter, HTTPException
from ..database import get_product, get_products, get_price_history

router = APIRouter()


@router.get("/products")
async def list_products(
    category: str | None = None,
    brand: str | None = None,
    minPrice: float | None = None,
    maxPrice: float | None = None,
):
    filters = {}
    if category:
        filters["category"] = category
    if brand:
        filters["brand"] = brand
    if minPrice is not None:
        filters["minPrice"] = minPrice
    if maxPrice is not None:
        filters["maxPrice"] = maxPrice

    return get_products(filters if filters else None)


@router.get("/products/opportunities")
async def get_opportunities():
    # Fetch last 100 products from DB
    products = get_products()
    opportunities = []

    for p in products:
        p_id = p.get("id")
        current_price = p.get("price")
        if not p_id or not current_price or current_price <= 0:
            continue

        history = get_price_history(p_id)
        prices = [h["price"] for h in history if h.get("price")]
        if len(prices) < 2:  # Needs at least a couple history entries to be considered
            continue

        avg_price = sum(prices) / len(prices)
        if current_price < avg_price:
            saving_pct = round(((avg_price - current_price) / avg_price) * 100, 1)
            # Only consider meaningful savings (> 1%)
            if saving_pct > 1.0:
                opportunities.append({
                    "id": p.get("id"),
                    "name": p.get("canonical_name") or p.get("name"),
                    "image": p.get("image"),
                    "price": current_price,
                    "old_price": p.get("old_price"),
                    "source_name": p.get("source_name"),
                    "rating": p.get("rating"),
                    "reviews_count": p.get("reviews_count"),
                    "product_link": p.get("product_link"),
                    "saving_pct": saving_pct,
                    "avg_price": round(avg_price, 2),
                    "min_price": round(min(prices), 2)
                })

    # Sort by saving percentage descending
    opportunities.sort(key=lambda x: x["saving_pct"], reverse=True)
    return opportunities[:4]


@router.get("/products/{product_id}")
async def get_product_by_id(product_id: str):
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product



@router.get("/products/{product_id}/prices")
async def get_product_prices(product_id: str):
    return get_price_history(product_id)
