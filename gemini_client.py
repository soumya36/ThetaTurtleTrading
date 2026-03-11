"""
gemini_client.py – Lightweight wrapper around Gemini REST Market-Data API.

Public endpoints (no API key needed):
    - list_symbols, symbol_details, get_network
    - ticker_v1, ticker_v2, pricefeed
    - order_book, trades, candles, derivative_candles
    - fee_promos, funding_amount

Authenticated endpoint:
    - fx_rate  (requires API key + secret)

Usage:
    from gemini_client import GeminiClient
    client = GeminiClient()                       # public data
    client = GeminiClient(api_key=..., api_secret=...)  # + FX rate
"""

import hashlib
import hmac
import base64
import json
import time
from typing import Optional

import requests

BASE_URL = "https://api.gemini.com"
SANDBOX_URL = "https://api.sandbox.gemini.com"


class GeminiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        sandbox: bool = False,
    ):
        self.base = SANDBOX_URL if sandbox else BASE_URL
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()

    # ── helpers ──────────────────────────────────────────────────────────
    def _get(self, path: str, params: Optional[dict] = None):
        url = f"{self.base}{path}"
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _authenticated_headers(self, payload_dict: dict) -> dict:
        """Build X-GEMINI-* headers for private endpoints."""
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret are required for this endpoint.")
        payload_dict["nonce"] = str(int(time.time() * 1000))
        encoded = base64.b64encode(json.dumps(payload_dict).encode())
        signature = hmac.new(
            self.api_secret.encode(), encoded, hashlib.sha384
        ).hexdigest()
        return {
            "X-GEMINI-APIKEY": self.api_key,
            "X-GEMINI-PAYLOAD": encoded.decode(),
            "X-GEMINI-SIGNATURE": signature,
            "Content-Type": "text/plain",
            "Content-Length": "0",
            "Cache-Control": "no-cache",
        }

    # ── public endpoints ────────────────────────────────────────────────

    def list_symbols(self) -> list[str]:
        """GET /v1/symbols – all tradeable symbols."""
        return self._get("/v1/symbols")

    def symbol_details(self, symbol: str) -> dict:
        """GET /v1/symbols/details/{symbol}"""
        return self._get(f"/v1/symbols/details/{symbol}")

    def get_network(self, token: str) -> dict:
        """GET /v1/network/{token} – supported blockchain networks."""
        return self._get(f"/v1/network/{token}")

    def ticker_v1(self, symbol: str) -> dict:
        """GET /v1/pubticker/{symbol} – bid/ask/last + 24h volume."""
        return self._get(f"/v1/pubticker/{symbol}")

    def ticker_v2(self, symbol: str) -> dict:
        """GET /v2/ticker/{symbol} – OHLC, hourly changes, bid/ask."""
        return self._get(f"/v2/ticker/{symbol.lower()}")

    def pricefeed(self) -> list[dict]:
        """GET /v1/pricefeed – price + 24h % change for every pair."""
        return self._get("/v1/pricefeed")

    def order_book(
        self, symbol: str, limit_bids: int = 50, limit_asks: int = 50
    ) -> dict:
        """GET /v1/book/{symbol}"""
        return self._get(
            f"/v1/book/{symbol}",
            params={"limit_bids": limit_bids, "limit_asks": limit_asks},
        )

    def trades(
        self,
        symbol: str,
        limit_trades: int = 50,
        timestamp: Optional[int] = None,
        since_tid: Optional[int] = None,
        include_breaks: bool = False,
    ) -> list[dict]:
        """GET /v1/trades/{symbol}"""
        params: dict = {"limit_trades": limit_trades, "include_breaks": include_breaks}
        if timestamp is not None:
            params["timestamp"] = timestamp
        if since_tid is not None:
            params["since_tid"] = since_tid
        return self._get(f"/v1/trades/{symbol}", params=params)

    @staticmethod
    def _normalize_tf(time_frame: str) -> str:
        """Gemini accepts 1m, 5m, 15m, 30m, 1hr, 6hr, 1day."""
        mapping = {"1h": "1hr", "6h": "6hr", "1d": "1day"}
        return mapping.get(time_frame, time_frame)

    def candles(self, symbol: str, time_frame: str = "1hr") -> list[list]:
        """GET /v2/candles/{symbol}/{time_frame}
        time_frame: 1m, 5m, 15m, 30m, 1hr, 6hr, 1day
        Returns list of [timestamp_ms, open, high, low, close, volume].
        """
        tf = self._normalize_tf(time_frame)
        return self._get(f"/v2/candles/{symbol.lower()}/{tf}")

    def derivative_candles(self, symbol: str, time_frame: str = "1m") -> list[list]:
        """GET /v2/derivatives/candles/{symbol}/{time_frame}"""
        return self._get(f"/v2/derivatives/candles/{symbol.lower()}/{time_frame}")

    def fee_promos(self) -> dict:
        """GET /v1/feepromos – symbols with active fee promotions."""
        return self._get("/v1/feepromos")

    def funding_amount(self, symbol: str) -> dict:
        """GET /v1/fundingamount/{symbol}"""
        return self._get(f"/v1/fundingamount/{symbol}")

    # ── authenticated endpoint ──────────────────────────────────────────

    def fx_rate(self, pair: str, timestamp_ms: int) -> dict:
        """GET /v2/fxrate/{pair}/{timestamp}  (requires Auditor role key)."""
        path = f"/v2/fxrate/{pair}/{timestamp_ms}"
        payload = {"request": path}
        headers = self._authenticated_headers(payload)
        url = f"{self.base}{path}"
        resp = self.session.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
