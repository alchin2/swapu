import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# --- Environment Setup ---
# Load variables from the .env file into os.environ
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing in .env")

# --- Supabase Clients ---
# Standard client (Respects database RLS policies)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Admin client (Bypasses all RLS policies - use with caution!)
if SUPABASE_SERVICE_ROLE_KEY:
    supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
else:
    print("Warning: SUPABASE_SERVICE_ROLE_KEY not found. Admin features may fail.")


router = APIRouter(
    prefix="/deals",
    tags=["Deals"]
)

# --- Pydantic Models ---

class DealBase(BaseModel):
    user1_id: str
    user2_id: str
    user1_item_id: str
    user2_item_id: str
    cash_difference: float = 0.0
    payer_id: Optional[str] = None
    status: str = "pending"

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    status: Optional[str] = None
    cash_difference: Optional[float] = None
    payer_id: Optional[str] = None

class DealResponse(DealBase):
    id: str
    created_at: str

# --- API Endpoints ---

@router.post("/", response_model=DealResponse, status_code=201)
def create_deal(deal: DealCreate):
    """Create a new deal."""
    try:
        # Example using the standard client
        response = supabase.table("deals").insert(deal.model_dump()).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create deal")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{deal_id}", response_model=DealResponse)
def get_deal(deal_id: str):
    """Fetch a specific deal by ID."""
    response = supabase.table("deals").select("*").eq("id", deal_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Deal not found")
    return response.data[0]

@router.get("/user/{user_id}", response_model=List[DealResponse])
def get_user_deals(user_id: str):
    """Fetch all deals involving a specific user."""
    response = supabase.table("deals").select("*").or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}").execute()
    return response.data

@router.patch("/{deal_id}", response_model=DealResponse)
def update_deal(deal_id: str, deal_update: DealUpdate):
    """Update a deal. Example using the admin client to bypass RLS."""
    update_data = deal_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    # If you have strict RLS that prevents users from updating certain fields, 
    # but the backend API is authorized to do so, use supabase_admin here:
    response = supabase_admin.table("deals").update(update_data).eq("id", deal_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Deal not found or update failed")
    return response.data[0]

@router.delete("/{deal_id}", status_code=204)
def delete_deal(deal_id: str):
    """Delete a deal."""
    response = supabase.table("deals").delete().eq("id", deal_id).execute()
    if not response.data:
         raise HTTPException(status_code=404, detail="Deal not found")
    return None