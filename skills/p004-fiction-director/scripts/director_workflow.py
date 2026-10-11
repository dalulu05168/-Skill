"""P004 draft-only director -> screenplay task -> gate -> rewrite request.

No model, web, WhatsApp, or trade execution is secretly invoked.
Requires a user-operated LLM handoff until a provider is explicitly configured.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from director_cast import plan as choose_cast
from scene_memory import scene_message_exists, approved_speakers

STORY = "p004-fiction-director-independent"
ROOT = Path(__file__).resolve().parents[1]
LESSONS = {0: "technical", 1: "philosophy", 2: "technical",
           3: "philosophy", 4: "technical"}
BANNED_CLAIMS = ("稳赚", "必涨", "保证盈利", "100% profit", "câștig garantat",
                 "profit garantat", "randament garantat", "profit sigur")


def _lesson(story_date, daypart):
    wd = date.fromisoformat(story_date).weekday()
    return LESSONS.get(wd) if daypart == "evening" else None


def prepare(roster, request, *, db_path=None, approved_roster_path=None):
    """Produces a complete manual-LLM task, not a completed novel scene."""
    casting = choose_cast(roster, request)
    if request.get("automatic_publish") is True or request.get("real_trading") is True:
        raise ValueError("publishing and trading are never authorized by this workflow")
    editor_note = request.get("director_override", "")
    if not isinstance(editor_note, str) or len(editor_note) > 1000:
        raise ValueError("director_override must be text max 1000 characters")
    cards = casting["cast"]
    if not cards:
        raise ValueError("no characters selected; change the topic before writing")
    session_date = casting["story_date"]
    task = {
        "story_id": STORY,
        "scene_id": request.get("scene_id"),
        "story_date": session_date,
        "daypart": casting["daypart"],
        "lesson_type": _lesson(session_date, casting["daypart"]),
        "simulation_only": True, "status": "DRAFT_NOT_ADOPTED",
        "fictional_case_only": True, "publishable": False,
        "topic_keywords": casting["topic_keywords"],
        "director_override": editor_note,
        "cast": cards, "approved_history": [],
        "known_trade_events": [], "financial_source_status": "HYPOTHETICAL",
    }
    scene_id = task["scene_id"]
    if not isinstance(scene_id, str) or not (1 <= len(scene_id) <= 80) or not all(
        ch.isascii() and (ch.isalnum() or ch in "_-") for ch in scene_id
    ):
        raise ValueError("scene_id requires 1-80 ASCII letters/numbers/-/_")
    if (db_path is None) != (approved_roster_path is None):
        raise ValueError("DB and official approved roster must both be provided")
    if db_path is not None:
        # Draft candidates are not silently promoted. Only confirmed persons can
        # receive quoted, already-adopted history from the isolated story ledger.
        allowed = approved_speakers(approved_roster_path)
        from scene_memory import person_history
        for speaker in ["assistant", "professor"] + [c["speaker_id"] for c in cards]:
            if speaker in allowed:
                history = person_history(
                    db_path, approved_roster_path, speaker, limit=6,
                    before_story_date=session_date, before_slot=casting["daypart"],
                    exclude_scene_id=scene_id)
                task["approved_history"].extend(history)
        # Grouping histories by speaker breaks the story timeline. Order globally
        # by date, daypart and original scene position, with a bounded payload.
        slot_order = {"morning": 0, "afternoon": 1, "evening": 2}
        task["approved_history"].sort(
            key=lambda m: (m["story_date"], slot_order.get(m["slot"], 99),
                           m["scene_id"], m.get("ordinal", 0)))
        task["approved_history"] = task["approved_history"][-50:]
    prompt = (
        "你是P004独立虚构财经教学小说的编剧，导演对故事排程有最高调度权。"
        "以下JSON是唯一身份、选角、题材及有效过去消息的依据。"
        "只写罗马尼亚语自然群聊对白，避免成员像同一个人、机械轮流、统一赞同。"
        "每人可不出场；群成员可以因具体事件质疑、互答、反问、跑题；有事实原因才能争论。"
        "助理亲切简短，教授只在晚间授课，周一三五技术，周二四理念，结尾鼓励参与和改善家庭生活。"
        "全部为显著披露的虚构教学排演，不要编造已发生的新闻、价格、收益、签到兑现、"
        "历史对话和真实交易。假设可以作为假设表达。"
        "已采用过去发言仅可使用 approved_history 对应 scene_id/message_id/speaker_id 作为 history_reference；"
        "这里没有的过去事件绝不可声称已发生。暂不允许 trade_reference，模块二尚未接通。"
        "每条消息必须有独立 message_id、speaker_id、text；回复当场前文写 reply_to。"
        "输出一个JSON对象，字段为 story_id/scene_id/story_date/daypart/lesson_type/"
        "simulation_only=true/fictional_case_only=true/status=DRAFT_NOT_ADOPTED/"
        "approved_by_user=false/publishable=false/messages。"
        "可选每条消息的 reply_to 或 history_reference。写完需要验证，不代表已批准或已发送。\n"
        + json.dumps(task, ensure_ascii=False, indent=2)
    )
    return {"task": task, "llm_prompt": prompt, "cast_count": len(cards),
            "model_invoked": False, "stage": "AWAITING_SCREENWRITER_JSON",
            "can_publish": False, "can_adopt_memory": False}


def review(prepared, manuscript, *, db_path=None, approved_roster_path=None):
    """Reject errors; even a clean draft still needs editorial approval."""
    task = prepared["task"]
    issues, warnings = [], []
    if not isinstance(manuscript, dict):
        return _report(["screenplay must be a JSON object"], [], task["scene_id"])
    for key in ("story_id", "scene_id", "story_date", "daypart", "lesson_type"):
        if manuscript.get(key) != task[key]:
            issues.append(f"{key}: output differs from the director's task")
    for key in ("simulation_only", "fictional_case_only"):
        if manuscript.get(key) is not True:
            issues.append(f"{key}: fictional education disclosure missing")
    if manuscript.get("status") != "DRAFT_NOT_ADOPTED":
        issues.append("draft may not label itself as adopted")
    if manuscript.get("approved_by_user") is not False or manuscript.get("publishable") is not False:
        issues.append("draft cannot claim approval or publishability")
    if any(key in manuscript for key in ("trades", "actual_transactions", "order_submitted")):
        issues.append("simulated trading facts cannot be invented in a script")
    messages = manuscript.get("messages")
    if not isinstance(messages, list) or not 1 <= len(messages) <= 200:
        issues.append("messages must be 1-200 objects")
        return _report(issues, warnings, task["scene_id"])
    allowed = {"assistant"} | {x["speaker_id"] for x in task["cast"]}
    if task["daypart"] == "evening" and task["lesson_type"] is not None:
        allowed.add("professor")
    seen = set()
    members = 0
    for index, m in enumerate(messages, 1):
        if not isinstance(m, dict):
            issues.append(f"message {index}: expected object")
            continue
        mid, sid, body = m.get("message_id"), m.get("speaker_id"), m.get("text")
        if not isinstance(mid, str) or not mid or len(mid)>80 or not all(
            c.isascii() and (c.isalnum() or c in "_-") for c in mid
        ):
            issues.append(f"message {index}: invalid message_id")
        elif mid in seen:
            issues.append(f"message {index}: duplicate message_id")
        if sid not in allowed:
            issues.append(f"message {index}: unauthorized speaker {sid!r}")
        if sid not in ("assistant", "professor") and sid in allowed:
            members += 1
        if not isinstance(body, str) or not body.strip() or len(body)>5000:
            issues.append(f"message {index}: invalid text")
        else:
            if any(t.casefold() in body.casefold() for t in BANNED_CLAIMS):
                issues.append(f"message {index}: unsupported guaranteed-return claim")
            if sid not in ("assistant", "professor") and len(body)>750:
                warnings.append(f"message {index}: member speech unusually long")
        if "reply_to" in m and m["reply_to"] not in seen:
            issues.append(f"message {index}: reply_to must point to earlier message in this scene")
        if "trade_reference" in m:
            issues.append(f"message {index}: module 2 connector unavailable; trade reference blocked")
        if "history_reference" in m:
            ref = m["history_reference"]
            valid = isinstance(ref, dict) and all(
                isinstance(ref.get(k), str) and ref[k] for k in ("scene_id", "message_id", "speaker_id")
            )
            if not valid:
                issues.append(f"message {index}: invalid history_reference")
            elif not any(
                    h.get("scene_id") == ref["scene_id"]
                    and h.get("message_id") == ref["message_id"]
                    and h.get("speaker_id") == ref["speaker_id"]
                    for h in task.get("approved_history", [])):
                issues.append(f"message {index}: history_reference missing from this scene's approved snapshot")
            elif (db_path is None or approved_roster_path is None
                  or not scene_message_exists(db_path, approved_roster_path,
                      scene_id=ref["scene_id"], message_id=ref["message_id"],
                      speaker_id=ref["speaker_id"],
                      before_story_date=task["story_date"], before_slot=task["daypart"])):
                issues.append(f"message {index}: history_reference is not previously adopted in this story")
        seen.add(mid)
    if task["daypart"] == "evening" and task["lesson_type"] is not None:
        if not any(isinstance(m, dict) and m.get("speaker_id") == "professor" for m in messages):
            issues.append("evening lesson missing professor")
    if members == 0:
        warnings.append("no speaking members; check whether silence is intentional")
    if len({m.get("speaker_id") for m in messages if isinstance(m, dict)}) < 3:
        warnings.append("few active voices; review whether that fits the scene")
    warnings.append("native Romanian idiom, dialogue originality, and factual claims require substantive editorial review")
    return _report(issues, warnings, task["scene_id"])


def _report(issues, warnings, scene_id):
    blocked = bool(issues)
    return {
        "status": "BLOCKED_REWRITE_REQUIRED" if blocked else "EDITORIAL_REVIEW_REQUIRED",
        "scene_id": scene_id,
        "blocking_issues": issues,
        "warnings": warnings,
        "rewrite_instruction": ("Return a corrected JSON for this same director task. "
                                "Fix only listed blocking issues; preserve valid character intent. "
                                + "; ".join(issues)) if blocked else None,
        "actual_ai_generation_performed": False,
        "fact_check_completed": False,
        "approved_for_publication": False,
        "memory_written": False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["prepare", "review"])
    p.add_argument("--request", type=Path)
    p.add_argument("--manuscript", type=Path)
    p.add_argument("--package", type=Path)
    p.add_argument("--roster", type=Path, default=ROOT/"characters"/"drafts"/"roster-v2.json")
    args = p.parse_args()
    if args.action == "prepare":
        if args.request is None:
            p.error("--request is required")
        result = prepare(json.loads(args.roster.read_text(encoding="utf-8")),
                         json.loads(args.request.read_text(encoding="utf-8")))
    else:
        if args.manuscript is None or args.package is None:
            p.error("--manuscript and --package are required")
        result = review(json.loads(args.package.read_text(encoding="utf-8")),
                        json.loads(args.manuscript.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
