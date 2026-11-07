"""Validated, provider-labelled intraday observations; no invented price points.

A quote and its intraday series refer to the exact same instrument.  Chart
points are never inferred from a quote or from the day high/low.
"""
from datetime import datetime, timedelta
import os
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo
import math
import xml.etree.ElementTree as ET

import requests

# Official BVB data vending service: delayed equities (15m), indices real time.
# Unlike the original online service, the delayed service is the preferred endpoint.
# Some installations require vendor credentials; never store them in the update ZIP.
BVB_DELAYED_ROOT = 'https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx'
BVB_ONLINE_ROOT = 'https://ws.bvb.ro/BVBOnline/Intraday.asmx'
BVB_PROVIDER = 'BVB IndicesDataSeries'
BVB_HEADERS = {'User-Agent': 'ELLERY-WESTCOTT/1.4.23', 'Cache-Control': 'no-cache'}


def bvb_xml(operation, code):
    """Official BVB SOAP 1.1 connection validated against its real 3-index service."""
    if operation not in ('IndicesDataSeries', 'GetIndex') or code not in ('BET', 'BET-NG', 'BET-FI'):
        raise ValueError('未经授权的BVB品种或操作')
    backend = os.getenv('EW_BVB_SERVICE', 'delayed').strip().lower()
    if backend not in ('delayed', 'online'):
        raise ValueError('EW_BVB_SERVICE只允许delayed或online')
    service = BVB_DELAYED_ROOT if backend == 'delayed' else BVB_ONLINE_ROOT
    user, password = os.getenv('EW_BVB_USER', ''), os.getenv('EW_BVB_PASSWORD', '')
    if bool(user) != bool(password):
        raise ValueError('BVB接口用户名和密码必须同时提供')
    envelope = ('<?xml version="1.0" encoding="utf-8"?>'
                '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
                '<soap:Header><Header xmlns="www.bvb.ro">'
                f'<User>{escape(user)}</User><Password>{escape(password)}</Password>'
                '</Header></soap:Header><soap:Body>'
                f'<{operation} xmlns="www.bvb.ro"><code>{code}</code></{operation}>'
                '</soap:Body></soap:Envelope>')
    response = requests.post(
        service, data=envelope.encode('utf-8'), timeout=12,
        headers={**BVB_HEADERS, 'Content-Type': 'text/xml; charset=utf-8',
                 'SOAPAction': f'"www.bvb.ro/{operation}"'},
    )
    response.raise_for_status()
    try:
        root_xml = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise ValueError('BVB服务未返回可解析的XML') from exc
    if any(node.tag.split('}')[-1] == 'Fault' for node in root_xml.iter()):
        raise ValueError('BVB SOAP拒绝请求；检查数据授权')
    if root_xml.tag.rsplit('}', 1)[-1].lower() == 'html':
        raise ValueError('BVB返回了网页而非行情XML')
    return response.content



def _row(value, stamp):
    if isinstance(value, bool):
        return None
    try:
        price = float(value)
    except (ValueError, TypeError):
        return None
    if not math.isfinite(price) or price <= 0 or not isinstance(stamp, datetime) or stamp.tzinfo is None:
        return None
    return {'time': stamp.isoformat(), 'price': price}


def _validate(points, quote_time, last, *, provider, instrument, tz):
    """Limit charts to one session, same symbol, and a quote-consistent last bar."""
    if not isinstance(quote_time, datetime) or quote_time.tzinfo is None:
        return None
    day = quote_time.astimezone(ZoneInfo(tz)).date()
    cleaned = {}
    for point in points:
        if not point:
            continue
        try:
            stamp = datetime.fromisoformat(point['time'])
            val = float(point['price'])
        except (ValueError, TypeError, KeyError):
            continue
        if stamp.tzinfo is None or stamp.astimezone(ZoneInfo(tz)).date() != day:
            continue
        if not math.isfinite(val) or val <= 0 or stamp > quote_time + timedelta(minutes=2):
            continue
        cleaned[stamp.isoformat()] = {'time': stamp.isoformat(), 'price': val}
    rows = sorted(cleaned.values(), key=lambda row: row['time'])
    if len(rows) < 2 or len(rows) > 10000:
        return None
    end = datetime.fromisoformat(rows[-1]['time'])
    if quote_time - end > timedelta(minutes=17):
        return None
    if abs(rows[-1]['price'] / float(last) - 1) > .01:
        return None
    # Constrain export payload; values are observed bars, never interpolated.
    if len(rows) > 600:
        step = max(1, (len(rows) - 1) // 599)
        rows = rows[::step]
        if rows[-1]['time'] != end.isoformat():
            rows.append(cleaned[end.isoformat()])
    return {'provider': provider, 'symbol': instrument, 'session_date': str(day),
            'interval': 'observed', 'points': rows}


def yahoo_series(bars, *, symbol, quote_time, last, timezone):
    """Copy 1-minute bars already fetched in yahoo_quote; no second request."""
    try:
        close = bars['Close'].dropna()
    except (TypeError, KeyError, AttributeError):
        return None
    points = []
    for stamp, price in close.items():
        time = stamp.to_pydatetime() if hasattr(stamp, 'to_pydatetime') else stamp
        points.append(_row(price, time))
    out = _validate(points, quote_time, last, provider='Yahoo Finance 1m', instrument=symbol, tz=timezone)
    if out:
        out['interval'] = '1m'
    return out


def parse_bvb_index_series(xml_bytes, *, symbol, quote_time, last):
    """Parse actual BVB SOAP XML by exact symbol; never derive series from a snapshot."""
    root = ET.fromstring(xml_bytes)
    if any(node.tag.split('}')[-1] == 'Fault' for node in root.iter()):
        raise ValueError('BVB SOAP返回Fault')
    points = []
    for entry in root.iter():
        fields = {node.tag.split('}')[-1]: (node.text or '').strip() for node in entry}
        if fields.get('Code') != symbol:
            continue
        raw = fields.get('LastUpdateTime') or fields.get('TradeTime')
        val = fields.get('CurrentValue') or fields.get('IndexValue')
        if not raw or not val:
            continue
        try:
            dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo('Europe/Bucharest'))
        points.append(_row(val, dt))
    if not points:
        raise ValueError('BVB未返回请求指数的有效分时点')
    return _validate(points, quote_time, last, provider=BVB_PROVIDER,
                     instrument=symbol, tz='Europe/Bucharest')



def bvb_index_series(symbol, *, quote_time, last):
    if symbol not in ('BET', 'BET-NG', 'BET-FI'):
        raise ValueError('Not an authorized BVB index')
    content = bvb_xml('IndicesDataSeries', symbol)
    return parse_bvb_index_series(content, symbol=symbol, quote_time=quote_time, last=last)


def chart_points(quote, *, symbol):
    """Recheck cached provider, instrument and quote status immediately before rendering."""
    if quote.get('status') not in ('OK', 'CLOSED'):
        return []
    series = quote.get('intraday')
    if not isinstance(series, dict) or series.get('symbol') != symbol:
        return []
    provider = series.get('provider')
    if provider not in ('BVB IndicesDataSeries', 'Yahoo Finance 1m'):
        return []
    stamp = quote.get('timestamp')
    if isinstance(stamp, str):
        try: stamp = datetime.fromisoformat(stamp)
        except ValueError: return []
    tz = 'Europe/Bucharest' if symbol.startswith('BET') else 'America/New_York'
    validated = _validate(series.get('points') or [], stamp, quote.get('last'),
                          provider=provider, instrument=symbol, tz=tz)
    return validated['points'] if validated else []