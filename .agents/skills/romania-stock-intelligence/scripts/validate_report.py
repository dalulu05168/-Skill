#!/usr/bin/env python3
"""Offline structural and arithmetic gate for Romania Stock Intelligence JSON.

No quotes are fetched or certified by this script. A 'PASS' means formatting and
self-consistency, not independent external-source authenticity.

Usage: python scripts/validate_report.py path/to/report.json
"""
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

VALID_KINDS = {"morning_0800", "midday_1300", "close_1800", "breaking"}
VALID_STATUS = {"preopen", "open", "close_snapshot", "confirmed_close", "non_trading_day", "unknown"}
VALID_DELAY = {"realtime", "delayed", "end_of_day", "unknown"}
VALID_QUALITY = {"verified", "provisional"}
VALID_EVENT = {"new", "revised", "unchanged"}
REQUIRED = ("report_id", "kind", "produced_at", "timezone", "market_status", "previous_report_id", "metrics", "events", "themes", "coverage_gaps", "notification_channel")
METRIC_REQUIRED = ("series", "value", "unit", "baseline", "observed_at", "timezone", "source_url", "delay_status", "vs_previous_brief", "quality")


def missing_keys(obj, keys, path, errors):
    if not isinstance(obj, dict):
        errors.append(f"{path}: expected object")
        return False
    for key in keys:
        if key not in obj:
            errors.append(f"{path}.{key}: missing")
    return True


def valid_time(raw, zone_name, path, errors):
    if not isinstance(raw, str):
        errors.append(f"{path}: ISO 8601 string required")
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path}: invalid ISO 8601 datetime")
        return None
    if dt.tzinfo is None or dt.utcoffset() is None:
        errors.append(f"{path}: missing timezone UTC offset")
        return None
    try:
        zone = ZoneInfo(zone_name)
    except (TypeError, ZoneInfoNotFoundError):
        errors.append(f"{path}: unknown IANA timezone {zone_name!r}")
        return dt
    if dt.astimezone(zone).utcoffset() != dt.utcoffset():
        errors.append(f"{path}: UTC offset conflicts with {zone_name} at that date")
    return dt


def valid_url(raw, path, errors):
    if not isinstance(raw, str):
        errors.append(f"{path}: source URL must be string")
        return
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.hostname in ("example.com", "example.invalid", "localhost"):
        errors.append(f"{path}: item-level http(s) source URL required; placeholders forbidden")


def finite_num(raw):
    return type(raw) in (int, float) and math.isfinite(raw)


