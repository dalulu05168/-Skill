#!/usr/bin/env python3
"""Fail-closed persona identity validator. stdlib only; no network, no edits.
Usage: python scripts/validate_persona_roster.py [optional-script-messages.json]
Optional file: JSON list or {"messages":[{"character_id":"07","name":"Ioana Petrescu","gender":"女","role":"新女","text":"..."}]}
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_ROLES = {"老男", "新男", "老女", "新女"}

def fail(message):
    raise ValueError(message)

def load(path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)

def validate():
    index_rows = load(ROOT / "characters" / "index.json")
    indexed = {str(x["id"]).zfill(2): x for x in index_rows}
    if len(index_rows) != 65 or len(indexed) != 65:
        fail("Expected exactly 65 unique indexed identities")
    paths = sorted((ROOT / "characters" / "profiles").glob("*_AI_Profile.json"))
    if len(paths) != 65:
        fail(f"Expected 65 full character profiles, found {len(paths)}")
    roster = {}
    for path in paths:
        profile = load(path)
        filename_id = path.name[:2]
        character_id = str(profile.get("character_id", "")).zfill(2)
        source = profile.get("source_profile") or {}
        gender = source.get("性别")
        role = source.get("学员资历")
        name = (profile.get("identity_extension") or {}).get("姓名")
        row = indexed.get(character_id)
        if character_id != filename_id or not row or not profile.get("simulation_only"):
            fail(f"Bad ID/index/simulation flag: {path.name}")
        if gender not in {"男", "女"} or role not in VALID_ROLES or not role.endswith(gender):
            fail(f"Sex or old/new tag inconsistent: {path.name}")
        if name != row.get("name") or gender != row.get("sex"):
            fail(f"Name/gender differs from index: {path.name}")
        source_id = re.search(r"\d+", str(source.get("编号", "")))
        if source_id and str(int(source_id.group())).zfill(2) != character_id:
            fail(f"Source member number mismatched: {path.name}")
        if character_id in roster:
            fail(f"Duplicate ID: {character_id}")
        roster[character_id] = {"name": name, "gender": gender, "role": role}
    if set(roster) != set(indexed):
        fail("Roster IDs differ from index")
    return roster

def validate_messages(roster, filename):
    raw = load(Path(filename))
    messages = raw["messages"] if isinstance(raw, dict) else raw
    if not isinstance(messages, list):
        fail("Message input must be a JSON list")
    for num, m in enumerate(messages, 1):
        cid = m.get("character_id")
        if cid is None:
            continue  # assistant/professor/system message
        cid = str(cid).zfill(2)
        ref = roster.get(cid)
        if ref is None:
            fail(f"Message {num}: nonexistent member {cid}")
        if m.get("name") != ref["name"] or m.get("gender") != ref["gender"] or m.get("role") != ref["role"]:
            fail(f"Message {num}: wrong name/gender/tag for {cid}")
    return len(messages)

if __name__ == "__main__":
    try:
        verified = validate()
        print(f"PASS: {len(verified)} full character identities agree with index and classification")
        for filename in sys.argv[1:]:
            print(f"PASS: validated {validate_messages(verified, filename)} dialogue messages in {filename}")
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
