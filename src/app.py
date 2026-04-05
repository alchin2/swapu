import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller.rest_api.chat_controller import create_chat_routes
from controller.rest_api.negotiation_controller import create_negotiation_routes
from websocket.chat_ws import router as chat_ws_router
from controller.rest_api.item_controller import create_item_routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
from controller.rest_api.deal_contoller import create_deal_routes


def create_application() -> FastAPI:
    app = FastAPI(
        title="TradeSwap API",
        description="Trading marketplace platform API",
        version="1.0.0",
        license_info={"name": "MIT License"},
        openapi_tags=[
            {"name": "Chat", "description": "Chatroom management for deals"},
            {"name": "Negotiation", "description": "AI agent deal negotiation"},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(create_chat_routes())
    app.include_router(create_negotiation_routes())
    app.include_router(chat_ws_router)
    app.include_router(create_item_routes())
    app.include_router(create_deal_routes())

    return app

app = create_application()