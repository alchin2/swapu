import os
import re
from functools import cached_property
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from core.exceptions import ConfigurationError, ExternalServiceError, ValidationError

_SAFE_FILE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
_DEFAULT_EXPIRATION_SECONDS = 900


class UploadService:
    @staticmethod
    def _resolve_access_key_id() -> str:
        return os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("ACCESS_KEY") or ""

    @staticmethod
    def _resolve_secret_access_key() -> str:
        return os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("SECRET_ACCESS_KEY") or ""

    @staticmethod
    def _resolve_region() -> str:
        return os.getenv("AWS_REGION") or ""

    @staticmethod
    def _resolve_bucket() -> str:
        return os.getenv("AWS_S3_BUCKET") or ""

    @cached_property
    def bucket_name(self) -> str:
        bucket_name = self._resolve_bucket().strip()
        if not bucket_name:
            raise ConfigurationError("AWS_S3_BUCKET is not configured.")
        return bucket_name

    @cached_property
    def region(self) -> str:
        region = self._resolve_region().strip()
        if not region:
            raise ConfigurationError("AWS_REGION is not configured.")
        return region

    @cached_property
    def client(self) -> BaseClient:
        access_key_id = self._resolve_access_key_id().strip()
        secret_access_key = self._resolve_secret_access_key().strip()
        if not access_key_id or not secret_access_key:
            raise ConfigurationError(
                "AWS credentials are not configured. Set AWS_ACCESS_KEY_ID/ACCESS_KEY and AWS_SECRET_ACCESS_KEY/SECRET_ACCESS_KEY."
            )

        return boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    @staticmethod
    def _normalize_file_name(file_name: str) -> str:
        normalized = file_name.strip()
        if not normalized:
            raise ValidationError("file_name is required.")

        safe_name = _SAFE_FILE_NAME.sub("-", normalized)
        safe_name = safe_name.strip(".-")
        if not safe_name:
            raise ValidationError("file_name must contain valid characters.")
        return safe_name

    @staticmethod
    def _validate_content_type(content_type: str) -> str:
        normalized = content_type.strip().lower()
        if not normalized:
            raise ValidationError("content_type is required.")
        if not normalized.startswith("image/"):
            raise ValidationError("Only image uploads are supported.")
        return normalized

    def _build_object_key(self, file_name: str, folder: str) -> str:
        safe_file_name = self._normalize_file_name(file_name)
        prefix = folder.strip().strip("/") or "items"
        extension = Path(safe_file_name).suffix.lower()
        if not extension:
            raise ValidationError("file_name must include a file extension.")
        return f"{prefix}/{uuid4()}{extension}"

    def _build_object_url(self, object_key: str) -> str:
        if self.region == "us-east-1":
            return f"https://{self.bucket_name}.s3.amazonaws.com/{object_key}"
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_key}"

    def create_presigned_upload(self, file_name: str, content_type: str, folder: str = "items") -> dict:
        normalized_content_type = self._validate_content_type(content_type)
        object_key = self._build_object_key(file_name, folder)

        try:
            upload_url = self.client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_key,
                    "ContentType": normalized_content_type,
                },
                ExpiresIn=_DEFAULT_EXPIRATION_SECONDS,
            )
        except (BotoCoreError, ClientError) as exc:
            raise ExternalServiceError("Failed to create S3 upload URL.") from exc

        return {
            "upload_url": upload_url,
            "file_url": self._build_object_url(object_key),
            "object_key": object_key,
            "method": "PUT",
            "headers": {"Content-Type": normalized_content_type},
            "expires_in": _DEFAULT_EXPIRATION_SECONDS,
            "bucket": self.bucket_name,
            "region": self.region,
        }

    def create_presigned_read_url(self, object_key: str, expiration: int = 3600) -> str:
        """Generate a presigned GET URL so private S3 objects can be read."""
        try:
            return self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )
        except (BotoCoreError, ClientError):
            return self._build_object_url(object_key)

    def extract_object_key(self, s3_url: str) -> str | None:
        """Extract the S3 object key from a full S3 URL."""
        marker = ".amazonaws.com/"
        idx = s3_url.find(marker)
        if idx != -1:
            return s3_url[idx + len(marker):]
        return None