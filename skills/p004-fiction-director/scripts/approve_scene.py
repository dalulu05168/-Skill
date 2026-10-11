"""Final editorial adoption gate for NEW P004 fictional scenes.

Separate from prompt generation and unapproved auditions. Requires explicit
operator+editorial confirmations and an approved roster. Never publishes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from director_workflow import review, STORY
from scene_memory import approved_speakers, adopt_scene


def finalize(prepared, manuscript, *, db_path, approved_roster_path,
             operator_confirmed=False, editorial_confirmed=False):
    if operator_confirmed is not True or editorial_confirmed is not True:
        raise ValueError("both explicit editorial and operator confirmations required")
    task = prepared["task"]
    if task.get("financial_source_status") != "HYPOTHETICAL":
        raise ValueError("hypothetical educational scenarios only")
    report = review(prepared, manuscript, db_path=db_path,
                    approved_roster_path=approved_roster_path)
    if report["blocking_issues"]:
        raise ValueError("QA blocked: " + "; ".join(report["blocking_issues"]))
    roster_allowed = approved_speakers(approved_roster_path)
    speakers = {m["speaker_id"] for m in manuscript["messages"]}
    not_approved = sorted(speakers - roster_allowed)
    if not_approved:
        raise ValueError("new-story unapproved speaker IDs: " + ", ".join(not_approved))
    scene = {
        "story_id": STORY, "scene_id": task["scene_id"],
        "story_date": task["story_date"], "slot": task["daypart"],
        "simulation_only": True, "approved_by_user": True,
        "messages": [{"message_id": m["message_id"], "speaker_id": m["speaker_id"],
                      "text": m["text"]} for m in manuscript["messages"]],
    }
    result = adopt_scene(db_path, approved_roster_path, scene, operator_confirmed=True)
    return {"status": result["status"], "scene_id": scene["scene_id"],
            "official_story_memory_written": result["status"] == "adopted",
            "published_to_whatsapp": False, "real_trade_executed": False,
            "fictional_teaching_only": True}


def main():
    p = argparse.ArgumentParser(description="Explicitly adopt a reviewed fictional scene")
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--manuscript", type=Path, required=True)
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--approved-roster", type=Path, required=True)
    p.add_argument("--editorial-confirmed", action="store_true")
    p.add_argument("--operator-confirmed", action="store_true")
    a = p.parse_args()
    result = finalize(
        json.loads(a.package.read_text(encoding="utf-8")),
        json.loads(a.manuscript.read_text(encoding="utf-8")),
        db_path=a.db, approved_roster_path=a.approved_roster,
        editorial_confirmed=a.editorial_confirmed,
        operator_confirmed=a.operator_confirmed)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
