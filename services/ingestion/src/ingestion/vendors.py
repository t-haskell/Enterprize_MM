"""Vendor SDK wrappers with retry + monitoring hooks."""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests

DEFAULT_TIMEOUT = float(os.getenv("VENDOR_HTTP_TIMEOUT", "10"))
MAX_RETRIES = int(os.getenv("VENDOR_HTTP_RETRIES", "3"))
BACKOFF_SECONDS = float(os.getenv("VENDOR_HTTP_BACKOFF", "1.5"))


class VendorRequestError(RuntimeError):
    """Raised when a vendor call fails after retries."""


def _retry_request(method: str, url: str, **kwargs: Any) -> requests.Response:
    last_error: Optional[BaseException] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(method, url, timeout=DEFAULT_TIMEOUT, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:  # pragma: no cover - network failure path
            last_error = exc
            if attempt == MAX_RETRIES:
                break
            sleep_for = BACKOFF_SECONDS * attempt
            time.sleep(min(sleep_for, 5.0))
    raise VendorRequestError(f"Failed request to {url}: {last_error}")


@dataclass
class PolygonClient:
    api_key: Optional[str]
    base_url: str = "https://api.polygon.io"

    @classmethod
    def from_env(cls) -> "PolygonClient":
        return cls(api_key=os.getenv("POLYGON_API_KEY"))

    def get_aggregates(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 5000,
        }
        url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{start:%Y-%m-%d}/{end:%Y-%m-%d}"
        if not self.api_key:
            return self._synthetic_equity_data(symbol, start, end)
        params["apiKey"] = self.api_key
        response = _retry_request("GET", url, params=params)
        payload = response.json()
        results = payload.get("results", [])
        if not results:
            return pd.DataFrame()
        frame = pd.DataFrame(results)
        frame.rename(
            columns={
                "t": "ts",
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
            },
            inplace=True,
        )
        frame["ts"] = pd.to_datetime(frame["ts"], unit="ms")
        frame["symbol"] = symbol
        return frame

    @staticmethod
    def _synthetic_equity_data(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        periods = (end.date() - start.date()).days + 1
        rows: List[Dict[str, Any]] = []
        base_price = 100 + random.random() * 20
        for idx in range(periods):
            ts = start + timedelta(days=idx)
            open_price = base_price + random.uniform(-1, 1)
            close_price = open_price + random.uniform(-2, 2)
            high_price = max(open_price, close_price) + random.random()
            low_price = min(open_price, close_price) - random.random()
            rows.append(
                {
                    "ts": ts,
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": int(1_000_000 + random.random() * 50_000),
                    "symbol": symbol,
                }
            )
        return pd.DataFrame(rows)


@dataclass
class SECEdgarClient:
    user_agent: Optional[str]
    base_url: str = "https://data.sec.gov"

    @classmethod
    def from_env(cls) -> "SECEdgarClient":
        return cls(user_agent=os.getenv("SEC_API_USER_AGENT"))

    def get_company_facts(self, cik: str) -> Dict[str, Any]:
        headers = {"User-Agent": self.user_agent or "enterprize-mm-ingestion"}
        url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik}.json"
        if not self.user_agent:
            return self._synthetic_company_facts(cik)
        response = _retry_request("GET", url, headers=headers)
        return response.json()

    @staticmethod
    def _synthetic_company_facts(cik: str) -> Dict[str, Any]:
        now = datetime.utcnow().date()
        value = 1_000_000_000 + random.randint(-50_000_000, 50_000_000)
        return {
            "cik": cik,
            "facts": {
                "IncomeStatement": {
                    "Revenues": {
                        "label": "Revenues",
                        "units": {
                            "USD": [
                                {
                                    "end": now.isoformat(),
                                    "val": value,
                                }
                            ]
                        },
                    }
                }
            },
        }


@dataclass
class RavenPackClient:
    api_key: Optional[str]
    base_url: str = "https://api.ravenpack.com"

    @classmethod
    def from_env(cls) -> "RavenPackClient":
        return cls(api_key=os.getenv("RAVENPACK_API_KEY"))

    def get_news(self, symbols: Iterable[str]) -> pd.DataFrame:
        if not self.api_key:
            return self._synthetic_news(symbols)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/data/v1/signals"
        params = {"tickers": ",".join(symbols), "limit": 100}
        response = _retry_request("GET", url, headers=headers, params=params)
        payload = response.json()
        return pd.DataFrame(payload.get("data", []))

    @staticmethod
    def _synthetic_news(symbols: Iterable[str]) -> pd.DataFrame:
        now = datetime.utcnow()
        rows: List[Dict[str, Any]] = []
        for symbol in symbols:
            rows.append(
                {
                    "symbol": symbol,
                    "headline": f"Synthetic headline for {symbol}",
                    "relevance": random.random(),
                    "sentiment": random.uniform(-1, 1),
                    "event_time": now.isoformat(),
                }
            )
        return pd.DataFrame(rows)


@dataclass
class MacroSignalsClient:
    api_key: Optional[str]

    @classmethod
    def from_env(cls) -> "MacroSignalsClient":
        return cls(api_key=os.getenv("MACRO_SIGNAL_API_KEY"))

    def latest_signals(self) -> pd.DataFrame:
        now = datetime.utcnow()
        rows = [
            {"indicator": "inflation", "value": random.uniform(1.5, 3.5), "as_of": now},
            {"indicator": "gdp_growth", "value": random.uniform(1.0, 3.0), "as_of": now},
            {"indicator": "rates", "value": random.uniform(2.5, 5.0), "as_of": now},
        ]
        return pd.DataFrame(rows)


@dataclass
class InsiderActivityClient:
    api_key: Optional[str]

    @classmethod
    def from_env(cls) -> "InsiderActivityClient":
        return cls(api_key=os.getenv("INSIDER_API_KEY"))

    def latest_activity(self, symbols: Iterable[str]) -> pd.DataFrame:
        now = datetime.utcnow()
        rows = []
        for symbol in symbols:
            rows.append(
                {
                    "symbol": symbol,
                    "insider": "Synthetic Insider",
                    "role": "Director",
                    "transaction_type": random.choice(["Buy", "Sell"]),
                    "shares": random.randint(100, 5000),
                    "transaction_date": now.date(),
                    "price": random.uniform(50, 250),
                    "source": "synthetic",
                }
            )
        return pd.DataFrame(rows)
