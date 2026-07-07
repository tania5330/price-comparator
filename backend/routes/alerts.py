from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import (
    get_alerts,
    add_alert,
    update_alert,
    delete_alert,
    search_products_db,
)

router = APIRouter()


class AlertPayload(BaseModel):
    product_id: str
    product_name: str
    target_price: float
    condition: str = "below"
    current_price: float = 0
    is_active: bool = True


class AlertUpdatePayload(BaseModel):
    is_active: bool | None = None
    target_price: float | None = None
    condition: str | None = None


@router.get("/alerts")
async def list_alerts():
    return get_alerts()


@router.post("/alerts")
async def create_alert(payload: AlertPayload):
    return add_alert(payload.model_dump())


@router.patch("/alerts/{alert_id}")
async def patch_alert(alert_id: int, payload: AlertUpdatePayload):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = update_alert(alert_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result


@router.delete("/alerts/{alert_id}")
async def remove_alert(alert_id: int):
    delete_alert(alert_id)
    return {"ok": True}


@router.get("/alerts/search-products")
async def search_products_for_alerts(q: str = ""):
    if len(q) < 2:
        return []
    return search_products_db(q)
