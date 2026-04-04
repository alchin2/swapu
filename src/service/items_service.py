from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

from src.database.client import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/items", tags=["Items"])

# Schema Definitions
class ItemBase(BaseModel):
    owner_id: UUID
    name: str
    category: str
    condition: str
    price: float
    confidence_score: Optional[float] = None
    image_url: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    price: Optional[float] = None
    confidence_score: Optional[float] = None
    image_url: Optional[str] = None

class Item(ItemBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item_in: ItemCreate):
    """
    Create a new item
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured")
        
    try:
        new_item_data = {
            "id": str(uuid4()),
            "owner_id": str(item_in.owner_id),
            "name": item_in.name,
            "category": item_in.category,
            "condition": item_in.condition,
            "price": item_in.price,
            "confidence_score": item_in.confidence_score,
            "image_url": item_in.image_url,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("items").insert(new_item_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create item")
            
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create item")

@router.patch("/{item_id}", response_model=Item)
async def update_item(item_id: UUID, item_in: ItemUpdate):
    """
    Update an existing item
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured")
        
    try:
        update_data = item_in.model_dump(exclude_unset=True)
        
        if not update_data:
            # If no fields to update, just return the existing item
            response = supabase.table("items").select("*").eq("id", str(item_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
            return response.data[0]
            
        response = supabase.table("items").update(update_data).eq("id", str(item_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or no changes made")
            
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update item")

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: UUID):
    """
    Delete an item by its ID
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured")
        
    try:
        # Supabase API usually returns the deleted rows
        response = supabase.table("items").delete().eq("id", str(item_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
            
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete item")
