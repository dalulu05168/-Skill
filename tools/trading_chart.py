"""Read-only Yahoo Finance daily history for local TradingView Lightweight Charts.

This module only retrieves public price history; it never places or changes orders.
"""
from __future__ import annotations

import json
import math
import threading
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from trading_symbol_lookup import SymbolLookupError, lookup_symbol

_ALLOWED_RANGES = {"6mo", "1y", "5y"}
_TIMEOUT_SECONDS = 10
_MAX_RESPONSE_BYTES = 2_000_000
_CACHE_TTL_SECONDS = 900
_cache: dict[tuple[str, str], tuple[float, dict]] = {}
_lock = threading.Lock()


class ChartDataError(RuntimeError):
    """A public market-data response could not be used safely."""


def _json(url: str) -> dict:
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; NUVEXA-ChartHistory/1.0)",
    })
    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ChartDataError("Yahoo Finance 历史行情暂不可用，请稍后重试") from exc
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise ChartDataError("历史行情响应过大，已停止读取")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChartDataError("历史行情服务返回了无法识别的数据") from exc
    if not isinstance(result, dict):
        raise ChartDataError("历史行情服务返回了无法识别的数据")
    return result


def _market_day(epoch: int, timezone_name: str) -> str:
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        zone = timezone.utc
    return datetime.fromtimestamp(epoch, zone).date().isoformat()


def get_history(symbol: str, range_name: str = "1y") -> dict:
    """Return validated daily OHLC data for an exact resolved listing."""
    range_name = str(range_name or "1y").strip().lower()
    if range_name not in _ALLOWED_RANGES:
        raise ValueError("图表周期仅支持 6个月、1年或5年")
    instrument = lookup_symbol(symbol)
    resolved = instrument["symbol"]
    key = (resolved, range_name)
    now = time.monotonic()
    with _lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < _CACHE_TTL_SECONDS:
            return dict(cached[1])
        if cached:
            _cache.pop(key, None)

    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + quote(resolved, safe="") + f"?range={range_name}&interval=1d")
    payload = _json(url)
    try:
        chart = payload.get("chart") or {}
        if chart.get("error"):
            raise ChartDataError("Yahoo Finance 未返回该证券的历史行情")
        result = (chart.get("result") or [None])[0]
        meta = result.get("meta") if isinstance(result, dict) else None
        timestamps = result.get("timestamp") if isinstance(result, dict) else None
        quote_list = ((result.get("indicators") or {}).get("quote") or []) if isinstance(result, dict) else []
        first_quote = quote_list[0] if quote_list else {}
    except (AttributeError, TypeError, IndexError) as exc:
        raise ChartDataError("历史行情服务返回了无法识别的数据") from exc
    if not isinstance(meta, dict) or not isinstance(timestamps, list) or not isinstance(first_quote, dict):
        raise ChartDataError("该代码没有可用的日线历史行情")
    if str(meta.get("symbol") or "").upper() != resolved.upper():
        raise ChartDataError("服务返回的证券代码与请求不一致，已停止绘图")

    timezone_name = str(meta.get("exchangeTimezoneName") or "UTC")
    closes = first_quote.get("close") or []
    opens = first_quote.get("open") or []
    highs = first_quote.get("high") or []
    lows = first_quote.get("low") or []
    points: list[dict] = []
    seen_days: set[str] = set()
    for index, epoch in enumerate(timestamps):
        if isinstance(epoch, bool) or not isinstance(epoch, (int, float)):
            continue
        if index >= len(closes):
            continue
        close = closes[index]
        if isinstance(close, bool) or not isinstance(close, (int, float)) or not math.isfinite(close) or close <= 0:
            continue
        day = _market_day(int(epoch), timezone_name)
        if day in seen_days:
            continue
        seen_days.add(day)
        point = {"time": day, "value": float(close)}
        for key_name, values in (("open", opens), ("high", highs), ("low", lows)):
            value = values[index] if index < len(values) else None
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0:
                point[key_name] = float(value)
        points.append(point)
    points.sort(key=lambda item: item["time"])
    if not points:
        raise ChartDataError("该代码没有可用的日线收盘价")
    # Guard the page and desktop renderer against unexpectedly large responses.
    points = points[-1300:]
    data = {
        "symbol": resolved,
        "name": str(meta.get("longName") or meta.get("shortName") or instrument.get("name") or resolved),
        "market": str(meta.get("fullExchangeName") or meta.get("exchangeName") or instrument.get("market") or ""),
        "currency": str(meta.get("currency") or instrument.get("currency") or ""),
        "provider": "Yahoo Finance",
        "range": range_name,
        "interval": "1d",
        "timezone": timezone_name,
        "points": points,
    }
    with _lock:
        _cache[key] = (time.monotonic(), dict(data))
        if len(_cache) > 64:
            oldest = sorted(_cache, key=lambda item: _cache[item][0])[:len(_cache) - 64]
            for old_key in oldest:
                _cache.pop(old_key, None)
    return data
