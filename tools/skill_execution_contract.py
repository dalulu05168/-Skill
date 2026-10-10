"""Fail-closed preparation for fictional-role, assistant, news and professor scripts.

Static checks cannot judge subtle voice, freshness or authenticity. Every gate
reports verification boundaries; these reports NEVER approve external publication.
"""
from datetime import date
from pathlib import Path
import json
import re

DIRECTOR = Path(__file__).resolve().parents[1] / "skills" / "romania-market-director"
DISCLOSURE = "【虚构教学模拟】"
EMOJI_RX = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF]")


def load_official_memory(ids):
    """Read actual approved simulation memory; fail instead of inventing history."""
    state = json.loads((DIRECTOR / "memory/state.json").read_text(encoding="utf-8"))
    if state.get("scope") != "fictional_simulation_only":
        raise ValueError("Formal character memory has invalid scope")
    if not isinstance(state.get("adopted_scenes"), list) or not isinstance(state.get("characters"), dict):
        raise ValueError("Formal character memory is damaged")
    characters = state["characters"]
    return {
        "source": "skills/romania-market-director/memory/state.json",
        "state": "empty_no_official_history" if not state["adopted_scenes"] else "approved_scenes_present",
        "approved_scene_count": len(state["adopted_scenes"]),
        "selected_persona_memory": {cid: characters.get(cid, {}) for cid in ids},
        "no_history_is_not_evidence_of_past_interactions": True,
    }


def lesson_for(day, node, *, technical_material_available=False):
    """Authoritative Romanian weekday map; don't manufacture missing tech lessons."""
    weekday = date.fromisoformat(day).weekday()
    if node != "RO-10":
        return {"mode": "none", "can_speak": False,
                "reason": "Professor only at 19:30 RO-10"}
    if weekday >= 5:
        return {"mode": "none", "can_speak": False, "reason": "No automatic weekend professor class"}
    mode = "technical" if weekday in (0, 2, 4) else "philosophy"
    return {
        "mode": mode, "can_speak": True, "slot": "RO-10", "time_local": "19:30",
        "timezone": "Europe/Bucharest",
        "technical_source_status": ("user_supplied_verified" if technical_material_available
                                    else "original_user_technical_course_not_in_repository")
        if mode == "technical" else "not_applicable",
        "lesson_chain": (
            {"Monday": "detect and explain common error", "Wednesday": "verify and discuss invalidation",
             "Friday": "case exercise and review"} if mode == "technical" else
            {"Tuesday": "conceptual principle", "Thursday": "application and comparison"}
        ),
        "must_verify_source_and_past_lesson": True,
    }


