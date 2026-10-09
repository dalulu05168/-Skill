#!/usr/bin/env python3
"""Unified *internal* finance SKILL runner: one call, no ZIP installation.

Runs real local RSS/roster/market-metadata code and emits a gated review packet.
Does NOT use an LLM, independently verify article content, trade or publish.
Python 3.11+, stdlib only.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
INTEL = ROOT / ".agents/skills/romania-stock-intelligence"
DIRECTOR = ROOT / "skills/romania-market-director"
sys.path.insert(0, str(INTEL))
sys.path.insert(0, str(INTEL / "scripts"))
sys.path.insert(0, str(DIRECTOR / "scripts"))

import rss_intake  # noqa: E402
import validate_persona_roster as personas  # noqa: E402
from finance_skill_editorial import audit_editorial  # noqa: E402
from content_routing import routing_snapshot  # noqa: E402
from rsi_core.quality import audit_observations  # noqa: E402

BUCHAREST = ZoneInfo("Europe/Bucharest")
SOURCE_ID = "BVB_NEWS_RSS"
SKILL_ORDER = [
    "skills/bvb-fact-check/SKILL.md",
    "skills/news-priority/SKILL.md",
    "skills/romania-market-director/SKILL.md",
    "skills/character-consistency/SKILL.md",
    "skills/script-qa/SKILL.md",
]
BOUNDARIES = (
    "News is unverified until original-source human review; metadata checks "
    "are NOT factual verification. The 65 members are fictional educational "
    "personas, not customer testimonials. No autonomous external publication."
)


def slot_for(now, requested=None):
    schedule = json.loads((INTEL / "config/schedule.json").read_text(encoding="utf-8"))
    if schedule.get("timezone") != "Europe/Bucharest" or len(schedule.get("runs", [])) != 16:
        raise ValueError("Authoritative 16-node schedule missing or changed")
    local = now.astimezone(BUCHAREST)
    runs = schedule["runs"]
    if requested:
        chosen = next((x for x in runs if x["id"] == requested), None)
        if not chosen:
            raise ValueError("Unknown node ID (expected RO-01 through RO-16)")
        return {**chosen, "date": local.date().isoformat(),
                "slot_mode": "explicit_node_no_run_claim",
                "timezone": "Europe/Bucharest"}
    for delta in range(8):
        day = local.date() + timedelta(days=delta)
        weekday = day.weekday()
        label = "工作日" if weekday < 5 else "周六" if weekday == 5 else "周日"
        for entry in runs:
            if entry["days"] != label:
                continue
            hh, mm = map(int, entry["publication"].split(":"))
            instant = datetime(day.year, day.month, day.day, hh, mm, tzinfo=BUCHAREST)
            if instant > local:
                return {**entry, "date": day.isoformat(),
                        "slot_mode": "next_preparation_target_not_scheduled",
                        "timezone": "Europe/Bucharest"}
    raise ValueError("No upcoming node in 8 days")


def validate_messages(messages, roster, selected):
    errors = []
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")
    for index, msg in enumerate(messages, 1):
        if not isinstance(msg, dict):
            errors.append(f"message {index}: object required")
            continue
        if not isinstance(msg.get("text"), str) or not msg["text"].strip():
            errors.append(f"message {index}: nonempty text required")
        if msg.get("speaker") == "教授" and selected["id"] != "RO-10":
            errors.append(f"message {index}: professor permitted only in RO-10 (19:30 class)")
        cid = msg.get("character_id")
        if cid is None:
            if msg.get("speaker") not in {"助理", "教授", "系统"}:
                errors.append(f"message {index}: explicit assistant/professor/system speaker required")
            continue
        key = str(cid).zfill(2)
        identity = roster.get(key)
        if not identity:
            errors.append(f"message {index}: nonexistent member {key}")
        elif any(msg.get(field) != identity[target] for field, target
                 in (("name", "name"), ("gender", "gender"), ("role", "role"))):
            errors.append(f"message {index}: ID/name/gender/new-old classification mismatch ({key})")
        if msg.get("speaker") == "教授":
            errors.append(f"message {index}: persona cannot impersonate professor")
    return errors


def run_pipeline(spec=None, *, at=None, node_id=None, fetch_rss=False, state_file=None):
    """Return report; network access happens ONLY when fetch_rss=True."""
    spec = spec if spec is not None else {}
    if not isinstance(spec, dict):
        raise ValueError("Input must be a JSON object")
    if fetch_rss and state_file is None:
        raise ValueError("--fetch-rss needs --state outside the repository")
    now = at or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("--at requires ISO 8601 time with UTC offset")
    selected = slot_for(now, requested=node_id)
    roster = personas.validate()  # loads all 65 complete profiles and cross-checks identity
    messages = spec.get("messages", [])
    issues = validate_messages(messages, roster, selected)
    editorial = audit_editorial(spec.get("editorial_packet"), messages)
    issues.extend(editorial["issues"])
    if isinstance(spec.get("editorial_packet"), dict):
        packet = spec["editorial_packet"]
        if packet.get("date") != selected["date"] or packet.get("node_id") != selected["id"]:
            issues.append("editorial_packet date/node does not match selected slot")
    queue = spec.get("news_queue")
    if queue is not None and (not isinstance(queue, dict) or not isinstance(queue.get("items"), list)):
        raise ValueError("news_queue must be an RSS review report with items array")
    if fetch_rss:
        payload = rss_intake.official_fetch(SOURCE_ID)
        items = rss_intake.parse_feed(payload, SOURCE_ID)
        path = Path(state_file)
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        updated, rows = rss_intake.triage(items, previous)
        # State is persisted *only* after successful fetch/parse/triage.
        rss_intake.write_json(path, updated)
        source = "official_rss_fetched_articles_not_verified"
    else:
        rows = queue["items"] if queue else []
        source = "submitted_queue_not_source_attested" if queue else "no_news_input"

    news = []
    for i, item in enumerate(rows):
        if not isinstance(item, dict) or not all(
            isinstance(item.get(f), str) and item.get(f)
            for f in ("item_id", "title", "url", "digest")
        ):
            issues.append(f"news item {i+1}: invalid review row")
            continue
        if not rss_intake._official(item["url"]):
            issues.append(f"news item {i+1}: untrusted article URL")
            continue
        news.append({
            "item_id": item["item_id"], "digest": item["digest"],
            "title": item["title"], "url": item["url"],
            "published_at": item.get("published_at"),
            "change_state": item.get("change_state", "unconfirmed"),
            "review_priority": ("review_soon" if item.get("urgency_hint") ==
                                "priority_review_candidate" else "routine_review"),
            "evidence_status": "UNVERIFIED", "requires_human_article_review": True,
        })
    news.sort(key=lambda r: (r["review_priority"] != "review_soon", r["title"]))

    observations = spec.get("observations")
    audit = None
    if observations is not None:
        registry = json.loads((INTEL / "config/source-registry.json").read_text(encoding="utf-8"))
        audit = audit_observations(observations, registry, now=now)
        if audit["gate"] == "fail":
            issues.append("Financial observation metadata audit failed")
    if messages and not spec.get("fictional_simulation_notice", False):
        issues.append("Draft containing personas lacks explicit fictional simulation notice")
    if any(m.get("speaker") == "教授" for m in messages if isinstance(m, dict)):
        if selected["id"] != "RO-10":
            issues.append("Professor outside authorized class slot")

    return {
        "schema_version": "1.0",
        "runner": "unified-finance-skill-hub",
        "generated_at": now.isoformat(),
        "source_scope": "dalulu05168/-Skill only; no cross-project character or data import",
        "slot": selected,
        "content_classification": {
            "category": next(r["category"] for r in routing_snapshot()["nodes"] if r["id"] == selected["id"]),
            "schedule_unchanged": True, "review_required": True,
            "message_targets": routing_snapshot()["daily_targets"],
        },
        "routing": {
            "skill_sequence": SKILL_ORDER,
            "news_fact_check": "manual_original_article_review_required",
            "news_priority": "keyword_triage_only_not_verified",
            "assistant": "editorial_brief_task_only_not_generated",
            "professor": ("evening_class_editorial_brief_task_only_not_generated"
                          if selected["id"] == "RO-10" else "not_in_current_slot"),
            "members": "validated_65_fictional_personas_only",
            "script_qa": "structural_check_plus_manual_editor_required",
        },
        "news": {"feed": SOURCE_ID if fetch_rss else None, "acquisition": source,
                 "pending_count": len(news), "items": news},
        "market_metadata_audit": audit or {"gate": "not_run", "reason": "No observations supplied"},
        "editorial_audit": editorial,
        "characters": {"roster_count": len(roster), "draft_message_count": len(messages),
                       "identity_gate": "fail" if issues else "pass_for_checked_fields"},
        "review": {
            "status": "BLOCKED" if issues else "NEEDS_REVIEW",
            "issues": issues,
            "next_action": ("Correct input/identity or metadata violations"
                            if issues else "Verify original news and data, prepare assistant/class draft, perform human editorial approval"),
            "publish_status": "BLOCKED_NO_AUTOMATIC_PUBLICATION",
            "boundaries": BOUNDARIES,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="One finance SKILL route -> internal review packet")
    parser.add_argument("--input", help="Optional JSON: news_queue, observations and/or messages")
    parser.add_argument("--fetch-rss", action="store_true", help="Explicitly fetch official BVB news RSS")
    parser.add_argument("--state", help="Outside-repo persistent news review state (needed for --fetch-rss)")
    parser.add_argument("--node", help="Explicit 16-node ID, e.g. RO-10; default next local slot")
    parser.add_argument("--at", help="Offset-aware ISO-8601 time for reproducible routing")
    parser.add_argument("--out", help="Output review JSON; defaults to stdout")
    args = parser.parse_args(argv)
    try:
        spec = json.loads(Path(args.input).read_text(encoding="utf-8")) if args.input else {}
        clock = datetime.fromisoformat(args.at.replace("Z", "+00:00")) if args.at else None
        report = run_pipeline(spec, at=clock, node_id=args.node,
                              fetch_rss=args.fetch_rss, state_file=args.state)
        if args.out:
            rss_intake.write_json(args.out, report)
            print(f"Internal review packet: {args.out}")
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2 if report["review"]["status"] == "BLOCKED" else 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"SKILL HUB FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
