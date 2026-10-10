"""Module 1 -> independent editorial fact-check -> Module 3 evidence handoff.

An input saying "verified":true never attests authenticity. This gate strictly
validates source provenance, source-specific records, timestamps, units and
explicit *human* review metadata. It is NOT network fact verification and never
authorizes public publication or real trades.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, time, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from news_collection import _config

BUCHAREST = ZoneInfo("Europe/Bucharest")
SHA256 = re.compile(r"^[a-fA-F0-9]{64}$")
ALLOWED_KINDS = {"news", "market", "macro", "course_source"}

def _date_time(value, label):
    if not isinstance(value, str):
        raise ValueError(label + " missing")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(label + " invalid ISO8601") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(label + " timezone required")
    return dt.astimezone(timezone.utc)

def _original_url(source, url):
    if not isinstance(url, str) or len(url) > 2048:
        return False
    p = urlsplit(url)
    approved = set(source.get("allowed_hosts") or [])
    registry_url = urlsplit(source["uri"])
    approved.add(registry_url.hostname)
    try:
        return (p.scheme == "https" and p.hostname in approved and
                p.port in (None, 443) and p.username is None and
                p.password is None and p.path not in ("", "/"))
    except ValueError:
        return False

def review_handoff(packet, *, no_later_than=None):
    """Reject unverifiable evidence; never convert user-provided claims into confirmed data.

    An 'APPROVED' record is a named human's check of an original document, not
    an independent machine certification. Hash is provenance metadata for the
    saved original; it isn't sufficient alone to prove accurate facts.
    """
    issues = []
    if not isinstance(packet, dict):
        return {"status": "BLOCKED", "issues": ["Review packet required"],
                "usable_facts": [], "facts_machine_verified": False,
                "public_release_allowed": False}
    plan, slots, sources = _config()
    id = packet.get("node_id")
    slot = next((s for s in slots if s["id"] == id), None)
    if slot is None:
        issues.append("Unknown node")
    day = packet.get("date")
    try:
        run_day = datetime.fromisoformat(day).date()
        if day != run_day.isoformat() or isinstance(day, bool):
            raise ValueError
    except (ValueError, TypeError):
        run_day = None
        issues.append("Valid calendar date YYYY-MM-DD required")
    cutoff = None
    if slot and run_day:
        run_clock = time.fromisoformat(slot["publication"])
        cutoff = datetime.combine(run_day, run_clock, tzinfo=BUCHAREST).astimezone(timezone.utc)
        label = ("工作日" if run_day.weekday() < 5 else
                 "周六" if run_day.weekday() == 5 else "周日")
        if slot["days"] != label:
            issues.append("Node is not scheduled on that date")
    if no_later_than is not None:
        if no_later_than.tzinfo is None or no_later_than.utcoffset() is None:
            raise ValueError("no_later_than requires timezone")
        if cutoff and cutoff > no_later_than.astimezone(timezone.utc):
            issues.append("Future slot; cannot use information not yet published")
    rows = packet.get("facts")
    if not isinstance(rows, list) or len(rows) > 30:
        rows = []
        issues.append("facts must be a list with at most 30 records")
    if packet.get("news_images") not in (None, False, []):
        issues.append("News images are disabled")
    verified = []
    for n, row in enumerate(rows, 1):
        errors = []
        if not isinstance(row, dict):
            issues.append(f"fact {n}: object required")
            continue
        kind, source_id = row.get("kind"), row.get("source_id")
        if kind not in ALLOWED_KINDS:
            errors.append("invalid kind")
        source = sources.get(source_id) if isinstance(source_id, str) else None
        if source is None:
            errors.append("source_id not in official source registry")
        elif source_id not in {x[0] for x in plan["source_sections"].get(id, [])}:
            errors.append("source not scheduled for this node")
        if source is not None and not _original_url(source, row.get("original_url")):
            errors.append("original_url is not an official issuer/record page")
        for field in ("claim", "original_excerpt", "reviewer", "market_relevance",
                      "counter_factors", "uncertainty"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append("missing " + field)
        if row.get("review_decision") != "APPROVED":
            errors.append("explicit editorial approval required")
        if row.get("original_page_opened") is not True:
            errors.append("reviewer must check original page")
        if not isinstance(row.get("evidence_sha256"), str) or not SHA256.fullmatch(row["evidence_sha256"]):
            errors.append("original source SHA256 provenance required")
        timestamps = {}
        for field in ("published_at", "observed_at", "reviewed_at"):
            try:
                timestamps[field] = _date_time(row.get(field), field)
            except ValueError as exc:
                errors.append(str(exc))
        if cutoff:
            for field, dt in timestamps.items():
                if dt > cutoff:
                    errors.append(field + " after requested article/lesson time")
        if timestamps.get("observed_at") and timestamps.get("published_at") and timestamps["observed_at"] < timestamps["published_at"]:
            errors.append("observation earlier than publication")
        if kind == "market":
            for field in ("instrument", "value", "unit", "baseline", "delay_status"):
                if not isinstance(row.get(field), (str, int, float)) or isinstance(row.get(field), bool) or not str(row[field]).strip():
                    errors.append("market missing " + field)
        if errors:
            issues.extend(f"fact {n}: {s}" for s in errors)
        else:
            verified.append({
                "source_id": source_id, "kind": kind,
                "claim": row["claim"], "original_url": row["original_url"],
                "original_excerpt": row["original_excerpt"],
                "evidence_sha256": row["evidence_sha256"].lower(),
                "published_at": row["published_at"],
                "observed_at": row["observed_at"],
                "reviewed_at": row["reviewed_at"],
                "reviewer": row["reviewer"],
                "market_relevance": row["market_relevance"],
                "counter_factors": row["counter_factors"],
                "uncertainty": row["uncertainty"],
                "data": {k: row[k] for k in ("instrument","value","unit","baseline","delay_status") if k in row},
            })
    if not rows:
        issues.append("No approved factual sources; educational theory only")
    return {
        "status": "BLOCKED" if issues else "EDITOR_REVIEWED_FOR_SCRIPT",
        "issues": issues, "usable_facts": verified if not issues else [],
        "facts_machine_verified": False,
        "independent_original_article_review": "DECLARED_BY_NAMED_HUMAN_NOT_RECHECKED_BY_THIS_CODE",
        "human_source_review_required": True,
        "public_release_allowed": False, "news_images_enabled": False,
        "date": day, "node_id": id,
    }