def audit_member_voice(messages, profiles, period=None):
    """Validate testable persona red lines; subjectivity produces warnings not fake pass."""
    problems, warnings = [], []
    used = {}
    allowed_media = {"TEXT", "EMOJI", "GIF", "PNG"}
    for i, m in enumerate(messages, 1):
        if not isinstance(m, dict):
            problems.append(f"message {i}: object required")
            continue
        cid = str(m.get("character_id", "")).zfill(2)
        profile = profiles.get(cid)
        if profile is None:
            problems.append(f"message {i}: persona not in approved 65-person roster")
            continue
        dna = profile.get("language_dna", {})
        style = dna.get("句长与互动策略", {})
        preference = dna.get("表情习惯", {})
        policy = dna.get("媒体行为管理_v4", {}).get("媒体许可策略", {})
        text = str(m.get("text") or "").replace(DISCLOSURE, "").strip()
        medium = m.get("media_type", "TEXT")
        if medium not in allowed_media:
            problems.append(f"message {i}: unsupported media_type")
        elif medium == "GIF" and policy.get("GIF") is not True:
            problems.append(f"message {i}: GIF is forbidden for persona {cid}")
        elif medium == "PNG" and policy.get("PNG") is not True:
            problems.append(f"message {i}: PNG is forbidden for persona {cid}")
        elif medium == "EMOJI" and policy.get("纯Emoji") is not True:
            problems.append(f"message {i}: emoji-only post is forbidden for persona {cid}")
        if medium in ("GIF", "PNG"):
            if not isinstance(m.get("asset_id"), str) or not m["asset_id"].strip():
                problems.append(f"message {i}: media asset_id required; unavailable media cannot claim sent")
            else:
                media = dna.get("媒体行为管理_v4", {})
                allowed_ids = media.get(("GIF" if medium == "GIF" else "PNG") + "素材ID_可参考", [])
                if m["asset_id"] not in allowed_ids:
                    problems.append(f"message {i}: asset not allowed for persona {cid}")
            if m.get("asset_verified") is not True:
                problems.append(f"message {i}: asset availability/permission not verified")
        emojis = EMOJI_RX.findall(text)
        if emojis and policy.get("纯Emoji") is False:
            problems.append(f"message {i}: emoji is forbidden for persona {cid}")
        preferred = set(preference.get("常用", []))
        for emoji in emojis:
            if preferred and not any(emoji in p for p in preferred):
                warnings.append(f"message {i}: emoji {emoji} is outside the persona preference set")
        max_one = preference.get("群聊表情管理_v3", {}).get("单条消息建议上限")
        if isinstance(max_one, int) and len(emojis) > max_one:
            warnings.append(f"message {i}: emoji count exceeds personal soft limit")
        used[cid] = used.get(cid, 0) + len(emojis)
        words = len(text)
        tiers = style.get("长度分级", {})
        discussion = tiers.get("讨论解释", {})
        max_characters = discussion.get("中文字符")
        if (isinstance(max_characters, list) and len(max_characters) == 2
                and isinstance(max_characters[1], int) and words > max_characters[1]):
            warnings.append(f"message {i}: length exceeds personal dialogue guidance ({words} chars)")
        if period in ("上午", "下午", "晚上"):
            activity = profile.get("activity_pattern", {})
            quiet = activity.get("通常沉默", [])
            # Preference and busy period are editorial hints, not a hard prohibition.
            if activity.get("允许沉默") is False:
                warnings.append(f"message {i}: review persona activity availability")
    for cid, total in used.items():
        preference = profiles[cid].get("language_dna", {}).get("表情习惯", {})
        max_daily = preference.get("群聊表情管理_v3", {}).get("每日建议上限_软限制")
        if isinstance(max_daily, int) and total > max_daily:
            warnings.append(f"persona {cid}: today's draft exceeds emoji soft limit")
    return {"issues": problems, "warnings": warnings, "human_review_required": True,
            "voice_verified": False, "naturalness_verified": False,
            "checked_members": len(used), "period": period}


def audit_publication_packet(packet):
    """Check mandatory declared evidence for a publish-intended packet.

    Strict fields are descriptive editorial data, not proof claims are true.
    """
    errors = []
    if not isinstance(packet, dict):
        return {"status": "BLOCKED", "issues": ["publication_packet required"],
                "human_review_required": True, "facts_verified": False}
    def need(obj, fields, prefix):
        if not isinstance(obj, dict):
            errors.append(prefix + ": object required")
            return
        for k in fields:
            if not isinstance(obj.get(k), str) or not obj[k].strip():
                errors.append(prefix + ": missing " + k)
    need(packet.get("assistant"), ("event", "evidence_url", "observed_at", "market_link",
                                   "causal_path", "counter_factors", "uncertainty",
                                   "next_check"), "assistant")
    news = packet.get("news", None)
    if not isinstance(news, list):
        errors.append("news: list required")
    else:
        for i, n in enumerate(news, 1):
            need(n, ("original_url", "published_at", "event_at", "why_relevant",
                     "source_status"), f"news {i}")
    if packet.get("node") == "RO-10":
        need(packet.get("professor"), ("date", "course_type", "learning_objective", "principle",
                                      "example", "mistake", "practice", "next_link",
                                      "source_status"), "professor")
        p = packet.get("professor")
        if isinstance(p, dict) and isinstance(p.get("date"), str):
            try:
                expected = lesson_for(p["date"], packet["node"])
            except ValueError:
                errors.append("professor: invalid date")
            else:
                if not expected["can_speak"] or expected["mode"] != p.get("course_type"):
                    errors.append("professor: wrong weekday/course mode")
    if packet.get("fictional_characters_used") is True:
        if packet.get("simulation_notice") is not True:
            errors.append("characters: disclosure required")
        if packet.get("memory_checked") is not True or packet.get("roster_checked") is not True:
            errors.append("characters: explicit memory and roster review required")
    return {"status": "BLOCKED" if errors else "NEEDS_HUMAN_REVIEW",
            "issues": errors, "human_review_required": True,
            "facts_verified": False, "language_quality_verified": False,
            "publication_allowed": False}
