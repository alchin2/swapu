from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller.rest_api.chat_controller import create_chat_routes
from controller.rest_api.item_controller import create_item_routes


def create_application() -> FastAPI:
    app = FastAPI(
        title="TradeSwap API",
        description="Trading marketplace platform API",
        version="1.0.0",
        license_info={"name": "MIT License"},
        openapi_tags=[
            {"name": "Chat", "description": "Chatroom management for deals"},
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
    app.include_router(create_item_routes())

    return app


app = create_application()