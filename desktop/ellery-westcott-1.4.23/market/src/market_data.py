"""Market monitor v3: GUI / --check / --auto."""
import io
import json
from pathlib import Path
import math
import os
import queue
import re
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageDraw, ImageFont

import verify
import intraday


# 指标格式：名称、代码、小数位、单位、来源
MARKETS = {
    "RO": {
        "title": "Romania Markets",
        "tab": "罗马尼亚",
        "tz": "Europe/Bucharest",
        "opening": (10, 0),
        "closing": (18, 0),
        "run": (10, 20),
        "items": [
            ("BET Index", "BET", 2, "", "BVB"),
            ("BET-NG Energy Index", "BET-NG", 2, "", "BVB"),
            ("BET-FI Index", "BET-FI", 2, "", "BVB"),
            ("Banca Transilvania (TLV)", "TLV.RO", 4, "RON", "Yahoo"),
            ("BRD Groupe Societe Generale", "BRD.RO", 4, "RON", "Yahoo"),
            ("Hidroelectrica (H2O)", "H2O.RO", 4, "RON", "Yahoo"),
            ("OMV Petrom (SNP)", "SNP.RO", 4, "RON", "Yahoo"),
            ("Romgaz (SNG)", "SNG.RO", 3, "RON", "Yahoo"),
        ],
    },
    "US": {
        "title": "U.S. Markets",
        "tab": "美国",
        "tz": "America/New_York",
        "opening": (9, 30),
        "closing": (16, 0),
        "run": (9, 50),
        "items": [
            ("Dow Jones", "^DJI", 2, "", "Yahoo"),
            ("S&P 500", "^GSPC", 2, "", "Yahoo"),
            ("Nasdaq Composite", "^IXIC", 2, "", "Yahoo"),
            ("US 10Y Treasury Yield", "^TNX", 3, "%", "Yahoo"),
            ("Gold futures GC=F", "GC=F", 2, "USD/oz", "Yahoo"),
            ("Brent futures BZ=F", "BZ=F", 2, "USD/bbl", "Yahoo"),
        ],
    },
}

# Explicit instruments: the Nasdaq Composite is IXIC, not NDX/QQQ.
# Futures are deliberately left with Yahoo until exact-contract intraday bars
# with a source timestamp are available through this endpoint.
TV_SYMBOLS = {
    "^DJI": "DJ:DJI", "^GSPC": "SP:SPX", "^IXIC": "NASDAQ:IXIC",
    "^TNX": "TVC:US10Y", "BET": "BVB:BET", "BET-NG": "BVB:BETNG",
    "TLV.RO": "BVB:TLV", "BRD.RO": "BVB:BRD", "H2O.RO": "BVB:H2O",
    "SNP.RO": "BVB:SNP", "SNG.RO": "BVB:SNG", "BET-FI": "BVB:BETFI",
    "EURRON=X": "FX_IDC:EURRON",
}
TV_FIELDS = "name,description,exchange,type,currency,close,close|1,change,change_abs,time|1,update_time,update_mode,pricescale,minmov"


def quote_provider():
    value = os.getenv("EW_QUOTE_SOURCE", "hybrid").lower()
    return value if value in ("hybrid", "tradingview", "original") else "hybrid"


