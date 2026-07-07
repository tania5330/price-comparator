from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..scraper import scrape_google_shopping
from ..database import save_products, save_search

router = APIRouter()


class SearchPayload(BaseModel):
    query: str
    location: str = "United States"


@router.post("/search")
async def search_products(payload: SearchPayload):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    results = await scrape_google_shopping(payload.query, payload.location)

    # Persist products and search history
    if results:
        save_products(results)
    save_search(payload.query, len(results))

    return results
