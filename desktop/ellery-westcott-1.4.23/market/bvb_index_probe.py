"""BVB official 3-index historical series probe for ELLERY WESTCOTT desktop.
This verifies transport, XML shape, instrument identity and evidence, not Windows UI.
No synthetic prices, credentials, or chart drawings are generated here.
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

SYMBOLS = ("BET", "BET-NG", "BET-FI")
ROOT = "https://ws.bvb.ro/BVBDelayedWS/Intraday.asmx"
TZ = ZoneInfo("Europe/Bucharest")
FIELDS = {
    "symbol": ("Code", "IndexCode"),
    "time": ("LastUpdateTime", "TradeTime", "DateTime", "Timestamp"),
    "price": ("CurrentValue", "IndexValue", "Value"),
}
def local(tag):
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]

def parse_series(xml, symbol):
    """Return only observed points explicitly labelled with the requested symbol."""
    if symbol not in SYMBOLS:
        raise ValueError("unsupported_index")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ValueError("malformed_xml") from exc
    if any(local(node.tag) == "Fault" for node in root.iter()):
        raise ValueError("soap_fault")
    points = {}
    for row in root.iter():
        children = {local(child.tag): (child.text or "").strip() for child in row}
        if len(children) < 3:
            continue
        code = next((children[k] for k in FIELDS["symbol"] if children.get(k)), None)
        if code != symbol:
            continue
        when = next((children[k] for k in FIELDS["time"] if children.get(k)), None)
        price = next((children[k] for k in FIELDS["price"] if children.get(k)), None)
        if not when or not price:
            continue
        try:
            timestamp = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=TZ)
            value = float(price)
            if not (0 < value < 1e12):
                continue
        except (ValueError, OverflowError):
            continue
        iso = timestamp.astimezone(TZ).isoformat()
        points[iso] = {"time": iso, "price": value}
    return [points[k] for k in sorted(points)]

def request_service(symbol, operation="IndicesDataSeries", timeout=12):
    if symbol not in SYMBOLS or operation not in ("IndicesDataSeries", "GetIndex"):
        raise ValueError("invalid_service_operation")
    qs = urllib.parse.urlencode({"code": symbol})
    base_headers = {
        "User-Agent": "ELLERY-WESTCOTT-Source-Probe/1.4.23",
        "Accept": "application/xml,text/xml",
        "Cache-Control": "no-cache",
    }
    endpoint = f"{ROOT}/{operation}"
    envelope = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        '<soap:Header><Header xmlns="www.bvb.ro">'
        '<User></User><Password></Password>'
        '</Header></soap:Header>'
        f'<soap:Body><{operation} xmlns="www.bvb.ro">'
        f'<code>{symbol}</code></'
        f'{operation}></soap:Body></soap:Envelope>'
    ).encode("utf-8")
    methods = [
        ("GET", urllib.request.Request(f"{endpoint}?{qs}", headers=base_headers)),
        ("FORM_POST", urllib.request.Request(
            endpoint, data=qs.encode("ascii"), method="POST",
            headers={**base_headers, "Content-Type": "application/x-www-form-urlencoded"})),
        ("SOAP_1_1", urllib.request.Request(
            ROOT, data=envelope, method="POST",
            headers={**base_headers, "Content-Type": "text/xml; charset=utf-8",
                     "SOAPAction": f'"www.bvb.ro/{operation}"'})),
    ]
    errors = []
    for label, req in methods:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = resp.read(2_000_001)
                if len(payload) > 2_000_000:
                    raise ValueError("oversized_response")
                if not payload.lstrip().startswith(b"<"):
                    raise ValueError("response_not_xml")
                ET.fromstring(payload)  # reject HTML and malformed XML
                if b"<html" in payload[:500].lower():
                    raise ValueError("unexpected_html")
                print(f'BVB_TRANSPORT_SUCCESS symbol={symbol} method={label}', file=sys.stderr)
                return payload
        except urllib.error.HTTPError as exc:
            errors.append(f"{label}_HTTP_{exc.code}")
        except urllib.error.URLError as exc:
            errors.append(f"{label}_{type(exc.reason).__name__}")
        except (TimeoutError, OSError, ET.ParseError, ValueError) as exc:
            errors.append(f"{label}_{type(exc).__name__}")
    raise ValueError(";".join(errors))


def check(symbol, now=None):
    now = now or dt.datetime.now(TZ)
    info = {"symbol": symbol, "provider": "BVB delayed official",
            "operation": "IndicesDataSeries", "source_url": ROOT,
            "checked_at": now.isoformat(), "status": "NOT_VERIFIED",
            "points": 0, "session_date": None, "latest_time": None}
    try:
        data = request_service(symbol)
        series = parse_series(data, symbol)
        if len(series) < 2:
            raise ValueError("insufficient_matching_points")
        days = {p["time"][:10] for p in series}
        if len(days) != 1:
            raise ValueError("mixed_market_dates")
        latest = series[-1]["time"]
        info.update(points=len(series), session_date=next(iter(days)), latest_time=latest)
        # Last trading session series might be older over a weekend; connectivity
        # is not the same as ready-to-publish, and must never imply LIVE.
        age = (now - dt.datetime.fromisoformat(latest)).total_seconds()
        info["age_minutes"] = round(age / 60, 2)
        info["status"] = "HISTORICAL_SERIES_OK"
        if age < -120:
            info["status"] = "INVALID_FUTURE_TIMESTAMP"
        elif 0 <= age <= 17 * 60 and now.weekday() < 5:
            info["status"] = "RECENT_SERIES_AVAILABLE"
    except urllib.error.HTTPError as exc:
        info["error"] = f"HTTP_{exc.code}"
    except (urllib.error.URLError, TimeoutError) as exc:
        info["error"] = type(exc).__name__
    except (ValueError, OSError) as exc:
        info["error"] = str(exc)
    return info

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="build/market-bvb/evidence.json")
    args = parser.parse_args(argv)
    results = [check(symbol) for symbol in SYMBOLS]
    ok = all(x["status"] in ("HISTORICAL_SERIES_OK", "RECENT_SERIES_AVAILABLE") for x in results)
    report = {"purpose": "non-publishing provider connectivity check",
              "verified_3_of_3": ok, "release_approved": False,
              "actual_windows_template_tested": False,
              "results": results}
    from pathlib import Path
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if ok else 2

if __name__ == "__main__":
    sys.exit(main())
