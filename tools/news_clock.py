"""Opt-in local scheduler for P004 Module 1.

At each Bucharest preparation minute fetch only approved BVB RSS sources.
Never calls Module 3 or WhatsApp; all results remain unverified and local.
Process must be running. No default background job, daemon service or cloud cron.
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from news_collection import collect, due_slots, rss_intake, BUCHAREST

def run_due(data_dir, *, at=None, collector=collect):
    """Idempotently collect this minute's sources and persist audit status."""
    at = at or datetime.now(timezone.utc)
    directory = Path(data_dir).expanduser().resolve()
    ledger_path = directory / "news-clock-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}
    date = at.astimezone(BUCHAREST).date().isoformat()
    results = []
    for node in due_slots(at):
        key = date + "/" + node
        if key in ledger:
            results.append({"node_id": node, "state": "ALREADY_ATTEMPTED", "attempt": ledger[key]})
            continue
        try:
            report = collector(node, directory, at=at)
            status = "SOURCE_ERRORS_REVIEW_REQUIRED" if report["any_source_failed"] else "COLLECTED_UNVERIFIED"
            record = {"state": status, "attempted_at": at.isoformat(), "facts_verified": False,
                      "summary": [{k: t.get(k) for k in ("source_id", "state", "items_received", "error")}
                                  for t in report["items"]]}
        except (ValueError, KeyError, OSError, RuntimeError, json.JSONDecodeError) as exc:
            record = {"state": "FAILED_NO_PUBLICATION", "attempted_at": at.isoformat(),
                      "facts_verified": False, "error": str(exc)[:400]}
        ledger[key] = record
        rss_intake.write_json(ledger_path, ledger)
        results.append({"node_id": node, **record})
    return {"local_date": date, "time": at.astimezone(BUCHAREST).isoformat(),
            "due": due_slots(at), "runs": results, "publication_count": 0}

def main(argv=None):
    parser = argparse.ArgumentParser(description="Local DST-aware BVB news clock; no auto publishing")
    parser.add_argument("--data-dir", default=str(Path.home() / ".romania-finance-skill-hub"))
    parser.add_argument("--once", action="store_true", help="Inspect due minute and execute once")
    parser.add_argument("--watch", action="store_true", help="Explicit persistent opt-in local schedule")
    args = parser.parse_args(argv)
    if not args.once and not args.watch:
        parser.error("Must explicitly choose --once or --watch (never background by default)")
    if args.once:
        print(json.dumps(run_due(args.data_dir), ensure_ascii=False, indent=2))
        return
    print("P004 news clock running. Bucharest timezone/DST. No image creation and NO automatic publishing.", flush=True)
    while True:
        try:
            report = run_due(args.data_dir)
            if report["due"]:
                print(json.dumps(report, ensure_ascii=False), flush=True)
        except (ValueError, KeyError, OSError, RuntimeError) as exc:
            print("SCHEDULE ERROR (not published): " + str(exc), flush=True)
        time.sleep(20)

if __name__ == "__main__":
    main()
