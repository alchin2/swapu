from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field

from core.auth import get_current_user
from service.matching_service import MatchingService


class MatchRequest(BaseModel):
    item_ids: list[str] = Field(min_length=1)
    category: str | None = None
    name: str | None = None
    condition: str | None = None


class AgentDealRequest(BaseModel):
    category: str | None = None
    condition: str | None = None


def create_match_routes() -> APIRouter:
    router = APIRouter(prefix="/match", tags=["Matching"])
    service = MatchingService()

    @router.post("/{user_id}")
    def find_matches(user_id: str, request: MatchRequest, limit: int = Query(10, ge=1, le=50), _: dict = Depends(get_current_user)):
        """Find best trade matches for a user's offered items.

        - item_ids: items the user is willing to offer
        - category: filter results to a desired category
        - name: partial text search on item name
        - condition: minimum condition (like_new, good, fair, poor)
        """
        return service.find_matches(
            user_id=user_id,
            item_ids=request.item_ids,
            category=request.category,
            name=request.name,
            condition=request.condition,
            limit=limit,
        )

    @router.post("/{user_id}/auto-deal")
    def create_agent_selected_deal(user_id: str, request: AgentDealRequest, background_tasks: BackgroundTasks, _: dict = Depends(get_current_user)):
        """Agent picks the best trade from the user's full collection, creates
        the deal, and queues AI negotiation in the background."""
        result = service.create_best_agent_deal(
            user_id=user_id,
            category=request.category,
            condition=request.condition,
        )
        background_tasks.add_task(
            MatchingService.run_negotiation_background, result["deal"]["id"]
        )
        return result

    return router
