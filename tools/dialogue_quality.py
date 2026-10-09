"""Conservative dialogue checks for disclosed, fictional finance teaching scripts.

This does not judge natural language reliably or verify any financial facts.
Hard red lines block adoption; writing-style warnings require human review.
No model, network, clock, account or publication dependencies.
"""
import re
from collections import Counter

DISCLOSURE = "【虚构教学模拟】"
HYPOTHETICAL = "【假设】"

PERSONAL_TRADE = re.compile(
    r"我(?:今天|昨天|刚刚|刚才|之前|已经|上周|本周|现在|目前|这次|那次)?"
    r"(?:买入了|卖出了|买了|卖了|赚了|亏了|被套了|持有了|账户赚了|账户亏了)"
)
GUARANTEE = re.compile(r"(?:稳赚不赔|保证收益|保本高收益|包赚|百分之百赚钱|绝对不会亏)")
NEGATED = ("不要相信", "不能保证", "无法保证", "不是", "所谓", "警惕", "别信", "没有")
EMPTY_AGREEMENT = {"同意", "赞同", "确实", "没错", "说得对", "感谢教授",
                   "老师厉害", "教授厉害", "受教了", "+1", "学到了"}
FORMALISMS = ("综上所述", "总而言之", "值得我们深入思考", "从宏观层面来看")
PRAISE = re.compile(r"(?:教授|老师|助理).{0,8}(?:太厉害|真厉害|完全正确|说得真好|太专业|太棒)")


def _body(text):
    return str(text).replace(DISCLOSURE, "").strip()


def audit_dialogue(messages):
    """Audit order, independent voices, conversational density and hard red lines.

    A member may start a topic without reply_to. Reply targets can be other
    earlier members, the assistant/professor source, or any earlier message.
    There is deliberately no mandatory reply rate or fixed turn count.
    """
    if not isinstance(messages, list):
        return {"issues": ["messages must be an array"], "warnings": [],
                "metrics": {}, "human_review_required": True}
    issues, warnings = [], []
    seen, previous, repeats = set(), None, Counter()
    total_members = peer_replies = independent = praise_streak = low_value = 0
    for i, message in enumerate(messages, 1):
        if not isinstance(message, dict):
            issues.append(f"message {i}: object required")
            continue
        mid = message.get("message_id")
        if not isinstance(mid, str) or not mid or len(mid) > 80 or mid in seen:
            issues.append(f"message {i}: unique message_id required")
        ref = message.get("reply_to")
        if ref not in (None, "", "source"):
            if not isinstance(ref, str) or ref not in seen:
                issues.append(f"message {i}: reply_to must reference an earlier message")
            elif previous is not None:
                peer_replies += int(message.get("character_id") is not None)
        if isinstance(mid, str):
            seen.add(mid)
        if message.get("character_id") is None:
            praise_streak = 0
            continue
        total_members += 1
        if ref in (None, ""):
            independent += 1
        if message.get("simulation_only") is False:
            issues.append(f"message {i}: fictional member cannot claim real identity")
        if message.get("experience_kind") == "real":
            issues.append(f"message {i}: fictional member cannot claim real experience")
        text = message.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        body = _body(text)
        if PERSONAL_TRADE.search(body) and HYPOTHETICAL not in body:
            issues.append(f"message {i}: first-person transaction needs explicit hypothetical label")
        if GUARANTEE.search(body) and not any(term in body for term in NEGATED):
            issues.append(f"message {i}: unsupported guaranteed-return claim")
        compact = re.sub(r"[\s\W_]+", "", body)
        if compact in EMPTY_AGREEMENT or len(compact) <= 2:
            low_value += 1
            warnings.append(f"message {i}: low-information agreement or filler")
        if len(body) > 130 or any(s in body for s in FORMALISMS):
            warnings.append(f"message {i}: check overly long/formal member voice against profile")
        if body:
            repeats[body] += 1
        if PRAISE.search(body) or body in {"感谢教授", "老师厉害", "教授厉害"}:
            praise_streak += 1
            if praise_streak >= 2:
                issues.append(f"message {i}: mechanical praise chorus")
        else:
            praise_streak = 0
        previous = mid
    for body, count in repeats.items():
        if count >= 2:
            warnings.append(f"repeated member wording ({count} times): {body[:24]}")
    if total_members >= 5 and low_value * 2 >= total_members:
        warnings.append("too many empty agreement turns; add evidence, questions or genuine differences")
    if total_members >= 5 and independent == 0:
        warnings.append("all members reply to others; allow independent or topic-changing remarks")
    return {
        "issues": issues, "warnings": warnings,
        "metrics": {"member_turns": total_members, "peer_or_prior_replies": peer_replies,
                    "independent_turns": independent, "low_information_turns": low_value},
        "human_review_required": True,
        "naturalness_verified": False,
        "facts_verified": False,
    }
