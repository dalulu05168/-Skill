"""Director's *fictional, disclosed* newsroom scene cues, never a synthetic audience.

Curate upstream proposals using transparent, balanced editorial factors. Scores
are review prioritization, not fact verification or publishing authorization.
Continue a fictional dialogue only from explicitly adopted scenes/threads.
"""
from datetime import datetime
from urllib.parse import urlsplit


def _rating(row, key):
    val = row.get(key, 0)
    if type(val) is not int or not 0 <= val <= 4:
        raise ValueError(f"{key} must be an integer from 0 to 4")
    return val


def rank_news_for_review(candidates, *, max_candidates=6):
    """Rank supplied records for human fact checking and discussion selection.

    Prioritization NEVER excludes a materially significant downside story for
    being negative about a short-horizon trading outlook. 'Talkability' cannot
    outrank economic impact/relevance. No record is treated as source-confirmed.
    """
    if not isinstance(candidates, list):
        raise ValueError("candidates must be an array")
    if type(max_candidates) is not int or not 1 <= max_candidates <= 30:
        raise ValueError("max_candidates must be 1..30")
    seen, ranked = set(), []
    for n, row in enumerate(candidates, 1):
        if not isinstance(row, dict):
            raise ValueError(f"candidate {n} must be an object")
        headline, url = row.get("headline"), row.get("original_url")
        if not isinstance(headline, str) or not headline.strip() or len(headline) > 450:
            raise ValueError(f"candidate {n} needs a genuine headline")
        if not isinstance(url, str) or not urlsplit(url).scheme in ("https", "http") or not urlsplit(url).netloc:
            raise ValueError(f"candidate {n} needs a source URL")
        record_id = row.get("item_id")
        if not isinstance(record_id, str) or not record_id.strip() or len(record_id) > 140:
            raise ValueError(f"candidate {n} needs a stable item_id")
        key = (url.split("#")[0], record_id)
        if key in seen:
            continue
        seen.add(key)
        relevance = _rating(row, "romania_relevance")
        materiality = _rating(row, "market_materiality")
        freshness = _rating(row, "new_evidence")
        discussion = _rating(row, "discussion_potential")
        risk = row.get("material_downside_risk") is True
        score = materiality * 5 + relevance * 4 + freshness * 2 + discussion
        if risk:
            score += 2  # downside material must not be silently deprioritized
        ranked.append({
            "item_id": record_id, "headline": headline.strip(), "original_url": url,
            "published_at": row.get("published_at"),
            "priority_score": score, "material_downside_risk": risk,
            "editorial_reason": {
                "market_materiality": materiality,
                "romania_relevance": relevance,
                "new_evidence": freshness,
                "discussion_potential": discussion,
                "downside_risk_retained": risk,
            },
            "fact_status": "UNVERIFIED",
            "requires_independent_original_source_check": True,
            "publication_approved": False,
        })
    ranked.sort(key=lambda r: (-r["priority_score"], r["item_id"]))
    # Preserve audit details for all items, not just proposed topics.
    return {
        "review_queue": ranked,
        "shortlist_for_fact_check": ranked[:max_candidates],
        "excluded_as_not_current_shortlist": ranked[max_candidates:],
        "selection_basis": "market impact + Romania relevance + new evidence, then discussion value",
        "source_facts_verified": False,
        "not_a_publish_queue": True,
        "do_not_hide_material_negative_news": True,
    }


def plan_disclosed_scene(node, topic, selected_ids, adopted_sessions, *, unresolved_threads=None):
    """Offer cross-node narrative *cues*; never generates fake real-person posts.

    Imported state must contain explicitly adopted simulation sessions. This
    function does not invent a previous disagreement if nothing is recorded.
    """
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("topic must be supplied")
    if not isinstance(selected_ids, list) or len(set(selected_ids)) != len(selected_ids):
        raise ValueError("selected_ids must be a unique list")
    if not isinstance(adopted_sessions, list):
        raise ValueError("adopted_sessions must be a list")
    if unresolved_threads is None:
        unresolved_threads = []
    if not isinstance(unresolved_threads, list):
        raise ValueError("unresolved_threads must be a list")

    callbacks = []
    for session in adopted_sessions:
        if not isinstance(session, dict) or session.get("status") not in ("adopted", "approved"):
            continue
        msgs = session.get("messages")
        if not isinstance(msgs, list):
            continue
        involved = [m for m in msgs if isinstance(m, dict)
                    and m.get("character_id") in selected_ids]
        if involved:
            callbacks.append({
                "scene_id": session.get("id") or session.get("scene_id"),
                "date": session.get("date"), "topic": session.get("topic"),
                "observed_ids": sorted({m["character_id"] for m in involved}),
                "from_actual_adopted_scene": True,
                "status": "available_as_context_not_a_required_reference",
            })
    explicit = []
    for thread in unresolved_threads:
        if not isinstance(thread, dict) or thread.get("status") not in ("open", "pending"):
            continue
        if not thread.get("scene_id") or not thread.get("question"):
            continue
        if not any(c["scene_id"] == thread["scene_id"] for c in callbacks):
            continue
        explicit.append({
            "scene_id": thread["scene_id"], "question": str(thread["question"])[:400],
            "status": thread["status"], "follow_up": "optional_if_character_motivated",
        })
    return {
        "mode": "fictional_educational_rehearsal_disclosed_not_real_investors",
        "node": node, "current_topic": topic.strip(),
        "continuity_candidates": callbacks[-10:],
        "previous_unresolved_threads": explicit,
        "previous_disagreement_claim": "none_on_record" if not explicit else "only_explicitly_logged_threads",
        "optional_beats": [
            {"id": "current", "rule": "Host presents genuinely checked event or marks unknown; no fabricated numbers"},
            {"id": "overlap", "rule": "Members may continue previous documented question even when a new topic starts; never mandatory"},
            {"id": "peer", "rule": "Members can disagree on interpretations, ask for evidence, joke or remain silent; no assigned fixed pro/con ratios"},
            {"id": "assistant", "rule": "Step in if actual claim is misleading or dispute stops being constructive; summarize known facts and unresolved views without forcing consensus"},
            {"id": "open", "rule": "Mark pending questions and return in a later approved scene only if something meaningful changed"},
        ],
        "allowed_dispute": "civil disagreement about claims, conditions, timing or evidence; no abusive attacks, threats or fabricated accusations",
        "attendance": "no_fixed_members_or_message_count",
        "requires_disclosure": True,
        "auto_publish": False,
        "authenticity_verified": False,
        "no_fake_historical_dialogue": True,
    }
