from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from service.negotiation_service import NegotiationService


class StartNegotiationRequest(BaseModel):
    deal_id: str


def create_negotiation_routes() -> APIRouter:
    router = APIRouter(prefix="/negotiate", tags=["Negotiation"])
    service = NegotiationService()

    @router.post("", status_code=200)
    def start_negotiation(request: StartNegotiationRequest):
        """Start an AI agent negotiation for a deal."""
        try:
            result = service.start_negotiation(request.deal_id)
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/{deal_id}/logs")
    def get_negotiation_logs(deal_id: str):
        """Get negotiation logs for a deal."""
        return service.get_negotiation_logs(deal_id)

    return router
