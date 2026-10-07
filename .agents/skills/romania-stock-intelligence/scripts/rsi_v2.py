#!/usr/bin/env python3
"""Romania Stock Intelligence V2 executable command-line entrypoint.

Requires Python >=3.11. No dependencies, external data fetching, or side effects
except explicit --db (SQLite), --out (JSON/text) and event history writes.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rsi_core.common import DataError, load_json, write_json  # noqa: E402
from rsi_core.quality import audit_observations  # noqa: E402
from rsi_core.bet import analyze_bet  # noqa: E402
from rsi_core.events import radar  # noqa: E402
from rsi_core.professor import generate_lesson  # noqa: E402
from rsi_core.storage import History  # noqa: E402
from validate_report import validate  # noqa: E402


def invoke(argv=None):
    parser = argparse.ArgumentParser(description="RSI V2: audit, BET estimate, event triage, persistence, Professor briefing")
    sub = parser.add_subparsers(dest="cmd", required=True)
    def source(name, db=False, registry=False, out=True):
        p = sub.add_parser(name)
        p.add_argument("input", help="JSON input file")
        if db: p.add_argument("--db", required=True, help="SQLite DB path; created on explicit invocation")
        if registry: p.add_argument("--registry", default=str(ROOT / "config/source-registry.json"))
        if out: p.add_argument("--out", help="optional output file")
        return p
    a = source("audit", registry=True)
    a.add_argument("--max-age-minutes", type=int, default=1440)
    a.add_argument("--tolerance-pct", type=float, default=0.5)
    source("bet")
    source("events", db=True)
    source("store", db=True)
    source("compare", db=True)
    source("professor")
    args = parser.parse_args(argv)
    try:
        data = load_json(args.input)
        if args.cmd == "audit":
            result = audit_observations(data, load_json(args.registry), tolerance_pct=args.tolerance_pct, max_age_minutes=args.max_age_minutes)
        elif args.cmd == "bet":
            result = analyze_bet(data)
        elif args.cmd == "events":
            with History(args.db) as h:
                result = radar(data, history=h)
        elif args.cmd in ("store", "compare"):
            errors = validate(data)
            if errors:
                raise DataError("Legacy report validation failed: " + "; ".join(errors[:8]))
            with History(args.db) as h:
                result = h.comparison(data) if args.cmd == "compare" else h.save_report(data)
        elif args.cmd == "professor":
            result = generate_lesson(data)
        else:
            raise AssertionError("Unexpected command")
        if args.out:
            if isinstance(result, str):
                out = Path(args.out)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(result, encoding="utf-8")
            else:
                write_json(args.out, result)
            print(f"Written: {args.out}")
        else:
            print(result if isinstance(result, str) else json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if args.cmd == "audit" and result["gate"] == "fail" else 0
    except (DataError, OSError, KeyError, TypeError) as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(invoke())
