"""Derived performance for the educational, simulation-only trading ledger."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

_LOCAL_ZONE = ZoneInfo("Europe/Bucharest")


def _number(value, fallback=0.0):
    if isinstance(value, bool):
        return fallback
    try:
        result = float(value)
    except (TypeError, ValueError):
        return fallback
    return result if math.isfinite(result) else fallback


def _instant(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_LOCAL_ZONE)
    return parsed.astimezone(_LOCAL_ZONE)


def _date_key(value):
    instant = _instant(value)
    return instant.date().isoformat() if instant else None


def summarize_performance(state: dict) -> dict:
    """Summarize confirmed sales and open positions without inventing mark-to-market data.

    A daily return is net realized P/L on the Bucharest sale date and in one
    currency divided by that currency's sold positions' combined buy-cost basis.
    The header total is the arithmetic sum of daily/currency percentages, not a
    compounded or FX-converted portfolio return.
    """
    holdings = state.get("holdings", []) if isinstance(state, dict) else []
    transactions = state.get("transactions", []) if isinstance(state, dict) else []
    events = {}
    for event in transactions:
        if not isinstance(event, dict) or not event.get("holding_id"):
            continue
        kind = event.get("type")
        if kind in ("buy", "sell"):
            events.setdefault((str(event["holding_id"]), kind), event)

    records = []
    daily = defaultdict(lambda: {"net_pnl": 0.0, "cost_basis": 0.0, "closed_count": 0})
    for holding in holdings:
        if not isinstance(holding, dict):
            continue
        hid = str(holding.get("id") or "")
        buy_event = events.get((hid, "buy"), {})
        sell_event = events.get((hid, "sell"), {})
        buy_at = holding.get("buy_at") or buy_event.get("created_at")
        sell_at = holding.get("sold_at") or sell_event.get("created_at")
        buy_price = _number(holding.get("buy_price", buy_event.get("unit_price")))
        sell_price = _number(holding.get("sold_price", sell_event.get("unit_price")))
        quantity = _number(holding.get("quantity", buy_event.get("quantity")))
        closed = holding.get("status") == "sold" and sell_price > 0 and quantity > 0 and buy_price > 0
        pnl = (sell_price - buy_price) * quantity if closed else None
        cost_basis = buy_price * quantity if closed else None
        roi = (sell_price / buy_price - 1.0) * 100 if closed else None
        sale_day = _date_key(sell_at) if closed else None
        if sale_day:
            currency = str(holding.get("currency") or buy_event.get("currency") or "—").upper()
            aggregate = daily[(sale_day, currency)]
            aggregate["net_pnl"] += pnl
            aggregate["cost_basis"] += cost_basis
            aggregate["closed_count"] += 1
        records.append({
            "holding_id": hid,
            "person_id": str(holding.get("person_id") or ""),
            "symbol": str(holding.get("symbol") or ""),
            "name": str(holding.get("name") or ""),
            "market": str(holding.get("market") or ""),
            "currency": str(holding.get("currency") or ""),
            "quantity": quantity,
            "buy_at": buy_at,
            "buy_price": buy_price,
            "sell_at": sell_at if closed else None,
            "sell_price": sell_price if closed else None,
            "pnl": pnl,
            "roi_pct": roi,
            "status": "closed" if closed else "holding",
        })

    records.sort(key=lambda item: str(item.get("sell_at") or item.get("buy_at") or ""), reverse=True)
    daily_returns = []
    for (day, currency), aggregate in sorted(daily.items()):
        cost = aggregate["cost_basis"]
        pct = aggregate["net_pnl"] / cost * 100 if cost > 0 else 0.0
        daily_returns.append({
            "date": day,
            "currency": currency,
            "net_pnl": round(aggregate["net_pnl"], 8),
            "cost_basis": round(cost, 8),
            "return_pct": pct,
            "closed_count": aggregate["closed_count"],
        })
    return {
        "records": records,
        "daily_returns": daily_returns,
        "total_percent": sum(item["return_pct"] for item in daily_returns),
        "formula": "group by Bucharest sale date and currency; daily realized P/L / same-day sold cost basis; daily percentages summed, not compounded or FX-converted",
        "simulation_only": True,
        "unrealized_pnl_included": False,
    }
