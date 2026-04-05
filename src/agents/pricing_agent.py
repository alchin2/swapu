import logging
import os
import asyncio
from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

try:
    from browser_use_sdk.v3 import AsyncBrowserUse
except ImportError:  # pragma: no cover - optional dependency in local dev
    AsyncBrowserUse = None

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
        # Browser Use client — pass API key from BROWSER_USE env var
        self.client = None
        if AsyncBrowserUse is not None:
            api_key = os.getenv("BROWSER_USE")
            if api_key:
                try:
                    self.client = AsyncBrowserUse(api_key=api_key, timeout=120.0)
                except Exception as e:
                    logger.error("Failed to init Browser Use client: %s", e)
        self.item_service = ItemService()
        self.allowed_categories = [
            'textbooks', 'iclicker', 'lab_supplies', 'dining_dollars',
            'electronics', 'dorm_essentials', 'clothing', 'trading_cards',
            'games', 'instruments', 'art_supplies', 'sports_equipment',
            'transport', 'tickets', 'other'
        ]
        # Concurrency and spacing controls to avoid overwhelming the Browser Use infrastructure
        try:
            self.concurrency = int(os.getenv("PRICING_AGENT_CONCURRENCY", "10"))
        except Exception:
            self.concurrency = 10
        try:
            self.delay_seconds = float(os.getenv("PRICING_AGENT_DELAY_SECONDS", "0.1"))
        except Exception:
            self.delay_seconds = 1.0
        # Semaphore to limit concurrent BrowserUse runs
        self._semaphore = asyncio.Semaphore(self.concurrency)

    async def get_aggregated_price_and_category(self, item_id: str, item_name: str, item_condition: str, input_price: float = 0.0):
        """
        Runs the Browser Use agent in the background to scrape multiple platforms,
        determines average price and category, and updates the database.
        Implements fallback for reliability (no timeout).
        """
        logger.info(f"Starting pricing agent for item: {item_name} (ID: {item_id}, Condition: {item_condition})")

        # Limit concurrency and optionally add a small delay before each run to space requests
        async with self._semaphore:
            if self.delay_seconds and self.delay_seconds > 0:
                logger.debug(f"Delaying pricing run for {self.delay_seconds}s to space out BrowserUse tasks")
                await asyncio.sleep(self.delay_seconds)

            if self.client is None:
                logger.warning("browser_use_sdk is not installed. Falling back to the provided item price.")
                pricing_data = {
                    "average_price": input_price if input_price is not None else 10.0,
                    "new_price": input_price if input_price is not None else 10.0,
                    "category": "other",
                    "confidence_score": 0.0,
                }
            else:
                task_prompt = f"""
                Search for the item '{item_name}' across multiple platforms including eBay, Facebook Marketplace, Craigslist, and Amazon.
                First, determine the average price of this item based on the listings you find for items in similar condition (Condition/Quality: '{item_condition}'). We will call this the average_price.
                Second, find the price of a BRAND NEW version of this exact same item. This is the new_price.
                You MUST categorize the item into ONE of these categories (no exceptions, do not invent new categories): textbooks, iclicker, lab_supplies, dining_dollars, electronics, dorm_essentials, clothing, trading_cards, games, instruments, art_supplies, sports_equipment, transport, tickets, other.
                Provide a confidence_score between 0.0 and 1.0 based on how consistently you found this item and its price across these platforms.

                CRITICAL: Your final output MUST be exactly in valid JSON format like this, with NO backticks or markdown or text outside it:
                {{"average_price": 12.50, "new_price": 25.00, "category": "electronics", "confidence_score": 0.85}}
                """

                import json

                pricing_data = None
                result = None
                try:
                    result = await self.client.run(task=task_prompt, model="bu-max")
                    output = result.final_result() if hasattr(result, 'final_result') else getattr(result, 'output', '')
                    
                    if isinstance(output, str):
                        start_idx = output.find('{')
                        end_idx = output.rfind('}')
                        if start_idx != -1 and end_idx != -1:
                            clean_output = output[start_idx:end_idx + 1]
                            pricing_data = json.loads(clean_output)
                        else:
                            raise ValueError(f"No JSON brackets found in output: {output}")
                    elif isinstance(output, dict):
                        pricing_data = output
                    else:
                         raise ValueError(f"Unexpected type for output: {type(output)}")
                        
                    logger.info(f"Successfully parsed JSON output: {pricing_data}")
                except Exception as e:
                    logger.error(f"Pricing agent failed: {e}. Using fallback.")
                    fallback_price = input_price if input_price is not None else 10.0
                    pricing_data = {
                        "average_price": fallback_price,
                        "new_price": fallback_price,
                        "category": "other",
                        "confidence_score": 0.0,
                    }
        # --- Post-processing ---
        predicted_price = float(pricing_data.get("average_price", 0.0))
        new_price = float(pricing_data.get("new_price", predicted_price))
        confidence_score = float(pricing_data.get("confidence_score", 0.0))
        category = pricing_data.get("category", "other")
        # Strict category enforcement
        if category not in self.allowed_categories:
            logger.warning(f"Unrecognized category '{category}', defaulting to 'other'.")
            category = "other"
        # Condition multiplier
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
        # Price safety logic
        final_price = max(round(final_price, 2), 1.00)
        update_data = {
            "price": final_price,
            "category": category,
            "confidence_score": confidence_score
        }
        try:
            self.item_service.update_item(item_id, update_data)
            logger.info(f"Successfully updated item {item_id} in database with final price {final_price}.")
        except Exception as e:
            logger.error(f"Failed to update item {item_id} in database: {e}")
        logger.info(
            "Pricing completed for item=%s predicted=%.2f new=%.2f confidence=%.2f final=%.2f category=%s",
            item_id,
            predicted_price,
            new_price,
            confidence_score,
            final_price,
            category,
        )

# Create a singleton instance to be used across the app
pricing_agent = PricingAgent()
