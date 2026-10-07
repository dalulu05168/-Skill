"""SQLite history for actual supplied report versions and event snapshots.

No background scheduler, cloud service, or market-data feed is created.
"""
import json
import sqlite3
from pathlib import Path
from datetime import timezone
from .common import DataError, sha256_object, timestamp

DDL = """
CREATE TABLE IF NOT EXISTS reports (
  report_id TEXT PRIMARY KEY,
  produced_at TEXT NOT NULL,
  report_sha256 TEXT NOT NULL,
  payload TEXT NOT NULL,
  stored_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_reports_time ON reports(produced_at);
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  fingerprint TEXT NOT NULL,
  payload TEXT NOT NULL,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL
);
"""


class History:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA busy_timeout = 5000")
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.executescript(DDL)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    def save_report(self, data):
        # Caller MUST validate data against V1 validation first.
        rid = data["report_id"]
        produced = timestamp(data["produced_at"], data["timezone"], "produced_at")
        digest = sha256_object(data)
        with self.db:
            existing = self.db.execute("SELECT report_sha256 FROM reports WHERE report_id=?", (rid,)).fetchone()
            if existing:
                if existing[0] != digest:
                    raise DataError(f"Existing report {rid} differs; reports are immutable; use a revision ID outside this registry")
                return {"status":"unchanged", "report_id":rid, "sha256":digest}
            self.db.execute("INSERT INTO reports(report_id,produced_at,report_sha256,payload) VALUES(?,?,?,?)", (rid, produced.astimezone(timezone.utc).isoformat(), digest, json.dumps(data, ensure_ascii=False, sort_keys=True)))
        return {"status":"saved", "report_id":rid, "sha256":digest}

    def previous(self, before=None):
        if before:
            utc_before = timestamp(before, "Europe/Bucharest", "before").astimezone(timezone.utc).isoformat()
            row = self.db.execute("SELECT payload FROM reports WHERE produced_at < ? ORDER BY produced_at DESC LIMIT 1", (utc_before,)).fetchone()
        else:
            row = self.db.execute("SELECT payload FROM reports ORDER BY produced_at DESC LIMIT 1").fetchone()
        return json.loads(row[0]) if row else None

    def comparison(self, current):
        prev = self.previous(before=current["produced_at"])
        if not prev:
            return {"status":"no_previous_report", "reason":"No earlier stored report", "series":[]}
        older = {m["series"]:(m["value"],m["unit"]) for m in prev.get("metrics", [])}
        entries = []
        for m in current.get("metrics", []):
            old = older.get(m["series"])
            if old is None or old[1] != m["unit"]:
                entries.append({"series":m["series"], "status":"not_comparable", "reason":"Series absent or unit mismatch"})
            else:
                entries.append({"series":m["series"], "status":"compared", "old":old[0], "new":m["value"], "unit":m["unit"], "delta":round(m["value"] - old[0], 8)})
        return {"status":"compared", "previous_report_id":prev["report_id"], "series":entries}

    def upsert_event(self, event, seen_at):
        eid = event["event_id"]
        digest = sha256_object(event)
        with self.db:
            row = self.db.execute("SELECT fingerprint,first_seen FROM events WHERE event_id=?", (eid,)).fetchone()
            if not row:
                status = "new"
                self.db.execute("INSERT INTO events VALUES(?,?,?,?,?)", (eid, digest, json.dumps(event, ensure_ascii=False, sort_keys=True), seen_at, seen_at))
            else:
                status = "unchanged" if row[0] == digest else "revised"
                self.db.execute("UPDATE events SET fingerprint=?,payload=?,last_seen=? WHERE event_id=?", (digest, json.dumps(event, ensure_ascii=False, sort_keys=True), seen_at, eid))
        return status
