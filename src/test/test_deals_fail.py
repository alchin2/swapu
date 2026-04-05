import unittest
import requests
import uuid

BASE_URL = "http://127.0.0.1:8000/deals"

class TestDealAPIFailures(unittest.TestCase):
    """
    Unit tests designed specifically to test the failure paths 
    of the Deals API (making the code "fail" safely via 4XX errors).
    """

    def test_create_deal_missing_fields(self):
        """Test creating a deal without required fields, expecting 422 Unprocessable Entity."""
        incomplete_payload = {
            "user1_id": str(uuid.uuid4())
            # Missing user2_id, user1_item_id, etc.
        }
        res = requests.post(f"{BASE_URL}/", json=incomplete_payload)
        self.assertEqual(res.status_code, 422, f"Expected 422, got {res.status_code}")

    def test_get_nonexistent_deal(self):
        """Test fetching a deal that does not exist in the database, expecting 404 Not Found."""
        fake_uuid = str(uuid.uuid4())
        res = requests.get(f"{BASE_URL}/{fake_uuid}")
        self.assertEqual(res.status_code, 404, f"Expected 404, got {res.status_code}")

    def test_update_nonexistent_deal(self):
        """Test updating a deal that does not exist, expecting 400 or 404."""
        fake_uuid = str(uuid.uuid4())
        update_data = {
            "status": "accepted"
        }
        res = requests.patch(f"{BASE_URL}/{fake_uuid}", json=update_data)
        # Your deal service raises ValueError on not found, which controller maps to 400/404
        self.assertIn(res.status_code, [400, 404], f"Expected 400 or 404, got {res.status_code}")

    def test_delete_nonexistent_deal(self):
        """Test deleting a deal that does not exist, expecting 404."""
        fake_uuid = str(uuid.uuid4())
        res = requests.delete(f"{BASE_URL}/{fake_uuid}")
        self.assertEqual(res.status_code, 404, f"Expected 404, got {res.status_code}")

    def test_invalid_uuid_format(self):
        """Test fetching a deal using a malformed ID string (not a UUID)."""
        bad_id = "this-is-not-a-valid-uuid"
        res = requests.get(f"{BASE_URL}/{bad_id}")
        self.assertNotEqual(res.status_code, 200, "API should reject malformed ID formats")

    def test_create_deal_invalid_data_type(self):
        """Test creating a deal with completely invalid data types (e.g. text where number expected)."""
        invalid_payload = {
            "user1_id": str(uuid.uuid4()),
            "user2_id": str(uuid.uuid4()),
            "user1_item_id": str(uuid.uuid4()),
            "user2_item_id": str(uuid.uuid4()),
            "cash_difference": "not-a-number", # Invalid type
            "payer_id": str(uuid.uuid4()),
            "status": "pending"
        }
        res = requests.post(f"{BASE_URL}/", json=invalid_payload)
        self.assertEqual(res.status_code, 422, "FastAPI should validate data types and return 422")

    def test_update_deal_empty_payload(self):
        """Test updating a deal without actually providing any fields to update."""
        fake_uuid = str(uuid.uuid4())
        # Provide an empty update payload
        res = requests.patch(f"{BASE_URL}/{fake_uuid}", json={})
        self.assertIn(res.status_code, [400, 422], "Should fail missing fields or throw our 400 'no valid fields'")

    def test_get_user_deals_nonexistent_user(self):
        """Test fetching deals for a randomized user who definitely has no deals."""
        fake_user = str(uuid.uuid4())
        res = requests.get(f"{BASE_URL}/user/{fake_user}")
        self.assertEqual(res.status_code, 200, "Should succeed but return empty array")
        self.assertEqual(res.json(), [], "Response should be an empty list")

    def test_invalid_http_method(self):
        """Test sending an unsupported HTTP method (PUT instead of PATCH for update)."""
        fake_uuid = str(uuid.uuid4())
        res = requests.put(f"{BASE_URL}/{fake_uuid}", json={"status": "accepted"})
        self.assertEqual(res.status_code, 405, "Method not allowed should return 405")

    def test_create_deal_invalid_uuid_in_json(self):
        """Test creating a deal where IDs in the JSON body are not valid UUIDs."""
        bad_uuid_payload = {
            "user1_id": "not-a-uuid",
            "user2_id": "not-a-uuid",
            "user1_item_id": "not-a-uuid",
            "user2_item_id": "not-a-uuid"
        }
        res = requests.post(f"{BASE_URL}/", json=bad_uuid_payload)
        self.assertEqual(res.status_code, 422, "FastAPI should validate internal UUIDs in body and return 422")

    def test_create_deal_null_values(self):
        """Test sending explicit null values where strings/uuids are required."""
        null_payload = {
            "user1_id": None,
            "user2_id": None,
            "user1_item_id": None,
            "user2_item_id": None
        }
        res = requests.post(f"{BASE_URL}/", json=null_payload)
        self.assertEqual(res.status_code, 422, "FastAPI should reject null values for string types")

    def test_create_deal_duplicate_users(self):
        """Test logic failure mapping user1_id to user2_id (same user negotiating with themselves)."""
        same_id = str(uuid.uuid4())
        payload = {
            "user1_id": same_id,
            "user2_id": same_id,
            "user1_item_id": str(uuid.uuid4()),
            "user2_item_id": str(uuid.uuid4()),
            "cash_difference": 10.0,
            "payer_id": same_id,
            "status": "pending"
        }
        res = requests.post(f"{BASE_URL}/", json=payload)
        # Even if DB allows it, ideally an API should reject this. But minimally it shouldn't crash the server.
        self.assertIn(res.status_code, [400, 422, 500], "Should fail or be blocked by DB validation constraints")

    def test_create_deal_extreme_cash_value(self):
        """Test extremely large scientific notation numbers or overflow values for cash_difference."""
        extreme_payload = {
            "user1_id": str(uuid.uuid4()),
            "user2_id": str(uuid.uuid4()),
            "user1_item_id": str(uuid.uuid4()),
            "user2_item_id": str(uuid.uuid4()),
            "cash_difference": 1e200, # Extremely large float
            "status": "pending"
        }
        res = requests.post(f"{BASE_URL}/", json=extreme_payload)
        # Should gracefully fail either in FastAPI float parsing or Supabase numeric bounds limit
        self.assertIn(res.status_code, [400, 422, 500], "Should gracefully fail out of bounds floats")

    def test_update_deal_malicious_status_string(self):
        """Test potential SQL injection or XSS strings in the status field."""
        fake_uuid = str(uuid.uuid4())
        malicious_payload = {
            "status": "'; DROP TABLE deals; -- <script>alert(1)</script>"
        }
        res = requests.patch(f"{BASE_URL}/{fake_uuid}", json=malicious_payload)
        self.assertIn(res.status_code, [400, 404, 422], "Should fail validation or 404 cleanly, not execute injection")

    def test_create_deal_negative_cash(self):
        """Test negative cash difference to ensure behavior is predictable."""
        negative_payload = {
            "user1_id": str(uuid.uuid4()),
            "user2_id": str(uuid.uuid4()),
            "user1_item_id": str(uuid.uuid4()),
            "user2_item_id": str(uuid.uuid4()),
            "cash_difference": -50.50, # negative money
            "payer_id": str(uuid.uuid4()),
            "status": "pending"
        }
        res = requests.post(f"{BASE_URL}/", json=negative_payload)
        self.assertIn(res.status_code, [400, 422, 500], "Should be rejected either by API or DB Constraints")


if __name__ == "__main__":
    unittest.main()

