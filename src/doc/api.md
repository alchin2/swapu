# TradeSwap API Reference

This document describes the current HTTP API exposed by the FastAPI application in `src/app.py`.

## Base Information

- App name: `TradeSwap API`
- Version: `1.1.0`
- Default error format:

```json
{
  "error": "validation_error",
  "detail": "Human-readable error message"
}
```

## Error Codes

| HTTP Status | `error` value | Meaning |
| --- | --- | --- |
| `400` | `validation_error` | Invalid request data or invalid domain action |
| `403` | `forbidden` | Caller is not allowed to perform the action |
| `404` | `not_found` | Requested resource does not exist |
| `409` | `conflict` | Request conflicts with current system state |
| `500` | `configuration_error` or `internal_error` | Server configuration or unexpected failure |
| `502` | `external_service_error` | A dependent external service failed |

## Users

Base path: `/users`

### `POST /users`

Register a new user.

Request body:

```json
{
  "email": "user@example.com",
  "name": "Jane Doe",
  "max_cash_amt": 50.0,
  "max_cash_pct": 20.0
}
```

### `GET /users`

List all users (used by frontend guest account selector).

### `GET /users/{user_id}`

Get a user by ID.

### `GET /users/email/{email}`

Look up a user by email address.

### `PATCH /users/{user_id}`

Update a user's profile or cash trade limits.

Request body:

```json
{
  "name": "Jane Smith",
  "max_cash_amt": 100.0,
  "max_cash_pct": 50.0
}
```

### `DELETE /users/{user_id}`

Delete a user account and all associated records.

## Uploads

Base path: `/uploads`

Use this endpoint before creating an item when the frontend needs to upload image files to S3.

Backend configuration:

- Bucket env: `AWS_S3_BUCKET`
- Region env: `AWS_REGION`
- Access key env: `AWS_ACCESS_KEY_ID` or legacy `ACCESS_KEY`
- Secret key env: `AWS_SECRET_ACCESS_KEY` or legacy `SECRET_ACCESS_KEY`

Current project bucket:

- `diamondhack-tradingshop`

Recommended flow:

1. Call `POST /uploads/presign` once per image.
2. Upload the file bytes from the frontend directly to the returned `upload_url` using the returned HTTP method and headers.
3. Collect each returned `file_url`.
4. Call `POST /items/` with those URLs in `image_urls`.

### `POST /uploads/presign`

Create a presigned S3 upload URL for an image file.

Request body:

```json
{
  "file_name": "ti84-front.png",
  "content_type": "image/png",
  "folder": "items"
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `file_name` | string | yes | Original file name, must include extension |
| `content_type` | string | yes | Must be an image MIME type like `image/png` |
| `folder` | string | no | S3 key prefix, defaults to `items` |

Success response: `200 OK`

Example response:

```json
{
  "upload_url": "https://diamondhack-tradingshop.s3.amazonaws.com/items/5b8f2d9d-0b84-4422-9f74-2f5d6e08af95.png?...",
  "file_url": "https://diamondhack-tradingshop.s3.amazonaws.com/items/5b8f2d9d-0b84-4422-9f74-2f5d6e08af95.png",
  "object_key": "items/5b8f2d9d-0b84-4422-9f74-2f5d6e08af95.png",
  "method": "PUT",
  "headers": {
    "Content-Type": "image/png"
  },
  "expires_in": 900,
  "bucket": "diamondhack-tradingshop",
  "region": "us-east-1"
}
```

Frontend upload example:

```http
PUT {upload_url}
Content-Type: image/png

