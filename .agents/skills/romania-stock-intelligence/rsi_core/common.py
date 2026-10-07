"""Shared strict datetime, numerical, evidence and JSON helpers (stdlib only)."""
import ipaddress
import json
import math
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


class DataError(ValueError):
    """Data insufficient, inconsistent, or potentially misleading."""


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise DataError(f"Cannot read valid JSON from {path}: {e}") from e


def number(value, field):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise DataError(f"{field}: a finite JSON number is required")
    return float(value)


def timestamp(value, zone="Europe/Bucharest", field="timestamp"):
    if not isinstance(value, str):
        raise DataError(f"{field}: must be ISO 8601 with explicit UTC offset")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not parsed.tzinfo or parsed.utcoffset() is None:
            raise ValueError("timezone missing")
        expected = parsed.astimezone(ZoneInfo(zone)).utcoffset()
        if parsed.utcoffset() != expected:
            raise ValueError(f"offset conflicts with {zone} at that date")
        return parsed
    except (ValueError, KeyError) as e:
        raise DataError(f"{field}: {e}") from e


def web_url(value, field="source_url"):
    if not isinstance(value, str):
        raise DataError(f"{field}: https URL required")
    parsed = urlparse(value)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise DataError(f"{field}: public HTTPS URL required")
    if host in ("localhost", "example.com", "example.org", "example.invalid") or host.endswith(".local"):
        raise DataError(f"{field}: placeholder/local URL rejected")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None and not ip.is_global:
        raise DataError(f"{field}: non-public IP rejected")
    if "." not in host:
        raise DataError(f"{field}: public hostname required")
    return value


def nonempty(value, field):
    if not isinstance(value, str) or not value.strip():
        raise DataError(f"{field}: non-empty string required")
    return value.strip()


def write_json(path, obj):
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_object(obj):
    import hashlib
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