def parse_tradingview(doc, symbol):
    exchange, name = symbol.split(":", 1)
    if doc.get("name") != name or doc.get("exchange") != exchange:
        raise ValueError("TradingView 返回品种与请求不符")
    expected_type = "bond" if symbol == "TVC:US10Y" else "stock" if name in ("TLV", "BRD", "H2O", "SNP", "SNG") else "forex" if exchange == "FX_IDC" else "index"
    if doc.get("type") != expected_type:
        raise ValueError("TradingView 品种类型不符")
    if expected_type in ("stock", "forex") and doc.get("currency") != "RON":
        raise ValueError("TradingView 币种不符，未采用该价格")
    mode = doc.get("update_mode", "")
    delay_match = re.fullmatch(r"delayed_streaming_(\d+)", mode)
    if mode != "streaming" and not delay_match:
        raise ValueError("TradingView 未提供可用的分时行情模式")
    def numeric(field):
        value = doc.get(field)
        if isinstance(value, bool) or value is None:
            raise ValueError("TradingView 缺少分时价格、时间或前收参考")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("TradingView 分时数据无效")
        return value
    # close|1 and time|1 are a pair. update_time is a scanner refresh time,
    # which can be current while the actual bars are delayed by 10-15 minutes.
    last, bar_time = numeric("close|1"), numeric("time|1")
    current, delta = numeric("close"), numeric("change_abs")
    prev = current - delta
    if min(last, prev, current, bar_time) <= 0:
        raise ValueError("TradingView 价格、前收或分时时间无效")
    pct = numeric("change")
    if abs((current / prev - 1) * 100 - pct) > 0.01:
        raise ValueError("TradingView 日涨跌额与涨跌幅不一致")
    return {
        "last": last, "prev": prev, "pct": (last / prev - 1) * 100,
        "timestamp": datetime.fromtimestamp(bar_time, timezone.utc),
        "provider": "tradingview", "source": "TradingView public scanner", "provider_symbol": symbol,
        "instrument_name": doc.get("description", name),
        "quote_kind": "1分钟K线收盘及其起始时间",
        "delay_seconds": int(delay_match[1]) if delay_match else 0,
        "update_mode": mode, "scanner_update_time": doc.get("update_time"),
        "prev_basis": "TradingView 同品种日涨跌额反推前收（close-change_abs）",
    }


def tradingview_quote(symbol):
    response = requests.get(
        "https://scanner.tradingview.com/symbol",
        params={"symbol": symbol, "fields": TV_FIELDS, "no_404": "true"},
        headers={"User-Agent": "Mozilla/5.0", "Origin": "https://www.tradingview.com"},
        timeout=12,
    )
    response.raise_for_status()
    return parse_tradingview(response.json(), symbol)


def original_quote(key, item):
    if item[1] == 'EURRON=X':
        return tradingview_quote(TV_SYMBOLS[item[1]])
    if item[1] == '^TNX':
        raise ValueError('US10Y必须使用同品种收益率来源；请选择智能混合或TradingView，未以TNX指数替代')
    return bvb_quote(item[1]) if item[4] == "BVB" else yahoo_quote(item[1], MARKETS[key]["tz"])


def hybrid_quote(key, item):
    """Prefer the intended instrument's primary feed; only adopt valid newer backups."""
    symbol = item[1]
    if symbol == 'EURRON=X':
        q = tradingview_quote(TV_SYMBOLS[symbol])
        q['selection_policy'] = 'EUR/RON现价与日涨跌参考统一采用FX_IDC:EURRON；失败时不切换不同日切基准'
        return q
    if symbol == "^TNX":
        q = tradingview_quote(TV_SYMBOLS[symbol])
        q["selection_policy"] = "US10Y收益率采用TV；不以CBOE TNX指数替代"
        return q
    primary = (lambda: bvb_quote(symbol)) if symbol in ("BET", "BET-NG", "BET-FI") else (
        (lambda: bvb_stock_quote(symbol.split(".")[0])) if symbol in ("TLV.RO", "BRD.RO", "H2O.RO", "SNP.RO", "SNG.RO")
        else (lambda: yahoo_quote(symbol, MARKETS[key]["tz"])))
    candidates, notes = [], []
    now = now_for(key)
    def consider(fetch, label):
        try:
            q = fetch()
            status, reason = validate(key, item, q, now=now)
            if status not in ("OK", "CLOSED"):
                notes.append(f"{label}：{reason}")
                return None
            candidates.append(q)
            return q
        except Exception as exc:
            notes.append(f"{label}失败：{type(exc).__name__}: {exc}")
            return None
    q = consider(primary, "主来源")
    # Closed-session snapshots retain the primary closing quote. During trading,
    # probe backups if the primary is unavailable or older than two minutes.
    need_backup = q is None or (validate(key, item, q, now=now)[0] == "OK"
                               and now - q["timestamp"] > timedelta(minutes=2))
    if need_backup:
        if symbol in ("TLV.RO", "BRD.RO", "H2O.RO", "SNP.RO", "SNG.RO"):
            consider(lambda: yahoo_quote(symbol, MARKETS[key]["tz"]), "Yahoo备用")
        if symbol in TV_SYMBOLS:
            consider(lambda: tradingview_quote(TV_SYMBOLS[symbol]), "TV备用")
    if not candidates:
        raise ValueError("；".join(notes) or "没有有效报价")
    chosen = max(candidates, key=lambda value: value["timestamp"])
    chosen["selection_policy"] = "美国指数/期货Yahoo优先；罗马尼亚证券BVB优先；备用仅采用有效且更新的报价"
    chosen["fallback_reason"] = "；".join(notes + (["采用时间更新的备用报价"] if chosen is not q else []))
    return chosen


