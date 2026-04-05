"""
ASI1-powered negotiation for trades.

Two LLM agents (one per user) negotiate the cash_difference for a deal
using the ASI1 chat completions API (OpenAI-compatible).
Each agent knows its user's constraints and haggles hard over multiple rounds.
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
ASI1_KEY = os.getenv("ASI1_API_KEY") or os.getenv("FETCH")
MAX_ROUNDS = 8
# Agents must bargain at least this many rounds before accepting
MIN_ROUNDS_BEFORE_ACCEPT = 4

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
                "message": {
                    "type": "string",
                    "description": "A short conversational message to the other agent (1-2 sentences, like a real person negotiating)",
                },
            },
            "required": ["action", "cash_difference", "payer_id", "reasoning", "message"],
        },
    },
}


@dataclass
class UserContext:
    user_id: str
    item_price: float
    max_cash_amt: float
    max_cash_pct: float


def _build_system_prompt(user: UserContext, opponent: UserContext, role: str, personality: str) -> str:
    max_from_pct = user.item_price * (user.max_cash_pct / 100.0)
    max_willing = min(user.max_cash_amt, max_from_pct) if user.max_cash_pct > 0 else user.max_cash_amt

    price_diff = abs(user.item_price - opponent.item_price)
    user_has_cheaper = user.item_price < opponent.item_price

    if user_has_cheaper:
        fair_cash = price_diff
        position = (
            f"Your item is worth LESS (${user.item_price:.2f} vs ${opponent.item_price:.2f}), "
            f"so you would need to add cash. The raw difference is ${price_diff:.2f}.\n"
            f"YOUR GOAL: Minimize the cash YOU pay. Start by offering significantly less than "
            f"the price difference — try to pay as little as possible. Argue your item has "
            f"extra value (sentimental, rare, good condition, etc). Concede slowly."
        )
    else:
        fair_cash = price_diff
        position = (
            f"Your item is worth MORE (${user.item_price:.2f} vs ${opponent.item_price:.2f}), "
            f"so the opponent should add cash. The raw difference is ${price_diff:.2f}.\n"
            f"YOUR GOAL: Maximize the cash the OPPONENT pays you. Start by demanding MORE than "
            f"the price difference — argue your item has extra value. Only concede gradually "
            f"when the opponent pushes back. Hold firm for at least a few rounds."
        )

    return (
        f"You are a savvy negotiation agent acting for user {user.user_id}.\n"
        f"Personality: {personality}\n\n"
        f"TRADE SITUATION:\n"
        f"  Your item: ${user.item_price:.2f}\n"
        f"  Their item: ${opponent.item_price:.2f}\n"
        f"  Price gap: ${price_diff:.2f}\n\n"
        f"POSITION:\n{position}\n\n"
        f"HARD CONSTRAINTS:\n"
        f"- You MUST NOT agree to pay more than ${max_willing:.2f} in cash.\n"
        f"- If a deal would require you to pay more than your limit, REJECT it.\n\n"
        f"NEGOTIATION STRATEGY:\n"
        f"- You are {role}.\n"
        f"- Be assertive! Don't cave in easily. Push for a better deal.\n"
        f"- In early rounds, DO NOT accept. Always counter with a better offer for your side.\n"
        f"- Only consider accepting after round 4+ if the offer is reasonable.\n"
        f"- When countering, move your offer only slightly toward the middle each time.\n"
        f"- Use persuasive arguments: item condition, market value, rarity, demand.\n"
        f"- Your 'message' should sound like a real person haggling — be conversational.\n\n"
        f"IDs:\n"
        f"  Your user_id: {user.user_id}\n"
        f"  Opponent user_id: {opponent.user_id}\n"
        f"  Set payer_id to whoever pays the cash.\n"
    )


PERSONALITIES = [
    "Shrewd and calculating. You always point out flaws in the other side's position. You love a good deal and won't settle for less than you deserve. You use phrases like 'Look, let's be real here...' and 'I think we both know...'",
    "Friendly but firm. You're polite but you drive a hard bargain. You compliment the other item but always steer back to why your offer is fair. You say things like 'I appreciate that, but...' and 'How about we meet closer to...'",
]


def _call_asi1(messages: list) -> dict:
    """Call ASI1 chat completions API and return parsed JSON move."""
    if not ASI1_KEY:
        raise RuntimeError("ASI1_API_KEY is not configured.")
    headers = {
        "Authorization": f"Bearer {ASI1_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "asi1",
        "messages": messages,
        "response_format": RESPONSE_FORMAT,
        "temperature": 0.7,
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

    # Build system prompts with distinct personalities
    sys1 = _build_system_prompt(user1, user2, "Agent 1 (opening negotiator)", PERSONALITIES[0])
    sys2 = _build_system_prompt(user2, user1, "Agent 2 (responding negotiator)", PERSONALITIES[1])

    # Conversation histories for each agent
    history1 = [{"role": "system", "content": sys1}]
    history2 = [{"role": "system", "content": sys2}]

    # Step 1: Agent 1 makes opening offer
    history1.append({
        "role": "user",
        "content": (
            "Make your OPENING offer for this trade. Remember, you're a tough negotiator — "
            "start with an aggressive offer that favors YOUR side. Don't start near the fair "
            "price; leave room to negotiate. Use action 'offer'. Write a short conversational "
            "'message' like you're talking to the other trader."
        ),
    })

    move1 = _call_asi1(history1)
    logger.info("[Round 1] Agent1 opening: %s", json.dumps(move1))
    history1.append({"role": "assistant", "content": json.dumps(move1)})

    log_entry = {
        "action": move1["action"],
        "cash_difference": move1["cash_difference"],
        "payer_id": move1["payer_id"],
        "reasoning": move1["reasoning"],
        "message": move1.get("message", ""),
    }
    logs.append({
        "agent": f"agent_{user1.user_id[:8]}",
        "content": json.dumps(log_entry),
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
            current_history = history2
            current_user = user2
            agent_label = f"agent_{user2.user_id[:8]}"
        else:
            current_history = history1
            current_user = user1
            agent_label = f"agent_{user1.user_id[:8]}"

        # Feed the last move to the current agent
        prompt = (
            f"The opponent's latest move:\n"
            f"  Action: {last_move['action']}\n"
            f"  Proposed cash: ${last_move['cash_difference']:.2f}\n"
            f"  Payer: {last_move['payer_id'][:8]}...\n"
            f"  They said: \"{last_move.get('message', last_move.get('reasoning', ''))}\"\n\n"
            f"Round {round_num} of {MAX_ROUNDS}. "
        )

        if round_num < MIN_ROUNDS_BEFORE_ACCEPT:
            prompt += (
                "It's still EARLY in negotiation. DO NOT accept yet — you should 'counter' "
                "with a better deal for your side. Push back on their offer. Be persuasive."
            )
        elif round_num == MAX_ROUNDS:
            prompt += (
                "This is the FINAL round. You must decide: 'accept' the current offer if "
                "it's within your limits, or 'reject' if you can't agree. No more counters."
            )
        elif round_num >= MIN_ROUNDS_BEFORE_ACCEPT:
            prompt += (
                "You've been going back and forth. You MAY 'accept' if the offer is "
                "reasonable, or 'counter' one more time to try to squeeze out a better deal. "
                "Consider whether continuing to push will help."
            )

        prompt += " Include a conversational 'message'."

        current_history.append({"role": "user", "content": prompt})
        move = _call_asi1(current_history)

        # Force counter in early rounds if agent tries to accept too soon
        if move["action"] == "accept" and round_num < MIN_ROUNDS_BEFORE_ACCEPT:
            logger.info("[Round %d] Agent tried to accept too early, forcing counter", round_num)
            move["action"] = "counter"
            move["message"] = move.get("message", "") + " ...but let me think about that a bit more."

        logger.info("[Round %d] %s: %s", round_num, agent_label, json.dumps(move))
        current_history.append({"role": "assistant", "content": json.dumps(move)})

        log_entry = {
            "action": move["action"],
            "cash_difference": move["cash_difference"],
            "payer_id": move["payer_id"],
            "reasoning": move["reasoning"],
            "message": move.get("message", ""),
        }
        logs.append({
            "agent": agent_label,
            "content": json.dumps(log_entry),
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
