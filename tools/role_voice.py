"""Role-specific voice guidance and conservative 65-person dialogue audit.

Profiles are read from the existing canonical roster; this is not a new persona
database. Surface detectable copy/paste/analyst-speak issues as editorial warnings,
not false claims that a heuristic has understood tone or verified expertise.
"""
from __future__ import annotations

import re
from collections import defaultdict

DISCLOSURE = "【虚构教学模拟】"
HYPOTHETICAL = "【假设】"
FORMAL_ANALYST = (
    "综上所述", "基于上述分析", "综合基本面与技术面",
    "从宏观层面来看", "我们认为市场将", "投资者应当重点关注",
    "结合当前宏观经济形势", "根据我们的研究判断",
    "风险收益比显著改善", "综合各类指标判断",
    "从估值逻辑出发", "整体来看该标的",
    "我们建议投资者", "从行业基本面分析",
    "由此可以得出结论", "当前的市场运行逻辑",
)
PROFESSIONAL_SELF_LABEL = re.compile(
    r"(?:我(?:是|作为)(?:一名)?(?:资深|专业|持牌|注册)?"
    r"(?:投资顾问|金融分析师|证券分析师|研究员|基金经理)|"
    r"作为(?:持牌|注册)(?:投资顾问|证券分析师))"
)
UNSUPPORTED_ANALYST_ADVICE = ("我们建议投资者", "投资者应当重点关注", "根据我们的研究判断")
PERSONAL_TRADE_PRESSURE = re.compile(
    r"(?:听我的(?:就)?买|大家(?:必须|都要)跟上|"
    r"跟着(?:我|教授|助理)买(?:就)?能赚)"
)
REPEAT_SYMBOLS = re.compile(r"[\s\W_]+", re.UNICODE)


def role_voice_contract():
    """Provide distinct instructions for three roles, without moving teaching roles."""
    return {
        "member": {
            "register": "everyday_conversational",
            "expertise": "ordinary person limited by personal work, investing experience and existing profile",
            "language": "personal preferred language; Chinese examples are semantic reference, not automatic Romanian translations",
            "length": "usually one brief thought or question; rarely two; explain more only when the conversation motivates it",
            "avoid": ["press-release/analyst monologues", "investment-adviser recommendations",
                      "sounding like other members", "repeat-the-assistant summaries",
                      "unverified self-awarded finance credentials"],
        },
        "assistant": {
            "register": "professional_accessible",
            "expertise": "source-led market analysis, credible explanation and patient moderation",
            "structure": "observed fact/source/time -> conditional market mechanism -> counter-factor -> next observation",
            "length": "brief for ordinary updates; expand when explaining hard questions",
            "avoid": ["financial guarantees", "unverified price quotes",
                      "talking down to learners", "turning every answer into a lecture"],
        },
        "professor": {
            "register": "expert_academic",
            "expertise": "precise technical or investment-theory education without invented personal credentials",
            "structure": "concept and assumptions -> rigorous causal logic -> sourced example and contrary case -> limitation -> exercise",
            "length": "structured and substantive, not inflated jargon or invented formal credentials",
            "schedule": "Romania-local RO-10 19:30 on weekdays only; Mon/Wed/Fri technical, Tue/Thu philosophy",
            "avoid": ["guaranteed returns", "unsupported causal claims",
                      "invented technical-course originals", "fake qualifications"],
        },
    }


def member_voice_briefs(profiles, selected_ids):
    """Small model-facing identity cues, each extracted from that person's actual profile."""
    if not isinstance(profiles, dict):
        raise ValueError("profiles must be a mapping")
    if not isinstance(selected_ids, list):
        raise ValueError("selected_ids must be a list")
    result = []
    for raw in selected_ids:
        cid = str(raw).zfill(2)
        p = profiles.get(cid)
        if not isinstance(p, dict):
            raise ValueError("Missing actual v4.1 profile: " + cid)
        identity = p.get("identity_extension", {})
        source = p.get("source_profile", {})
        dna = p.get("language_dna", {})
        personality = p.get("personality", {})
        lang = dna.get("角色语言执行_v4_1", {})
        length = dna.get("句长与互动策略", {}).get("长度分级", {})
        casual = dna.get("群聊短句优先示例", [])
        if not isinstance(casual, list):
            casual = []
        tags = personality.get("核心标签", [])
        if not isinstance(tags, list):
            tags = []
        result.append({
            "character_id": cid,
            "name": identity.get("姓名"),
            "occupation": source.get("工作_职业"),
            "traits": tags[:6],
            "speaking_pattern": dna.get("典型结构", ""),
            "native_language": lang.get("母语或优先输出语言"),
            "register": "自然、有个性、生活化的成员；不是财经主播、助理或教授",
            "ordinary_range": length.get("普通发言", {}),
            "short_examples_for_tone_only": casual[:3],
            "silence_allowed": p.get("activity_pattern", {}).get("允许沉默", True),
            "style_guard": "职业影响关注点，不意味着投资分析资质；不照抄例句、不重复专家术语、不复制其他成员语气",
        })
    return result


def _spoken(text):
    return str(text or "").replace(DISCLOSURE, "").replace(HYPOTHETICAL, "").strip()


def audit_member_register(messages, profiles):
    """Report likely role/style drift. Warnings must be reviewed, not auto-rejected."""
    if not isinstance(messages, list):
        return {"issues": ["messages must be an array"], "warnings": [],
                "human_review_required": True, "member_voice_verified": False}
    issues, warnings = [], []
    normalized = defaultdict(set)
    names = {}
    for index, row in enumerate(messages, 1):
        if not isinstance(row, dict) or row.get("character_id") is None:
            # The assistant and professor are *allowed* to use technical language.
            continue
        cid = str(row["character_id"]).zfill(2)
        p = profiles.get(cid)
        if not isinstance(p, dict):
            issues.append(f"message {index}: person not in canonical roster")
            continue
        text = _spoken(row.get("text"))
        if not text:
            continue
        style_hits = [phrase for phrase in FORMAL_ANALYST if phrase in text]
        if any(phrase in text for phrase in UNSUPPORTED_ANALYST_ADVICE):
            issues.append(f"message {index}: member {cid} is speaking as a professional investment adviser")
        if style_hits or (len(text) >= 90 and
                          sum(text.count(x) for x in ("因此", "同时", "此外", "综上", "值得关注")) >= 3):
            warnings.append(f"message {index}: member {cid} sounds like a professional market report; rewrite in own everyday voice")
        if PROFESSIONAL_SELF_LABEL.search(text):
            warnings.append(f"message {index}: member {cid} claims financial credentials; check actual profile and source")
        if PERSONAL_TRADE_PRESSURE.search(text):
            issues.append(f"message {index}: member {cid} pressures others to trade")
        key = REPEAT_SYMBOLS.sub("", text).casefold()
        if len(key) >= 10:
            normalized[key].add(cid)
            names[key] = text
    for key, ids in normalized.items():
        if len(ids) >= 2:
            warnings.append("copy-like wording shared across distinct members " +
                            ",".join(sorted(ids)) + ": " + names[key][:48])
    return {
        "issues": issues,
        "warnings": list(dict.fromkeys(warnings)),
        "human_review_required": True,
        "member_voice_verified": False,
        "professor_expertise_verified": False,
        "semantic_register_verified": False,
    }
