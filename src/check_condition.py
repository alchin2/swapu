from database.supabase_client import get_supabase_client

c = get_supabase_client()

# Try common condition values
for val in ["new", "like_new", "good", "fair", "poor", "New", "Like New", "Good", "Fair", "Poor"]:
    try:
        r = c.table("items").insert({
            "owner_id": "11111111-1111-1111-1111-111111111111",
            "name": "test",
            "category": "test",
            "condition": val,
            "price": 1.00,
            "confidence_score": 0.5
        }).execute()
        print(f"'{val}' -> ACCEPTED (id={r.data[0]['id']})")
        # Clean up
        c.table("items").delete().eq("id", r.data[0]["id"]).execute()
        break
    except Exception as e:
        err = str(e)
        if "items_condition_check" in err:
            print(f"'{val}' -> rejected")
        else:
            print(f"'{val}' -> other error: {err}")
            break
