"""Conservative continuity and empathetic writing checks for P004's 65-person editor.

Deterministic checks only. This does NOT fact-check external news, infer intent
with a model, prove literary quality, or authorize public posting.
"""
from __future__ import annotations

import re
from collections import Counter

DISCLOSURE = "【虚构教学模拟】"
HYPOTHETICAL = "【假设】"
META_SPEECH = re.compile(
    r"(?:我是(?:虚构|虚拟|模拟)(?:人物|角色|成员)|"
    r"我们(?:都是|是)(?:虚构|虚拟|模拟)(?:人物|成员|角色)|"
    r"按照剧本(?:要求|安排)|这只是(?:虚拟|模拟)群聊|"
    r"作为(?:人工智能|AI)(?:角色|人物))"
)
INVALIDATION = re.compile(
    r"(?:别矫情|你想太多了|有什么可怕的|别杞人忧天|"
    r"你太敏感了|你不懂就别问|不要再问这种问题)"
)
PERSONAL_ATTACK = re.compile(
    r"(?:你(?:就是|真是|这个)?(?:傻逼|蠢货|废物)|"
    r"你(?:根本)?不配(?:投资|发言|提问)|滚出(?:这个)?群)"
)
PRESSURE = re.compile(
    r"(?:不(?:赶紧)?买(?:入)?(?:就)?(?:会)?后悔|"
    r"必须(?:立刻|马上|今天)买入|"
    r"跟着(?:教授|老师|助理)(?:买|下单)(?:就)?(?:能)?赚|"
    r"放心(?:跟单|上车)(?:肯定)?赚钱)"
)
PAST_CLAIM = re.compile(
    r"(?:你(?:昨天|上次|前天)(?:说|提过|问过)|"
    r"我们(?:昨天|上次|前天)(?:聊过|讨论过|争论过)|"
    r"上(?:一次|周)(?:你|我们)(?:讲过|说过|买过|卖过))"
)
ASSERTED_VERIFIED = re.compile(
    r"(?:已经(?:被)?官方确认|监管(?:已经)?证实|"
    r"我已经核实了(?:这条|所有|全部)(?:消息|行情|数据))"
)
LATIN_WORD = re.compile(r"[a-zA-Z]{3,}")
HAN = re.compile(r"[\u3400-\u9fff]{2,}")


def _body(value):
    return str(value).replace(DISCLOSURE, "").strip()


def _topic_tokens(value):
    """High-precision cues only, never a semantic classifier."""
    raw = str(value or "")
    terms = {x.lower() for x in LATIN_WORD.findall(raw)}
    for part in HAN.findall(raw):
        if len(part) < 3:
            continue
        terms.update(part[i:i + 2] for i in range(len(part) - 1)
                     if part[i:i + 2] not in {"这个", "那个", "我们", "你们",
                                             "大家", "今天", "如何", "什么"})
    return terms


def _approved_memory_ref(ref, sessions, selected_ids, current_day):
    """Return (valid, reason), checking referenced *adopted* scene and message."""
    if not isinstance(ref, dict):
        return False, "continuity_ref must be an object with session_id and message_id"
    sid, mid = ref.get("session_id"), ref.get("message_id")
    if not isinstance(sid, str) or not sid or not isinstance(mid, str) or not mid:
        return False, "continuity_ref must contain nonempty session_id and message_id"
    scenes = [s for s in sessions if isinstance(s, dict)
              and (s.get("id") or s.get("scene_id")) == sid
              and s.get("status") in ("adopted", "approved")]
    if not scenes:
        return False, "continuity_ref does not identify an approved scene"
    scene = scenes[0]
    day = scene.get("date")
    if isinstance(day, str) and isinstance(current_day, str) and day > current_day:
        return False, "continuity_ref points to a scene dated after this draft"
    for m in scene.get("messages", []):
        if (isinstance(m, dict) and m.get("message_id") == mid
                and str(m.get("character_id", "")).zfill(2) in selected_ids):
            return True, ""
    return False, "continuity_ref message not found in the selected cast's approved history"


def audit_storycraft(messages, *, draft=None, sessions=None):
    """Validate traceable continuity and hard social-pressure boundaries.

    Warnings are prompts for editors, not reliable detection of meaning or tone.
    Optional citations to past scene messages are verified against approved-only
    local state. No recorded history means unknown, never 'remembered'.
    """
    if not isinstance(messages, list):
        return {"status": "BLOCKED", "issues": ["messages must be an array"],
                "warnings": [], "publication_allowed": False,
                "human_review_required": True, "facts_verified": False,
                "naturalness_verified": False}
    if not isinstance(draft, dict):
        draft = {}
    if not isinstance(sessions, list):
        sessions = []
    selected = {str(i).zfill(2) for i in draft.get("selected_ids", [])}
    topic = str(draft.get("topic") or "").strip()
    topic_terms = _topic_tokens(topic)
    issues, warnings = [], []
    anchored = 0
    unanchored = 0
    previous_openings = Counter()

    for i, message in enumerate(messages, 1):
        if not isinstance(message, dict):
            issues.append(f"message {i}: object required")
            continue
        body = _body(message.get("text") or "")
        if not body or message.get("character_id") is None:
            continue
        if META_SPEECH.search(body):
            warnings.append(f"message {i}: character sounds like production notes rather than in-scene speech")
        if INVALIDATION.search(body):
            warnings.append(f"message {i}: emotionally dismissive response needs a more respectful rewrite")
        if PERSONAL_ATTACK.search(body):
            issues.append(f"message {i}: insulting or demeaning another person")
        if PRESSURE.search(body):
            issues.append(f"message {i}: high-pressure financial persuasion")
        if ASSERTED_VERIFIED.search(body) and not message.get("evidence_ref"):
            warnings.append(f"message {i}: source-verification claim needs independently checked evidence")
        if body and len(body) >= 8:
            previous_openings[body[:7]] += 1

        ref = message.get("continuity_ref")
        if ref is not None:
            valid, reason = _approved_memory_ref(
                ref, sessions, selected, draft.get("date"))
            if valid:
                anchored += 1
            else:
                issues.append(f"message {i}: {reason}")
        elif message.get("historical_claim") is True:
            issues.append(f"message {i}: explicit historical claim lacks approved continuity_ref")
        elif PAST_CLAIM.search(body):
            unanchored += 1
            warnings.append(f"message {i}: apparent previous-dialogue claim has no traceable approved history citation")

        if (len(body) >= 22 and len(topic) >= 4 and len(topic_terms) >= 2
                and not message.get("reply_to")
                and not (_topic_tokens(body) & topic_terms)):
            warnings.append(f"message {i}: possible topic drift; editor must check relevance to '{topic[:50]}'")

    for phrase, count in previous_openings.items():
        if count >= 3:
            warnings.append(f"{count} messages share the same opening; check independent character voices")

    return {
        "status": "BLOCKED" if issues else "NEEDS_HUMAN_REVIEW",
        "issues": issues,
        "warnings": list(dict.fromkeys(warnings)),
        "metrics": {"history_citations_verified": anchored,
                    "history_claims_without_citations": unanchored,
                    "member_messages": sum(isinstance(m, dict) and
                                           m.get("character_id") is not None for m in messages)},
        "human_review_required": True,
        "facts_verified": False,
        "naturalness_verified": False,
        "semantic_relevance_verified": False,
        "publication_allowed": False,
    }
