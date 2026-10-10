"""P004 fictional-scene memory, SQLite standard library only.

This module deliberately cannot read the legacy persona directory and cannot
infer real financial trades. Only user-adopted fiction is stored; trading data
belongs to module 2 and will be accessed through a separate read-only adapter.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

STORY_ID = "p004-fiction-director-independent"
ID = re.compile(r"[A-Za-z0-9_-]{1,80}\\Z")
PERSON_ID = re.compile(r"(?:0[1-9]|[1-5][0-9]|6[0-5])\\Z")
SPEAKERS = frozenset({"assistant", "professor"})
MAX_MESSAGES = 200
MAX_TEXT = 5000


def _required_id(value, name):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError(f"{name} must be 1-80 ASCII letters/digits/_/-")
    return value


def _valid_date(value):
    if not isinstance(value, str):
        raise ValueError("story_date must be an ISO date")
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError as exc:
        raise ValueError("story_date must be YYYY-MM-DD") from exc
    return value


def approved_speakers(roster_path):
    """Read ONLY a separately approved new-story roster; never old personas."""
    roster = json.loads(Path(roster_path).read_text(encoding="utf-8"))
    if roster.get("story_id") != STORY_ID or not isinstance(roster.get("characters"), list):
        raise ValueError("new-story roster is missing/invalid")
    ids = set()
    for item in roster["characters"]:
        if not isinstance(item, dict) or item.get("approved_by_user") is not True:
            raise ValueError("all listed new personas must be explicitly approved")
        cid = item.get("id")
        if not isinstance(cid, str) or not PERSON_ID.fullmatch(cid) or cid in ids:
            raise ValueError("invalid/duplicate new persona ID")
        ids.add(cid)
    return ids | SPEAKERS


@contextmanager
def _connect(db_path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 5000")
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def initialize(db_path):
    """Creates an empty ledger; it never imports old histories."""
    with _connect(db_path) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS scenes (
                scene_id TEXT PRIMARY KEY,
                story_id TEXT NOT NULL,
                story_date TEXT NOT NULL,
                slot TEXT NOT NULL,
                adopted_at TEXT NOT NULL,
                content_sha256 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                scene_id TEXT NOT NULL REFERENCES scenes(scene_id) ON DELETE RESTRICT,
                message_id TEXT NOT NULL,
                speaker_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                body TEXT NOT NULL,
                PRIMARY KEY(scene_id, message_id),
                UNIQUE(scene_id, ordinal)
            );
            CREATE INDEX IF NOT EXISTS idx_person_history ON messages(speaker_id, scene_id);
        """)


def _validate_scene(scene, roster_path):
    if not isinstance(scene, dict):
        raise ValueError("scene must be an object")
    if scene.get("story_id") != STORY_ID:
        raise ValueError("cannot import another story")
    if scene.get("simulation_only") is not True or scene.get("approved_by_user") is not True:
        raise ValueError("only explicitly approved fictional scenes can be adopted")
    scene_id = _required_id(scene.get("scene_id"), "scene_id")
    story_date = _valid_date(scene.get("story_date"))
    slot = scene.get("slot", "")
    if not isinstance(slot, str) or len(slot) > 64:
        raise ValueError("slot must be text, max 64 characters")
    messages = scene.get("messages")
    if not isinstance(messages, list) or not 1 <= len(messages) <= MAX_MESSAGES:
        raise ValueError("messages must contain 1-200 entries")
    allow = approved_speakers(roster_path)
    seen = set()
    clean = []
    for n, msg in enumerate(messages):
        if not isinstance(msg, dict):
            raise ValueError(f"message {n+1} must be an object")
        mid = _required_id(msg.get("message_id"), "message_id")
        if mid in seen:
            raise ValueError("duplicate message ID")
        seen.add(mid)
        sid = msg.get("speaker_id")
        if not isinstance(sid, str) or sid not in allow:
            raise ValueError("unknown/unapproved speaker ID")
        body = msg.get("text")
        if not isinstance(body, str) or not body.strip() or len(body) > MAX_TEXT:
            raise ValueError("invalid/oversized message")
        clean.append({"message_id": mid, "speaker_id": sid, "text": body.strip()})
    canonical = {"scene_id": scene_id, "story_date": story_date, "slot": slot,
                 "messages": clean, "story_id": STORY_ID}
    content_sha256 = hashlib.sha256(json.dumps(canonical, ensure_ascii=False,
                                                sort_keys=True, separators=(",", ":")
                                               ).encode("utf-8")).hexdigest()
    return canonical, content_sha256


