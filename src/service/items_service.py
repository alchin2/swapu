from datetime import datetime, timezone
import logging
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from core.exceptions import ExternalServiceError, NotFoundError, ValidationError
from service.base import SupabaseService

logger = logging.getLogger(__name__)

# Schema Definitions
class ItemBase(BaseModel):
    owner_id: UUID
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=80)
    condition: str = Field(min_length=1, max_length=40)
    price: float = Field(gt=0)
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)
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


class ItemService(SupabaseService):
    def get_items(self):
        try:
            response = self.client.table("items").select("*").execute()
            return response.data
        except Exception as e:
            logger.exception("Error fetching items", exc_info=e)
            raise ExternalServiceError("Could not fetch items.") from e

    def get_item(self, item_id: str):
        try:
            item_id = self.require_identifier(item_id, "item_id")
            response = self.client.table("items").select("*").eq("id", item_id).limit(1).execute()
            if not response.data:
                raise NotFoundError(f"Item '{item_id}' not found.")
            return response.data[0]
        except NotFoundError:
            raise
        except Exception as e:
            logger.exception("Error fetching item %s", item_id, exc_info=e)
            raise ExternalServiceError("Could not fetch item.") from e

    def create_item(self, owner_id: str, name: str, category: str, condition: str, price: float, confidence_score: Optional[float] = None, image_url: Optional[str] = None):
        owner_id = self.require_identifier(owner_id, "owner_id")
        if price <= 0:
            raise ValidationError("price must be greater than zero.")
        try:
            new_item_data = {
                "id": str(uuid4()),
                "owner_id": owner_id,
                "name": name.strip(),
                "category": category.strip(),
                "condition": condition.strip(),
                "price": price,
                "confidence_score": confidence_score,
                "image_url": image_url,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            response = self.client.table("items").insert(new_item_data).execute()

            if not response.data:
                raise ValidationError("Failed to create item.")

            return response.data[0]
        except ValidationError:
            raise
        except Exception as e:
            logger.exception("Error creating item", exc_info=e)
            raise ExternalServiceError("Could not create item.") from e

    def update_item(self, item_id: str, update_data: dict):
        item_id = self.require_identifier(item_id, "item_id")
        if not update_data:
            return self.get_item(item_id)

        if "price" in update_data and update_data["price"] is not None and update_data["price"] <= 0:
            raise ValidationError("price must be greater than zero.")

        try:
            response = self.client.table("items").update(update_data).eq("id", item_id).execute()

            if not response.data:
                raise NotFoundError(f"Item '{item_id}' not found.")

            return response.data[0]
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.exception("Error updating item %s", item_id, exc_info=e)
            raise ExternalServiceError("Could not update item.") from e

    def delete_item(self, item_id: str):
        item_id = self.require_identifier(item_id, "item_id")
        try:
            response = self.client.table("items").delete().eq("id", item_id).execute()

            if not response.data:
                raise NotFoundError(f"Item '{item_id}' not found.")

            return None
        except NotFoundError:
            raise
        except Exception as e:
            logger.exception("Error deleting item %s", item_id, exc_info=e)
            raise ExternalServiceError("Could not delete item.") from e