def check_tv_against_original(key, item, quote):
    if item[1] == 'EURRON=X':
        return 'NONE', 'EUR/RON统一使用同一日切基准；同一来源不作为双源确认', {}
    if item[1] == "^TNX":
        return "NONE", "TV US10Y为国债收益率；Yahoo TNX为CBOE指数，未作等价双源校验", {}
    try:
        other = original_quote(key, item)
        gap = abs((quote["timestamp"] - other["timestamp"]).total_seconds())
        detail = {"source": other["source"], "last": other["last"], "quote_time": other["timestamp"].isoformat()}
        if gap > 120:
            return "ERROR", f"两来源报价时间相差{gap / 60:.1f}分钟，未声称双源一致", detail
        diff = abs(quote["last"] - other["last"]) / other["last"]
        if diff > verify.DEFAULT_TOL:
            return "MISMATCH", f"与{other['source']}同品种报价冲突（偏差{diff:.3%}），已隐藏", detail
        return "MATCH", f"与{other['source']}同品种报价一致（时间差{gap:.0f}秒，偏差{diff:.3%}）", detail
    except Exception as exc:
        return "ERROR", f"原来源核对失败：{type(exc).__name__}: {exc}", {}


MAX_AGE = timedelta(minutes=17)


def now_for(key):
    return datetime.now(ZoneInfo(MARKETS[key]["tz"]))


# -------------------- BVB 官方公开网页 --------------------

class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, value):
        if not self.hidden and value.strip():
            self.parts.append(value.strip())


def number(value):
    value = re.sub(r"\s+", "", value).replace("−", "-")
    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    else:
        value = value.replace(",", ".")
    return float(value)


def parse_bvb(html, symbol):
    parser = PageText()
    parser.feed(html)
    text = " ".join(parser.parts)

    heading = re.search(
        r"\b" + re.escape(symbol) + r"\s*®?\s*\(",
        text,
    )
    if not heading:
        raise ValueError("BVB 页面缺少对应指数标题")

    section = text[heading.end():heading.end() + 1500]
    match = re.search(
        r"(\d[\d.,]*)\s+"
        r"(\d{2}\.\d{2}\.\d{4})\s*/\s*"
        r"(\d{2}:\d{2}:\d{2})"
        r"[^%]{0,80}?"
        r"([+\-−]?\s*\d+(?:[.,]\d+)?)\s*%",
        section,
    )
    if not match:
        raise ValueError(
            "BVB 页面结构变化或缺少报价时间，未采用猜测数据"
        )

    last, day, clock, pct = match.groups()
    last, pct = number(last), number(pct)

    if not math.isfinite(pct) or pct <= -100:
        raise ValueError("BVB 涨跌幅无效")

    stamp = datetime.strptime(
        day + " " + clock,
        "%d.%m.%Y %H:%M:%S",
    ).replace(tzinfo=ZoneInfo("Europe/Bucharest"))

    return {
        "last": last,
        # 网页涨跌幅有舍入，反算前收盘价仅用于校验。
        "prev": last / (1 + pct / 100),
        "pct": pct,
        "timestamp": stamp,
        "source": "BVB public page",
    }