def adopt_scene(db_path, roster_path, scene, *, operator_confirmed=False):
    """Atomically adopt an explicitly approved scene; never overwrite history.

    The caller must have already confirmed the final copy; this module only
    enforces deterministic provenance and isolation, NOT factual truth/tone.
    """
    if operator_confirmed is not True:
        raise ValueError("operator_confirmed=True required")
    clean, digest = _validate_scene(scene, roster_path)
    initialize(db_path)
    with _connect(db_path) as db:
        old = db.execute("SELECT content_sha256 FROM scenes WHERE scene_id = ?",
                         (clean["scene_id"],)).fetchone()
        if old:
            if old[0] == digest:
                return {"status": "already_adopted", "scene_id": clean["scene_id"]}
            raise ValueError("scene ID already adopted with different content; cannot overwrite")
        db.execute("INSERT INTO scenes (scene_id,story_id,story_date,slot,adopted_at,content_sha256) "
                   "VALUES (?,?,?,?,?,?)",
                   (clean["scene_id"], STORY_ID, clean["story_date"], clean["slot"],
                    datetime.now(timezone.utc).isoformat(), digest))
        db.executemany("INSERT INTO messages (scene_id,message_id,speaker_id,ordinal,body) "
                       "VALUES (?,?,?,?,?)",
                       [(clean["scene_id"], msg["message_id"], msg["speaker_id"], n,
                         msg["text"]) for n, msg in enumerate(clean["messages"])])
    return {"status": "adopted", "scene_id": clean["scene_id"],
            "messages": len(clean["messages"]), "content_sha256": digest}


def person_history(db_path, roster_path, speaker_id, *, limit=100, keyword=None):
    """Return only verified-scope adopted messages, oldest-to-newest."""
    if speaker_id not in approved_speakers(roster_path):
        raise ValueError("unapproved speaker ID")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 160):
        raise ValueError("invalid keyword")
    initialize(db_path)
    sql = ("SELECT s.scene_id,s.story_date,s.slot,m.message_id,m.speaker_id,m.body "
           "FROM messages m JOIN scenes s ON s.scene_id = m.scene_id "
           "WHERE s.story_id = ? AND m.speaker_id = ?")
    args = [STORY_ID, speaker_id]
    if keyword:
        sql += " AND instr(m.body, ?) > 0"
        args.append(keyword)
    sql += " ORDER BY s.story_date DESC,s.adopted_at DESC,m.ordinal DESC LIMIT ?"
    args.append(limit)
    with _connect(db_path) as db:
        rows = db.execute(sql, args).fetchall()
    return [{"scene_id": row[0], "story_date": row[1], "slot": row[2],
             "message_id": row[3], "speaker_id": row[4], "text": row[5],
             "simulation_only": True} for row in reversed(rows)]


def scene_message_exists(db_path, roster_path, *, scene_id, message_id, speaker_id):
    """For exact continuity_ref checks: unapproved people and unknown refs fail."""
    _required_id(scene_id, "scene_id")
    _required_id(message_id, "message_id")
    if speaker_id not in approved_speakers(roster_path):
        return False
    initialize(db_path)
    with _connect(db_path) as db:
        row = db.execute("SELECT 1 FROM scenes s JOIN messages m ON s.scene_id=m.scene_id "
                         "WHERE s.story_id=? AND s.scene_id=? AND m.message_id=? AND m.speaker_id=?",
                         (STORY_ID, scene_id, message_id, speaker_id)).fetchone()
    return row is not None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Independent fictional-scene memory (no old personas)")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--roster", required=True, type=Path)
    parser.add_argument("--person", required=True, help="approved persona 01-65, assistant, or professor")
    parser.add_argument("--keyword", default=None)
    args = parser.parse_args()
    print(json.dumps(person_history(args.db, args.roster, args.person, keyword=args.keyword),
                     ensure_ascii=False, indent=2))
