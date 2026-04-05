from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, status

from service.items_service import ItemService, Item, ItemCreate, ItemUpdate
from agents.pricing_agent import pricing_agent


def create_item_routes() -> APIRouter:
    router = APIRouter(prefix="/items", tags=["Items"])
    item_service = ItemService()

    @router.get("/", response_model=List[Item])
    def get_items():
        """Get all items"""
        return item_service.get_items()

    @router.get("/{item_id}", response_model=Item)
    def get_item(item_id: UUID):
        """Get an item by its ID"""
        return item_service.get_item(str(item_id))

    @router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
    async def create_item(request: ItemCreate, background_tasks: BackgroundTasks):
        """Create a new item"""
        item = item_service.create_item(
            owner_id=str(request.owner_id),
            name=request.name,
            category=request.category,
            condition=request.condition,
            price=request.price,
            confidence_score=request.confidence_score,
            image_url=request.image_url,
        )
        background_tasks.add_task(
            pricing_agent.get_aggregated_price_and_category,
            item["id"],
            item["name"],
            item["condition"],
            item["price"],
        )
        return item

    @router.patch("/{item_id}", response_model=Item)
    def update_item(item_id: UUID, request: ItemUpdate):
        """Update an existing item"""
        update_data = request.model_dump(exclude_unset=True)
        return item_service.update_item(str(item_id), update_data)

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(item_id: UUID):
        """Delete an item by its ID"""
        item_service.delete_item(str(item_id))
        return None

    return router
