import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from core.exceptions import NotFoundError, ValidationError
from service.matching_service import MatchingService


def _mock_table(table_name: str, responses: dict):
    """Build a fluent mock for self.client.table(name).select(...)...execute()."""
    table = MagicMock()

    def _execute_data(data):
        ex = MagicMock()
        ex.data = data
        return ex

    chain = table.select.return_value
    # support .eq / .in_ / .neq chaining — always returns same chain
    for method in ("eq", "neq", "in_", "ilike", "single", "order", "limit"):
        getattr(chain, method).return_value = chain
    chain.execute.return_value = _execute_data(responses.get(table_name, []))
    return table


class TestMatchingService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MatchingService()

    @patch("service.matching_service.NegotiationService")
    @patch("service.matching_service.ChatService")
    @patch("service.matching_service.DealService")
    def test_create_best_agent_deal_creates_and_negotiates_top_match(
        self,
        deal_service_cls: MagicMock,
        chat_service_cls: MagicMock,
        negotiation_service_cls: MagicMock,
    ) -> None:
        best_match = {
            "other_user_id": "user-2",
            "other_item_id": "item-2",
            "my_offer_item_id": "item-1",
            "price_diff": 15.0,
            "who_pays": "user-1",
        }
        created_deal = {"id": "deal-1"}
        updated_deal = {
            "id": "deal-1",
            "status": "negotiating",
            "cash_difference": 12.0,
        }
        chatroom = {"id": "chat-1", "deal_id": "deal-1"}
        negotiation = {
            "logs": [{"agent": "agent_user-1", "content": "ok", "step": 1}],
            "result": {
                "deal_id": "deal-1",
                "status": "accepted",
                "final_cash_difference": 12.0,
                "final_payer_id": "user-1",
                "total_steps": 2,
            },
        }

        deal_service = deal_service_cls.return_value
        deal_service.create_deal.return_value = created_deal
        deal_service.get_deal.return_value = updated_deal
        chat_service_cls.return_value.create_chatroom.return_value = chatroom
        negotiation_service_cls.return_value.start_negotiation.return_value = negotiation

        # Mock the DB calls inside create_best_agent_deal:
        #   items table → user's collection
        #   deals table → no active deals
        mock_client = MagicMock()

        def table_router(name):
            if name == "items":
                return _mock_table("items", {"items": [{"id": "item-1"}, {"id": "item-3"}]})
            if name == "deals":
                return _mock_table("deals", {"deals": []})
            return _mock_table(name, {})

        mock_client.table.side_effect = table_router
        self.service._client = mock_client

        with patch.object(self.service, "find_matches", return_value=[best_match]) as find_matches:
            result = self.service.create_best_agent_deal(
                user_id="user-1",
                category="electronics",
                condition="good",
            )

        # find_matches should be called with ALL available item IDs
        find_matches.assert_called_once_with(
            user_id="user-1",
            item_ids=["item-1", "item-3"],
            category="electronics",
            condition="good",
            limit=1,
        )
        deal_service.create_deal.assert_called_once_with(
            {
                "user1_id": "user-1",
                "user2_id": "user-2",
                "user1_item_id": "item-1",
                "user2_item_id": "item-2",
                "cash_difference": 15.0,
                "payer_id": "user-1",
                "status": "pending",
            }
        )
        chat_service_cls.return_value.create_chatroom.assert_called_once_with("deal-1")
        negotiation_service_cls.return_value.start_negotiation.assert_called_once_with("deal-1")
        self.assertEqual(result["selected_match"], best_match)
        self.assertEqual(result["deal"], updated_deal)
        self.assertEqual(result["chatroom"], chatroom)
        self.assertEqual(result["negotiation"], negotiation)
        self.assertEqual(result["next_actions"], ["accept", "decline", "counter"])

    def test_create_best_agent_deal_raises_when_no_items(self) -> None:
        """User has no items in their collection."""
        mock_client = MagicMock()
        mock_client.table.return_value = _mock_table("items", {"items": []})
        self.service._client = mock_client

        with self.assertRaises(ValidationError):
            self.service.create_best_agent_deal(user_id="user-1")

    def test_create_best_agent_deal_raises_when_no_match_exists(self) -> None:
        mock_client = MagicMock()

        def table_router(name):
            if name == "items":
                return _mock_table("items", {"items": [{"id": "item-1"}]})
            if name == "deals":
                return _mock_table("deals", {"deals": []})
            return _mock_table(name, {})

        mock_client.table.side_effect = table_router
        self.service._client = mock_client

        with patch.object(self.service, "find_matches", return_value=[]):
            with self.assertRaises(NotFoundError):
                self.service.create_best_agent_deal(user_id="user-1")


if __name__ == "__main__":
    unittest.main()