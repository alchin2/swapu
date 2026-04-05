from typing import List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from service.deal_service import DealService

# --- Pydantic Models ---

class DealBase(BaseModel):
    user1_id: str
    user2_id: str
    user1_item_id: str
    user2_item_id: str
    cash_difference: float = Field(default=0.0, ge=0)
    payer_id: Optional[str] = None
    status: Literal["pending", "negotiating", "accepted", "declined"] = "pending"

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    status: Optional[Literal["pending", "negotiating", "accepted", "declined"]] = None
    cash_difference: Optional[float] = Field(default=None, ge=0)
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
        return deal_service.create_deal(deal.model_dump())

    @router.get("/{deal_id}", response_model=DealResponse)
    def get_deal(deal_id: str):
        """Fetch a specific deal by ID."""
        return deal_service.get_deal(deal_id)

    @router.get("/user/{user_id}", response_model=List[DealResponse])
    def get_user_deals(user_id: str):
        """Fetch all deals involving a specific user."""
        return deal_service.get_user_deals(user_id)

    @router.patch("/{deal_id}", response_model=DealResponse)
    def update_deal(deal_id: str, deal_update: DealUpdate):
        """Update a deal."""
        update_data = deal_update.model_dump(exclude_unset=True)
        return deal_service.update_deal(deal_id, update_data)

    @router.delete("/{deal_id}", status_code=204)
    def delete_deal(deal_id: str):
        """Delete a deal."""
        deal_service.delete_deal(deal_id)
        return None

    return router