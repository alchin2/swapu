from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

from database.supabase_client import get_supabase_client
try:
    supabase = get_supabase_client()
except ValueError:
    supabase = None

logger = logging.getLogger(__name__)

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

class ItemService:
    def get_items(self):
        if not supabase:
            raise ValueError("Database connection not configured")
        
        try:
            response = supabase.table("items").select("*").execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching items: {str(e)}")
            raise ValueError("Could not fetch items")

    def get_item(self, item_id: str):
        if not supabase:
            raise ValueError("Database connection not configured")
            
        try:
            response = supabase.table("items").select("*").eq("id", item_id).execute()
            if not response.data:
                raise ValueError("Item not found")
            return response.data[0]
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching item {item_id}: {str(e)}")
            raise ValueError("Could not fetch item")

    def create_item(self, owner_id: str, name: str, category: str, condition: str, price: float, confidence_score: Optional[float] = None, image_url: Optional[str] = None):
        if not supabase:
            raise ValueError("Database connection not configured")
            
        try:
            new_item_data = {
                "id": str(uuid4()),
                "owner_id": owner_id,
                "name": name,
                "category": category,
                "condition": condition,
                "price": price,
                "confidence_score": confidence_score,
                "image_url": image_url,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = supabase.table("items").insert(new_item_data).execute()
            
            if not response.data:
                raise ValueError("Failed to create item")
                
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating item: {str(e)}")
            raise ValueError("Could not create item")

    def update_item(self, item_id: str, update_data: dict):
        if not supabase:
            raise ValueError("Database connection not configured")
            
        if not update_data:
            # If no fields to update, just return the existing item
            response = supabase.table("items").select("*").eq("id", item_id).execute()
            if not response.data:
                raise ValueError("Item not found")
            return response.data[0]
            
        try:
            response = supabase.table("items").update(update_data).eq("id", item_id).execute()
            
            if not response.data:
                raise ValueError("Item not found or no changes made")
                
            return response.data[0]
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating item {item_id}: {str(e)}")
            raise ValueError("Could not update item")

    def delete_item(self, item_id: str):
        if not supabase:
            raise ValueError("Database connection not configured")
            
        try:
            response = supabase.table("items").delete().eq("id", item_id).execute()
            
            if not response.data:
                raise ValueError("Item not found")
                
            return None
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deleting item {item_id}: {str(e)}")
            raise Exception("Could not delete item")
