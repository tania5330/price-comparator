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


@router.get("/products/{product_id}")
async def get_product_by_id(product_id: str):
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/products/{product_id}/prices")
async def get_product_prices(product_id: str):
    return get_price_history(product_id)
