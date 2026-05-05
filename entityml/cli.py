from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

from entityml import EntityMLAPIError, EntityMLAuthError, EntityMLClient


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="entityml")
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key (fallback: ENTITY_API_KEY environment variable)",
    )
    parser.add_argument(
        "--base-url",
        default="https://api.entityml.com",
        help="API base URL (default: https://api.entityml.com)",
    )

    commands = parser.add_subparsers(dest="command")

    commands.add_parser("health", help="Check API health")

    monitoring = commands.add_parser("monitoring-status", help="Check infrastructure status")
    monitoring.add_argument("--token", default=None, help="Optional monitoring status token")

    lookup_slug = commands.add_parser("lookup-slug", help="Resolve a Polymarket slug or URL")
    lookup_slug.add_argument("--slug", required=True)

    polymarket = commands.add_parser("polymarket", help="Polymarket endpoints")
    polymarket_commands = polymarket.add_subparsers(dest="subcommand")

    poly_list = polymarket_commands.add_parser(
        "list-markets", help="List stored Polymarket market condition IDs"
    )
    poly_list.add_argument("--prefix", default=None)
    poly_list.add_argument("--offset", type=int, default=0)
    poly_list.add_argument("--limit", type=int, default=100)

    poly_date_range = polymarket_commands.add_parser(
        "date-range", help="Get stored date range for a Polymarket market"
    )
    poly_date_range.add_argument("--condition-id", required=True)

    poly_market_data = polymarket_commands.add_parser(
        "market-data", help="Fetch raw polymarket market data"
    )
    poly_market_data.add_argument("--condition-id", required=True)
    poly_market_data.add_argument("--date", required=True)
    poly_market_data.add_argument("--offset", type=int, default=0)
    poly_market_data.add_argument("--limit", type=int, default=10000)

    poly_market_range = polymarket_commands.add_parser(
        "market-data-range", help="Fetch raw Polymarket data across a timestamp range"
    )
    poly_market_range.add_argument("--condition-id", required=True)
    poly_market_range.add_argument("--start-timestamp", type=int, required=True)
    poly_market_range.add_argument("--end-timestamp", type=int, required=True)
    poly_market_range.add_argument("--cursor", default=None)
    poly_market_range.add_argument("--limit", type=int, default=10000)

    poly_summary = polymarket_commands.add_parser(
        "orderbook-summary", help="Fetch polymarket orderbook summary"
    )
    poly_summary.add_argument("--condition-id", required=True)
    poly_summary.add_argument("--asset-id", required=True)
    poly_summary.add_argument("--date", required=True)
    poly_summary.add_argument("--resolution", type=int, default=60)

    kalshi = commands.add_parser("kalshi", help="Kalshi endpoints")
    kalshi_commands = kalshi.add_subparsers(dest="subcommand")

    kalshi_list = kalshi_commands.add_parser(
        "list-markets", help="List stored Kalshi market tickers"
    )
    kalshi_list.add_argument("--prefix", default=None)
    kalshi_list.add_argument("--offset", type=int, default=0)
    kalshi_list.add_argument("--limit", type=int, default=100)

    kalshi_date_range = kalshi_commands.add_parser(
        "date-range", help="Get stored date range for a Kalshi ticker"
    )
    kalshi_date_range.add_argument("--ticker", required=True)

    kalshi_market_data = kalshi_commands.add_parser(
        "market-data", help="Fetch raw kalshi market data"
    )
    kalshi_market_data.add_argument("--ticker", required=True)
    kalshi_market_data.add_argument("--date", required=True)
    kalshi_market_data.add_argument("--offset", type=int, default=0)
    kalshi_market_data.add_argument("--limit", type=int, default=10000)

    kalshi_market_range = kalshi_commands.add_parser(
        "market-data-range", help="Fetch raw Kalshi data across a timestamp range"
    )
    kalshi_market_range.add_argument("--ticker", required=True)
    kalshi_market_range.add_argument("--start-timestamp", type=int, required=True)
    kalshi_market_range.add_argument("--end-timestamp", type=int, required=True)
    kalshi_market_range.add_argument("--cursor", default=None)
    kalshi_market_range.add_argument("--limit", type=int, default=10000)

    kalshi_summary = kalshi_commands.add_parser(
        "orderbook-summary", help="Fetch kalshi orderbook summary"
    )
    kalshi_summary.add_argument("--ticker", required=True)
    kalshi_summary.add_argument("--date", required=True)
    kalshi_summary.add_argument("--resolution", type=int, default=60)

    api_keys = commands.add_parser("api-keys", help="API key management")
    api_key_commands = api_keys.add_subparsers(dest="subcommand")

    api_keys_create = api_key_commands.add_parser("create", help="Create an API key")
    api_keys_create.add_argument("--name", required=True)
    api_keys_create.add_argument("--user-id", required=True)

    api_keys_list = api_key_commands.add_parser("list", help="List API keys")
    api_keys_list.add_argument("--user-id", required=True)

    api_keys_delete = api_key_commands.add_parser("delete", help="Delete an API key")
    api_keys_delete.add_argument("--key-id", required=True)
    api_keys_delete.add_argument("--user-id", required=True)

    api_keys_last_used = api_key_commands.add_parser("last-used", help="Get API key last-used time")
    api_keys_last_used.add_argument("--key-id", required=True)

    api_keys_name = api_key_commands.add_parser("name", help="Get API key name")
    api_keys_name.add_argument("--key-id", required=True)

    billing = commands.add_parser("billing", help="Billing and usage endpoints")
    billing_commands = billing.add_subparsers(dest="subcommand")

    checkout = billing_commands.add_parser("checkout", help="Create a Stripe checkout session")
    checkout.add_argument("--user-id", required=True)
    checkout.add_argument("--email", required=True)
    checkout.add_argument("--success-url", required=True)
    checkout.add_argument("--cancel-url", required=True)
    checkout.add_argument("--tier", default="starter")

    portal = billing_commands.add_parser("portal", help="Create a Stripe portal session")
    portal.add_argument("--user-id", required=True)
    portal.add_argument("--return-url", required=True)

    subscription_status = billing_commands.add_parser(
        "subscription-status", help="Get subscription status"
    )
    subscription_status.add_argument("--user-id", required=True)

    usage = billing_commands.add_parser("usage", help="Get monthly API usage")
    usage.add_argument("--user-id", required=True)

    analytics = commands.add_parser("analytics", help="Usage analytics endpoints")
    analytics_commands = analytics.add_subparsers(dest="subcommand")

    request_count = analytics_commands.add_parser(
        "user-request-count", help="Get total request count for a user"
    )
    request_count.add_argument("--user-id", required=True)

    request_count_timeframe = analytics_commands.add_parser(
        "user-request-count-timeframe", help="Get hourly request counts in a timeframe"
    )
    request_count_timeframe.add_argument("--user-id", required=True)
    request_count_timeframe.add_argument("--start-time", type=int, required=True)
    request_count_timeframe.add_argument("--end-time", type=int, required=True)

    recent_requests = analytics_commands.add_parser(
        "user-recent-requests", help="Get recent API requests for a user"
    )
    recent_requests.add_argument("--user-id", required=True)
    recent_requests.add_argument("--limit", type=int, default=10)

    analytics_commands.add_parser("system-stats", help="Get system-wide API stats")

    popular_markets = analytics_commands.add_parser(
        "popular-markets", help="Get the most frequently queried markets"
    )
    popular_markets.add_argument("--limit", type=int, default=20)
    popular_markets.add_argument("--days", type=int, default=30)

    return parser


