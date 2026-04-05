from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from service.matching_service import MatchingService


class MatchRequest(BaseModel):
    item_ids: list[str]
    category: str | None = None
    name: str | None = None
    condition: str | None = None


def create_match_routes() -> APIRouter:
    router = APIRouter(prefix="/match", tags=["Matching"])
    service = MatchingService()

    @router.post("/{user_id}")
    def find_matches(user_id: str, request: MatchRequest, limit: int = Query(10, ge=1, le=50)):
        """Find best trade matches for a user's offered items.

        - item_ids: items the user is willing to offer
        - category: filter results to a desired category
        - name: partial text search on item name
        - condition: minimum condition (like_new, good, fair, poor)
        """
        try:
            return service.find_matches(
                user_id=user_id,
                item_ids=request.item_ids,
                category=request.category,
                name=request.name,
                condition=request.condition,
                limit=limit,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router
