from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from service.deal_service import DealService

# --- Pydantic Models ---

class DealBase(BaseModel):
    user1_id: UUID
    user2_id: UUID
    user1_item_id: UUID
    user2_item_id: UUID
    cash_difference: float = Field(default=0.0, ge=0)
    payer_id: Optional[UUID] = None
    status: Literal["pending", "negotiating", "accepted", "declined"] = "pending"

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    status: Optional[Literal["pending", "negotiating", "accepted", "declined"]] = None
    cash_difference: Optional[float] = Field(default=None, ge=0)
    payer_id: Optional[UUID] = None

class DealResponse(DealBase):
    id: UUID
    created_at: str


def create_deal_routes() -> APIRouter:
    router = APIRouter(prefix="/deals", tags=["Deals"])
    deal_service = DealService()

    @router.post("/", response_model=DealResponse, status_code=201)
    def create_deal(deal: DealCreate):
        """Create a new deal."""
        return deal_service.create_deal(deal.model_dump(mode="json"))

    @router.get("/{deal_id}", response_model=DealResponse)
    def get_deal(deal_id: UUID):
        """Fetch a specific deal by ID."""
        return deal_service.get_deal(str(deal_id))

    @router.get("/user/{user_id}", response_model=List[DealResponse])
    def get_user_deals(user_id: UUID):
        """Fetch all deals involving a specific user."""
        return deal_service.get_user_deals(str(user_id))

    @router.patch("/{deal_id}", response_model=DealResponse)
    def update_deal(deal_id: UUID, deal_update: DealUpdate):
        """Update a deal."""
        update_data = deal_update.model_dump(exclude_unset=True, mode="json")
        return deal_service.update_deal(str(deal_id), update_data)

    @router.delete("/{deal_id}", status_code=204)
    def delete_deal(deal_id: UUID):
        """Delete a deal."""
        deal_service.delete_deal(str(deal_id))
        return None

    return router