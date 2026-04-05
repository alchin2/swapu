"""
ASI1-powered negotiation for trades.

Two LLM agents (one per user) negotiate the cash_difference for a deal
using the ASI1 chat completions API (OpenAI-compatible).
Each agent knows its user's constraints and reasons about offers.
"""
import json
import logging
import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ASI1_BASE = "https://api.asi1.ai/v1"
ASI1_KEY = os.getenv("FETCH")
MAX_ROUNDS = 6

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "negotiation_move",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "action": {
                    "type": "string",
                    "description": "One of: offer, accept, reject, counter",
                },
                "cash_difference": {
                    "type": "number",
                    "description": "The cash amount proposed (0 if reject)",
                },
                "payer_id": {
                    "type": "string",
                    "description": "user_id of who pays the cash difference",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of why this move was chosen",
                },
            },
            "required": ["action", "cash_difference", "payer_id", "reasoning"],
        },
    },
}


@dataclass
class UserContext:
    user_id: str
    item_price: float
    max_cash_amt: float
    max_cash_pct: float


def _build_system_prompt(user: UserContext, opponent: UserContext, role: str) -> str:
    max_from_pct = user.item_price * (user.max_cash_pct / 100.0)
    max_willing = min(user.max_cash_amt, max_from_pct)

    return (
        f"You are a negotiation agent acting on behalf of user {user.user_id}.\n"
        f"You are {role} in this trade negotiation.\n\n"
        f"YOUR ITEM: worth ${user.item_price:.2f}\n"
        f"OPPONENT'S ITEM: worth ${opponent.item_price:.2f}\n"
        f"PRICE DIFFERENCE: ${abs(user.item_price - opponent.item_price):.2f}\n\n"
        f"YOUR CONSTRAINTS:\n"
        f"- Max cash you can pay: ${max_willing:.2f}\n"
        f"- Max cash amount setting: ${user.max_cash_amt:.2f}\n"
        f"- Max cash percentage setting: {user.max_cash_pct}%\n\n"
        f"RULES:\n"
        f"- If your item is worth LESS, you may need to pay cash to make up the difference.\n"
        f"- If your item is worth MORE, the opponent should pay you.\n"
        f"- You MUST NOT agree to pay more than ${max_willing:.2f}.\n"
        f"- Try to get a fair deal close to the actual price difference.\n"
        f"- Respond with action: 'offer' (first move), 'accept', 'reject', or 'counter'.\n"
        f"- Set payer_id to the user_id of whoever pays the cash.\n"
        f"  Your user_id: {user.user_id}\n"
        f"  Opponent user_id: {opponent.user_id}\n"
    )


def _call_asi1(messages: list) -> dict:
    """Call ASI1 chat completions API and return parsed JSON move."""
    headers = {
        "Authorization": f"Bearer {ASI1_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "asi1",
        "messages": messages,
        "response_format": RESPONSE_FORMAT,
        "temperature": 0.4,
    }
    logger.info("Calling ASI1 API...")
    resp = requests.post(
        f"{ASI1_BASE}/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    if not resp.ok:
        logger.error("ASI1 API error %s: %s", resp.status_code, resp.text[:500])
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    move = json.loads(content)
    logger.info("ASI1 response: %s", json.dumps(move, indent=2))
    return move


def run_negotiation(
    deal_id: str,
    user1: UserContext,
    user2: UserContext,
) -> dict:
    """
    Run a negotiation between two ASI1 LLM agents.
    Returns negotiation logs and final result.
    """
    logs = []
    logger.info("Starting negotiation for deal %s", deal_id)
    logger.info("User1: %s (item=$%.2f, max_cash=$%.2f, max_pct=%.1f%%)",
                user1.user_id[:8], user1.item_price, user1.max_cash_amt, user1.max_cash_pct)
    logger.info("User2: %s (item=$%.2f, max_cash=$%.2f, max_pct=%.1f%%)",
                user2.user_id[:8], user2.item_price, user2.max_cash_amt, user2.max_cash_pct)

    # Build system prompts
    sys1 = _build_system_prompt(user1, user2, "Agent 1 (opening negotiator)")
    sys2 = _build_system_prompt(user2, user1, "Agent 2 (responding negotiator)")

    # Conversation histories for each agent
    history1 = [{"role": "system", "content": sys1}]
    history2 = [{"role": "system", "content": sys2}]

    # Step 1: Agent 1 makes opening offer
    history1.append({
        "role": "user",
        "content": (
            "Make your opening offer for this trade. "
            "Consider the price difference and your constraints. "
            "Use action 'offer'."
        ),
    })

    move1 = _call_asi1(history1)
    logger.info("[Round 1] Agent1 opening: %s", json.dumps(move1))
    history1.append({"role": "assistant", "content": json.dumps(move1)})
    logs.append({
        "agent": f"agent_{user1.user_id[:8]}",
        "content": f"Offer: ${move1['cash_difference']:.2f} paid by {move1['payer_id'][:8]}... | {move1['reasoning']}",
        "step": 1,
    })

    last_move = move1
    final_status = "rejected"
    final_cash = 0.0
    final_payer = ""
    total_steps = 1

    for round_num in range(2, MAX_ROUNDS + 1):
        # Determine whose turn it is
        if round_num % 2 == 0:
            # Agent 2's turn
            current_history = history2
            other_history = history1
            current_user = user2
            agent_label = f"agent_{user2.user_id[:8]}"
        else:
            # Agent 1's turn
            current_history = history1
            other_history = history2
            current_user = user1
            agent_label = f"agent_{user1.user_id[:8]}"

        # Feed the last move to the current agent
        prompt = (
            f"The opponent's move: {json.dumps(last_move)}\n\n"
            f"Round {round_num}/{MAX_ROUNDS}. "
        )
        if round_num == MAX_ROUNDS:
            prompt += "This is the FINAL round. You must 'accept' or 'reject'."
        else:
            prompt += "Respond with 'accept', 'reject', or 'counter'."

        current_history.append({"role": "user", "content": prompt})
        move = _call_asi1(current_history)
        logger.info("[Round %d] %s: %s", round_num, agent_label, json.dumps(move))
        current_history.append({"role": "assistant", "content": json.dumps(move)})

        logs.append({
            "agent": agent_label,
            "content": f"{move['action'].capitalize()}: ${move['cash_difference']:.2f} paid by {move['payer_id'][:8]}... | {move['reasoning']}",
            "step": round_num,
        })

        total_steps = round_num

        if move["action"] == "accept":
            final_status = "accepted"
            final_cash = last_move["cash_difference"]
            final_payer = last_move["payer_id"]
            break
        elif move["action"] == "reject":
            final_status = "rejected"
            break

        last_move = move

    logger.info("Negotiation complete: status=%s, cash=$%.2f, payer=%s, steps=%d",
                final_status, final_cash, final_payer[:8] if final_payer else "none", total_steps)

    return {
        "logs": logs,
        "result": {
            "deal_id": deal_id,
            "status": final_status,
            "final_cash_difference": final_cash,
            "final_payer_id": final_payer,
            "total_steps": total_steps,
        },
    }
