import logging
from typing import Literal
from pydantic import BaseModel, ValidationError
from browser_use_sdk.v3 import AsyncBrowserUse
from service.items_service import ItemService

logger = logging.getLogger(__name__)

CategoryType = Literal[
    'textbooks', 'iclicker', 'lab_supplies', 'dining_dollars', 
    'electronics', 'dorm_essentials', 'clothing', 'trading_cards', 
    'games', 'instruments', 'art_supplies', 'sports_equipment', 
    'transport', 'tickets', 'other'
]

class PricingResult(BaseModel):
    average_price: float
    category: CategoryType
    confidence_score: float

class PricingAgent:
    def __init__(self):
        self.client = AsyncBrowserUse()
        self.item_service = ItemService()

    async def get_aggregated_price_and_category(self, item_id: str, item_name: str, item_condition: str):
        """
        Runs the Browser Use agent in the background to scrape multiple platforms,
        determines average price and category, and updates the database.
        """
        logger.info(f"Starting pricing agent for item: {item_name} (ID: {item_id}, Condition: {item_condition})")
        
        task_prompt = f"""
        Search for the item '{item_name}' across multiple platforms including eBay, Facebook Marketplace, Craigslist, and Amazon.
        First, determine the average price of this item based on the listings you find for items in similar condition (Condition/Quality: '{item_condition}'). We will call this the average_price.
        Second, find the price of a BRAND NEW version of this exact same item. This is the new_price.
        Determine the most appropriate category for this item from this specific list: textbooks, iclicker, lab_supplies, dining_dollars, electronics, dorm_essentials, clothing, trading_cards, games, instruments, art_supplies, sports_equipment, transport, tickets, other.
        Provide a confidence_score between 0.0 and 1.0 based on how consistently you found this item and its price across these platforms.
        
        CRITICAL: Your final output MUST be exactly in valid JSON format like this, with NO backticks or markdown or text outside it:
        {{"average_price": 12.50, "new_price": 25.00, "category": "electronics", "confidence_score": 0.85}}
        """
        
        try:
            import json
            result = await self.client.run(
                task=task_prompt,
                model="bu-max"
            )
            
            # The result.output will be a string. Strip potential markdown backticks that the LLM might have added.
            clean_output = result.output[result.output.find('{'):result.output.rfind('}')+1]
            pricing_data = json.loads(clean_output)
            
            logger.info(f"Successfully parsed JSON output: {pricing_data}")
            
            # Calculate final price using the formula
            predicted_price = float(pricing_data.get("average_price", 0.0))
            new_price = float(pricing_data.get("new_price", predicted_price))
            confidence_score = float(pricing_data.get("confidence_score", 0.0))
            
            # Apply condition multiplier
            condition_lower = item_condition.lower()
            if condition_lower == 'good':
                multiplier = 0.9
            elif condition_lower == 'fair':
                multiplier = 0.7
            elif condition_lower == 'poor':
                multiplier = 0.5
            else:
                multiplier = 1.0 # Default fallback
                
            final_price = (predicted_price * confidence_score) + (new_price * multiplier * (1 - confidence_score))
            final_price = round(final_price, 2)
            
            # Prepare data to update in Supabase
            update_data = {
                "price": final_price,
                "category": pricing_data.get("category", "other"),
                "confidence_score": confidence_score
            }
            
            # Update item in the database
            self.item_service.update_item(item_id, update_data)
            logger.info(f"Successfully updated item {item_id} in database with final price {final_price}.")
            
            # Print to terminal directly as requested
            print(f"\n====================================")
            print(f"🎉 NEW PRICE PREDICTION ADDED TO DB:")
            print(f"Predicted Price (from condition): ${predicted_price:.2f}")
            print(f"Brand New Price: ${new_price:.2f}")
            print(f"Confidence Score: {confidence_score}")
            print(f"Condition Multiplier: {multiplier} ({item_condition})")
            print(f"FINAL CALCULATED PRICE: ${final_price:.2f}")
            print(f"Category: {pricing_data.get('category', 'other')}")
            print(f"====================================\n")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from agent output (Raw output might be an error like 'Task ended unexpectedly'): {e} | Raw output: {result.output}")
        except Exception as e:
            logger.error(f"Error running pricing agent for item {item_id}: {str(e)}")

# Create a singleton instance to be used across the app
pricing_agent = PricingAgent()
