"""Manual participant trade *recording* and CSV export, never execution.

Records only what an operator entered about the existing 65 v4.1 fictional
participants; no brokerage, orders, recommendations, price feed or verification.
Shares the established trading-65.json ledger without changing its schema.
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from trading_65 import (CURRENCIES, _date, _id, _number, _profiles, _text,
                        utc_now, validate_state)

BUCHAREST = ZoneInfo("Europe/Bucharest")
FIELDS = (
    "记录编号", "参与人员编号", "参与人员姓名", "买卖方向", "股票代码", "股票名称",
    "市场", "交易日期", "数量", "单价", "币种", "记录金额",
    "录入时间UTC", "录入来源", "参考编号", "备注", "执行已核验", "教学模拟",
)


def add_record(ledger, profiles, request):
    """Append a user-entered entry without fabricating holdings or executions."""
    validate_state(ledger)
    _profiles(profiles)
    if not isinstance(request, dict):
        raise ValueError("交易记录必须为对象")
    pid = _id(request.get("person_id"))
    direction = request.get("trade_type")
    if direction not in ("buy", "sell"):
        raise ValueError("请选择买入或卖出")
    trade_date = _date(request.get("trade_date"))
    currency = request.get("currency", "RON")
    if currency not in CURRENCIES:
        raise ValueError("不支持的币种")
    qty = _number(request.get("quantity"), "交易数量", integer=True, minimum=1, maximum=1_000_000_000)
    price = _number(request.get("unit_price"), "交易单价", minimum=0.000001, maximum=1_000_000_000)
    symbol = _text(request.get("symbol"), "股票代码", 30).upper()
    name = _text(request.get("name"), "股票名称", 120)
    market = _text(request.get("market", "BVB"), "市场", 40)
    note = request.get("note", "")
    reference = request.get("reference", "")
    if not isinstance(note, str) or len(note) > 500:
        raise ValueError("备注不能超过500字")
    if not isinstance(reference, str) or len(reference) > 120:
        raise ValueError("参考编号不能超过120字")
    item = {
        "id": "tx-" + uuid.uuid4().hex,
        "type": direction,
        "person_id": pid,
        "offer_id": None,
        "holding_id": None,
        "created_at": utc_now(),
        "trade_date": trade_date,
        "symbol": symbol,
        "name": name,
        "market": market,
        "quantity": qty,
        "unit_price": price,
        "currency": currency,
        "reference": reference.strip(),
        "note": note.strip(),
        "record_origin": "manual-entry",
        "execution_verified": False,
        "simulation_only": True,
    }
    ledger["transactions"].append(item)
    ledger["revision"] = int(ledger["revision"]) + 1
    return {"record": item, "warning": "仅保存人工填报记录，不验证实际成交，也不改变持仓或资金"}


def _csv_safe(value):
    """Avoid spreadsheet formula execution even when older records are untrusted."""
    s = "" if value is None else str(value)
    if s.lstrip().startswith(("=", "+", "-", "@")) or s.startswith(("\t", "\r", "\n")):
        return "'" + s
    return s


def _record_date(item):
    if isinstance(item.get("trade_date"), str):
        return _date(item["trade_date"])
    created = item.get("created_at")
    if not isinstance(created, str):
        return ""
    try:
        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        return dt.astimezone(BUCHAREST).date().isoformat() if dt.tzinfo else ""
    except ValueError:
        return ""


def csv_export(ledger, profiles, *, person_id=None, start_date=None,
               end_date=None, trade_type=None):
    """Return UTF-8 BOM CSV of *saved* manual and legacy simulation entries.

    Empty matches yield only the headings. Export never writes/changes state.
    """
    validate_state(ledger)
    _profiles(profiles)
    pid = _id(person_id) if person_id else None
    start = _date(start_date) if start_date else None
    end = _date(end_date) if end_date else None
    if start is not None and end is not None and start > end:
        raise ValueError("开始日期不能晚于结束日期")
    if trade_type not in (None, "", "buy", "sell"):
        raise ValueError("交易方向必须是买入或卖出")
    offers = {o["id"]: o for o in ledger["offers"]}
    holdings = {h["id"]: h for h in ledger["holdings"]}
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(FIELDS)
    for tx in ledger["transactions"]:
        if tx.get("type") not in ("buy", "sell"):
            continue
        if pid is not None and tx.get("person_id") != pid:
            continue
        if trade_type and tx["type"] != trade_type:
            continue
        day = _record_date(tx)
        if (start is not None and (not day or day < start) or
            end is not None and (not day or day > end)):
            continue
        hold = holdings.get(tx.get("holding_id")) or {}
        offer = offers.get(tx.get("offer_id")) or {}
        symbol = tx.get("symbol") or hold.get("symbol") or offer.get("symbol") or ""
        stock_name = tx.get("name") or hold.get("name") or offer.get("name") or ""
        market = tx.get("market") or hold.get("market") or offer.get("market") or ""
        quantity = tx.get("quantity")
        unit_price = tx.get("unit_price")
        amount = (str(Decimal(str(quantity)) * Decimal(str(unit_price)))
                  if quantity is not None and unit_price is not None else "")
        person = profiles[tx["person_id"]]["identity_extension"]["姓名"]
        row = (
            tx.get("id"), tx["person_id"], person,
            "买入" if tx["type"] == "buy" else "卖出",
            symbol, stock_name, market, day, quantity, unit_price,
            tx.get("currency", hold.get("currency", offer.get("currency", ""))),
            amount, tx.get("created_at"),
            "人工填报" if tx.get("record_origin") == "manual-entry" else "既有模拟交易流程",
            tx.get("reference", ""), tx.get("note", ""),
            "否", "是",
        )
        writer.writerow([_csv_safe(v) for v in row])
    return "\ufeff" + out.getvalue()
