from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from core.auth import get_current_user
from service.chat_service import ChatService


class CreateChatroomRequest(BaseModel):
    deal_id: str


class SendMessageRequest(BaseModel):
    sender_id: str
    content: str = Field(min_length=1, max_length=4000)


def create_chat_routes() -> APIRouter:
    router = APIRouter(prefix="/chatrooms", tags=["Chat"])
    chat_service = ChatService()

    @router.post("", status_code=201)
    def create_chatroom(request: CreateChatroomRequest, _: dict = Depends(get_current_user)):
        """Create a chatroom for a deal. Only one chatroom per deal."""
        return chat_service.create_chatroom(request.deal_id)

    @router.delete("/{chatroom_id}")
    def delete_chatroom(chatroom_id: str, _: dict = Depends(get_current_user)):
        """Delete a chatroom and all its messages."""
        return chat_service.delete_chatroom(chatroom_id)

    @router.get("/{chatroom_id}")
    def get_chatroom(chatroom_id: str, _: dict = Depends(get_current_user)):
        """Get chatroom details including deal participants."""
        return chat_service.get_chatroom(chatroom_id)

    @router.get("/user/{user_id}")
    def get_user_chatrooms(user_id: str, _: dict = Depends(get_current_user)):
        """Get all chatrooms a user is part of."""
        return chat_service.get_chatrooms_by_user(user_id)

    @router.get("/{chatroom_id}/messages")
    def get_messages(chatroom_id: str, limit: int = Query(50, ge=1, le=200), _: dict = Depends(get_current_user)):
        """Get messages in a chatroom."""
        return chat_service.get_messages(chatroom_id, limit=limit)

    @router.post("/{chatroom_id}/messages", status_code=201)
    def send_message(chatroom_id: str, request: SendMessageRequest, _: dict = Depends(get_current_user)):
        """Send a message in a chatroom (REST fallback before WebSocket)."""
        return chat_service.send_message(chatroom_id, request.sender_id, request.content)

    return router
