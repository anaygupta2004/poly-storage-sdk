import unittest

from entityml import EntityMLClient
from poly_storage_sdk import PolyStorageClient


class FakeResponse:
    status_code = 200
    text = ""

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse({"ok": True})


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.session = FakeSession()
        self.client = EntityMLClient(
            api_key="test-key",
            base_url="https://api.entityml.com",
            session=self.session,
        )

    @property
    def last_call(self):
        return self.session.calls[-1]

    def test_polymarket_orderbook_summary_sends_asset_id(self):
        self.assertIsInstance(self.client, PolyStorageClient)

        self.client.polymarket.get_orderbook_summary(
            condition_id="0xabc",
            asset_id="token-1",
            date="2026-04-02",
            resolution=60,
        )

        self.assertEqual(
            self.last_call["url"],
            "https://api.entityml.com/api/v1/polymarket/market/orderbook-summary",
        )
        self.assertEqual(
            self.last_call["params"],
            {
                "condition_id": "0xabc",
                "asset_id": "token-1",
                "date": "2026-04-02",
                "resolution": 60,
            },
        )

    def test_range_methods_omit_empty_cursor(self):
        self.client.polymarket.get_market_data_range(
            condition_id="0xabc",
            start_timestamp=1775000000000,
            end_timestamp=1775000060000,
        )
        self.assertNotIn("cursor", self.last_call["params"])

        self.client.kalshi.get_market_data_range(
            ticker="KXBTC-TEST",
            start_timestamp=1775000000000,
            end_timestamp=1775000060000,
            cursor="next",
        )
        self.assertEqual(self.last_call["params"]["cursor"], "next")

    def test_orderbook_summary_accepts_timestamp_window(self):
        self.client.polymarket.get_orderbook_summary(
            condition_id="0xabc",
            asset_id="token-1",
            start_timestamp=1775000000000,
            end_timestamp=1775000060000,
        )
        self.assertEqual(
            self.last_call["params"],
            {
                "condition_id": "0xabc",
                "asset_id": "token-1",
                "start_timestamp": 1775000000000,
                "end_timestamp": 1775000060000,
                "resolution": 60,
            },
        )

        self.client.kalshi.get_orderbook_summary(
            ticker="KXBTC-TEST",
            start_timestamp=1775000000000,
            end_timestamp=1775000060000,
        )
        self.assertEqual(
            self.last_call["params"],
            {
                "ticker": "KXBTC-TEST",
                "start_timestamp": 1775000000000,
                "end_timestamp": 1775000060000,
                "resolution": 60,
            },
        )

    def test_inventory_and_date_range_methods(self):
        self.client.polymarket.list_markets(prefix="0xabc", offset=10, limit=5)
        self.assertEqual(self.last_call["url"], "https://api.entityml.com/api/v1/polymarket/market/list")
        self.assertEqual(self.last_call["params"], {"prefix": "0xabc", "offset": 10, "limit": 5})

        self.client.kalshi.get_market_date_range(ticker="KXBTC-TEST")
        self.assertEqual(self.last_call["url"], "https://api.entityml.com/api/v1/kalshi/market/date-range")
        self.assertEqual(self.last_call["params"], {"ticker": "KXBTC-TEST"})

    def test_lookup_billing_analytics_and_monitoring_methods(self):
        self.client.lookup.polymarket_slug(slug="will-bitcoin-hit-100k")
        self.assertEqual(self.last_call["url"], "https://api.entityml.com/api/v1/lookup/slug")

        self.client.billing.create_checkout_session(
            user_id="user-1",
            email="person@example.com",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            tier="pro",
        )
        self.assertEqual(self.last_call["url"], "https://api.entityml.com/api/v1/subscriptions/checkout")
        self.assertEqual(self.last_call["json"]["tier"], "pro")

        self.client.billing.stripe_webhook(
            raw_payload='{"type":"invoice.paid"}',
            stripe_signature="sig",
        )
        self.assertEqual(self.last_call["url"], "https://api.entityml.com/api/v1/webhooks/stripe")
        self.assertEqual(self.last_call["data"], '{"type":"invoice.paid"}')
        self.assertEqual(self.last_call["headers"], {"stripe-signature": "sig"})

        self.client.analytics.get_popular_markets(limit=3, days=7)
        self.assertEqual(self.last_call["url"], "https://api.entityml.com/api/v1/stats/popular-markets")
        self.assertEqual(self.last_call["params"], {"limit": 3, "days": 7})

        self.client.system.monitoring_status(token="status-token")
        self.assertEqual(self.last_call["url"], "https://api.entityml.com/api/v1/monitoring/status")
        self.assertEqual(self.last_call["headers"], {"x-monitoring-token": "status-token"})


if __name__ == "__main__":
    unittest.main()
