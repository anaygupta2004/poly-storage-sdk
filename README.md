# entityml

Official Python SDK for the EntityML Market Data API.

## Install

```bash
pip install entityml
```

## Usage

```python
from entityml import EntityMLClient

client = EntityMLClient(api_key="YOUR_API_KEY")

health = client.system.health()
markets = client.polymarket.list_markets(prefix="0x8213", limit=10)
date_range = client.polymarket.get_market_date_range(
    condition_id="0x0008043c3ed513ecff7ee64380fc943dc73eb3dfb6674f281149efe4769f7515",
)
data = client.polymarket.get_market_data(
    condition_id="0x0008043c3ed513ecff7ee64380fc943dc73eb3dfb6674f281149efe4769f7515",
    date="2026-02-13",
)
summary = client.polymarket.get_orderbook_summary(
    condition_id="0x0008043c3ed513ecff7ee64380fc943dc73eb3dfb6674f281149efe4769f7515",
    asset_id="97684905927345553455494278582909124912046930226695064344571162061840768197777",
    date="2026-02-13",
    resolution=60,
)
kalshi_data = client.kalshi.get_market_data(
    ticker="KXBTC-26FEB2606-B60125",
    date="2026-02-26",
)
```

## Endpoint groups

- `client.polymarket`: list markets, date ranges, daily data, timestamp ranges, and orderbook summaries.
- `client.kalshi`: list markets, date ranges, daily data, timestamp ranges, and orderbook summaries.
- `client.lookup`: Polymarket slug lookup.
- `client.api_keys`: create, list, delete, last-used, and name lookup.
- `client.billing`: checkout, portal, subscription status, usage, and raw Stripe webhook forwarding.
- `client.analytics`: user request counts, recent requests, system stats, and popular markets.
- `client.system`: health and monitoring status.