def validate(data):
    errors = []
    if not missing_keys(data, REQUIRED, "report", errors):
        return errors
    if data.get("notification_channel") != "chatgpt_only":
        errors.append("report.notification_channel: must be chatgpt_only")
    if data.get("timezone") != "Europe/Bucharest":
        errors.append("report.timezone: must be Europe/Bucharest")
    kind = data.get("kind")
    if kind not in VALID_KINDS:
        errors.append("report.kind: invalid")
    if data.get("market_status") not in VALID_STATUS:
        errors.append("report.market_status: invalid")
    if data.get("market_status") == "confirmed_close" and data.get("official_close_confirmed") is not True:
        errors.append("report.official_close_confirmed: required true for confirmed_close")
    if kind == "close_1800" and data.get("market_status") == "preopen":
        errors.append("report: impossible 18:00 preopen status")
    rid = data.get("report_id")
    if not isinstance(rid, str) or not re.fullmatch(r"RSI-\d{8}-(0800|1300|1800|BREAKING)", rid):
        errors.append("report.report_id: wrong format")
    elif kind in VALID_KINDS:
        expected = {"morning_0800": "0800", "midday_1300": "1300", "close_1800": "1800", "breaking": "BREAKING"}[kind]
        if rid.rsplit("-", 1)[1] != expected:
            errors.append("report.report_id: does not match report kind")
    report_dt = valid_time(data.get("produced_at"), "Europe/Bucharest", "report.produced_at", errors)
    if report_dt and isinstance(rid, str) and re.fullmatch(r"RSI-\d{8}-(0800|1300|1800|BREAKING)", rid):
        if report_dt.strftime("%Y%m%d") != rid.split("-")[1]:
            errors.append("report.report_id: date must match Bucharest produced_at")
    prev_id = data.get("previous_report_id")
    if prev_id is not None and (not isinstance(prev_id, str) or not re.fullmatch(r"RSI-\d{8}-(0800|1300|1800|BREAKING)", prev_id)):
        errors.append("report.previous_report_id: invalid format")
    for field in ("metrics", "events", "themes", "coverage_gaps"):
        if not isinstance(data.get(field), list):
            errors.append(f"report.{field}: expected array")
    if not isinstance(data.get("metrics"), list):
        return errors
    if not data.get("metrics") and not data.get("coverage_gaps"):
        errors.append("report: no figures and no documented coverage gap")
    seen = set()
    for idx, m in enumerate(data.get("metrics", [])):
        p = f"metrics[{idx}]"
        if not missing_keys(m, METRIC_REQUIRED, p, errors):
            continue
        if not isinstance(m.get("series"), str) or not m["series"].strip():
            errors.append(f"{p}.series: non-empty string required")
        if not finite_num(m.get("value")):
            errors.append(f"{p}.value: finite numeric value required, or move to coverage_gaps")
        if not isinstance(m.get("unit"), str) or not m["unit"].strip():
            errors.append(f"{p}.unit: non-empty unit required")
        dt = valid_time(m.get("observed_at"), m.get("timezone"), f"{p}.observed_at", errors)
        if dt and report_dt and dt > report_dt:
            errors.append(f"{p}.observed_at: cannot be after report issuance")
        identity = (m.get("series"), m.get("observed_at"))
        if identity in seen:
            errors.append(f"{p}: duplicate series & observation timestamp")
        seen.add(identity)
        valid_url(m.get("source_url"), f"{p}.source_url", errors)
        if m.get("delay_status") not in VALID_DELAY:
            errors.append(f"{p}.delay_status: invalid")
        if m.get("delay_status") == "delayed" and (not isinstance(m.get("delay_minutes"), int) or m["delay_minutes"] < 0):
            errors.append(f"{p}.delay_minutes: nonnegative integer required when delayed")
        if m.get("quality") not in VALID_QUALITY:
            errors.append(f"{p}.quality: invalid")
        b = m.get("baseline")
        if missing_keys(b, ("description", "status"), f"{p}.baseline", errors):
            if b.get("status") not in ("compared", "not_available"):
                errors.append(f"{p}.baseline.status: invalid")
            if not isinstance(b.get("description"), str) or not b["description"].strip():
                errors.append(f"{p}.baseline.description: explain comparison benchmark")
            if b.get("status") == "compared" and not finite_num(b.get("value")):
                errors.append(f"{p}.baseline.value: numeric required for compared baseline")
            if b.get("status") == "compared":
                valid_time(b.get("observed_at"), m.get("timezone"), f"{p}.baseline.observed_at", errors)
        c = m.get("vs_previous_brief")
        if missing_keys(c, ("status",), f"{p}.vs_previous_brief", errors):
            if c.get("status") == "compared":
                if not isinstance(c.get("previous_report_id"), str):
                    errors.append(f"{p}.vs_previous_brief.previous_report_id: required")
                if prev_id is None:
                    errors.append(f"{p}.vs_previous_brief: cannot compare with an absent report.previous_report_id")
                if prev_id is not None and c.get("previous_report_id") != prev_id:
                    errors.append(f"{p}.vs_previous_brief: comparison must match reported previous_report_id")
                if not finite_num(c.get("previous_value")) or not finite_num(c.get("change_value")):
                    errors.append(f"{p}.vs_previous_brief: previous_value and change_value required")
                elif finite_num(m.get("value")) and abs((m["value"] - c["previous_value"]) - c["change_value"]) > 0.00001:
                    errors.append(f"{p}.vs_previous_brief: numeric change does not match current minus previous")
                if c.get("change_unit") != m.get("unit"):
                    errors.append(f"{p}.vs_previous_brief.change_unit: must equal metric unit for absolute change")
            elif c.get("status") == "not_available":
                if not isinstance(c.get("reason"), str) or not c["reason"].strip():
                    errors.append(f"{p}.vs_previous_brief.reason: required")
            else:
                errors.append(f"{p}.vs_previous_brief.status: invalid")
    for idx, e in enumerate(data.get("events", [])):
        p = f"events[{idx}]"
        if not missing_keys(e, ("headline", "published_at", "effective_at", "timezone", "source_url", "change_status"), p, errors):
            continue
        if not isinstance(e.get("headline"), str) or not e["headline"].strip():
            errors.append(f"{p}.headline: empty")
        valid_time(e.get("published_at"), e.get("timezone"), f"{p}.published_at", errors)
        if e.get("effective_at") is not None:
            valid_time(e["effective_at"], e.get("timezone"), f"{p}.effective_at", errors)
        valid_url(e.get("source_url"), f"{p}.source_url", errors)
        if e.get("change_status") not in VALID_EVENT:
            errors.append(f"{p}.change_status: invalid")
    for idx, t in enumerate(data.get("themes", [])):
        if not missing_keys(t, ("title", "facts", "analysis", "scenario", "risk"), f"themes[{idx}]", errors):
            continue
        for field in ("title", "facts", "analysis", "scenario", "risk"):
            if not isinstance(t.get(field), str):
                errors.append(f"themes[{idx}].{field}: string required")
    for idx, gap in enumerate(data.get("coverage_gaps", [])):
        if not missing_keys(gap, ("series", "reason", "next_action"), f"coverage_gaps[{idx}]", errors):
            continue
        for field in ("series", "reason", "next_action"):
            if not isinstance(gap.get(field), str) or not gap[field].strip():
                errors.append(f"coverage_gaps[{idx}].{field}: non-empty string required")
    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_report.py report.json")
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot parse JSON: {exc}")
        return 2
    errors = validate(data)
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for issue in errors:
            print(" -", issue)
        return 1
    print("PASS: structural/temporal/arithmetic checks passed; source truth requires separate verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
