import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controller.rest_api.chat_controller import create_chat_routes
from controller.rest_api.deal_contoller import create_deal_routes
from controller.rest_api.item_controller import create_item_routes
from controller.rest_api.match_controller import create_match_routes
from controller.rest_api.negotiation_controller import create_negotiation_routes
from controller.rest_api.user_controller import create_user_routes
from core.exceptions import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    app = FastAPI(
        title="TradeSwap API",
        description="Trading marketplace platform API",
        version="1.1.0",
        license_info={"name": "MIT License"},
        openapi_tags=[
            {"name": "Chat", "description": "Chatroom management for deals"},
            {"name": "Deals", "description": "Trade deal lifecycle management"},
            {"name": "Items", "description": "Marketplace inventory management"},
            {"name": "Negotiation", "description": "AI agent deal negotiation"},
            {"name": "Matching", "description": "Smart trade matching"},
            {"name": "Users", "description": "User profiles and preferences"},
            {"name": "System", "description": "Operational endpoints"},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        payload = exc.to_payload()
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": payload.code, "detail": payload.detail},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "detail": "An unexpected server error occurred."},
        )

    @app.get("/health", tags=["System"])
    def health_check() -> dict:
        return {"status": "ok"}

    app.include_router(create_chat_routes())
    app.include_router(create_deal_routes())
    app.include_router(create_item_routes())
    app.include_router(create_match_routes())
    app.include_router(create_negotiation_routes())
    app.include_router(create_user_routes())

    return app


app = create_application()