def parse_bvb_service_index(xml_bytes, symbol):
    """Official BVB GetIndex value and session timestamp; no price estimation."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_bytes)
    for node in root.iter():
        if node.tag.split('}')[-1] != 'TypeIndices':
            continue
        fields = {child.tag.split('}')[-1]:(child.text or '').strip() for child in node}
        if fields.get('Code') != symbol:
            continue
        try:
            last = float(fields['CurrentValue']); delta=float(fields['NetChange'])
            percent=float(fields['PrcChange']); stamp=datetime.fromisoformat(fields['LastUpdateTime'].replace('Z','+00:00'))
        except (ValueError, KeyError) as exc:
            raise ValueError('BVB官方指数缺少价格、涨跌或交易时间') from exc
        prev = last - delta
        if not all(math.isfinite(v) for v in (last, prev, delta, percent)) or min(last,prev)<=0:
            raise ValueError('BVB指数数值无效')
        if abs((last/prev-1)*100-percent)>0.06:
            raise ValueError('BVB指数涨跌额与涨跌幅不一致')
        if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=ZoneInfo('Europe/Bucharest'))
        return {'last':last,'prev':prev,'pct':(last/prev-1)*100,'timestamp':stamp,
                'source':'BVB official GetIndex','provider':'bvb','provider_symbol':'BVB:'+symbol,
                'prev_basis':'BVB官方NetChange反推前收','quote_kind':'官方指数当前值及更新时间'}
    raise ValueError('BVB官方接口未返回请求的指数')


def bvb_official_quote(symbol):
    return parse_bvb_service_index(intraday.bvb_xml('GetIndex', symbol),symbol)


def bvb_quote(symbol):
    # First try the documented BVB delayed-data service. It explicitly provides
    # indices; fallback to the official public index page if API needs credentials.
    try:
        return bvb_official_quote(symbol)
    except Exception as service_exc:
        response = requests.get(
            "https://www.bvb.ro/FinancialInstruments/Indices/IndicesProfiles.aspx",
            params={"i": symbol}, headers={"User-Agent": "Mozilla/5.0",
                                         "Cache-Control": "no-cache"}, timeout=12)
        response.raise_for_status()
        quote = parse_bvb(response.text, symbol)
        quote['provider'] = 'bvb'
        quote['provider_symbol'] = 'BVB:' + symbol
        quote['fallback_reason'] = 'BVB官方指数API不可用：'+type(service_exc).__name__
        return quote


def parse_bvb_stock(html, symbol):
    parser = PageText()
    parser.feed(html)
    text = " ".join(parser.parts)
    if not re.search(r"Simbol:\s*" + re.escape(symbol) + r"\b", text):
        raise ValueError("BVB股票代码与请求不符")
    num = r"([+\-−]?\d[\d.,]*)"
    reference = re.search(r"Pret referinta\s+" + num, text)
    latest = re.search(r"Ultimul pret\s+" + num + r"\s+Var\s+" + num + r"\s+Var \(%\)\s+" + num, text)
    if not reference or not latest:
        raise ValueError("BVB股票页面缺少明确的价格字段")
    clock = re.search(r"Data/ora\s+(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2})", text[latest.end():])
    if not clock:
        raise ValueError("BVB股票缺少成交时间")
    last, delta, pct = map(number, latest.groups())
    prev = number(reference[1])
    if min(last, prev) <= 0 or abs(last-prev-delta) > 0.00011 or abs((last/prev-1)*100-pct) > 0.011:
        raise ValueError("BVB股票价格、参考价与涨跌幅不一致")
    return dict(last=last, prev=prev, pct=(last/prev-1)*100,
                timestamp=datetime.strptime(clock[1], "%d.%m.%Y %H:%M:%S").replace(tzinfo=ZoneInfo("Europe/Bucharest")),
                source="BVB official stock page", provider="bvb", provider_symbol="BVB:"+symbol,
                quote_kind="官方页面最后成交价；公开页面可能延迟", prev_basis="BVB Pret referinta官方参考价")


def bvb_stock_quote(symbol):
    response = requests.get("https://www.bvb.ro/FinancialInstruments/Details/FinancialInstrumentsDetails.aspx",
                            params={"s": symbol}, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}, timeout=25)
    response.raise_for_status()
    return parse_bvb_stock(response.text, symbol)


# -------------------- Yahoo 分时行情 --------------------

def yahoo_quote(symbol, tz):
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    bars = ticker.history(
        period="5d",
        interval="1m",
        auto_adjust=False,
    )
    if bars.empty or bars["Close"].dropna().empty:
        raise ValueError("Yahoo 没有返回分时行情")

    close = bars["Close"].dropna()
    stamp = close.index[-1].to_pydatetime()

    if stamp.tzinfo is None:
        raise ValueError("Yahoo 报价缺少时区")

    last = float(close.iloc[-1])
    quote_kind = "1分钟K线收盘及其起始时间"
    # Capture intraday metadata before requesting daily history, which can
    # replace yfinance's cached chart metadata. Keep price and time paired.
    try:
        meta = dict(ticker.get_history_metadata())
    except (AttributeError, TypeError, ValueError, OSError):
        meta = {}
    try:
        raw_time = meta["regularMarketTime"]
        market_time = raw_time.to_pydatetime() if hasattr(raw_time, "to_pydatetime") else raw_time
        if not isinstance(market_time, datetime):
            market_time = datetime.fromtimestamp(float(raw_time), stamp.tzinfo)
        if market_time.tzinfo is None:
            raise ValueError("Yahoo metadata timestamp has no timezone")
        market_time = market_time.astimezone(stamp.tzinfo)
        market_price = float(meta["regularMarketPrice"])
        if math.isfinite(market_price) and market_price > 0 and stamp <= market_time <= stamp + timedelta(minutes=2):
            last, stamp = market_price, market_time
            quote_kind = "Yahoo regularMarketPrice及regularMarketTime配对"
    except (KeyError, TypeError, ValueError, OverflowError, OSError):
        pass

    daily = ticker.history(
        period="1mo",
        interval="1d",
        auto_adjust=False,
    )
    if daily.empty:
        raise ValueError("Yahoo 没有返回前收盘价")

    # Keep the daily/session date in the instrument's exchange timezone.  In
    # particular, FX daily bars must not be dated using the dashboard timezone.
    quote_day = stamp.date()
    prior = daily.loc[daily.index.date < quote_day, "Close"].dropna()
    if prior.empty:
        raise ValueError("无法确定前一交易日收盘价")

    # A range response can lag the latest daily session at the opening bell.
    # Retry the exact expected date; never accept an older session as its substitute.
    calendar_key = 'RO' if symbol in ('TLV.RO', 'BRD.RO', 'H2O.RO', 'SNP.RO', 'SNG.RO') else 'US' if symbol in ('^DJI', '^GSPC', '^IXIC') else None
    if calendar_key:
        expected = quote_day - timedelta(days=1)
        while trading_day(calendar_key, expected) is False:
            expected -= timedelta(days=1)
        if trading_day(calendar_key, expected) is not None and prior.index[-1].date() != expected:
            targeted = ticker.history(start=expected.isoformat(), end=quote_day.isoformat(), interval='1d', auto_adjust=False)
            if not targeted.empty:
                exact = targeted.loc[targeted.index.date == expected, 'Close'].dropna()
                if not exact.empty:
                    prior = exact

    prev = float(prior.iloc[-1])
    prev_check = "DAILY"
    prev_basis = "前一交易日日线收盘"
    # Undated chart metadata can reference an older range or settlement.
    # Anchor change to the dated previous daily session instead.

    history = intraday.yahoo_series(bars, symbol=symbol, quote_time=stamp, last=last, timezone=tz)
    return {
        "intraday": history,
        "chart_note": "Yahoo 1分钟行情" if history else "Yahoo无可用的同日分时序列",
        "last": last,
        "provider": "yahoo", "provider_symbol": symbol, "quote_kind": quote_kind,
        "prev": prev,
        "prev_check": prev_check,
        "prev_date": prior.index[-1].date().isoformat(),
        "reference_version": 2,
        "prev_basis": prev_basis,
        "timestamp": stamp,
        "source": "Yahoo Finance",
    }


# -------------------- 时间及有效性检查 --------------------

CALENDAR=json.loads((Path(__file__).with_name('trading-calendar.json')).read_text(encoding='utf-8'))

def trading_day(key, day):
    dates=CALENDAR[key].get(str(day.year))
    if dates is None:return None
    return day.weekday()<5 and day.strftime('%m-%d') not in dates

def validate(key, item, quote, now=None):
    cfg=MARKETS[key];now=now or now_for(key)
    now=now.astimezone(ZoneInfo(cfg['tz']));stamp=quote['timestamp']
    if stamp.tzinfo is None:return 'STALE','报价缺少时区'
    stamp=stamp.astimezone(ZoneInfo(cfg['tz']))
    if not all(isinstance(quote.get(k),(int,float)) and not isinstance(quote.get(k),bool) and math.isfinite(quote[k]) and quote[k]>0 for k in ('last','prev')):
        return 'NA','价格或前收盘价无效'
    if item[1] == 'EURRON=X' and quote.get('provider') == 'yahoo':
        return 'UNVERIFIED', '汇率前收基准已统一，请重新获取行情'
    if quote.get('provider') == 'yahoo' and item[1] in ('^DJI', '^GSPC', '^IXIC', 'TLV.RO', 'BRD.RO', 'H2O.RO', 'SNP.RO', 'SNG.RO'):
        previous_session = stamp.date() - timedelta(days=1)
        while trading_day(key, previous_session) is False:
            previous_session -= timedelta(days=1)
        if trading_day(key, previous_session) is None:
            return 'UNVERIFIED', '前收交易日历尚未覆盖该年份'
        if quote.get('prev_date') != previous_session.isoformat():
            return 'NA', '前收盘价日期不是紧邻的前一交易日，请重新获取行情'
    expected=(quote['last']/quote['prev']-1)*100
    if 'pct' in quote and (not isinstance(quote['pct'],(int,float)) or isinstance(quote['pct'],bool) or not math.isfinite(quote['pct']) or abs(quote['pct']-expected)>0.011):
        return 'NA','涨跌幅与现价及前收不一致'
    if stamp>now+timedelta(minutes=2):return 'STALE','报价时间位于未来'
    if item[1]!='EURRON=X':
        day_open=trading_day(key,now.date())
        if day_open is None:return 'UNVERIFIED','交易日历尚未覆盖该年份，需更新日历后校验'
        closing=tuple(CALENDAR['early_closes'].get(key,{}).get(now.date().isoformat(),cfg['closing']))
        closed=not day_open or (now.hour,now.minute)<cfg['opening'] or (now.hour,now.minute)>=closing
        if closed:
            last_session=now.date()
            if not day_open or (now.hour,now.minute)<cfg['opening']:
                last_session-=timedelta(days=1)
                while trading_day(key,last_session) is False or last_session.weekday()>=5:last_session-=timedelta(days=1)
            if stamp.date()<last_session:return 'STALE','报价早于最近交易日，不能作为有效收盘快照'
            return 'CLOSED','常规股票交易窗口关闭；此快照不作为开盘行情发布'
    if stamp.date()!=now.date() or now-stamp>MAX_AGE:return 'STALE',f'报价{stamp:%Y-%m-%d %H:%M:%S %Z}，非当天或超过17分钟（含15分钟延迟容差）'
    if item[1]!='EURRON=X' and (stamp.hour,stamp.minute)<cfg['opening']:return 'STALE','报价产生于常规股票开盘前'
    delay=quote.get('delay_seconds')
    note=(f'TV标示延迟{delay//60}分钟；采用分时K线时间' if delay else 'TV标示streaming；采用分时K线时间' if delay==0 else '来源仍可能存在延迟')
    return 'OK','时间通过校验；'+note


def apply_verify(q):
    """Hide values whose two sources disagree (and, in strict mode, unconfirmed ones)."""
    if q.get("status") not in ("OK", "CLOSED"):
        return
    verdict = q.get("verify")
    if verdict == "MISMATCH":
        q["status"], q["reason"] = "CONFLICT", q.get("verify_note", "双源数值不一致")
    elif verdict != "MATCH" and verify.STRICT:
        q["status"], q["reason"] = "UNVERIFIED", q.get("verify_note", "第二来源失败（严格模式）")



def attach_index_series(key, symbol, quote):
    """Attach ACTUAL observations to a validated quote, never a fabricated TV series.

    TradingView scanner is snapshot-only. If that snapshot is selected, fetch
    the same index's independent BVB/Yahoo minutes and label its true provider.
    Reject mismatched symbol/session/last price, and leave the chart empty on
    access failure. Never relabel Yahoo/BVB observations as TradingView data.
    """
    if symbol not in ('BET','BET-NG','BET-FI','^DJI','^GSPC','^IXIC'):
        return quote
    if quote.get('status') not in ('OK','CLOSED'):
        return quote
    if intraday.chart_points(quote,symbol=symbol):
        return quote
    try:
        if key == 'RO':
            series=intraday.bvb_index_series(symbol, quote_time=quote['timestamp'],last=quote['last'])
        else:
            import yfinance as yf
            bars=yf.Ticker(symbol).history(period='5d',interval='1m',auto_adjust=False)
            series=intraday.yahoo_series(bars,symbol=symbol,quote_time=quote['timestamp'],
                                         last=quote['last'],timezone=MARKETS[key]['tz'])
        if series:
            quote['intraday']=series
            quote['chart_source']=series['provider']
            quote['chart_note']='逐点来自 '+series['provider']+'；行情报价来自 '+quote.get('source','未知来源')
        else:
            quote.pop('intraday',None)
            quote['chart_note']='不同交易时段或不同价格，未取得可验证的同品种分时数据'
    except Exception as exc:
        quote.pop('intraday',None)
        quote['chart_note']='分时源不可用：'+type(exc).__name__
    return quote


def fetch_market(key, provider=None):
    provider = provider or quote_provider()
    if provider not in ("hybrid", "tradingview", "original"):
        raise ValueError("未知行情来源")
    data = {}
    verify.begin_fetch()

    for item in MARKETS[key]["items"]:
        label, symbol, _, _, source = item
        try:
            if provider == "hybrid":
                q = hybrid_quote(key, item)
                q["verify"] = "NONE"
                q["verify_note"] = "主源及备用策略；未声称双源一致"
            elif provider == "tradingview" and symbol in TV_SYMBOLS:
                try:
                    q = tradingview_quote(TV_SYMBOLS[symbol])
                except Exception as tv_error:
                    q = original_quote(key, item)
                    q["fallback_reason"] = f"TV获取失败，回退原来源：{type(tv_error).__name__}: {tv_error}"
            else:
                q = original_quote(key, item)

            q["status"], q["reason"] = validate(key, item, q)

            if q["status"] in ("OK", "CLOSED") and "verify" not in q:
                if q.get("provider") == "tradingview":
                    q["verify"], q["verify_note"], q["secondary"] = check_tv_against_original(key, item, q)
                else:
                    q["verify"], q["verify_note"], q["secondary"] = verify.crosscheck(symbol, q["last"], q.get("pct", (q["last"] / q["prev"] - 1) * 100), quote_time=q["timestamp"])
                apply_verify(q)

            apply_verify(q)
            if q["status"] in ("OK", "CLOSED"):
                q.setdefault(
                    "pct",
                    (q["last"] / q["prev"] - 1) * 100,
                )
                attach_index_series(key, symbol, q)

            data[label] = q

        except Exception as exc:
            data[label] = {
                "status": "NA",
                "source": source,
                "reason": f"{type(exc).__name__}: {exc}",
            }

    return data


def refresh(key, data):
    for item in MARKETS[key]["items"]:
        q = data.setdefault(item[0], {"status": "NA", "source": item[4],
                                     "reason": "新增指标尚无缓存，请重新获取真实行情"})
        if "timestamp" in q:
            q["status"], q["reason"] = validate(key, item, q)
            apply_verify(q)


def publishable(key, data):
    refresh(key, data)
    rows = MARKETS[key]["items"]
    return all(data.get(row[0], {}).get("status") == "OK" for row in rows)

