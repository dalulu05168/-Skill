"""Opt-in, provenance-checked import of user-approved *fictional* scene history.

This is deliberately not a watcher or auto-import: no historic conversations,
old 70/72-person files, or drafts are adopted. Importing is a separate,
explicitly confirmed operation after a genuine approved source exists.
"""
import hashlib
import json
from pathlib import Path


def stage_approved_scene(repo_root, source_path, state, profiles):
    repo_root = Path(repo_root).resolve()
    source = (repo_root / source_path).resolve()
    approved = (repo_root / "skills/romania-market-director/library/approved").resolve()
    if approved not in source.parents or source.suffix.lower() != ".json":
        raise ValueError("Source must be a JSON document inside approved/; drafts are excluded")
    if not source.is_file():
        raise ValueError("Approved source document not found")
    raw = source.read_bytes()
    document = json.loads(raw.decode("utf-8"))
    if not isinstance(document, dict) or document.get("approved_by_user") is not True:
        raise ValueError("Source is not explicitly confirmed as a user-approved final scene")
    if document.get("simulation_only") is not True:
        raise ValueError("Only fictional simulation history may be imported")
    sid = document.get("scene_id")
    if not isinstance(sid, str) or not sid.strip() or len(sid) > 128:
        raise ValueError("Unique scene_id required")
    if not isinstance(state.get("adopted_scenes"), list) or not isinstance(state.get("characters"), dict):
        raise ValueError("Memory state invalid")
    if any((x.get("scene_id") if isinstance(x, dict) else x) == sid for x in state["adopted_scenes"]):
        raise ValueError("Scene already adopted; never silently overwrite")
    if not isinstance(document.get("messages"), list) or not document["messages"]:
        raise ValueError("Approved scene must contain authored dialogue messages")
    characters = {}
    ids = set()
    for i, message in enumerate(document["messages"], 1):
        if not isinstance(message, dict):
            raise ValueError(f"Message {i}: object required")
        cid = str(message.get("character_id", "")).zfill(2)
        person = profiles.get(cid)
        if person is None:
            raise ValueError(f"Message {i}: not an approved 65-person identity")
        if message.get("name") != person["identity_extension"]["姓名"]:
            raise ValueError(f"Message {i}: name mismatch")
        if message.get("gender") != person["source_profile"]["性别"] or message.get("role") != person["source_profile"]["学员资历"]:
            raise ValueError(f"Message {i}: identity classification mismatch")
        if message.get("simulation_only") is not True or "【虚构教学模拟】" not in str(message.get("text", "")):
            raise ValueError(f"Message {i}: fictional disclosure required")
        mid = message.get("message_id")
        if not isinstance(mid, str) or not mid.strip() or mid in ids:
            raise ValueError(f"Message {i}: unique message_id required")
        ids.add(mid)
        characters.setdefault(cid, []).append({
            "scene_id": sid, "message_ref": mid,
            "date": document.get("date"), "node": document.get("node"),
            "text": message["text"], "reply_to": message.get("reply_to"),
            "status": "adopted_user_approved_fiction"
        })
    return {
        "scene_id": sid, "source_path": source.relative_to(repo_root).as_posix(),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "date": document.get("date"), "node": document.get("node"),
        "events": characters, "approved_by_user": True
    }


def apply_staged_scene(state, staged, *, operator_confirmed=False):
    """Return a fresh memory state. Caller manages reviewing and persistence."""
    if operator_confirmed is not True or staged.get("approved_by_user") is not True:
        raise ValueError("Explicit operator confirmation is required to import history")
    updated = json.loads(json.dumps(state, ensure_ascii=False))
    if any((x.get("scene_id") if isinstance(x, dict) else x) == staged["scene_id"]
           for x in updated["adopted_scenes"]):
        raise ValueError("Scene already adopted")
    updated["adopted_scenes"].append({
        "scene_id": staged["scene_id"], "source_path": staged["source_path"],
        "source_sha256": staged["source_sha256"],
        "date": staged["date"], "node": staged["node"],
    })
    for cid, events in staged["events"].items():
        character = updated["characters"].setdefault(cid, {})
        character.setdefault("speech_events", []).extend(events)
    return updated
