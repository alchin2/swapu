# Database Schema

Supabase (PostgreSQL). All primary keys are `uuid` with `gen_random_uuid()` default.

```sql
-- ============================================================
-- Users
-- ============================================================
CREATE TABLE users (
    id            uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    email         text        NOT NULL UNIQUE,
    name          text,
    password_hash text,                          -- bcrypt hash, NULL for legacy users
    max_cash_amt  numeric,                       -- max absolute cash a user will pay on a trade
    max_cash_pct  numeric,                       -- max cash as % of item price (0-100)
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- Items  (a user's collection — things they own / offer)
-- ============================================================
CREATE TABLE items (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id         uuid        NOT NULL REFERENCES users(id),
    name             text        NOT NULL,
    category         text        NOT NULL,
    condition        text,                      -- like_new | good | fair | poor
    price            numeric     NOT NULL,
    confidence_score numeric,                   -- 0-1 pricing confidence from agent
    image_url        text,                      -- comma-separated URLs stored as text
    created_at       timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- User Categories  (what a user WANTS to receive)
-- ============================================================
CREATE TABLE user_categories (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid        NOT NULL REFERENCES users(id),
    category    text        NOT NULL             -- comma-separated wanted categories
);

-- ============================================================
-- Deals
-- ============================================================
CREATE TABLE deals (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user1_id        uuid        NOT NULL REFERENCES users(id),
    user2_id        uuid        NOT NULL REFERENCES users(id),
    user1_item_id   uuid        NOT NULL REFERENCES items(id),
    user2_item_id   uuid        NOT NULL REFERENCES items(id),
    cash_difference numeric     NOT NULL DEFAULT 0,
    payer_id        uuid        REFERENCES users(id),
    status          text        NOT NULL DEFAULT 'pending',  -- pending | negotiating | accepted | declined
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- Chatrooms  (one per deal)
-- ============================================================
CREATE TABLE chatrooms (
    id      uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id uuid    NOT NULL UNIQUE REFERENCES deals(id)
);

-- ============================================================
-- Messages
-- ============================================================
CREATE TABLE messages (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    chatroom_id uuid        NOT NULL REFERENCES chatrooms(id),
    sender_id   uuid        NOT NULL REFERENCES users(id),
    content     text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- Negotiation Logs  (agent conversation steps)
-- ============================================================
CREATE TABLE neg_logs (
    id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id    uuid        NOT NULL REFERENCES deals(id),
    agent      text        NOT NULL,
    content    text        NOT NULL,
    step       int4        NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

## Relationships

| FK | From | To |
|----|------|----|
| `items.owner_id` | items | users |
| `user_categories.user_id` | user_categories | users |
| `deals.user1_id` | deals | users |
| `deals.user2_id` | deals | users |
| `deals.user1_item_id` | deals | items |
| `deals.user2_item_id` | deals | items |
| `deals.payer_id` | deals | users |
| `chatrooms.deal_id` | chatrooms | deals |
| `messages.chatroom_id` | messages | chatrooms |
| `messages.sender_id` | messages | users |
| `neg_logs.deal_id` | neg_logs | deals |
