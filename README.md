# poly-storage-sdk

Official Python SDK for the Entity Market Data API.

## Install

```bash
pip install poly-storage-sdk
```

## Usage

```python
from poly_storage_sdk import PolyStorageClient

client = PolyStorageClient(api_key="YOUR_API_KEY")

health = client.system.health()
data = client.polymarket.get_market_data(
    condition_id="0x0008043c3ed513ecff7ee64380fc943dc73eb3dfb6674f281149efe4769f7515",
    date="2026-02-13",
)
```
