"""Conservative editorial significance triage for *unverified* RSS candidates.

This module only prioritizes original-article verification tasks; it cannot
authenticate a headline, determine a real market effect, or authorize publication.
No heuristic scores are treated as validated facts.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone, timedelta

CRITICAL = (
    ("halt / exchange closure", (
        r"\btrading\s+(?:halt|suspension|suspended|stopped)\b",
        r"\b(?:market|exchange)\s+(?:shutdown|closure|halted|closed\s+unexpectedly)\b",
        r"\bsuspendarea\s+tranzactionarii\b",
        r"\bsuspendarea\s+tranzacționării\b",
        r"停牌", r"暂停交易", r"交易所临时关闭",
    )),
    ("default / insolvency", (
        r"\b(?:insolvency|insolvență|default|bankruptcy|faliment)\b",
        r"债务违约", r"破产清算", r"流动性危机",
    )),
    ("material enforcement or system incident", (
        r"\b(?:market\s+manipulation|trading\s+ban|fraud\s+investigation)\b",
        r"操纵市场调查", r"重大监管处罚", r"证券交易系统故障",
    )),
)
IMPORTANT = (
    ("central bank / macro decision", (
        r"\b(?:central\s+bank|banca\s+națională|banca\s+nationala|bnr|ecb|bce)\b.{0,45}\b(?:rate|dobând|doband|decision|decizi|policy)\w*",
        r"\b(?:rate|dobând|doband)\w*.{0,45}\b(?:bnr|ecb|bce|central\s+bank)\b",
        r"\b(?:inflation|inflație|inflatie|consumer\s+price|cpi|gdp|pib)\b",
        r"基准利率决议", r"央行利率", r"通胀数据", r"国内生产总值",
    )),
    ("issuer profits / revision", (
        r"\b(?:profit\s+warning|earnings\s+warning|revenue\s+guidance|financial\s+results|raport\s+financiar|rezultate\s+financiare|earnings\s+report)\b",
        r"业绩预警", r"利润预警", r"财报公告", r"盈利预测下调",
    )),
    ("capital structure / material transaction", (
        r"\b(?:dividend|dividende|major\s+acquisition|takeover|merger|fuziune|major\s+contract|capital\s+increase|majorare\s+de\s+capital|bond\s+issuance)\b",
        r"分红决定", r"重大并购", r"增发", r"重大合同", r"融资调整",
    )),
    ("energy / supply shock", (
        r"\b(?:oil\s+(?:supply|embargo)|gas\s+(?:supply|outage)|energie\s+criză|energy\s+shortage|pipeline\s+shutdown)\b",
        r"能源供应中断", r"天然气供应中断", r"石油禁运",
    )),
)

def _has(text, patterns):
    return any(re.search(p, text, flags=re.IGNORECASE | re.UNICODE) for p in patterns)

def _published_at(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return date.astimezone(timezone.utc) if date.tzinfo and date.utcoffset() is not None else None

def assess_news(item, now):
    """Returns explicitly provisional relevance and evidence gaps.

    Reviewer must open the original article and check the event, magnitude,
    source date, issuer, Romania/BVB transmission and counter-factors.
    """
    if not isinstance(item, dict) or not isinstance(item.get("title"), str):
        raise ValueError("News item with title required")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Timezone-aware review time required")
    headline = re.sub(r"\s+", " ", item["title"]).strip()
    timestamp = _published_at(item.get("published_at"))
    gaps = []
    if timestamp is None:
        gaps.append("missing_or_invalid_timezone_aware_publication_date")
    else:
        delay = now.astimezone(timezone.utc) - timestamp
        if delay < -timedelta(minutes=15):
            gaps.append("future_publication_timestamp")
        if delay > timedelta(days=7):
            gaps.append("stale_or_historical_older_than_7_days")
    if re.search(r"\d(?:[.,]\d+)?\s*(?:%|pct|bps|basis\s+points|ron|eur|lei|mil(?:ion|lioane)|mld|miliard)", headline, flags=re.I):
        gaps.append("quantitative_claim_needs_original_table_and_baseline")
    category = "routine"
    tier = "P2"
    for label, patterns in CRITICAL:
        if _has(headline, patterns):
            category, tier = label, "P0"
            break
    if tier == "P2":
        for label, patterns in IMPORTANT:
            if _has(headline, patterns):
                category, tier = label, "P1"
                break
    # Generic announcements, opinion and PR do not become important just
    # because the RSS source's keyword hint says urgent.
    hold = any(x in gaps for x in (
        "future_publication_timestamp",
        "stale_or_historical_older_than_7_days",
        "missing_or_invalid_timezone_aware_publication_date",
    ))
    return {
        "tier_candidate": tier,
        "event_category_candidate": category,
        "headline_only": True,
        "impact_on_romania": "UNVERIFIED_REQUIRES_CAUSAL_ANALYSIS",
        "significance_reason": (
            "Potential high-impact event: verify market interruption, source and affected securities" if tier == "P0"
            else "Potential material event: verify issuer/macro details and BVB sector transmission" if tier == "P1"
            else "No confirmed material market event from headline alone; archive or review routinely"
        ),
        "headline_review_priority": ("hold_metadata_review" if hold else
                                     "review_soon" if tier in ("P0", "P1") else "routine_review"),
        "metadata_holds_highlight": hold,
        "evidence_gaps": gaps,
        "numerical_source_check_required": "quantitative_claim_needs_original_table_and_baseline" in gaps,
        "facts_verified": False,
        "publishable": False,
        "manual_article_and_independent_data_review": True,
    }
