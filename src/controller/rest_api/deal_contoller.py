from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from service.deal_service import DealService

# --- Pydantic Models ---

class DealBase(BaseModel):
    user1_id: str
    user2_id: str
    user1_item_id: str
    user2_item_id: str
    cash_difference: float = 0.0
    payer_id: Optional[str] = None
    status: str = "pending"

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    status: Optional[str] = None
    cash_difference: Optional[float] = None
    payer_id: Optional[str] = None

class DealResponse(DealBase):
    id: str
    created_at: str


def create_deal_routes() -> APIRouter:
    router = APIRouter(prefix="/deals", tags=["Deals"])
    deal_service = DealService()

    @router.post("/", response_model=DealResponse, status_code=201)
    def create_deal(deal: DealCreate):
        """Create a new deal."""
        try:
            return deal_service.create_deal(deal.model_dump())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{deal_id}", response_model=DealResponse)
    def get_deal(deal_id: str):
        """Fetch a specific deal by ID."""
        try:
            return deal_service.get_deal(deal_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/user/{user_id}", response_model=List[DealResponse])
    def get_user_deals(user_id: str):
        """Fetch all deals involving a specific user."""
        try:
            return deal_service.get_user_deals(user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.patch("/{deal_id}", response_model=DealResponse)
    def update_deal(deal_id: str, deal_update: DealUpdate):
        """Update a deal."""
        try:
            update_data = deal_update.model_dump(exclude_unset=True)
            return deal_service.update_deal(deal_id, update_data)
        except ValueError as e:
            if "not found" in str(e).lower() or "no valid fields" in str(e).lower():
                raise HTTPException(status_code=400, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/{deal_id}", status_code=204)
    def delete_deal(deal_id: str):
        """Delete a deal."""
        try:
            deal_service.delete_deal(deal_id)
            return None
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router