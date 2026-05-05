from __future__ import annotations

import os
from typing import Any, Dict, Optional, Union

import requests

from .errors import PolyStorageAPIError, PolyStorageAuthError


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/api/v1"):
        return normalized
    return f"{normalized}/api/v1"


def _without_none(values: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if values is None:
        return None
    return {key: value for key, value in values.items() if value is not None}


class _BaseService:
    def __init__(self, client: "PolyStorageClient") -> None:
        self._client = client

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        data_body: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        requires_auth: bool = False,
    ) -> Dict[str, Any]:
        if requires_auth and not self._client.api_key:
            raise PolyStorageAuthError(
                "API key is required for this endpoint. Set api_key or ENTITY_API_KEY.",
                status_code=401,
                detail="API key required",
            )

        url = f"{self._client.base_url}{path}"
        try:
            response = self._client.session.request(
                method=method,
                url=url,
                params=_without_none(params),
                json=json_body,
                data=data_body,
                headers=headers,
                timeout=self._client.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise PolyStorageAPIError(
                f"Network error while calling {url}: {exc}",
                status_code=None,
                detail=str(exc),
            ) from exc

        response_data: Any
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}

        if response.status_code >= 400:
            detail = (
                response_data.get("detail")
                or response_data.get("message")
                or response.text
                or "Request failed"
            )
            if response.status_code in (401, 403):
                raise PolyStorageAuthError(
                    f"Authentication failed ({response.status_code})",
                    status_code=response.status_code,
                    detail=str(detail),
                    response_body=response_data,
                )
            raise PolyStorageAPIError(
                f"Request failed ({response.status_code})",
                status_code=response.status_code,
                detail=str(detail),
                response_body=response_data,
            )

        if isinstance(response_data, dict):
            return response_data
        return {"data": response_data}


class SystemService(_BaseService):
    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def monitoring_status(self, *, token: Optional[str] = None) -> Dict[str, Any]:
        headers = {"x-monitoring-token": token} if token else None
        return self._request("GET", "/monitoring/status", headers=headers)


