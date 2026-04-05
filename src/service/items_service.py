from datetime import datetime, timezone
import logging
from typing import Optional
from uuid import UUID, uuid4

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator

from core.exceptions import ExternalServiceError, NotFoundError, ValidationError
from service.base import SupabaseService

logger = logging.getLogger(__name__)

_upload_service = None


def _get_upload_service():
    global _upload_service
    if _upload_service is None:
        from service.upload_service import UploadService
        _upload_service = UploadService()
    return _upload_service


def _to_presigned_url(s3_url: str) -> str:
    """Convert a raw S3 URL to a presigned read URL."""
    try:
        svc = _get_upload_service()
        key = svc.extract_object_key(s3_url)
        if key:
            return svc.create_presigned_read_url(key)
    except Exception:
        pass
    return s3_url


def _split_image_urls(raw_value: Optional[str]) -> list[str]:
    if not raw_value:
        return []
    return [url.strip() for url in raw_value.split(",") if url.strip()]


def _join_image_urls(image_urls: list[str]) -> str:
    cleaned_urls = [url.strip() for url in image_urls if url and url.strip()]
    if not cleaned_urls:
        raise ValidationError("At least one image URL is required.")
    return ",".join(cleaned_urls)

# Schema Definitions
class ItemBase(BaseModel):
    owner_id: UUID
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=80)
    condition: str = Field(min_length=1, max_length=40)
    price: float = Field(gt=0)
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)
    image_urls: list[AnyHttpUrl] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_image_url(cls, data):
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        if "image_urls" not in normalized and "image_url" in normalized:
            raw_value = normalized.get("image_url")
            if isinstance(raw_value, str):
                normalized["image_urls"] = _split_image_urls(raw_value)
        return normalized

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    price: Optional[float] = None
    confidence_score: Optional[float] = None
    image_urls: Optional[list[AnyHttpUrl]] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_image_url(cls, data):
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        if "image_urls" not in normalized and "image_url" in normalized:
            raw_value = normalized.get("image_url")
            if isinstance(raw_value, str):
                normalized["image_urls"] = _split_image_urls(raw_value)
        return normalized

class Item(ItemBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemService(SupabaseService):
    @staticmethod
    def _format_item(item_row: dict) -> dict:
        formatted = dict(item_row)
        raw_urls = _split_image_urls(formatted.get("image_url"))
        formatted["image_urls"] = [_to_presigned_url(url) for url in raw_urls]
        return formatted

    def get_items(self):
        try:
            response = self.client.table("items").select("*").execute()
            return [self._format_item(item) for item in response.data or []]
        except Exception as e:
            logger.exception("Error fetching items", exc_info=e)
            raise ExternalServiceError("Could not fetch items.") from e

    def get_item(self, item_id: str):
        try:
            item_id = self.require_identifier(item_id, "item_id")
            response = self.client.table("items").select("*").eq("id", item_id).limit(1).execute()
            if not response.data:
                raise NotFoundError(f"Item '{item_id}' not found.")
            return self._format_item(response.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.exception("Error fetching item %s", item_id, exc_info=e)
            raise ExternalServiceError("Could not fetch item.") from e

    def create_item(self, owner_id: str, name: str, category: str, condition: str, price: float, confidence_score: Optional[float] = None, image_urls: Optional[list[str]] = None):
        owner_id = self.require_identifier(owner_id, "owner_id")
        if price <= 0:
            raise ValidationError("price must be greater than zero.")
        if not image_urls:
            raise ValidationError("At least one uploaded image is required to create an item.")
        try:
            new_item_data = {
                "id": str(uuid4()),
                "owner_id": owner_id,
                "name": name.strip(),
                "category": category.strip(),
                "condition": condition.strip(),
                "price": price,
                "confidence_score": confidence_score,
                "image_url": _join_image_urls(image_urls),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            response = self.client.table("items").insert(new_item_data).execute()

            if not response.data:
                raise ValidationError("Failed to create item.")

            return self._format_item(response.data[0])
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

        if "image_urls" in update_data:
            raw_image_urls = update_data.pop("image_urls")
            if raw_image_urls is not None:
                update_data["image_url"] = _join_image_urls([str(url) for url in raw_image_urls])

        try:
            response = self.client.table("items").update(update_data).eq("id", item_id).execute()

            if not response.data:
                raise NotFoundError(f"Item '{item_id}' not found.")

            return self._format_item(response.data[0])
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
