"""Deterministic rehearsal-only casting planner for P004 fictional characters.

The chief director chooses a credible mix of speakers; the screenplay writer
creates dialogue separately. No language model, news API, trading API, or
legacy persona files are accessed here. Draft personas CANNOT be published.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

STORY = "p004-fiction-director-independent"
DAYPARTS = {"morning", "afternoon", "evening"}
TOPIC_ALIASES = {
    "能源": ("能源", "油价", "燃料", "电费", "电力", "石油", "供暖", "汽油", "煤", "燃油"),
    "银行": ("银行", "贷款", "利率", "信用", "存款", "股息"),
    "科技": ("科技", "软件", "技术", "AI", "互联网"),
    "消费": ("消费", "零售", "食品", "服务", "药房", "购买力"),
    "交通": ("交通", "运输", "物流", "港口", "汽油", "航运", "燃料"),
    "通胀": ("通胀", "物价", "生活成本", "购买力", "食品"),
    "利润": ("利润", "盈利", "现金流", "收入", "成本", "财务", "报表"),
    "汇率": ("汇率", "外汇", "欧元", "出口", "进口", "列伊"),
    "教育": ("教育", "孩子", "学习", "家庭", "学校"),
}
PART_HINTS = {
    "morning": ("上午", "清晨", "早晨", "午休", "午间"),
    "afternoon": ("下午", "午后", "午间", "傍晚", "换班"),
    "evening": ("晚上", "晚间", "夜间", "傍晚", "下班", "晚饭"),
}


def _keywords(raw):
    if not isinstance(raw, list) or not 1 <= len(raw) <= 12:
        raise ValueError("topic_keywords must be 1-12 nonempty strings")
    if any(not isinstance(x, str) or not x.strip() or len(x)>50 for x in raw):
        raise ValueError("invalid topic keyword")
    return tuple(dict.fromkeys(k.strip() for k in raw))


def _score(character, keywords, daypart, recent_ids):
    interests = " ".join(character["interest_triggers"])
    occupation = character["occupation"]
    family = character["family_motivation"]
    matched = set()
    score = 0
    for word in keywords:
        aliases = TOPIC_ALIASES.get(word, (word,))
        if any(a.casefold() in interests.casefold() for a in aliases):
            score += 6
            matched.add(word + "→个人关注")
        elif any(a.casefold() in occupation.casefold() for a in aliases):
            score += 4
            matched.add(word + "→职业经验")
        elif any(a.casefold() in family.casefold() for a in aliases):
            score += 3
            matched.add(word + "→家庭关注")
    if not matched:
        return None
    if any(word in character["availability_note"] for word in PART_HINTS[daypart]):
        score += 2
        matched.add("时间适配（仅参考，不代表在线）")
    if character["id"] in recent_ids:
        score -= 4
        matched.add("近期刚出场：降权")
    return {"speaker_id": character["id"], "name": character["name"],
            "main_behavior": character["main_behavior"],
            "secondary_behavior": character["secondary_behavior"],
            "matched_reasons": sorted(matched), "score": score,
            "voice_brief": {
                "sentence_length": character["voice"]["sentence_length"],
                "catchphrase_reference": character["voice"]["catchphrases"],
                "register": character["voice"]["register"],
                "emoji_style": character["voice"]["emoji_style"],
                "coarse_language_style": character["voice"]["coarse_language_style"],
            },
            "silence_allowed": True,
            "no_past_story_inferred": True}


def plan(rehearsal_roster, request):
    """Create *candidate* cast cards; never write scenes or official memory."""
    if rehearsal_roster.get("story_id") != STORY:
        raise ValueError("cannot use legacy or other-story character files")
    if rehearsal_roster.get("version") != "draft-v2" or rehearsal_roster.get("status") != "DRAFT_NOT_APPROVED":
        raise ValueError("only isolated draft-v2 rehearsal roster is accepted")
    if not isinstance(request, dict) or request.get("simulation_only") is not True:
        raise ValueError("explicit fictional-rehearsal request is required")
    if request.get("source_status") != "HYPOTHETICAL":
        raise ValueError("only explicitly hypothetical topics are supported in this prototype")
    daypart = request.get("daypart")
    if daypart not in DAYPARTS:
        raise ValueError("daypart must be morning/afternoon/evening")
    story_date = request.get("story_date")
    if not isinstance(story_date,str):
        raise ValueError("story_date must be YYYY-MM-DD")
    try:
        session_date = date.fromisoformat(story_date)
    except ValueError as e:
        raise ValueError("invalid story_date") from e
    if session_date.isoformat()!=story_date:
        raise ValueError("story_date must be YYYY-MM-DD")
    keywords = _keywords(request.get("topic_keywords"))
    max_members = request.get("max_members", 8)
    if type(max_members) is not int or not 1 <= max_members <= 15:
        raise ValueError("max_members must be between 1 and 15")
    recent_ids = request.get("recent_member_ids", [])
    if not isinstance(recent_ids,list) or any(not isinstance(x,str) for x in recent_ids):
        raise ValueError("recent_member_ids must be a list of IDs")
    if len(recent_ids)>65:
        raise ValueError("recent_member_ids too long")
    candidates = []
    people = rehearsal_roster.get("people", [])
    if not isinstance(people,list) or len(people)!=65:
        raise ValueError("candidate roster must contain 65 people")
    for item in people:
        if item.get("approved_by_user") is not False or item.get("initial_history") != []:
            raise ValueError("cannot cast altered/approved/prehistoric draft character")
        card = _score(item, keywords, daypart, set(recent_ids))
        if card and card["score"] >= 2:
            candidates.append(card)
    candidates.sort(key=lambda x: (-x["score"], x["speaker_id"]))

    # Avoid filling each scene with the same behavioral type when alternatives exist.
    chosen, seen_groups = [], set()
    for card in candidates:
        if len(chosen)>=max_members:
            break
        if card["main_behavior"] not in seen_groups:
            chosen.append(card)
            seen_groups.add(card["main_behavior"])
    for card in candidates:
        if len(chosen)>=max_members:
            break
        if card not in chosen:
            chosen.append(card)

    is_workday = session_date.weekday()<5
    return {
        "story_id": STORY, "source_status":"HYPOTHETICAL",
        "simulation_only":True, "draft_only":True, "publishable":False,
        "story_date":story_date, "daypart":daypart,
        "topic_keywords":list(keywords),
        "cast":chosen, "cast_count":len(chosen),
        "professor_allowed":daypart=="evening" and is_workday,
        "assistant_may_host":True,
        "no_autogenerated_dialogue":True,
        "no_trading_or_publication_side_effects":True,
        "directorial_note":"每名候选只有发言资格、不是必须发言；选角理由仅来自档案兴趣/职业/家庭与候选时间，不能凭空生成过去聊天、持仓、收益或实时在线状态。候选姓名和档案须用户确认后才能用于正式剧情。"
    }


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--roster",type=Path,default=Path(__file__).resolve().parents[1]/"characters"/"drafts"/"roster-v2.json")
    parser.add_argument("--request",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(plan(json.loads(args.roster.read_text(encoding="utf-8")),
                          json.loads(args.request.read_text(encoding="utf-8"))),
                     ensure_ascii=False, indent=2))