<raw file bytes>
```

Notes:

- The upload URL is short-lived and currently expires after `900` seconds.
- The backend only presigns uploads for content types beginning with `image/`.
- The backend generates a unique S3 object key and returns the final public/object URL as `file_url`.
- `file_url` is the value you should send later in `POST /items/` or `PATCH /items/{item_id}`.

## System

### `GET /health`

Health check endpoint.

Response:

```json
{
  "status": "ok"
}
```

## Items

Base path: `/items`

### Item Shape

```json
{
  "id": "0f52df66-bd60-4b1f-a76b-c151dc62d7b0",
  "owner_id": "9f2f4487-98f0-42b4-9ed1-c8cc8f2c1b2a",
  "name": "TI-84 Plus",
  "category": "electronics",
  "condition": "good",
  "price": 45,
  "confidence_score": 0.82,
  "image_urls": [
    "https://diamondhack-tradingshop.s3.amazonaws.com/items/ti84-front.png"
  ],
  "created_at": "2026-04-04T18:43:00.000000+00:00"
}
```

### `GET /items/`

Get all items.

Success response: `200 OK`

Response body: array of item objects.

### `GET /items/{item_id}`

Get a single item by UUID.

Success response: `200 OK`

### `POST /items/`

Create an item.

Request body:

```json
{
  "owner_id": "9f2f4487-98f0-42b4-9ed1-c8cc8f2c1b2a",
  "name": "TI-84 Plus",
  "category": "electronics",
  "condition": "good",
  "price": 45,
  "confidence_score": 0.82,
  "image_urls": [
    "https://diamondhack-tradingshop.s3.amazonaws.com/items/ti84-front.png"
  ]
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `owner_id` | UUID | yes | Owner user ID |
| `name` | string | yes | 1 to 200 characters |
| `category` | string | yes | 1 to 80 characters |
| `condition` | string | yes | 1 to 40 characters |
| `price` | number | yes | Must be `> 0` |
| `confidence_score` | number or null | no | Between `0` and `1` |
| `image_urls` | array of URLs | yes | At least one uploaded image URL is required |

Success response: `201 Created`

Notes:

- After item creation, a background task is scheduled to re-evaluate price and category using the pricing agent.
  - You must upload at least one image before calling `POST /items/`.
- The API accepts `image_urls` and stores them in the database `image_url` text column as a comma-separated string.

## Uploads

Base path: `/uploads`

Use this endpoint before creating an item when the frontend needs to upload image files to S3.

Recommended flow:

1. Call `POST /uploads/presign` once per image.
2. Upload the file bytes from the frontend directly to the returned `upload_url` using the returned HTTP method and headers.
3. Collect each returned `file_url`.
4. Call `POST /items/` with those URLs in `image_urls`.

### `POST /uploads/presign`

Create a presigned S3 upload URL for an image file.

Request body:

```json
{
  "file_name": "ti84-front.png",
  "content_type": "image/png",
  "folder": "items"
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `file_name` | string | yes | Original file name, must include extension |
| `content_type` | string | yes | Must be an image MIME type like `image/png` |
| `folder` | string | no | S3 key prefix, defaults to `items` |

Success response: `200 OK`

Example response:

```json
{
  "upload_url": "https://diamondhack-tradingshop.s3.amazonaws.com/items/5b8f2d9d-0b84-4422-9f74-2f5d6e08af95.png?...",
  "file_url": "https://diamondhack-tradingshop.s3.amazonaws.com/items/5b8f2d9d-0b84-4422-9f74-2f5d6e08af95.png",
  "object_key": "items/5b8f2d9d-0b84-4422-9f74-2f5d6e08af95.png",
  "method": "PUT",
  "headers": {
    "Content-Type": "image/png"
  },
  "expires_in": 900,
  "bucket": "diamondhack-tradingshop",
  "region": "us-east-1"
}
```

### `PATCH /items/{item_id}`

Update an item.

Request body example:

```json
{
  "price": 55,
  "condition": "like_new",
  "image_urls": [
    "https://diamondhack-tradingshop.s3.amazonaws.com/items/ti84-front.png",
    "https://diamondhack-tradingshop.s3.amazonaws.com/items/ti84-back.png"
  ]
}
```

All fields are optional.

Success response: `200 OK`

### `DELETE /items/{item_id}`

Delete an item.

Success response: `204 No Content`

## Deals

Base path: `/deals`

### Deal Shape

```json
{
  "id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce",
  "user1_id": "11111111-1111-1111-1111-111111111111",
  "user2_id": "22222222-2222-2222-2222-222222222222",
  "user1_item_id": "33333333-3333-3333-3333-333333333333",
  "user2_item_id": "44444444-4444-4444-4444-444444444444",
  "cash_difference": 20,
  "payer_id": "11111111-1111-1111-1111-111111111111",
  "status": "pending",
  "created_at": "2026-04-04T18:43:00.000000+00:00"
}
```

### `POST /deals/`

Create a deal.

Request body:

```json
{
  "user1_id": "11111111-1111-1111-1111-111111111111",
  "user2_id": "22222222-2222-2222-2222-222222222222",
  "user1_item_id": "33333333-3333-3333-3333-333333333333",
  "user2_item_id": "44444444-4444-4444-4444-444444444444",
  "cash_difference": 20,
  "payer_id": "11111111-1111-1111-1111-111111111111",
  "status": "pending"
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `user1_id` | string | yes | First user |
| `user2_id` | string | yes | Second user |
| `user1_item_id` | string | yes | Item offered by first user |
| `user2_item_id` | string | yes | Item offered by second user |
| `cash_difference` | number | no | Defaults to `0`, must be `>= 0` |
| `payer_id` | string or null | no | User paying the cash difference |
| `status` | string | no | One of `pending`, `negotiating`, `accepted`, `declined` |

Success response: `201 Created`

### `GET /deals/{deal_id}`

Get a deal by ID.

Success response: `200 OK`

### `GET /deals/user/{user_id}`

Get all deals involving a user.

Success response: `200 OK`

Response body: array of deal objects.

### `PATCH /deals/{deal_id}`

Update a deal.

Request body example:

```json
{
  "status": "negotiating",
  "cash_difference": 15,
  "payer_id": "11111111-1111-1111-1111-111111111111"
}
```

All fields are optional.

Success response: `200 OK`

### `DELETE /deals/{deal_id}`

Delete a deal.

Success response: `204 No Content`

## Chatrooms

Base path: `/chatrooms`

### `POST /chatrooms`

Create a chatroom for a deal. Only one chatroom is allowed per deal.

Request body:

```json
{
  "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce"
}
```

Success response: `201 Created`

Example response:

```json
{
  "id": "8b4bc4a2-4d17-4af7-bab4-b8e99785db6d",
  "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce"
}
```

### `DELETE /chatrooms/{chatroom_id}`

Delete a chatroom and all of its messages.

Success response: `200 OK`

Example response:

```json
{
  "message": "Chatroom '8b4bc4a2-4d17-4af7-bab4-b8e99785db6d' deleted successfully."
}
```

### `GET /chatrooms/{chatroom_id}`

Get a chatroom and its linked deal summary.

Example response:

```json
{
  "id": "8b4bc4a2-4d17-4af7-bab4-b8e99785db6d",
  "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce",
  "deals": {
    "user1_id": "11111111-1111-1111-1111-111111111111",
    "user2_id": "22222222-2222-2222-2222-222222222222",
    "status": "pending"
  }
}
```

### `GET /chatrooms/user/{user_id}`

Get all chatrooms associated with deals that include the user.

Success response: `200 OK`

Response body: array of chatroom objects.

### `GET /chatrooms/{chatroom_id}/messages`

Get messages in a chatroom.

Query parameters:

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `limit` | integer | no | Default `50`, min `1`, max `200` |

Example response:

```json
[
  {
    "id": "b9d9409f-6ca5-4dc1-9472-0a3381d4a3c3",
    "chatroom_id": "8b4bc4a2-4d17-4af7-bab4-b8e99785db6d",
    "sender_id": "11111111-1111-1111-1111-111111111111",
    "content": "Would you add $20?",
    "created_at": "2026-04-04T18:45:00.000000+00:00"
  }
]
```

### `POST /chatrooms/{chatroom_id}/messages`

Create a message in a chatroom.

Request body:

```json
{
  "sender_id": "11111111-1111-1111-1111-111111111111",
  "content": "Would you add $20?"
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `sender_id` | string | yes | Must belong to the deal participants |
| `content` | string | yes | 1 to 4000 characters |

Success response: `201 Created`

## Matching

Base path: `/match`

### `POST /match/{user_id}`

Find trade matches for a user based on offered items, wanted categories, and price compatibility.

Query parameters:

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `limit` | integer | no | Default `10`, min `1`, max `50` |

Request body:

```json
{
  "item_ids": [
    "33333333-3333-3333-3333-333333333333"
  ],
  "category": "electronics",
  "name": "calculator",
  "condition": "good"
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `item_ids` | array of strings | yes | Must contain at least one item ID |
| `category` | string or null | no | Desired category filter |
| `name` | string or null | no | Partial item name search |
| `condition` | string or null | no | Minimum condition filter |

Example response:

```json
[
  {
    "other_user_id": "22222222-2222-2222-2222-222222222222",
    "other_user_name": "Sam",
    "other_item_id": "44444444-4444-4444-4444-444444444444",
    "other_item_name": "Nintendo Switch",
    "other_item_category": "electronics",
    "other_item_condition": "good",
    "other_item_price": 180,
    "my_offer_item_id": "33333333-3333-3333-3333-333333333333",
    "my_offer_item_name": "TI-84 Plus",
    "my_offer_item_price": 160,
    "price_diff": 20,
    "who_pays": "11111111-1111-1111-1111-111111111111"
  }
]
```

### `POST /match/{user_id}/auto-deal`

Agent-driven trade: automatically discover the user's full item collection, find the best mutual match (other user has what I want AND wants what I have), create the deal, create a chatroom, and run AI negotiation — all in one call. The user only provides their ID.

Request body:

```json
{
  "category": "electronics",
  "condition": "good"
}
```

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `category` | string or null | no | Filter to a specific wanted category |
| `condition` | string or null | no | Minimum item condition filter |

The agent automatically:
1. Fetches all items owned by the user (their collection from `items` table).
2. Excludes items already in active deals.
3. Reads the user's wanted categories from `user_categories`.
4. Finds other users whose items match what the user wants AND who want what the user has.
5. Ranks by smallest price difference within `max_cash_amt` / `max_cash_pct`.
6. Creates a deal with the best match, opens a chatroom, and runs AI negotiation.
7. Returns the result so the user can **accept**, **decline**, or **counter**.

Request fields: same as `POST /match/{user_id}`.

Example response:

```json
{
  "selected_match": {
    "other_user_id": "22222222-2222-2222-2222-222222222222",
    "other_user_name": "Sam",
    "other_item_id": "44444444-4444-4444-4444-444444444444",
    "other_item_name": "Nintendo Switch",
    "other_item_category": "electronics",
    "other_item_condition": "good",
    "other_item_price": 180,
    "my_offer_item_id": "33333333-3333-3333-3333-333333333333",
    "my_offer_item_name": "TI-84 Plus",
    "my_offer_item_price": 160,
    "price_diff": 20,
    "who_pays": "11111111-1111-1111-1111-111111111111"
  },
  "deal": {
    "id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce",
    "user1_id": "11111111-1111-1111-1111-111111111111",
    "user2_id": "22222222-2222-2222-2222-222222222222",
    "user1_item_id": "33333333-3333-3333-3333-333333333333",
    "user2_item_id": "44444444-4444-4444-4444-444444444444",
    "cash_difference": 20,
    "payer_id": "11111111-1111-1111-1111-111111111111",
    "status": "negotiating",
    "created_at": "2026-04-05T12:00:00.000000+00:00"
  },
  "chatroom": {
    "id": "8b4bc4a2-4d17-4af7-bab4-b8e99785db6d",
    "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce"
  },
  "negotiation": {
    "logs": [
      {
        "agent": "agent_11111111",
        "content": "Offer: $20.00 paid by 11111111... | Opening offer based on value difference",
        "step": 1
      }
    ],
    "result": {
      "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce",
      "status": "accepted",
      "final_cash_difference": 20,
      "final_payer_id": "11111111-1111-1111-1111-111111111111",
      "total_steps": 3
    }
  },
  "next_actions": [
    "accept",
    "decline",
    "counter"
  ]
}
```

Notes:

- The best match is the first ranked result from the standard matching flow.
- The created deal stays in `negotiating` when the agents reach terms and is then waiting for a user decision.
- If the agents reject the deal, the returned deal status will be `declined` and `next_actions` will suggest another search.

## Negotiation

Base path: `/negotiate`

### `POST /negotiate`

Start AI-driven negotiation for a deal.

Request body:

```json
{
  "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce"
}
```

Success response: `200 OK`

Example response:

```json
{
  "logs": [
    {
      "agent": "agent_11111111",
      "content": "Offer: $20.00 paid by 11111111... | Opening offer based on value difference",
      "step": 1
    }
  ],
  "result": {
    "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce",
    "status": "accepted",
    "final_cash_difference": 20,
    "final_payer_id": "11111111-1111-1111-1111-111111111111",
    "total_steps": 3
  }
}
```

### `GET /negotiate/{deal_id}/logs`

Get persisted negotiation logs for a deal.

Example response:

```json
[
  {
    "id": "97a4f2ad-40c0-4b96-b6d5-05d7df7575de",
    "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce",
    "agent": "agent_11111111",
    "content": "Offer: $20.00 paid by 11111111... | Opening offer based on value difference",
    "step": 1,
    "created_at": "2026-04-04T18:50:00.000000+00:00"
  }
]
```

### `POST /negotiate/{deal_id}/confirm`

Confirm a negotiated deal.

Success response:

```json
{
  "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce",
  "status": "accepted"
}
```

### `POST /negotiate/{deal_id}/decline`

Decline a negotiated deal.

Success response:

```json
{
  "deal_id": "d4b95a18-9d58-45d2-a6bd-816fc1a1c6ce",
  "status": "declined"
}
```

### `POST /negotiate/{deal_id}/counter`

Counter a negotiated deal and rerun negotiation.

Request body:

```json
{
  "cash_difference": 15,
  "payer_id": "11111111-1111-1111-1111-111111111111"
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `cash_difference` | number | yes | Must be `>= 0` |
| `payer_id` | string | yes | User who pays the counter amount |

Success response: `200 OK`

Response body: same shape as `POST /negotiate`.

## Notes

- Trailing slash behavior matters on endpoints explicitly declared with `/`, such as `/items/` and `/deals/`.
- User, item, and deal IDs are treated as string UUIDs throughout the API.
- The negotiation and pricing flows depend on external services and may return `502 external_service_error` if those providers fail.