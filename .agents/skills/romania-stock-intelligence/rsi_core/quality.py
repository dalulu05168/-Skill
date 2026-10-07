"""Evidence checks and same-period cross-source conflict detection.

This is a local quality gate, NOT external truth or live-price certification.
"""
from datetime import datetime, timezone
from urllib.parse import urlparse
from .common import DataError, load_json, nonempty, number, timestamp, web_url

DELAY = {"realtime", "delayed", "end_of_day", "unknown"}
STATUS = {"publisher_observed", "provisional"}


def audit_observations(payload, registry=None, now=None, tolerance_pct=0.5, max_age_minutes=1440):
    """Fail closed for missing provenance. Return JSON-serializable findings.

    Comparability requires equal instrument, unit, observation date and <=15m time gap.
    Conflicts are observations needing reconciliation, NOT proof either source is right.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("observations"), list):
        raise DataError("observations: list required")
    if tolerance_pct < 0 or max_age_minutes < 0:
        raise DataError("tolerance and max age cannot be negative")
    refs = {s["id"]: s for s in (registry or {}).get("sources", [])}
    clock = now or datetime.now(timezone.utc)
    entries, findings = [], []
    for i, rec in enumerate(payload["observations"]):
        name = f"observations[{i}]"
        try:
            if not isinstance(rec, dict):
                raise DataError("object required")
            instrument = nonempty(rec.get("instrument"), "instrument")
            unit = nonempty(rec.get("unit"), "unit")
            val = number(rec.get("value"), "value")
            tz = nonempty(rec.get("timezone"), "timezone")
            observed = timestamp(rec.get("observed_at"), tz, "observed_at")
            source_id = nonempty(rec.get("source_id"), "source_id")
            url = web_url(rec.get("source_url"))
            evidence = nonempty(rec.get("evidence_locator"), "evidence_locator")
            if rec.get("delay_status") not in DELAY:
                raise DataError("delay_status invalid")
            if rec.get("status") not in STATUS:
                raise DataError("status must be publisher_observed or provisional")
            if rec["delay_status"] == "delayed" and (type(rec.get("delay_minutes")) is not int or rec["delay_minutes"] < 0):
                raise DataError("delay_minutes required for delayed data")
            if refs:
                if source_id not in refs:
                    raise DataError(f"unregistered source_id {source_id}")
                allowed = urlparse(refs[source_id]["uri"]).hostname
                actual = urlparse(url).hostname
                if actual != allowed and not actual.endswith("." + allowed):
                    raise DataError("source URL host differs from declared source")
            if observed > clock:
                findings.append({"code":"FUTURE_OBSERVATION", "severity":"error", "path":name, "message":"Observation is later than audit time"})
            age = (clock - observed).total_seconds() / 60
            if age > max_age_minutes:
                findings.append({"code":"STALE", "severity":"warning", "path":name, "message":f"Observed {age:.1f} minutes before audit; never label live"})
            if rec["delay_status"] == "realtime":
                findings.append({"code":"REALTIME_UNATTESTED", "severity":"warning", "path":name, "message":"A JSON file cannot establish a licensed realtime feed; independently confirm latency"})
            entries.append((i, instrument, unit, val, observed, source_id, evidence))
        except DataError as e:
            findings.append({"code":"INVALID_OBSERVATION", "severity":"error", "path":name, "message":str(e)})
    for x in range(len(entries)):
        for y in range(x + 1, len(entries)):
            a, b = entries[x], entries[y]
            if a[1:3] != b[1:3] or a[4].date() != b[4].date() or abs((a[4]-b[4]).total_seconds()) > 900:
                continue
            denom = max(abs(a[3]), abs(b[3]), 1e-9)
            divergence = 100 * abs(a[3] - b[3]) / denom
            if divergence > tolerance_pct:
                code = "INTERNAL_SOURCE_CONFLICT" if a[5] == b[5] else "SOURCE_CONFLICT"
                findings.append({"code":code, "severity":"error", "path":f"observations[{a[0]}] vs [{b[0]}]", "divergence_pct":round(divergence, 5), "message":"Same-period observations disagree; quarantine until reconciled. Different sources do not imply independent confirmation."})
    errors = sum(x["severity"] == "error" for x in findings)
    return {"gate":"fail" if errors else "pass_with_warnings" if findings else "pass", "audited":len(entries), "input_count":len(payload["observations"]), "errors":errors, "findings":findings, "scope":"metadata, freshness, internal consistency; NOT externally verified quote accuracy"}