class APIKeysService(_BaseService):
    def create(self, *, name: str, user_id: str) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/keys",
            params={"name": name, "user_id": user_id},
        )

    def list(self, *, user_id: str) -> Dict[str, Any]:
        return self._request("GET", "/keys", params={"user_id": user_id})

    def delete(self, *, key_id: str, user_id: str) -> Dict[str, Any]:
        return self._request(
            "DELETE",
            f"/keys/{key_id}",
            params={"user_id": user_id},
        )

    def get_last_used(self, *, key_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/keys/{key_id}/last-used")

    def get_name(self, *, key_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/keys/{key_id}/name")


class LookupService(_BaseService):
    def polymarket_slug(self, *, slug: str) -> Dict[str, Any]:
        return self._request("GET", "/lookup/slug", params={"slug": slug})


class PolymarketService(_BaseService):
    def list_markets(
        self,
        *,
        prefix: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/polymarket/market/list",
            params={"prefix": prefix, "offset": offset, "limit": limit},
            requires_auth=True,
        )

    def get_market_date_range(self, *, condition_id: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/polymarket/market/date-range",
            params={"condition_id": condition_id},
            requires_auth=True,
        )

    def get_market_data(
        self,
        *,
        condition_id: str,
        date: str,
        offset: int = 0,
        limit: int = 10000,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/polymarket/market/data",
            params={
                "condition_id": condition_id,
                "date": date,
                "offset": offset,
                "limit": limit,
            },
            requires_auth=True,
        )

    def get_market_data_range(
        self,
        *,
        condition_id: str,
        start_timestamp: int,
        end_timestamp: int,
        cursor: Optional[str] = None,
        limit: int = 10000,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/polymarket/market/data/range",
            params={
                "condition_id": condition_id,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "cursor": cursor,
                "limit": limit,
            },
            requires_auth=True,
        )

    def get_orderbook_summary(
        self,
        *,
        condition_id: str,
        asset_id: str,
        date: str,
        resolution: int = 60,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/polymarket/market/orderbook-summary",
            params={
                "condition_id": condition_id,
                "asset_id": asset_id,
                "date": date,
                "resolution": resolution,
            },
            requires_auth=True,
        )


class KalshiService(_BaseService):
    def list_markets(
        self,
        *,
        prefix: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/kalshi/market/list",
            params={"prefix": prefix, "offset": offset, "limit": limit},
            requires_auth=True,
        )

    def get_market_date_range(self, *, ticker: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/kalshi/market/date-range",
            params={"ticker": ticker},
            requires_auth=True,
        )

    def get_market_data(
        self,
        *,
        ticker: str,
        date: str,
        offset: int = 0,
        limit: int = 10000,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/kalshi/market/data",
            params={
                "ticker": ticker,
                "date": date,
                "offset": offset,
                "limit": limit,
            },
            requires_auth=True,
        )

    def get_market_data_range(
        self,
        *,
        ticker: str,
        start_timestamp: int,
        end_timestamp: int,
        cursor: Optional[str] = None,
        limit: int = 10000,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/kalshi/market/data/range",
            params={
                "ticker": ticker,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "cursor": cursor,
                "limit": limit,
            },
            requires_auth=True,
        )

    def get_orderbook_summary(
        self,
        *,
        ticker: str,
        date: str,
        resolution: int = 60,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/kalshi/market/orderbook-summary",
            params={
                "ticker": ticker,
                "date": date,
                "resolution": resolution,
            },
            requires_auth=True,
        )


class BillingService(_BaseService):
    def create_checkout_session(
        self,
        *,
        user_id: str,
        email: str,
        success_url: str,
        cancel_url: str,
        tier: str = "starter",
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/subscriptions/checkout",
            json_body={
                "user_id": user_id,
                "email": email,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "tier": tier,
            },
        )

    def create_portal_session(self, *, user_id: str, return_url: str) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/subscriptions/portal",
            json_body={"user_id": user_id, "return_url": return_url},
        )

    def get_subscription_status(self, *, user_id: str) -> Dict[str, Any]:
        return self._request("GET", "/subscriptions/status", params={"user_id": user_id})

    def get_usage(self, *, user_id: str) -> Dict[str, Any]:
        return self._request("GET", "/usage", params={"user_id": user_id})

    def stripe_webhook(
        self,
        *,
        raw_payload: Union[str, bytes],
        stripe_signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = {"stripe-signature": stripe_signature} if stripe_signature else None
        return self._request("POST", "/webhooks/stripe", data_body=raw_payload, headers=headers)


class AnalyticsService(_BaseService):
    def get_user_request_count(self, *, user_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/user/{user_id}/requests/count")

    def get_user_request_count_timeframe(
        self,
        *,
        user_id: str,
        start_time: int,
        end_time: int,
    ) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/user/{user_id}/requests/count/timeframe",
            params={"start_time": start_time, "end_time": end_time},
        )

    def get_user_recent_requests(self, *, user_id: str, limit: int = 10) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/user/{user_id}/requests/recent",
            params={"limit": limit},
        )

    def get_system_stats(self) -> Dict[str, Any]:
        return self._request("GET", "/stats")

    def get_popular_markets(self, *, limit: int = 20, days: int = 30) -> Dict[str, Any]:
        return self._request("GET", "/stats/popular-markets", params={"limit": limit, "days": days})


class PolyStorageClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://api.entityml.com",
        timeout_seconds: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("ENTITY_API_KEY")
        self.base_url = _normalize_base_url(base_url)
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "entityml-sdk/0.2.0",
            }
        )
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

        self.system = SystemService(self)
        self.api_keys = APIKeysService(self)
        self.lookup = LookupService(self)
        self.polymarket = PolymarketService(self)
        self.kalshi = KalshiService(self)
        self.billing = BillingService(self)
        self.analytics = AnalyticsService(self)


class EntityMLClient(PolyStorageClient):
    """Preferred client name for the EntityML Market Data API."""
