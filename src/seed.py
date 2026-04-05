"""Seed test data for the Chat API. Run from src/: python seed.py"""
import sys
sys.path.insert(0, ".")
from database.supabase_client import get_supabase_client

client = get_supabase_client()


def get_or_create_user(email, name, max_cash_amt, max_cash_pct):
    user = client.table("users").select("*").eq("email", email).execute().data
    if user:
        user = user[0]
        client.table("users").update({
            "max_cash_amt": max_cash_amt,
            "max_cash_pct": max_cash_pct,
        }).eq("id", user["id"]).execute()
        user["max_cash_amt"] = max_cash_amt
        user["max_cash_pct"] = max_cash_pct
    else:
        user = client.table("users").insert({
            "email": email,
            "name": name,
            "max_cash_amt": max_cash_amt,
            "max_cash_pct": max_cash_pct,
        }).execute().data[0]
    return user


# 1. Users
alice = get_or_create_user("alice@test.com", "Alice", 80.00, 40.00)
print(f"Alice:   {alice['id']}  (max_cash=$80, max_pct=40%)")

bob = get_or_create_user("bob@test.com", "Bob", 100.00, 50.00)
print(f"Bob:     {bob['id']}  (max_cash=$100, max_pct=50%)")

charlie = get_or_create_user("charlie@test.com", "Charlie", 60.00, 35.00)
print(f"Charlie: {charlie['id']}  (max_cash=$60, max_pct=35%)")

# 2. Items — varied categories for mutual matching
ps5_controller = client.table("items").insert({
    "owner_id": alice["id"],
    "name": "PS5 DualSense Controller",
    "category": "Gaming",
    "condition": "good",
    "price": 50.00,
    "confidence_score": 0.92,
    "image_url": "https://placehold.co/400x300?text=PS5+Controller",
}).execute().data[0]
print(f"PS5 Controller (Alice, Gaming):  {ps5_controller['id']}  ($50)")

airpods = client.table("items").insert({
    "owner_id": bob["id"],
    "name": "AirPods Pro 2nd Gen",
    "category": "Electronics",
    "condition": "good",
    "price": 120.00,
    "confidence_score": 0.88,
    "image_url": "https://placehold.co/400x300?text=AirPods+Pro",
}).execute().data[0]
print(f"AirPods Pro (Bob, Electronics):  {airpods['id']}  ($120)")

yoga_mat = client.table("items").insert({
    "owner_id": charlie["id"],
    "name": "Lululemon Yoga Mat",
    "category": "Sports",
    "condition": "like_new",
    "price": 80.00,
    "confidence_score": 0.95,
    "image_url": "https://placehold.co/400x300?text=Yoga+Mat",
}).execute().data[0]
print(f"Yoga Mat (Charlie, Sports):      {yoga_mat['id']}  ($80)")

# 3. User categories — what each user WANTS
# Alice has Gaming, wants Electronics,Books
# Bob has Electronics, wants Gaming,Sports
# Charlie has Sports, wants Electronics,Gaming
# Mutual matches: Alice<->Bob (Gaming<->Electronics), Bob<->Charlie (Electronics<->Sports)
try:
    client.table("user_categories").insert([
        {"user_id": alice["id"], "category": "Electronics,Books"},
        {"user_id": bob["id"], "category": "Gaming,Sports"},
        {"user_id": charlie["id"], "category": "Electronics,Gaming"},
    ]).execute()
    print("User categories created")
except Exception:
    print("User categories already exist, skipping")

# 4. Create a deal — Alice's PS5 Controller ($50) vs Bob's AirPods ($120)
deal = client.table("deals").insert({
    "user1_id": alice["id"],
    "user2_id": bob["id"],
    "user1_item_id": ps5_controller["id"],
    "user2_item_id": airpods["id"],
    "cash_difference": 70.00,
    "payer_id": alice["id"],
    "status": "pending",
}).execute().data[0]
print(f"\nDeal:  {deal['id']}  (Alice<->Bob, $70 diff, pending)")

print("\n--- Test Commands ---")
print(f"# Matching")
print(f"GET  /match/{alice['id']}/{ps5_controller['id']}")
print(f"GET  /match/{bob['id']}/{airpods['id']}")
print(f"GET  /match/{charlie['id']}/{yoga_mat['id']}")
print(f"\n# Negotiation")
print(f'POST /negotiate          body: {{"deal_id": "{deal["id"]}"}}')
print(f"GET  /negotiate/{deal['id']}/logs")
print(f"POST /negotiate/{deal['id']}/confirm")
print(f"POST /negotiate/{deal['id']}/decline")
print(f'POST /negotiate/{deal["id"]}/counter  body: {{"cash_difference": 50, "payer_id": "{alice["id"]}"}}')
print(f"\n# Users")
print(f"Alice:   {alice['id']}")
print(f"Bob:     {bob['id']}")
print(f"Charlie: {charlie['id']}")
