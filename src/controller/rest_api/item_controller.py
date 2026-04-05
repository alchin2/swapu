from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID

from service.items_service import ItemService, Item, ItemCreate, ItemUpdate


def create_item_routes() -> APIRouter:
    router = APIRouter(prefix="/items", tags=["Items"])
    item_service = ItemService()

    @router.get("/", response_model=List[Item])
    def get_items():
        """Get all items"""
        try:
            return item_service.get_items()
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/{item_id}", response_model=Item)
    def get_item(item_id: UUID):
        """Get an item by its ID"""
        try:
            return item_service.get_item(str(item_id))
        except ValueError as e:
            if str(e) == "Item not found":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
    def create_item(request: ItemCreate):
        """Create a new item"""
        try:
            return item_service.create_item(
                owner_id=str(request.owner_id),
                name=request.name,
                category=request.category,
                condition=request.condition,
                price=request.price,
                confidence_score=request.confidence_score,
                image_url=request.image_url
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.patch("/{item_id}", response_model=Item)
    def update_item(item_id: UUID, request: ItemUpdate):
        """Update an existing item"""
        try:
            update_data = request.model_dump(exclude_unset=True)
            return item_service.update_item(str(item_id), update_data)
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(item_id: UUID):
        """Delete an item by its ID"""
        try:
            item_service.delete_item(str(item_id))
            return None
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return router
