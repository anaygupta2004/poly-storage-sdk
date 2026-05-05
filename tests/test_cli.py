import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

from entityml.cli import main


class CLITests(unittest.TestCase):
    @patch("entityml.cli.EntityMLClient")
    def test_health_command(self, client_cls):
        client = client_cls.return_value
        client.system.health = Mock(return_value={"status": "healthy"})

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(["health"])

        self.assertEqual(code, 0)
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["status"], "healthy")

    @patch("entityml.cli.EntityMLClient")
    def test_polymarket_market_data_command(self, client_cls):
        client = client_cls.return_value
        client.polymarket.get_market_data = Mock(return_value={"data_count": 1})

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(
                [
                    "polymarket",
                    "market-data",
                    "--condition-id",
                    "0xabc",
                    "--date",
                    "2026-02-13",
                    "--offset",
                    "10",
                    "--limit",
                    "20",
                ]
            )

        self.assertEqual(code, 0)
        client.polymarket.get_market_data.assert_called_once_with(
            condition_id="0xabc",
            date="2026-02-13",
            offset=10,
            limit=20,
        )

    @patch("entityml.cli.EntityMLClient")
    def test_polymarket_orderbook_summary_requires_asset_id(self, client_cls):
        client = client_cls.return_value
        client.polymarket.get_orderbook_summary = Mock(return_value={"data_points": 1})

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(
                [
                    "polymarket",
                    "orderbook-summary",
                    "--condition-id",
                    "0xabc",
                    "--asset-id",
                    "token-1",
                    "--date",
                    "2026-04-02",
                    "--resolution",
                    "60",
                ]
            )

        self.assertEqual(code, 0)
        client.polymarket.get_orderbook_summary.assert_called_once_with(
            condition_id="0xabc",
            asset_id="token-1",
            date="2026-04-02",
            resolution=60,
        )

    @patch("entityml.cli.EntityMLClient")
    def test_range_lookup_billing_and_analytics_commands(self, client_cls):
        client = client_cls.return_value
        client.kalshi.get_market_data_range = Mock(return_value={"data_count": 0})
        client.lookup.polymarket_slug = Mock(return_value={"success": True})
        client.billing.get_usage = Mock(return_value={"api_calls": 10})
        client.analytics.get_popular_markets = Mock(return_value={"top_markets": []})

        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                main(
                    [
                        "kalshi",
                        "market-data-range",
                        "--ticker",
                        "KXBTC-TEST",
                        "--start-timestamp",
                        "1775000000000",
                        "--end-timestamp",
                        "1775000060000",
                        "--cursor",
                        "next",
                        "--limit",
                        "50",
                    ]
                ),
                0,
            )
        client.kalshi.get_market_data_range.assert_called_once_with(
            ticker="KXBTC-TEST",
            start_timestamp=1775000000000,
            end_timestamp=1775000060000,
            cursor="next",
            limit=50,
        )

        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["lookup-slug", "--slug", "will-bitcoin-hit-100k"]), 0)
        client.lookup.polymarket_slug.assert_called_once_with(slug="will-bitcoin-hit-100k")

        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["billing", "usage", "--user-id", "user-1"]), 0)
        client.billing.get_usage.assert_called_once_with(user_id="user-1")

        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["analytics", "popular-markets", "--limit", "3", "--days", "7"]), 0)
        client.analytics.get_popular_markets.assert_called_once_with(limit=3, days=7)

    def test_missing_command_returns_error_code(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = main([])
        self.assertEqual(code, 2)
        self.assertIn("usage:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
