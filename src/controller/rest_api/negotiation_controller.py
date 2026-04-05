from fastapi import APIRouter
from pydantic import BaseModel, Field

from service.negotiation_service import NegotiationService


class StartNegotiationRequest(BaseModel):
    deal_id: str


class CounterRequest(BaseModel):
    cash_difference: float = Field(ge=0)
    payer_id: str


def create_negotiation_routes() -> APIRouter:
    router = APIRouter(prefix="/negotiate", tags=["Negotiation"])
    service = NegotiationService()

    @router.post("", status_code=200)
    def start_negotiation(request: StartNegotiationRequest):
        """Start an AI agent negotiation for a deal."""
        return service.start_negotiation(request.deal_id)

    @router.get("/{deal_id}/logs")
    def get_negotiation_logs(deal_id: str):
        """Get negotiation logs for a deal."""
        return service.get_negotiation_logs(deal_id)

    @router.post("/{deal_id}/confirm")
    def confirm_negotiation(deal_id: str):
        """User confirms the negotiated deal."""
        return service.confirm_negotiation(deal_id)

    @router.post("/{deal_id}/decline")
    def decline_negotiation(deal_id: str):
        """User declines the negotiated deal."""
        return service.decline_negotiation(deal_id)

    @router.post("/{deal_id}/counter")
    def counter_negotiation(deal_id: str, request: CounterRequest):
        """User counters with new terms and re-runs negotiation."""
        return service.counter_negotiation(deal_id, request.cash_difference, request.payer_id)

    return router
