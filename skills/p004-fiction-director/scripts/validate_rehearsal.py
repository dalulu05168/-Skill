"""P004 offline fictional dialogue rehearsal gate (stdlib, no AI/API).

Checks identity, chronology, causal references, lesson scheduling and sandbox
status; it cannot judge human authenticity, language quality or financial truth.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

STORY_ID = "p004-fiction-director-independent"
DAYPARTS = {"morning": 0, "afternoon": 1, "evening": 2}
WEEKDAY_LESSON = {0: "technical", 1: "philosophy", 2: "technical",
                  3: "philosophy", 4: "technical"}


def validate(data: dict, draft: dict) -> dict:
    if not isinstance(data, dict) or data.get("story_id") != STORY_ID:
        raise ValueError("scene package belongs to another story")
    if data.get("status") != "SANDBOX_REHEARSAL_NOT_ADOPTED":
        raise ValueError("this validator only accepts unadopted sandbox")
    if data.get("simulation_only") is not True or data.get("fictional_case_only") is not True:
        raise ValueError("fiction-only sandbox label required")
    if draft.get("story_id") != STORY_ID or draft.get("status") != "DRAFT_NOT_APPROVED":
        raise ValueError("isolated draft roster required")
    people = draft.get("people")
    if not isinstance(people, list) or len(people) != 65:
        raise ValueError("new roster must have 65 candidate people")
    approved_ids = set()
    roles = {}
    for p in people:
        if not isinstance(p, dict) or p.get("approved_by_user") is not False:
            raise ValueError("rehearsal must not imply characters are approved")
        cid = p.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"(?:0[1-9]|[1-5][0-9]|6[0-5])", cid) or cid in approved_ids:
            raise ValueError("invalid or duplicate role ID")
        approved_ids.add(cid)
        roles[cid] = p.get("main_behavior")
    allowed = approved_ids | {"assistant", "professor"}
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or len(scenes) < 2:
        raise ValueError("sandbox needs at least two scenes")
    seen_scenes, previous_order, seen_messages = set(), None, {}
    speaking = Counter()
    cross_scene = []
    member_replies = 0
    instructor_lessons = 0
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError("scene must be an object")
        sid = scene.get("scene_id")
        if not isinstance(sid, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", sid) or sid in seen_scenes:
            raise ValueError("duplicate/bad scene_id")
        seen_scenes.add(sid)
        try:
            local_date = date.fromisoformat(scene["date"])
            if local_date.isoformat() != scene["date"]:
                raise ValueError
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("scene date must be ISO YYYY-MM-DD") from exc
        daypart = scene.get("daypart")
        if daypart not in DAYPARTS:
            raise ValueError("invalid daypart")
        order = (scene["date"], DAYPARTS[daypart])
        if previous_order is not None and order <= previous_order:
            raise ValueError("scenes not in chronological order")
        previous_order = order
        if not isinstance(scene.get("topic"), str) or not scene["topic"].strip():
            raise ValueError("scene topic missing")
        messages = scene.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("scene has no messages")
        professors = [m for m in messages if isinstance(m, dict) and m.get("speaker_id") == "professor"]
        if daypart != "evening" and professors:
            raise ValueError("professor may speak in evening only")
        if daypart == "evening":
            if local_date.weekday() not in WEEKDAY_LESSON:
                raise ValueError("weekend lesson requires explicit exception")
            if scene.get("lesson_type") != WEEKDAY_LESSON[local_date.weekday()]:
                raise ValueError("wrong weekday professor lesson type")
            if not professors:
                raise ValueError("evening lesson requires professor")
            instructor_lessons += 1
        elif scene.get("lesson_type") is not None:
            raise ValueError("daytime cannot set lesson_type")
        for m in messages:
            if not isinstance(m, dict):
                raise ValueError("message must be an object")
            mid, speaker = m.get("message_id"), m.get("speaker_id")
            if not isinstance(mid, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", mid) or mid in seen_messages:
                raise ValueError("duplicate/invalid message_id")
            if speaker not in allowed:
                raise ValueError("unknown new-story speaker")
            if not isinstance(m.get("text"), str) or not m["text"].strip():
                raise ValueError("empty message")
            if not isinstance(m.get("director_note"), str) or not m["director_note"].strip():
                raise ValueError("no causal/director note")
            if speaker in roles and len(m["text"]) > 750:
                raise ValueError("member monologue too long for this rehearsal")
            ref = m.get("reply_to")
            if ref is not None:
                if not isinstance(ref, str) or ref not in seen_messages:
                    raise ValueError("reply_to must reference a previously authored message")
                antecedent = seen_messages[ref]
                if antecedent["scene_id"] != sid:
                    cross_scene.append((mid, ref, order, antecedent["order"]))
                if speaker in roles and antecedent["speaker_id"] in roles:
                    member_replies += 1
            seen_messages[mid] = {"scene_id": sid, "order": order, "speaker_id": speaker}
            speaking[speaker] += 1
    types = {roles[k] for k in speaking if k in roles}
    if not set(["追随者", "观望者", "反驳者", "提问者"]).issubset(types):
        raise ValueError("rehearsal lacks key distinct behavior types")
    if member_replies < 2:
        raise ValueError("members never reply to one another")
    if not any(a[2][0] > a[3][0] for a in cross_scene):
        raise ValueError("rehearsal must include a cross-day callback")
    return {
        "status": "STRUCTURAL_REHEARSAL_PASS_NOT_LITERARY_CERTIFICATION",
        "scenes": len(scenes), "messages": len(seen_messages),
        "speakers": len(speaking), "member_speakers": len([x for x in speaking if x in roles]),
        "distinct_member_types": len(types), "member_to_member_replies": member_replies,
        "cross_scene_callbacks": len(cross_scene), "evening_professor_lessons": instructor_lessons,
        "wrote_memory": False, "real_market_claims_verified": False,
        "human_review_needed": ["Romanian idiom/naturalness", "multi-scene character voice",
                                "causal plausibility", "licensed factual news evidence"]
    }


def main():
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--rehearsal", type=Path, default=root / "examples" / "three-day-sandbox.json")
    parser.add_argument("--draft", type=Path, default=root / "characters" / "drafts" / "roster-v2.json")
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.rehearsal.read_text(encoding="utf-8")),
                              json.loads(args.draft.read_text(encoding="utf-8"))),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
