from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from core.auth import get_current_user
from service.deal_service import DealService
from service.chat_service import ChatService
from service.negotiation_service import NegotiationService

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
    chat_service = ChatService()

    def _run_negotiation_background(deal_id: str) -> None:
        try:
            NegotiationService().start_negotiation(deal_id)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Background negotiation failed for deal %s", deal_id)

    @router.post("/", response_model=DealResponse, status_code=201)
    def create_deal(deal: DealCreate, background_tasks: BackgroundTasks, _: dict = Depends(get_current_user)):
        """Create a new deal, chatroom, and kick off AI negotiation."""
        result = deal_service.create_deal(deal.model_dump(mode="json"))
        chat_service.create_chatroom(result["id"])
        background_tasks.add_task(_run_negotiation_background, result["id"])
        return result

    @router.get("/{deal_id}", response_model=DealResponse)
    def get_deal(deal_id: UUID, _: dict = Depends(get_current_user)):
        """Fetch a specific deal by ID."""
        return deal_service.get_deal(str(deal_id))

    @router.get("/user/{user_id}", response_model=List[DealResponse])
    def get_user_deals(user_id: UUID, _: dict = Depends(get_current_user)):
        """Fetch all deals involving a specific user."""
        return deal_service.get_user_deals(str(user_id))

    @router.patch("/{deal_id}", response_model=DealResponse)
    def update_deal(deal_id: UUID, deal_update: DealUpdate, _: dict = Depends(get_current_user)):
        """Update a deal."""
        update_data = deal_update.model_dump(exclude_unset=True, mode="json")
        return deal_service.update_deal(str(deal_id), update_data)

    @router.delete("/{deal_id}", status_code=204)
    def delete_deal(deal_id: UUID, _: dict = Depends(get_current_user)):
        """Delete a deal."""
        deal_service.delete_deal(str(deal_id))
        return None

    return router