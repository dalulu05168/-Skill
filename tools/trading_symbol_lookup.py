"""Read-only security metadata lookup via Yahoo Finance search and chart data.

This helper never submits or executes an order. Returned prices, when available,
are reference quotes only and must not be represented as completed trades.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

_SYMBOL = re.compile(r"^[A-Z0-9^][A-Z0-9.^=_-]{0,19}$")
_TIMEOUT_SECONDS = 8
_MAX_RESPONSE_BYTES = 180_000
_CACHE_TTL_SECONDS = 900
_cache: dict[str, tuple[float, dict]] = {}
_lock = threading.Lock()


class SymbolLookupError(RuntimeError):
    """The public metadata provider did not return a usable matching instrument."""


def _provider_json(url: str) -> dict:
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; NUVEXA-SymbolLookup/1.0)",
    })
    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SymbolLookupError("股票信息服务暂不可用，请稍后重试或手动填写") from exc
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise SymbolLookupError("股票信息响应过大，已停止读取")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SymbolLookupError("股票信息服务返回了无法识别的数据") from exc
    if not isinstance(result, dict):
        raise SymbolLookupError("股票信息服务返回了无法识别的数据")
    return result


def _resolve_provider_symbol(symbol: str) -> str:
    """Prefer exact listing matches; infer an un-suffixed BVB code only uniquely."""
    params = urlencode({"q": symbol, "quotesCount": 10, "newsCount": 0,
                        "enableFuzzyQuery": "false"})
    try:
        data = _provider_json("https://query1.finance.yahoo.com/v1/finance/search?" + params)
    except SymbolLookupError:
        # Exact chart lookup below remains useful if the search endpoint is unavailable.
        return symbol
    candidates = [item for item in data.get("quotes", [])
                  if isinstance(item, dict) and isinstance(item.get("symbol"), str)]
    exact = [item for item in candidates
             if item["symbol"].upper() == symbol]
    if len(exact) == 1:
        return exact[0]["symbol"].upper()
    if len(exact) > 1:
        equities = [item for item in exact
                    if str(item.get("quoteType") or "").upper() == "EQUITY"]
        if len(equities) == 1:
            return equities[0]["symbol"].upper()
        raise SymbolLookupError("该代码存在多个完全匹配结果，请输入带市场后缀的代码")

    # Yahoo Finance lists Romanian BVB listings with a .RO suffix (e.g. TLV.RO).
    # Only auto-select when exactly one BVB listing starts with the supplied code.
    bvb = [item for item in candidates
           if item["symbol"].upper().startswith(symbol + ".")
           and "BVB" in str(item.get("exchDisp") or item.get("exchange") or "").upper()
           and str(item.get("quoteType") or "").upper() == "EQUITY"]
    if len(bvb) == 1:
        return bvb[0]["symbol"].upper()
    if len(bvb) > 1:
        raise SymbolLookupError("该代码对应多个 BVB 股票，请输入完整代码以避免错配")
    return symbol


def lookup_symbol(symbol: str) -> dict:
    if not isinstance(symbol, str):
        raise ValueError("股票代码格式无效")
    symbol = symbol.strip().upper()
    if not _SYMBOL.fullmatch(symbol):
        raise ValueError("股票代码仅支持字母、数字及常见代码标点，长度最多20位")

    now = time.monotonic()
    with _lock:
        cached = _cache.get(symbol)
        if cached and now - cached[0] < _CACHE_TTL_SECONDS:
            return dict(cached[1])
        if cached:
            _cache.pop(symbol, None)

    resolved_symbol = _resolve_provider_symbol(symbol)
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(resolved_symbol, safe="") + "?range=1d&interval=1d"
    payload = _provider_json(url)
    try:
        chart = payload.get("chart") or {}
        error = chart.get("error")
        results = chart.get("result") or []
        meta = results[0].get("meta") if results else None
    except (AttributeError, TypeError, IndexError) as exc:
        raise SymbolLookupError("股票信息服务返回了无法识别的数据") from exc
    if error or not isinstance(meta, dict):
        raise SymbolLookupError("未找到该股票代码；请检查代码或手动填写")

    returned_symbol = str(meta.get("symbol") or "").upper()
    if returned_symbol != resolved_symbol:
        raise SymbolLookupError("服务返回的代码与匹配结果不一致，请手动核对")
    name = str(meta.get("longName") or meta.get("shortName") or "").strip()
    exchange = str(meta.get("fullExchangeName") or meta.get("exchangeName") or "").strip()
    currency = str(meta.get("currency") or "").strip().upper()
    if not name:
        raise SymbolLookupError("已匹配代码，但没有公司名称；请手动填写公司名称")

    price = meta.get("regularMarketPrice")
    if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0:
        price = None
    stamp = meta.get("regularMarketTime")
    if isinstance(stamp, bool) or not isinstance(stamp, (int, float)) or stamp <= 0:
        stamp = None

    result = {
        "symbol": returned_symbol,
        "name": name,
        "market": exchange or "交易所未提供",
        "currency": currency or None,
        "quote_type": str(meta.get("instrumentType") or "").strip() or None,
        "reference_price": float(price) if price is not None else None,
        "provider_timestamp": int(stamp) if stamp is not None else None,
        "provider": "Yahoo Finance",
        "price_is_reference_only": True,
    }
    with _lock:
        _cache[symbol] = (time.monotonic(), dict(result))
        if len(_cache) > 100:
            oldest = sorted(_cache, key=lambda key: _cache[key][0])[:len(_cache) - 100]
            for key in oldest:
                _cache.pop(key, None)
    return result
