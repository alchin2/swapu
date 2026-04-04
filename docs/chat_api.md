# TradeSwap Chat API Documentation

Base URL: `http://localhost:8000`

> Interactive docs available at `http://localhost:8000/docs` (Swagger UI)

---

## Endpoints

### 1. Create Chatroom

Creates a chatroom for a deal. Only **one chatroom per deal** is allowed. The two participants are determined by the deal's `user1_id` and `user2_id`.

```
POST /chatrooms
```

**Request Body**

```json
{
  "deal_id": "uuid-of-the-deal"
}
```

**Response** `201 Created`

```json
{
  "id": "generated-chatroom-uuid",
  "deal_id": "uuid-of-the-deal"
}
```

**Errors**

| Status | Reason |
|--------|--------|
| 400 | Deal not found or chatroom already exists for this deal |

---

### 2. Get Chatroom

```
GET /chatrooms/{chatroom_id}
```

**Response** `200 OK`

```json
{
  "id": "chatroom-uuid",
  "deal_id": "deal-uuid",
  "deals": {
    "id": "deal-uuid",
    "user1_id": "user-uuid",
    "user2_id": "user-uuid",
    "status": "pending"
  }
}
```

**Errors**

| Status | Reason |
|--------|--------|
| 404 | Chatroom not found |

---

### 3. Get User's Chatrooms

Returns all chatrooms where the user is a participant (as `user1` or `user2` in the deal).

```
GET /chatrooms/user/{user_id}
```

**Response** `200 OK`

```json
[
  {
    "id": "chatroom-uuid",
    "deal_id": "deal-uuid",
    "deals": {
      "id": "deal-uuid",
      "user1_id": "user-uuid",
      "user2_id": "user-uuid",
      "status": "pending"
    }
  }
]
```

Returns `[]` if the user has no chatrooms.

---

### 4. Delete Chatroom

Deletes a chatroom **and all its messages**.

```
DELETE /chatrooms/{chatroom_id}
```

**Response** `200 OK`

```json
{
  "message": "Chatroom {chatroom_id} deleted successfully"
}
```

**Errors**

| Status | Reason |
|--------|--------|
| 404 | Chatroom not found |

---

### 5. Get Messages

Returns messages in a chatroom ordered by creation time (oldest first).

```
GET /chatrooms/{chatroom_id}/messages?limit=50
```

**Query Parameters**

| Param | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| limit | int | 50 | 1–200 | Max number of messages to return |

**Response** `200 OK`

```json
[
  {
    "id": "message-uuid",
    "chatroom_id": "chatroom-uuid",
    "sender_id": "user-uuid",
    "content": "Hello!",
    "created_at": "2026-04-04T12:00:00Z"
  }
]
```

**Errors**

| Status | Reason |
|--------|--------|
| 404 | Chatroom not found |

---

### 6. Send Message

Sends a message in a chatroom. The sender must be one of the two deal participants.

```
POST /chatrooms/{chatroom_id}/messages
```

**Request Body**

```json
{
  "sender_id": "user-uuid",
  "content": "Hey, want to trade?"
}
```

**Response** `201 Created`

```json
{
  "id": "message-uuid",
  "chatroom_id": "chatroom-uuid",
  "sender_id": "user-uuid",
  "content": "Hey, want to trade?",
  "created_at": "2026-04-04T12:00:00Z"
}
```

**Errors**

| Status | Reason |
|--------|--------|
| 404 | Chatroom not found |
| 403 | Sender is not a participant in this chatroom |

---

## Running the Server

```bash
cd src
uvicorn app:app --reload
```

Server starts at `http://localhost:8000`. Open `/docs` for the interactive Swagger UI.
