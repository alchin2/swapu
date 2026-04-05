import asyncio
import logging
import os
from dotenv import load_dotenv

# Ensure we see the Agent's log messages in the terminal
logging.basicConfig(level=logging.INFO)

# Load the API key from .env and force override to ignore stale bash history
load_dotenv(override=True)

from agents.pricing_agent import PricingAgent

async def test_agent():
    # Make sure API key is loaded
    if not os.getenv("BROWSER_USE_API_KEY"):
        print("ERROR: BROWSER_USE_API_KEY is missing from your .env file!")
        return

    print("Initializing Pricing Agent...")
    agent = PricingAgent()
    
    # 1. Mock the ItemService so this test script doesn't try to save to your real Supabase Database
    class MockItemService:
        def update_item(self, item_id, update_data):
            print(f"\n[✅ MOCK DB SAVE SUCCESS] Item {item_id} updated with:")
            for key, value in update_data.items():
                print(f"  - {key}: {value}")
            
    agent.item_service = MockItemService()
    
    # 2. Setup your test data here
    test_id = "test-id-12345"
    test_name = "Nintendo Switch OLED Model"
    test_condition = "fair"
    
    print(f"\n🔍 Sending Agent to search for: '{test_name}' (Condition: {test_condition})")
    print("⏳ This usually takes 30-60 seconds. Sit tight...\n")
    
    # 3. Run the agent
    await agent.get_aggregated_price_and_category(test_id, test_name, test_condition)
    
    print("\n🏁 Agent test completed!")


if __name__ == "__main__":
    # Suppress HTTP Request logs from httpx so the terminal isn't too spammy
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    asyncio.run(test_agent())
