"""Time-window market brief for the original BVB v3.3 collector.

A real feed fetch is not a verified article. A delayed index observation is not
an exchange-authorized real-time quote. Never synthesize market numbers.
"""
from __future__ import annotations

from datetime import datetime, date, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import json
import math
import re
import sys
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".agents" / "skills" / "romania-stock-intelligence" / "config" / "schedule.json"
BUCHAREST = ZoneInfo("Europe/Bucharest")
sys.path.insert(0, str(ROOT / "tools"))
from news_materiality import assess_news

FEED_HOSTS = {
    "bvb-market": {"bvb.ro", "www.bvb.ro", "iris.bvb.ro"},
    "bvb-issuer": {"bvb.ro", "www.bvb.ro", "iris.bvb.ro"},
    "bvb-operation": {"bvb.ro", "www.bvb.ro", "iris.bvb.ro"},
    "ecb": {"ecb.europa.eu", "www.ecb.europa.eu"},
    "bursa": {"bursa.ro", "www.bursa.ro"},
}

def schedule():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    runs = config.get("runs", [])
    if config.get("timezone") != "Europe/Bucharest" or len(runs) != 16:
        raise ValueError("Canonical 16-node Bucharest schedule is missing")
    if len({r["id"] for r in runs}) != 16:
        raise ValueError("Duplicate BVB node identifiers")
    return runs

def _active_on(run, day: date):
    label = run["days"]
    weekday = day.weekday()
    return (label == "工作日" and weekday < 5 or
            label == "周六" and weekday == 5 or
            label == "周日" and weekday == 6)

def _local(day, time_label):
    hour, minute = (int(x) for x in time_label.split(":"))
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=BUCHAREST)

