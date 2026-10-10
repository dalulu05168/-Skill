"""65-person educational trading ledger. No brokerage/orders/live data or synthetic executions.

Ported and decoupled from growth-story-workspace trading-simulator.js and trade-dashboard.js.
Trading figures are manually entered fictional simulation values, not actual holdings.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SOURCE = "finance-director-65-v4.1"
CURRENCIES = {"RON", "EUR", "USD", "GBP", "HKD", "CNY"}
FREQUENCIES = {"HIGH", "MEDIUM", "LOW"}
BUCHAREST = ZoneInfo("Europe/Bucharest")


def today():
    return datetime.now(BUCHAREST).date().isoformat()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def fresh_state():
    return {"schema_version": "1.0", "roster_source": SOURCE, "simulation_only": True,
            "revision": 0, "eligibility": {}, "offers": [], "recommendations": [],
            "buy_plans": [], "holdings": [], "transactions": [],
            "settings": {"today_target": 8, "include_holding": False}}


def _id(value):
    val = str(value or "").zfill(2)
    if val not in {str(i).zfill(2) for i in range(1, 66)}:
        raise ValueError("交易成员只允许01–65号")
    return val


def _date(value):
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError()
        return value
    except (TypeError, ValueError):
        raise ValueError("日期必须为YYYY-MM-DD") from None


def _number(value, label, *, integer=False, minimum=0, maximum=None):
    if value is None or value == "" or isinstance(value, bool):
        raise ValueError(f"{label}不能为空")
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label}必须为数值") from None
    if not math.isfinite(n) or n < minimum or (maximum is not None and n > maximum) or (integer and not n.is_integer()):
        raise ValueError(f"{label}不符合范围")
    return int(n) if integer else n


def _text(v, label, length=120):
    if not isinstance(v, str) or not v.strip() or len(v.strip()) > length:
        raise ValueError(f"{label}不能为空或过长")
    return v.strip()


def _iso(v):
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("交易时间格式错误") from None


def _profiles(profiles):
    if len(profiles) != 65 or set(profiles) != {str(i).zfill(2) for i in range(1, 66)}:
        raise ValueError("权威65人资料不完整")
    for key, person in profiles.items():
        if str(person.get("character_id")) != key or not person.get("identity_extension", {}).get("姓名"):
            raise ValueError("成员身份不一致：" + key)


def validate_state(state):
    if (not isinstance(state, dict) or state.get("roster_source") != SOURCE or
            state.get("schema_version") != "1.0" or state.get("simulation_only") is not True):
        raise ValueError("交易数据不是65人正式模拟账本，拒绝导入旧70/72人记录")
    for prop in ("offers", "recommendations", "buy_plans", "holdings", "transactions"):
        if not isinstance(state.get(prop), list):
            raise ValueError("交易账本损坏：" + prop)
    if not isinstance(state.get("eligibility"), dict):
        raise ValueError("资格数据损坏")
    for pid in state["eligibility"]:
        _id(pid)
    for coll in ("buy_plans", "holdings", "transactions"):
        for item in state[coll]:
            _id(item["person_id"])
    for rec in state["recommendations"]:
        for item in rec.get("candidates", []):
            _id(item["person_id"])
    return state


def read_state(path):
    path = Path(path)
    if not path.exists():
        return fresh_state()
    return validate_state(json.loads(path.read_text(encoding="utf-8")))


def write_state(path, state):
    validate_state(state)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".trade-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def _member_eligibility(state, pid):
    return state["eligibility"].get(pid, {"opened": False, "funds": {}, "frequency": "MEDIUM", "required_today": False})


def _active(state, pid=None):
    return [h for h in state["holdings"] if h["status"] == "holding" and (pid is None or h["person_id"] == pid)]


def _funds(state, pid, currency):
    setting = _member_eligibility(state, pid)
    cap = setting.get("funds", {}).get(currency)
    if cap is None:
        return None
    spent = sum(float(h["quantity"]) * float(h["buy_price"]) for h in _active(state, pid) if h["currency"] == currency)
    return round(max(0.0, float(cap) - spent), 2)


def _offer(state, oid):
    return next((o for o in state["offers"] if o["id"] == oid), None) or _raise("股票计划不存在")


def _raise(message):
    raise ValueError(message)


def _rec(state, oid, day):
    return next((r for r in state["recommendations"] if r["offer_id"] == oid and r["date"] == day), None) or _raise("当日尚未生成推荐名单")


def _event(state, kind, pid, offer_id, holding_id=None, **extra):
    event = {"id": "tx-" + uuid.uuid4().hex, "type": kind, "person_id": pid,
             "offer_id": offer_id, "holding_id": holding_id, "created_at": utc_now(), "simulation_only": True, **extra}
    state["transactions"].append(event)
    return event


def _seed(pid, day):
    return int(hashlib.sha256(f"{pid}|{day}".encode()).hexdigest()[:12], 16) / 0xFFFFFFFFFFFF


def summary(state, profiles):
    _profiles(profiles)
    validate_state(state)
    holds = _active(state)
    people = []
    for pid, p in sorted(profiles.items()):
        cfg = _member_eligibility(state, pid)
        detail = p["identity_extension"]
        people.append({"id": pid, "name": detail["姓名"], "age": p["source_profile"].get("年龄"),
                       "gender": p["source_profile"].get("性别"),
                       "role": p["source_profile"].get("学员资历"),
                       "occupation": p["source_profile"].get("工作_职业"),
                       "city": detail.get("居住城市", ""),
                       "opened": cfg.get("opened", False), "funds": cfg.get("funds", {}),
                       "frequency": cfg.get("frequency", "MEDIUM"),
                       "required_today": cfg.get("required_today", False),
                       "hold_count": sum(h["person_id"] == pid for h in holds)})
    return {"source": SOURCE, "simulation_only": True, "market_date": today(),
            "revision": state["revision"], "people": people, "offers": state["offers"],
            "recommendations": state["recommendations"], "buy_plans": state["buy_plans"],
            "holdings": state["holdings"], "transactions": state["transactions"],
            "metrics": {"people": 65, "opened": sum(p["opened"] for p in people),
                        "holding_members": len({h["person_id"] for h in holds}),
                        "active_holdings": len(holds),
                        "sold_records": sum(h["status"] == "sold" for h in state["holdings"])}}


def snapshot(state, day=None, offer_id=None):
    validate_state(state)
    day = _date(day or today())
    if offer_id is not None:
        _offer(state, offer_id)
    facts = []
    for rec in state["recommendations"]:
        if rec["date"] != day or (offer_id is not None and rec["offer_id"] != offer_id):
            continue
        for c in rec["candidates"]:
            facts.append({"id": "candidate:" + rec["id"] + ":" + c["person_id"],
                          "character_id": c["person_id"], "kind": c["status"], "offer_id": rec["offer_id"]})
    for h in state["holdings"]:
        if offer_id is not None and h["offer_id"] != offer_id:
            continue
        facts.append({"id": "holding:" + h["id"], "character_id": h["person_id"],
                      "kind": "sold" if h["status"] == "sold" else "holding",
                      "offer_id": h["offer_id"], "record": dict(h)})
    return {"source": "trading-65", "date": day, "offer_id": offer_id,
            "simulation_only": True, "facts": facts,
            "required_participants": sorted({x["character_id"] for x in facts})}


def apply(state, profiles, action, data):
    """Explicit user actions only. Caller owns lock and atomic persistence."""
    _profiles(profiles)
    validate_state(state)
    if not isinstance(data, dict):
        raise ValueError("请求必须为对象")
    stamp = utc_now()
    result = None
    if action == "eligibility":
        pid = _id(data.get("person_id"))
        opened = data.get("opened")
        if not isinstance(opened, bool):
            raise ValueError("请明确选择是否已模拟开户")
        currency = str(data.get("currency", "RON")).upper()
        if currency not in CURRENCIES:
            raise ValueError("不支持的币种")
        current = _member_eligibility(state, pid)
        funds = dict(current.get("funds", {}))
        amount = data.get("funds")
        if amount == "":
            funds.pop(currency, None)
        elif amount is not None:
            funds[currency] = _number(amount, "模拟可用资金", minimum=0)
        frequency = data.get("frequency", current.get("frequency", "MEDIUM"))
        if frequency not in FREQUENCIES:
            raise ValueError("无效的参与频率")
        required_today = data.get("required_today", current.get("required_today", False))
        if not isinstance(required_today, bool):
            raise ValueError("指定参与标记无效")
        current = {"opened": opened, "funds": funds, "frequency": frequency, "required_today": required_today}
        state["eligibility"][pid] = current
        result = {"person_id": pid, **current}
    elif action == "create_offer":
        symbol = _text(data.get("symbol"), "股票代码", 30).upper()
        name = _text(data.get("name"), "股票名称")
        market = _text(data.get("market", "BVB"), "市场", 40)
        currency = str(data.get("currency", "RON")).upper()
        if currency not in CURRENCIES:
            raise ValueError("不支持的币种")
        offer = {"id": "of-" + uuid.uuid4().hex, "symbol": symbol, "name": name, "market": market,
                 "currency": currency, "unit_price": _number(data.get("unit_price"), "模拟单价", minimum=0.000001),
                 "min_shares": _number(data.get("min_shares"), "最低股数", integer=True, minimum=1),
                 "hold_days": _number(data.get("hold_days"), "持有天数", integer=True, minimum=0, maximum=3650),
                 "participant_count": _number(data.get("participant_count"), "参与人数", integer=True, minimum=1, maximum=65),
                 "discount_pct": _number(data.get("discount_pct", 0), "折扣比例", minimum=0, maximum=99),
                 "created_at": stamp, "simulation_only": True}
        state["offers"].append(offer)
        result = offer
    elif action == "recommend":
        offer = _offer(state, data.get("offer_id"))
        day = _date(data.get("date") or today())
        exists = next((r for r in state["recommendations"] if r["offer_id"] == offer["id"] and r["date"] == day), None)
        if exists:
            return exists  # Never reset invited/bought statuses on repeated clicks.
        candidates = []
        for pid in sorted(profiles):
            cfg = _member_eligibility(state, pid)
            funds = _funds(state, pid, offer["currency"])
            if not cfg.get("opened") or funds is None or funds + 1e-9 < offer["min_shares"] * offer["unit_price"]:
                continue
            owns = bool(_active(state, pid))
            score = (50 if cfg.get("required_today") else 0) + {"HIGH":30,"MEDIUM":20,"LOW":10}.get(cfg.get("frequency"),20) + (0 if owns else 15) + _seed(pid, day)
            candidates.append((score, pid))
        candidates.sort(key=lambda row: (-row[0], row[1]))
        rec = {"id": "rec-" + uuid.uuid4().hex, "date": day, "offer_id": offer["id"], "created_at": stamp,
               "candidates": [{"person_id": pid, "status": "pending"} for _, pid in candidates[:offer["participant_count"]]]}
        state["recommendations"].append(rec)
        result = rec
    elif action in ("invite", "reject"):
        offer = _offer(state, data.get("offer_id"))
        day = _date(data.get("date") or today())
        pid = _id(data.get("person_id"))
        rec = _rec(state, offer["id"], day)
        c = next((c for c in rec["candidates"] if c["person_id"] == pid), None) or _raise("成员不在候选名单")
        if c["status"] == "bought":
            raise ValueError("已经买入的交易不能撤销邀请")
        if action == "invite":
            if not _member_eligibility(state, pid).get("opened"):
                raise ValueError("成员尚未配置模拟开户")
            available = _funds(state, pid, offer["currency"])
            if available is None or available + 1e-9 < offer["unit_price"] * offer["min_shares"]:
                raise ValueError("成员资金未录入或不足")
            c["status"] = "invited"
            if not any(x["offer_id"] == offer["id"] and x["person_id"] == pid and x["date"] == day and x["status"] == "planned" for x in state["buy_plans"]):
                state["buy_plans"].append({"id": "bp-" + uuid.uuid4().hex, "person_id": pid,
                                           "offer_id": offer["id"], "date": day, "status": "planned", "source": "recommendation"})
        else:
            c["status"] = "rejected"
            state["buy_plans"] = [x for x in state["buy_plans"] if not (x["offer_id"] == offer["id"] and x["person_id"] == pid and x["status"] == "planned")]
        result = {"person_id": pid, "status": c["status"]}
    elif action == "buy":
        offer = _offer(state, data.get("offer_id"))
        day = _date(data.get("date") or today())
        pid = _id(data.get("person_id"))
        rec = _rec(state, offer["id"], day)
        candidate = next((x for x in rec["candidates"] if x["person_id"] == pid), None)
        if not candidate or candidate["status"] != "invited":
            raise ValueError("必须先邀请该成员，再确认买入")
        qty = _number(data.get("quantity"), "买入股数", integer=True, minimum=offer["min_shares"])
        funds = _funds(state, pid, offer["currency"])
        if funds is None or funds + 1e-9 < qty * offer["unit_price"]:
            raise ValueError("模拟资金未录入或不足")
        if any(x["person_id"] == pid and x["offer_id"] == offer["id"] and x["status"] == "holding" for x in state["holdings"]):
            raise ValueError("同一成员不可重复持有同一股票计划")
        buy_at = _iso(stamp)
        planned_sell = (buy_at + timedelta(days=offer["hold_days"])).isoformat()
        holding = {"id": "hd-" + uuid.uuid4().hex, "person_id": pid,
                   "offer_id": offer["id"], "symbol": offer["symbol"], "name": offer["name"],
                   "market": offer["market"], "currency": offer["currency"], "quantity": qty,
                   "buy_price": offer["unit_price"], "buy_at": stamp, "planned_sell_at": planned_sell,
                   "status": "holding", "simulation_only": True}
        state["holdings"].append(holding)
        candidate["status"] = "bought"
        for plan in state["buy_plans"]:
            if plan["offer_id"] == offer["id"] and plan["person_id"] == pid and plan["date"] == day and plan["status"] == "planned":
                plan.update({"status": "done", "holding_id": holding["id"], "completed_at": stamp})
        event = _event(state, "buy", pid, offer["id"], holding["id"], quantity=qty,
                       unit_price=offer["unit_price"], currency=offer["currency"])
        result = {"holding": holding, "transaction": event}
    elif action == "sell":
        hid = _text(data.get("holding_id"), "持仓编号")
        holding = next((h for h in state["holdings"] if h["id"] == hid), None) or _raise("持仓不存在")
        if holding["status"] != "holding":
            raise ValueError("这笔持仓已经卖出")
        if _iso(stamp) < _iso(holding["planned_sell_at"]):
            raise ValueError("尚未达到最低持有期限，不得卖出")
        price = _number(data.get("sell_price"), "模拟卖出价", minimum=0.000001)
        holding.update({"status": "sold", "sold_at": stamp, "sold_price": price})
        event = _event(state, "sell", holding["person_id"], holding["offer_id"], hid,
                       quantity=holding["quantity"], unit_price=price, currency=holding["currency"])
        result = {"holding": holding, "transaction": event}
    else:
        raise ValueError("不支持的交易操作")
    state["revision"] = int(state.get("revision", 0)) + 1
    return result