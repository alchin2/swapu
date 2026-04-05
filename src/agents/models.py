from pydantic import BaseModel


class NegotiationMove(BaseModel):
    """A single negotiation move returned by an ASI1 agent."""
    action: str  # "offer" | "accept" | "reject" | "counter"
    cash_difference: float
    payer_id: str  # user_id of who pays
    reasoning: str  # agent's explanation
