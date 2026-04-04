"""Seed test data for the Chat API. Run from src/: python seed.py"""
import sys
sys.path.insert(0, ".")
from database.supabase_client import get_supabase_client

client = get_supabase_client()

# 1. Get or create users
alice = client.table("users").select("*").eq("email", "alice@test.com").execute().data
if alice:
    alice = alice[0]
else:
    alice = client.table("users").insert({
        "email": "alice@test.com",
        "name": "Alice",
        "max_cash_amt": 50.00,
        "max_cash_pct": 20.00,
    }).execute().data[0]
print(f"Alice: {alice['id']}")

bob = client.table("users").select("*").eq("email", "bob@test.com").execute().data
if bob:
    bob = bob[0]
else:
    bob = client.table("users").insert({
        "email": "bob@test.com",
        "name": "Bob",
        "max_cash_amt": 100.00,
        "max_cash_pct": 30.00,
    }).execute().data[0]
print(f"Bob:   {bob['id']}")

# 2. Create items
switch = client.table("items").insert({
    "owner_id": alice["id"],
    "name": "Nintendo Switch",
    "category": "Electronics",
    "condition": "good",
    "price": 200.00,
    "confidence_score": 0.95,
    "image_url": "https://placehold.co/400x300?text=Nintendo+Switch",
}).execute().data[0]
print(f"Nintendo Switch: {switch['id']}")

macbook = client.table("items").insert({
    "owner_id": bob["id"],
    "name": "MacBook Air M1",
    "category": "Electronics",
    "condition": "fair",
    "price": 500.00,
    "confidence_score": 0.90,
    "image_url": "https://placehold.co/400x300?text=MacBook+Air+M1",
}).execute().data[0]
print(f"MacBook Air M1:  {macbook['id']}")

# 3. User categories
client.table("user_categories").insert([
    {"user_id": alice["id"], "category": "Electronics"},
    {"user_id": bob["id"], "category": "Electronics"},
]).execute()
print("User categories created")

# 4. Create a deal
deal = client.table("deals").insert({
    "user1_id": alice["id"],
    "user2_id": bob["id"],
    "user1_item_id": switch["id"],
    "user2_item_id": macbook["id"],
    "cash_difference": 300.00,
    "payer_id": alice["id"],
    "status": "pending",
}).execute().data[0]
print(f"Deal:  {deal['id']}")

print("\n--- Test the Chat API ---")
print(f'POST /chatrooms  body: {{"deal_id": "{deal["id"]}"}}')
print(f'Alice sender_id: {alice["id"]}')
print(f'Bob   sender_id: {bob["id"]}')
