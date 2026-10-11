"""Five independently governed P004 fictional skills inside the existing four-module host.

Uses the isolated director's real roster, workflow, review and memory. No
Ollama requirement; prompts can be passed to an existing AI chat. No silent
model call, no old character import, no trade execution, no WhatsApp posting.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "skills" / "p004-fiction-director"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from director_workflow import prepare, review
from approve_scene import finalize

DRAFT = ROOT / "characters" / "drafts" / "roster-v2.json"
APPROVED = ROOT / "characters" / "approved-roster.json"
ROLES = ("director", "writer", "professor", "assistant", "members")
SKILL_FILES = {role: ROOT.parent / ("p004-" + role) / "SKILL.md" for role in ROLES}
TOKEN = re.compile(r"^[A-Za-z0-9_-]{24,80}$")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + secrets.token_hex(6) + ".tmp")
    try:
        with tmp.open("x", encoding="utf-8") as out:
            json.dump(value, out, ensure_ascii=False, indent=2)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def location(data_dir, token):
    if not isinstance(token, str) or not TOKEN.fullmatch(token):
        raise ValueError("Invalid or missing story session token")
    return Path(data_dir) / "p004-five-skills" / "sessions" / (token + ".json")




def fingerprint(person):
    return hashlib.sha256(json.dumps(person, ensure_ascii=False,
         sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def approved_roster_path(data_dir):
    """Store approvals independently of git, in the same persistent workspace."""
    dest = Path(data_dir) / "p004-five-skills" / "approved-roster.json"
    if not dest.exists():
        save_json(dest, read_json(APPROVED))
    original = read_json(dest)
    candidates = {person["id"]: person for person in read_json(DRAFT)["people"]}
    if original.get("story_id") != "p004-fiction-director-independent":
        raise ValueError("Invalid independent approved roster")
    for item in original.get("characters", []):
        cid = item.get("id")
        if cid not in candidates or item.get("approved_by_user") is not True:
            raise ValueError("Invalid character approval entry")
        if item.get("profile_fingerprint") != fingerprint(candidates[cid]):
            raise ValueError("Approved candidate profile changed: review and reconcile manually")
    return dest


def characters(data_dir):
    roster = read_json(DRAFT)["people"]
    approved = read_json(approved_roster_path(data_dir))["characters"]
    ids = {p["id"] for p in approved}
    return {"people": [
        {"id": p["id"], "name": p["name"], "age": p["age"],
         "gender": p["gender"], "region": p["region"],
         "occupation": p["occupation"], "family_motivation": p["family_motivation"],
         "main_behavior": p["main_behavior"], "secondary_behavior": p["secondary_behavior"],
         "voice": p["voice"], "availability_note": p["availability_note"],
         "approved": p["id"] in ids}
        for p in roster
    ], "approved_count": len(ids), "candidate_count": 65,
        "fictional_only": True}


def approve_character(request, data_dir):
    """One real on-screen user review action for one persona; no bulk approval."""
    cid = request.get("id")
    if not isinstance(cid, str) or not re.fullmatch(r"(?:0[1-9]|[1-5][0-9]|6[0-5])", cid):
        raise ValueError("Choose one new persona 01-65")
    if request.get("reviewed") is not True or request.get("confirmed") is not True:
        raise ValueError("This person's biography and language must be individually reviewed and confirmed")
    candidates = {p["id"]: p for p in read_json(DRAFT)["people"]}
    person = candidates[cid]
    if request.get("confirmed_name") != person["name"]:
        raise ValueError("Confirm the displayed candidate name, not only a number")
    path = approved_roster_path(data_dir)
    state = read_json(path)
    if any(x["id"] == cid for x in state["characters"]):
        return {"id": cid, "status": "already_approved",
                "approved_count": len(state["characters"])}
    state["characters"].append({
        "id": cid, "name": person["name"], "approved_by_user": True,
        "profile_fingerprint": fingerprint(person)})
    state["characters"].sort(key=lambda x: x["id"])
    save_json(path, state)
    return {"id": cid, "status": "approved_after_individual_review",
            "approved_count": len(state["characters"])}

def skill_registry():
    """Describe actual first-class Skill files, not imaginary installed models."""
    rows = []
    for role, path in SKILL_FILES.items():
        if not path.is_file():
            raise ValueError("Missing first-class P004 Skill: " + role)
        raw = path.read_text(encoding="utf-8")
        if not raw.startswith("---\nname: p004-" + role + "\n"):
            raise ValueError("Invalid P004 Skill metadata for " + role)
        rows.append({"role": role, "skill_name": "p004-" + role,
                     "file": str(path.relative_to(ROOT.parent.parent)).replace("\\", "/"),
                     "defined": True, "installed_in_chatgpt": False})
    return rows


def status(data_dir):
    candidates = read_json(DRAFT)
    approved = read_json(approved_roster_path(data_dir))
    if candidates.get("status") != "DRAFT_NOT_APPROVED":
        raise ValueError("Expected isolated new-story draft roster")
    if approved.get("story_id") != candidates.get("story_id"):
        raise ValueError("Story identifiers mismatch")
    return {
        "story_id": candidates["story_id"], "skills": list(ROLES),
        "skill_definitions": skill_registry(),
        "skill_only_mode": True,
        "candidate_count": len(candidates["people"]),
        "approved_count": len(approved["characters"]),
        "writer_skill_defined": True,
        "writer_skill_automatically_invoked": False,
        "autonomous_writer_connected": False,
        "use_existing_ai_chat": True,
        "live_financial_news_verified": False,
        "module_two_transaction_linked": False,
        "formal_history_requires_approval": True,
        "publishes_to_whatsapp": False,
        "source": "new-isolated-fictional-roster-v2",
    }


def plan(request, data_dir):
    if not isinstance(request, dict):
        raise ValueError("director request must be an object")
    if request.get("simulation_only") is not True:
        raise ValueError("P004 screenplay must be explicitly fictional")
    if request.get("source_status") != "HYPOTHETICAL":
        raise ValueError("Only hypothetical topics, not purported live quotes")
    requested = {
        "scene_id": request.get("scene_id"),
        "story_date": request.get("story_date"),
        "daypart": request.get("daypart"),
        "topic_keywords": request.get("topic_keywords"),
        "max_members": request.get("max_members", 8),
        "recent_member_ids": request.get("recent_member_ids", []),
        "director_override": request.get("director_override", ""),
        "simulation_only": True,
        "source_status": "HYPOTHETICAL",
    }
    history_db = Path(data_dir) / "p004-five-skills" / "adopted-history.sqlite3"
    verified_roster = approved_roster_path(data_dir)
    # Only an actual adopted local SQLite ledger can supply character memories.
    history_args = ({"db_path": history_db, "approved_roster_path": verified_roster}
                    if history_db.is_file() else {})
    prepared = prepare(read_json(DRAFT), requested, **history_args)
    token = secrets.token_urlsafe(24)
    saved = {"prepared": prepared, "manuscript": None, "report": None, "adopted": False}
    save_json(location(data_dir, token), saved)
    return {
        "token": token,
        "task": prepared["task"],
        "prompt": prepared["llm_prompt"],
        "cast_count": prepared["cast_count"],
        "stage": "AWAITING_WRITER_SKILL",
        "next_skill": "p004-writer",
        "model_invoked": False,
        "history_written": False,
    }


def restore(request, data_dir):
    saved = read_json(location(data_dir, request.get("token")))
    return {
        "prepared": saved["prepared"], "manuscript": saved["manuscript"],
        "report": saved["report"], "adopted": saved["adopted"]
    }


def check(request, data_dir):
    path = location(data_dir, request.get("token"))
    saved = read_json(path)
    if saved.get("adopted"):
        raise ValueError("Adopted scenes cannot be overwritten")
    manuscript = request.get("manuscript")
    history_db = Path(data_dir) / "p004-five-skills" / "adopted-history.sqlite3"
    review_args = ({"db_path": history_db,
                    "approved_roster_path": approved_roster_path(data_dir)}
                   if history_db.is_file() else {})
    result = review(saved["prepared"], manuscript, **review_args)
    saved["manuscript"] = manuscript if not result["blocking_issues"] else None
    saved["report"] = result
    save_json(path, saved)
    return {"report": result, "editorial_review_required": not result["blocking_issues"],
            "official_history_written": False, "published": False}


def adopt(request, data_dir):
    if request.get("editorial_confirmed") is not True or request.get("operator_confirmed") is not True:
        raise ValueError("Both editorial and operator confirmations are required")
    path = location(data_dir, request.get("token"))
    saved = read_json(path)
    if saved.get("adopted"):
        raise ValueError("Already adopted; history cannot be overwritten")
    if (saved.get("report") or {}).get("status") != "EDITORIAL_REVIEW_REQUIRED" or not saved.get("manuscript"):
        raise ValueError("Only a structurally reviewed manuscript may be adopted")
    roster = approved_roster_path(data_dir)
    approved_count = len(read_json(roster)["characters"])
    if approved_count != 65:
        raise ValueError(f"New 65-person roster is not formally approved ({approved_count}/65)")
    db = Path(data_dir) / "p004-five-skills" / "adopted-history.sqlite3"
    approved_result = finalize(
        saved["prepared"], saved["manuscript"],
        db_path=db, approved_roster_path=roster,
        operator_confirmed=True, editorial_confirmed=True)
    saved["adopted"] = True
    save_json(path, saved)
    return {"adoption": approved_result, "published": False}


def dispatch(action, request, data_dir):
    if action == "status":
        return status(data_dir)
    if action == "characters":
        return characters(data_dir)
    if action == "approve-character":
        return approve_character(request, data_dir)
    if action == "plan":
        return plan(request, data_dir)
    if action == "restore":
        return restore(request, data_dir)
    if action == "review":
        return check(request, data_dir)
    if action == "adopt":
        return adopt(request, data_dir)
    raise ValueError("Unknown P004 action")