def _emit_json(payload: Dict[str, Any], *, stream) -> None:
    stream.write(json.dumps(payload, indent=2, sort_keys=True))
    stream.write("\n")


def _build_client(args: argparse.Namespace) -> EntityMLClient:
    api_key = args.api_key or os.getenv("ENTITY_API_KEY")
    return EntityMLClient(api_key=api_key, base_url=args.base_url)


def _execute(client: EntityMLClient, args: argparse.Namespace) -> Dict[str, Any]:
    if args.command == "health":
        return client.system.health()

    if args.command == "monitoring-status":
        return client.system.monitoring_status(token=args.token)

    if args.command == "lookup-slug":
        return client.lookup.polymarket_slug(slug=args.slug)

    if args.command == "polymarket":
        if args.subcommand == "list-markets":
            return client.polymarket.list_markets(
                prefix=args.prefix,
                offset=args.offset,
                limit=args.limit,
            )
        if args.subcommand == "date-range":
            return client.polymarket.get_market_date_range(condition_id=args.condition_id)
        if args.subcommand == "market-data":
            return client.polymarket.get_market_data(
                condition_id=args.condition_id,
                date=args.date,
                offset=args.offset,
                limit=args.limit,
            )
        if args.subcommand == "market-data-range":
            return client.polymarket.get_market_data_range(
                condition_id=args.condition_id,
                start_timestamp=args.start_timestamp,
                end_timestamp=args.end_timestamp,
                cursor=args.cursor,
                limit=args.limit,
            )
        if args.subcommand == "orderbook-summary":
            return client.polymarket.get_orderbook_summary(
                condition_id=args.condition_id,
                asset_id=args.asset_id,
                date=args.date,
                resolution=args.resolution,
            )

    if args.command == "kalshi":
        if args.subcommand == "list-markets":
            return client.kalshi.list_markets(
                prefix=args.prefix,
                offset=args.offset,
                limit=args.limit,
            )
        if args.subcommand == "date-range":
            return client.kalshi.get_market_date_range(ticker=args.ticker)
        if args.subcommand == "market-data":
            return client.kalshi.get_market_data(
                ticker=args.ticker,
                date=args.date,
                offset=args.offset,
                limit=args.limit,
            )
        if args.subcommand == "market-data-range":
            return client.kalshi.get_market_data_range(
                ticker=args.ticker,
                start_timestamp=args.start_timestamp,
                end_timestamp=args.end_timestamp,
                cursor=args.cursor,
                limit=args.limit,
            )
        if args.subcommand == "orderbook-summary":
            return client.kalshi.get_orderbook_summary(
                ticker=args.ticker,
                date=args.date,
                resolution=args.resolution,
            )

    if args.command == "api-keys":
        if args.subcommand == "create":
            return client.api_keys.create(name=args.name, user_id=args.user_id)
        if args.subcommand == "list":
            return client.api_keys.list(user_id=args.user_id)
        if args.subcommand == "delete":
            return client.api_keys.delete(key_id=args.key_id, user_id=args.user_id)
        if args.subcommand == "last-used":
            return client.api_keys.get_last_used(key_id=args.key_id)
        if args.subcommand == "name":
            return client.api_keys.get_name(key_id=args.key_id)

    if args.command == "billing":
        if args.subcommand == "checkout":
            return client.billing.create_checkout_session(
                user_id=args.user_id,
                email=args.email,
                success_url=args.success_url,
                cancel_url=args.cancel_url,
                tier=args.tier,
            )
        if args.subcommand == "portal":
            return client.billing.create_portal_session(
                user_id=args.user_id,
                return_url=args.return_url,
            )
        if args.subcommand == "subscription-status":
            return client.billing.get_subscription_status(user_id=args.user_id)
        if args.subcommand == "usage":
            return client.billing.get_usage(user_id=args.user_id)

    if args.command == "analytics":
        if args.subcommand == "user-request-count":
            return client.analytics.get_user_request_count(user_id=args.user_id)
        if args.subcommand == "user-request-count-timeframe":
            return client.analytics.get_user_request_count_timeframe(
                user_id=args.user_id,
                start_time=args.start_time,
                end_time=args.end_time,
            )
        if args.subcommand == "user-recent-requests":
            return client.analytics.get_user_recent_requests(
                user_id=args.user_id,
                limit=args.limit,
            )
        if args.subcommand == "system-stats":
            return client.analytics.get_system_stats()
        if args.subcommand == "popular-markets":
            return client.analytics.get_popular_markets(
                limit=args.limit,
                days=args.days,
            )

    raise EntityMLAPIError(
        "Unknown command",
        status_code=400,
        detail="Unknown command",
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help(sys.stderr)
        return 2

    try:
        client = _build_client(args)
        result = _execute(client, args)
        _emit_json(result, stream=sys.stdout)
        return 0
    except EntityMLAuthError as exc:
        _emit_json(
            {
                "error": "auth_error",
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
            stream=sys.stderr,
        )
        return 2
    except EntityMLAPIError as exc:
        _emit_json(
            {
                "error": "api_error",
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
            stream=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
