"""Source-aware event triage with explicit, explainable *review* priority.

Priority is NOT an estimated return, event probability or buy/sell signal.
"""
from datetime import datetime, timezone
from .common import DataError, nonempty, timestamp, web_url

CATEGORIES = {"central_bank", "earnings", "dividend", "energy", "currency", "sovereign_bond", "policy", "market_structure", "other"}
TRACKED = {"BET", "BVB", "RON", "ROMANIA", "EU", "US", "ENERGY", "BANKS"}


def radar(doc, history=None, as_of=None):
    if not isinstance(doc.get("events"), list):
        raise DataError("events must be an array")
    now = as_of or datetime.now(timezone.utc)
    results, ids, checked = [], set(), []
    for i, e in enumerate(doc["events"]):
        if not isinstance(e, dict):
            raise DataError(f"event[{i}]: object required")
        eid = nonempty(e.get("event_id"), "event_id")
        if eid in ids:
            raise DataError(f"Duplicate event_id {eid}")
        ids.add(eid)
        title = nonempty(e.get("title"), "title")
        category = e.get("category")
        if category not in CATEGORIES:
            raise DataError(f"{eid}: invalid category")
        publication = timestamp(e.get("published_at"), e.get("timezone", "Europe/Bucharest"), "published_at")
        if publication > now:
            raise DataError(f"{eid}: publication in the future")
        if e.get("effective_at"):
            timestamp(e["effective_at"], e.get("timezone", "Europe/Bucharest"), "effective_at")
        url = web_url(e.get("source_url"))
        nonempty(e.get("evidence_locator"), "evidence_locator")
        tags = e.get("relevance_tags")
        if not isinstance(tags, list) or not all(isinstance(t, str) and t.upper() in TRACKED for t in tags):
            raise DataError(f"{eid}: invalid relevance_tags")
        if len(set(tags)) != len(tags):
            raise DataError(f"{eid}: duplicate relevance tags")
        route = e.get("transmission_path")
        if not isinstance(route, list) or not all(isinstance(x, str) and x.strip() for x in route):
            raise DataError(f"{eid}: transmission_path must be a list of reasoned steps")
        checked.append((e, eid, title, category, publication, url, tags, route))
    # Validate the complete batch before recording ANY event.
    for e, eid, title, category, publication, url, tags, route in checked:
        novelty = history.upsert_event(e, now.isoformat()) if history else "not_tracked"
        # Transparent review queue only. Never claim causal strength from scores.
        age_hours = (now - publication).total_seconds() / 3600
        score = min(len(tags) * 2, 6) + (3 if age_hours <= 24 else 1 if age_hours <= 72 else 0) + (2 if novelty in ("new", "revised") else 0)
        results.append({"event_id":eid, "title":title, "category":category, "source_url":url, "published_at":publication.isoformat(), "review_priority_score":score, "review_band":"high" if score >= 9 else "medium" if score >= 5 else "low", "change_state":novelty, "relevance_tags":tags, "transmission_path":route, "uncertainty":e.get("uncertainty", "需独立分析，不能据此推断必然涨跌")})
    return {"as_of":now.isoformat(), "priority_definition":"recency + tag coverage + novelty; review triage only, not market-impact prediction", "events":sorted(results,key=lambda x:(-x["review_priority_score"],x["event_id"]))}
