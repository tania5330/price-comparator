from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import get_favorites, add_favorite, remove_favorite

router = APIRouter()


class FavoritePayload(BaseModel):
    product_id: str
    product_data: dict


@router.get("/favorites")
async def list_favorites():
    return get_favorites()


@router.post("/favorites")
async def create_favorite(payload: FavoritePayload):
    return add_favorite(payload.product_id, payload.product_data)


@router.delete("/favorites/{product_id}")
async def delete_favorite(product_id: str):
    remove_favorite(product_id)
    return {"ok": True}
