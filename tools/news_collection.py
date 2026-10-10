"""Deterministic Romania news source/time matrix and limited official RSS intake.

The matrix specifies WHEN, WHERE (site/section) and WHAT to inspect.
Only approved BVB RSS streams are machine-fetched; market and central-bank pages
are human-review entrypoints, never mislabelled as API/live prices.
No images, LLMs, publication, messaging or trading are performed.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
INTEL = ROOT / ".agents/skills/romania-stock-intelligence"
sys.path.insert(0, str(INTEL / "scripts"))
import rss_intake

PLAN_FILE = INTEL / "config/collection-plan.json"
SCHEDULE_FILE = INTEL / "config/schedule.json"
SOURCES_FILE = INTEL / "config/source-registry.json"
BUCHAREST = ZoneInfo("Europe/Bucharest")
DAY = ("工作日", "工作日", "工作日", "工作日", "工作日", "周六", "周日")

def _config():
    plan = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
    schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    registry = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    if plan.get("timezone") != "Europe/Bucharest" or schedule.get("timezone") != "Europe/Bucharest":
        raise ValueError("Romania timezone is mandatory")
    runs = schedule["runs"]
    if len(runs) != 16 or set(plan["source_sections"]) != {r["id"] for r in runs}:
        raise ValueError("16-node official collection mapping incomplete")
    if plan.get("news_images_enabled") is not False or plan.get("image_generation_tasks") != []:
        raise ValueError("News pictures have been disabled by the owner")
    ids = {s["id"]: s for s in registry["sources"]}
    for slot, tasks in plan["source_sections"].items():
        if not tasks:
            raise ValueError("No sources configured for " + slot)
        for task in tasks:
            if len(task) != 4:
                raise ValueError("Invalid source task for " + slot)
            source_id, section, content, method = task
            if source_id not in ids or method not in ("rss", "manual"):
                raise ValueError("Unknown source/mode for " + slot)
            if not section or not content:
                raise ValueError("Empty source section/purpose")
            uri = ids[source_id]["uri"]
            p = urlsplit(uri)
            if p.scheme != "https" or not p.hostname or p.username or p.password:
                raise ValueError("Unsafe official source URL: " + source_id)
            if method == "rss" and (source_id not in rss_intake.FEEDS or
                                    uri != rss_intake.FEEDS[source_id]):
                raise ValueError("RSS mode is restricted to registered BVB feeds")
    return plan, runs, ids

def slot_plan(node_id, *, at=None):
    """Human-readable source checklist, grounded in the unchanged 16-node clock."""
    plan, runs, sources = _config()
    slot = next((r for r in runs if r["id"] == node_id), None)
    if slot is None:
        raise ValueError("Unknown schedule node")
    at = at or datetime.now(timezone.utc)
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("Timezone-aware time required")
    local = at.astimezone(BUCHAREST)
    tasks = []
    for source_id, section, purpose, mode in plan["source_sections"][node_id]:
        source = sources[source_id]
        tasks.append({
            "source_id": source_id, "publisher": source["publisher"],
            "url": source["uri"], "site_section": section, "collect": purpose,
            "method": mode, "state": "NOT_YET_FETCHED" if mode == "rss"
                     else "REQUIRES_ORIGINAL_PAGE_REVIEW",
            "real_time_claim_permitted": False,
        })
    return {
        "node_id": node_id, "days": slot["days"], "topic": slot["topic"],
        "preparation": slot["preparation"], "publication": slot["publication"],
        "timezone": "Europe/Bucharest", "local_date": local.date().isoformat(),
        "day_matches": DAY[local.weekday()] == slot["days"],
        "tasks": tasks, "news_images_enabled": False,
        "no_automatic_publication": True,
        "notes": "任务时间是罗马尼亚栏目备料时间，不代表来源即时数据；人工核对原文/延迟/基准后才可用于群聊。",
    }

def due_slots(at):
    """Runs strictly on preparation minute, using IANA DST; no backdated claims."""
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("Timezone-aware time required")
    local = at.astimezone(BUCHAREST)
    _, runs, _ = _config()
    day = DAY[local.weekday()]
    hhmm = local.strftime("%H:%M")
    return [r["id"] for r in runs if r["days"] == day and r["preparation"] == hhmm]

def collect(node_id, state_dir, *, at=None, fetcher=None):
    """Explicit official RSS fetch with persistent *unverified* queues per source.

    Manual-only sources are never silently scraped or treated as empty/verified.
    On a source failure, other sources retain their independent results.
    """
    at = at or datetime.now(timezone.utc)
    planned = slot_plan(node_id, at=at)
    if not planned["day_matches"]:
        raise ValueError("Node scheduled on another weekday/weekend")
    state_dir = Path(state_dir).expanduser()
    if not state_dir.is_absolute():
        raise ValueError("Use an absolute persistent data directory")
    fetcher = fetcher or rss_intake.official_fetch
    outcomes = []
    for task in planned["tasks"]:
        outcome = {**task}
        if task["method"] == "manual":
            outcome["state"] = "MANUAL_PRIMARY_SOURCE_CHECK_REQUIRED"
        else:
            try:
                raw = fetcher(task["source_id"])
                articles = rss_intake.parse_feed(raw, task["source_id"])
                path = state_dir / "news-sources" / (task["source_id"].lower() + ".json")
                old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
                revised, pending = rss_intake.triage(articles, old)
                rss_intake.write_json(path, revised)
                outcome["state"] = "RSS_CANDIDATES_UNVERIFIED"
                outcome["items_received"] = len(articles)
                outcome["pending_versions"] = len(pending)
                outcome["pending"] = pending[:100]  # display limit; all queued versions remain on disk
            except (ValueError, OSError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
                outcome["state"] = "SOURCE_ERROR_NOT_VERIFIED"
                outcome["error"] = str(exc)[:350]
        outcomes.append(outcome)
    return {
        "node_id": node_id, "collected_at": at.isoformat(),
        "timezone": "Europe/Bucharest", "local_date": planned["local_date"],
        "preparation": planned["preparation"], "publication": planned["publication"],
        "items": outcomes, "any_source_failed": any(
            x["state"] == "SOURCE_ERROR_NOT_VERIFIED" for x in outcomes),
        "facts_verified": False, "approved_for_script": False,
        "news_images_enabled": False, "distribution_status": "NOT_PUBLISHED",
        "next_step": "Open each actual original article, verify names/dates/numbers/unit/baseline/as-of, record independent editorial sign-off.",
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description="P004 official collection clock; no publishing")
    parser.add_argument("--node", help="Node RO-01 to RO-16; defaults to all due now")
    parser.add_argument("--data-dir", default=str(Path.home() / ".romania-finance-skill-hub"))
    parser.add_argument("--collect", action="store_true", help="Explicit RSS collection; otherwise checklist only")
    parser.add_argument("--at", help="ISO8601 timezone-aware simulation time (inspection/testing)")
    args = parser.parse_args(argv)
    at = datetime.fromisoformat(args.at) if args.at else datetime.now(timezone.utc)
    targets = [args.node] if args.node else due_slots(at)
    if not targets:
        print(json.dumps({"due": [], "timezone": "Europe/Bucharest", "collection_started": False},
                         ensure_ascii=False, indent=2))
        return
    payload = ([collect(id, Path(args.data_dir).expanduser().resolve(), at=at)
                if args.collect else slot_plan(id, at=at) for id in targets])
    print(json.dumps({"due": targets, "results": payload}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
