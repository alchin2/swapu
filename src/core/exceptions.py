from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ErrorPayload:
    code: str
    detail: str


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail

    def to_payload(self) -> ErrorPayload:
        return ErrorPayload(code=self.code, detail=self.detail)


class ValidationError(AppError):
    status_code = 400
    code = "validation_error"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class AuthorizationError(AppError):
    status_code = 403
    code = "forbidden"


class ConfigurationError(AppError):
    status_code = 500
    code = "configuration_error"


class ExternalServiceError(AppError):
    status_code = 502
    code = "external_service_error"