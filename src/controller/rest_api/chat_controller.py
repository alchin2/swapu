from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from service.chat_service import ChatService


class CreateChatroomRequest(BaseModel):
    deal_id: str


class SendMessageRequest(BaseModel):
    sender_id: str
    content: str


def create_chat_routes() -> APIRouter:
    router = APIRouter(prefix="/chatrooms", tags=["Chat"])
    chat_service = ChatService()

    @router.post("", status_code=201)
    def create_chatroom(request: CreateChatroomRequest):
        """Create a chatroom for a deal. Only one chatroom per deal."""
        try:
            chatroom = chat_service.create_chatroom(request.deal_id)
            return chatroom
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.delete("/{chatroom_id}")
    def delete_chatroom(chatroom_id: str):
        """Delete a chatroom and all its messages."""
        try:
            return chat_service.delete_chatroom(chatroom_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/{chatroom_id}")
    def get_chatroom(chatroom_id: str):
        """Get chatroom details including deal participants."""
        try:
            return chat_service.get_chatroom(chatroom_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/user/{user_id}")
    def get_user_chatrooms(user_id: str):
        """Get all chatrooms a user is part of."""
        return chat_service.get_chatrooms_by_user(user_id)

    @router.get("/{chatroom_id}/messages")
    def get_messages(chatroom_id: str, limit: int = Query(50, ge=1, le=200)):
        """Get messages in a chatroom."""
        try:
            return chat_service.get_messages(chatroom_id, limit=limit)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.post("/{chatroom_id}/messages", status_code=201)
    def send_message(chatroom_id: str, request: SendMessageRequest):
        """Send a message in a chatroom (REST fallback before WebSocket)."""
        try:
            return chat_service.send_message(
                chatroom_id, request.sender_id, request.content
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    return router