def window_for(now: datetime, node_id: str | None = None):
    """Each brief covers the period since the previous preparation checkpoint.

    Stops at the current observation time, not a future publication time.
    The configured 16-node dates/times remain unchanged and are not scheduled.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Timezone-aware now is required")
    local = now.astimezone(BUCHAREST)
    rows = []
    for offset in (-3, -2, -1, 0, 1):
        day = local.date() + timedelta(days=offset)
        for run in schedule():
            if _active_on(run, day):
                rows.append({"run": run, "day": day, "prep": _local(day, run["preparation"])})
    rows.sort(key=lambda r: r["prep"])
    eligible = [r for r in rows if r["prep"] <= local]
    if not eligible:
        raise ValueError("No past BVB observation checkpoint")
    if node_id is None:
        chosen = eligible[-1]
    else:
        candidates = [r for r in eligible if r["run"]["id"] == node_id and r["day"] == local.date()]
        if not candidates:
            raise ValueError("Requested node has not reached preparation time")
        chosen = candidates[-1]
    at_index = rows.index(chosen)
    previous = rows[at_index-1] if at_index > 0 else None
    start = (previous["prep"] if previous else chosen["prep"] - timedelta(hours=24))
    # Explicit historical node: finish at that node's publication time.
    end = local if node_id is None else min(local, _local(chosen["day"], chosen["run"]["publication"]))
    if end < start:
        raise ValueError("Invalid node time window")
    return {
        "id": chosen["run"]["id"],
        "topic": chosen["run"]["topic"],
        "date": chosen["day"].isoformat(),
        "timezone": "Europe/Bucharest",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "preparation": chosen["run"]["preparation"],
        "publication": chosen["run"]["publication"],
        "execution": "on_demand_only_not_scheduled",
    }

def _published(raw):
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        at = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        try:
            at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    return at.astimezone(timezone.utc) if at.tzinfo is not None else None

def _article_url_valid(article):
    expected = FEED_HOSTS.get(article.get("sourceId"))
    try:
        u = urlsplit(article.get("url") or "")
        return bool(expected and u.scheme == "https" and u.hostname in expected
                    and u.port in (None, 443) and not u.username and not u.password)
    except ValueError:
        return False

def audit_news(articles, window, *, checked_at=None):
    """Metadata-level authenticity checks only. No claim of original fact review."""
    start = datetime.fromisoformat(window["start"]).astimezone(timezone.utc)
    end = datetime.fromisoformat(window["end"]).astimezone(timezone.utc)
    at = checked_at or end
    rows, held = [], []
    seen = set()
    for article in articles:
        if not isinstance(article, dict):
            continue
        ts = _published(article.get("dateRaw") or article.get("published_at"))
        if ts is None:
            held.append({"title": str(article.get("title") or "")[:150],
                         "status": "publication_timestamp_missing_or_invalid",
                         "url": str(article.get("url") or "")[:400]})
            continue
        if ts < start or ts > end:
            continue
        if not _article_url_valid(article):
            held.append({"title": str(article.get("title") or "")[:150],
                         "status": "untrusted_article_origin", "url": str(article.get("url") or "")[:400]})
            continue
        ident = (article.get("sourceId"), article.get("guid") or article.get("url"),
                 str(article.get("title") or ""))
        if ident in seen:
            continue
        seen.add(ident)
        news = {"title": str(article.get("title") or ""),
                "summary": str(article.get("description") or article.get("summary") or ""),
                "published_at": ts.isoformat()}
        importance = assess_news(news, at)
        rows.append({
            "title": news["title"][:260], "url": article["url"], "source": article.get("source"),
            "source_id": article["sourceId"], "published_at": ts.isoformat(),
            "priority_candidate": importance["tier_candidate"],
            "event_category_candidate": importance["event_category_candidate"],
            "potential_romania_impact": importance["significance_reason"],
            "source_metadata_checked": True,
            "original_article_checked": False,
            "independent_corroboration_checked": False,
            "facts_verified": False,
            "authenticity": "pending_original_and_independent_fact_check",
            "evidence_gaps": importance["evidence_gaps"] + [
                "read_full_original_document",
                "cross_check_quantities_dates_and_comparison_baselines",
                "independent_corroboration_where_available",
            ],
        })
    rank = {"P0": 0, "P1": 1, "P2": 2}
    rows.sort(key=lambda v: (rank.get(v["priority_candidate"], 2), -_published(v["published_at"]).timestamp()))
    return rows, held

def market_analysis(quote, hotspots):
    """Direction and hypotheses ONLY when a delayed quote has usable fields."""
    if not isinstance(quote, dict) or quote.get("state") != "ok":
        return {"status": "insufficient_market_data", "bet_direction": "unknown",
                "reason": "没有通过接口获得带数值和时间戳的 BET 指数，不能判断实际涨跌",
                "market_time": None, "numerical_claims_verified": False,
                "drivers": "仅列出候审热点，不能声称它们造成指数涨跌"}
    try:
        value = float(quote["value"])
        pct = float(quote["change"])
    except (TypeError, ValueError, KeyError):
        return market_analysis({"state": "unavailable"}, hotspots)
    stamp = quote.get("marketTime")
    if not math.isfinite(value) or not math.isfinite(pct) or value <= 0 or abs(pct) >= 90 or not stamp:
        return market_analysis({"state": "unavailable"}, hotspots)
    direction = "up" if pct > 0 else "down" if pct < 0 else "flat"
    return {"status": "provisional_delayed_observation", "bet_direction": direction,
            "bet_value": value, "bet_percent_change": pct,
            "market_time": stamp, "source": quote.get("url"),
            "quote_type": "official_delayed_source_not_real_time",
            "numerical_claims_verified": False,
            "drivers": "候审热点只表示待研究的潜在影响；尚不能证明实际涨跌原因",
            "bank_energy_weight_attribution": "unavailable_without_verified_constituent_weights_and_prices",
            "hotspot_candidates": len([n for n in hotspots if n["priority_candidate"] in ("P0", "P1")])}

def build_brief(snapshot, *, at=None, node_id=None):
    if not isinstance(snapshot, dict):
        raise ValueError("Collector result must be an object")
    now = at or datetime.now(timezone.utc)
    window = window_for(now, node_id)
    articles = snapshot.get("articles")
    if not isinstance(articles, list):
        raise ValueError("Collector did not return an article array")
    rows, held = audit_news(articles, window, checked_at=now)
    source_states = snapshot.get("sources") or []
    failed = [s for s in source_states if isinstance(s, dict) and s.get("state") != "ok"]
    return {
        "type": "bvb_time_window_market_brief",
        "collected_at": snapshot.get("fetchedAt"),
        "generated_at": now.isoformat(),
        "window": window,
        "news": {
            "count": len(rows),
            "priority_candidates": [r for r in rows if r["priority_candidate"] in ("P0","P1")],
            "other_window_articles": [r for r in rows if r["priority_candidate"] == "P2"],
            "held_for_metadata": held,
            "source_failures": failed,
            "fact_verification_status": "pending_original_and_independent_fact_check",
            "autofactcheck_success": False,
        },
        "market": market_analysis(snapshot.get("quote"), rows),
        "notices": [
            "此报告只选取指定节点时间范围内的资讯，不代表实时数据供给。",
            "RSS 源验证仅能确认采集位置和元数据，不能证实文章内容。",
            "BET 数据来自可用时的 BVB 延迟报价尝试，非获授权实时行情。",
            "没有原文与可复核数值时，不输出已确认市场因果结论。",
            "未启用自动定时、自动发布、AI 原创文章或其他模块业务。",
        ],
    }
