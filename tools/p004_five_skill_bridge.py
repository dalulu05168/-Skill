"""Five independently governed P004 fictional skills inside the existing four-module host.

Uses the isolated director's real roster, workflow, review and memory. No
Ollama requirement; prompts can be passed to an existing AI chat. No silent
model call, no old character import, no trade execution, no WhatsApp posting.
"""
from __future__ import annotations

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


def status():
    candidates = read_json(DRAFT)
    approved = read_json(APPROVED)
    if candidates.get("status") != "DRAFT_NOT_APPROVED":
        raise ValueError("Expected isolated new-story draft roster")
    if approved.get("story_id") != candidates.get("story_id"):
        raise ValueError("Story identifiers mismatch")
    return {
        "story_id": candidates["story_id"], "skills": list(ROLES),
        "candidate_count": len(candidates["people"]),
        "approved_count": len(approved["characters"]),
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
    prepared = prepare(read_json(DRAFT), requested)
    token = secrets.token_urlsafe(24)
    saved = {"prepared": prepared, "manuscript": None, "report": None, "adopted": False}
    save_json(location(data_dir, token), saved)
    return {
        "token": token,
        "task": prepared["task"],
        "prompt": prepared["llm_prompt"],
        "cast_count": prepared["cast_count"],
        "stage": "AWAITING_AI_SCREENWRITER",
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
    result = review(saved["prepared"], manuscript)
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
    if len(read_json(APPROVED)["characters"]) != 65:
        raise ValueError("New 65-person roster is not formally approved (currently 0/65)")
    db = Path(data_dir) / "p004-five-skills" / "adopted-history.sqlite3"
    approved_result = finalize(
        saved["prepared"], saved["manuscript"],
        db_path=db, approved_roster_path=APPROVED,
        operator_confirmed=True, editorial_confirmed=True)
    saved["adopted"] = True
    save_json(path, saved)
    return {"adoption": approved_result, "published": False}


def dispatch(action, request, data_dir):
    if action == "status":
        return status()
    if action == "plan":
        return plan(request, data_dir)
    if action == "restore":
        return restore(request, data_dir)
    if action == "review":
        return check(request, data_dir)
    if action == "adopt":
        return adopt(request, data_dir)
    raise ValueError("Unknown P004 action")
