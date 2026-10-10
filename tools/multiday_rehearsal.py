"""Three-day simulation-only storyline regression.

Designed for editor-confirmed, clearly labeled *fictional* rehearsal transcripts.
Runs deterministically, without a model, social network connection or data fetch.
It DOES NOT verify financial facts, approve public release, or persist memory.
"""
import re
from datetime import date

from content_routing import routing_snapshot
from dialogue_quality import DISCLOSURE, audit_dialogue
from skill_execution_contract import (
    audit_member_voice, audit_upstream_news_data, lesson_for,
)

ASSISTANT_FIELDS = (
    "event", "evidence_url", "observed_at", "market_link",
    "causal_path", "counter_factors", "uncertainty", "next_check",
)
PROFESSOR_FIELDS = (
    "learning_objective", "principle", "example", "mistake",
    "practice", "next_link", "source_status",
)


def _nonempty(row, key):
    return isinstance(row.get(key), str) and bool(row[key].strip())


def inspect_three_day_rehearsal(package, profiles, *, adopted_scenes=None):
    """Read-only quality gate for exactly three distinct Romanian-local dates.

    Day-to-day callbacks inside this package are fictitious rehearsal continuity.
    References to historic memory are allowed only from *already adopted*
    scenes, never draft/unchecked text. An upstream feed is only a candidate;
    an editor-provided 'verified' field cannot become objective verification.
    """
    if adopted_scenes is None:
        adopted_scenes = []
    if not isinstance(package, dict) or not isinstance(package.get("days"), list) or len(package["days"]) != 3:
        raise ValueError("Exactly three consecutive rehearsal days are required")
    if not isinstance(adopted_scenes, list) or not isinstance(profiles, dict):
        raise ValueError("profiles and adopted_scenes must have valid types")

    dates, problems, cautions = [], [], []
    scene_book, approved_book = {}, {}
    for prior in adopted_scenes:
        if not isinstance(prior, dict) or prior.get("status") not in ("adopted", "approved"):
            continue
        pid = prior.get("id") or prior.get("scene_id")
        if (isinstance(pid, str) and pid and isinstance(prior.get("messages"), list)
                and prior["messages"] and all(isinstance(m, dict) and m.get("simulation_only") is True
                                          and DISCLOSURE in str(m.get("text", ""))
                                          for m in prior["messages"])):
            approved_book[pid] = prior

    source_report = audit_upstream_news_data(package.get("upstream_packet"))
    if source_report["issues"]:
        problems.extend("upstream: " + x for x in source_report["issues"])
    news_ids = {}
    raw_input = package.get("upstream_packet")
    if isinstance(raw_input, dict) and isinstance(raw_input.get("news"), list):
        for news in raw_input["news"]:
            if isinstance(news, dict) and isinstance(news.get("item_id"), str) and news["item_id"]:
                if news["item_id"] in news_ids:
                    problems.append("upstream: duplicate news item_id " + news["item_id"])
                news_ids[news["item_id"]] = news

    schedule = routing_snapshot()
    nodes = {row["id"]: row for row in schedule["nodes"]}
    row_count, assistant_slots, professor_slots, peer_turns, old_callbacks = 0, 0, 0, 0, 0
    repeated_phrases, issue_counts = {}, {}
    for di, day in enumerate(package["days"], 1):
        if not isinstance(day, dict):
            problems.append(f"day {di}: object required")
            continue
        iso = day.get("date")
        try:
            day_date = date.fromisoformat(iso)
            if day_date.isoformat() != iso:
                raise ValueError
        except (TypeError, ValueError):
            problems.append(f"day {di}: invalid date")
            continue
        dates.append(day_date)
        if not isinstance(day.get("scenes"), list) or not day["scenes"]:
            problems.append(f"day {di}: scenes must be a non-empty array")
            continue
        prev_node = 0
        for si, scene in enumerate(day["scenes"], 1):
            prefix = f"day {di} scene {si}"
            if not isinstance(scene, dict):
                problems.append(prefix + ": object required")
                continue
            scene_id = scene.get("scene_id")
            if not isinstance(scene_id, str) or not scene_id or len(scene_id) > 120 or scene_id in scene_book or scene_id in approved_book:
                problems.append(prefix + ": unique scene_id required")
                continue
            node_id = scene.get("node")
            if node_id not in nodes:
                problems.append(prefix + ": unknown schedule node")
                continue
            node_num = int(node_id.split("-")[1])
            if node_num < prev_node:
                problems.append(prefix + ": scenes are out of node order within the day")
            prev_node = node_num
            node = nodes[node_id]
            is_weekend = day_date.weekday() >= 5
            if is_weekend and node_num < 13 or (not is_weekend and node_num > 12):
                problems.append(prefix + ": schedule node does not belong to that weekday")
            host_kind = scene.get("host_kind")
            if host_kind not in ("assistant", "professor", "none"):
                problems.append(prefix + ": host_kind must be assistant/professor/none")
            if host_kind == "professor":
                professor_slots += 1
                lesson = lesson_for(iso, node_id)
                if not lesson["can_speak"]:
                    problems.append(prefix + ": professor cannot teach at this date/node")
                elif not isinstance(scene.get("professor_course"), dict):
                    problems.append(prefix + ": professor_course must specify a draft lesson")
                else:
                    course = scene["professor_course"]
                    if course.get("course_type") != lesson["mode"]:
                        problems.append(prefix + ": professor course_type must match 135/24")
                    for key in PROFESSOR_FIELDS:
                        if not _nonempty(course, key):
                            problems.append(prefix + ": missing professor_" + key)
                    if lesson["mode"] == "technical" and lesson["technical_source_status"] == "original_user_technical_course_not_in_repository":
                        cautions.append(prefix + ": technical course uses reconstructed outline; original manuscript unavailable")
            if host_kind == "assistant":
                assistant_slots += 1

            claimed_news = scene.get("news_item_ids", [])
            if not isinstance(claimed_news, list):
                problems.append(prefix + ": news_item_ids must be an array")
                claimed_news = []
            for item_id in claimed_news:
                if not isinstance(item_id, str) or item_id not in news_ids:
                    problems.append(prefix + ": news item lacks source packet: " + str(item_id))
            if claimed_news:
                if host_kind != "assistant":
                    problems.append(prefix + ": new financial news requires assistant editorial context")
                analysis = scene.get("assistant_analysis")
                if not isinstance(analysis, dict):
                    problems.append(prefix + ": news requires assistant_analysis")
                else:
                    for k in ASSISTANT_FIELDS:
                        if not _nonempty(analysis, k):
                            problems.append(prefix + ": missing assistant_" + k)
                cautions.append(prefix + ": upstream story still needs independent original-source verification")

            msgs = scene.get("messages")
            if not isinstance(msgs, list):
                problems.append(prefix + ": messages must be an array")
                continue
            for mi, m in enumerate(msgs, 1):
                if not isinstance(m, dict):
                    problems.append(prefix + f": message {mi} must be an object")
                    continue
                cid = m.get("character_id")
                if cid not in profiles:
                    problems.append(prefix + f": unknown 65-person identity {cid}")
                    continue
                p = profiles[cid]
                correct = (p.get("identity_extension", {}).get("姓名"),
                           p.get("source_profile", {}).get("性别"),
                           p.get("source_profile", {}).get("学员资历"))
                given = (m.get("name"), m.get("gender"), m.get("role"))
                if given != correct:
                    problems.append(prefix + f": member {cid} identity/role mismatch")
                if m.get("simulation_only") is not True or not isinstance(m.get("text"), str) or DISCLOSURE not in m["text"]:
                    problems.append(prefix + f": member {cid} must be explicitly disclosed fiction")
                phrase = re.sub(r"\s+", "", str(m.get("text", "")).replace(DISCLOSURE, ""))
                if phrase:
                    repeated_phrases.setdefault(phrase, set()).add((di, scene_id))
            audit = audit_dialogue(msgs)
            personal = audit_member_voice(msgs, profiles)
            problems.extend(prefix + ": " + x for x in audit["issues"] + personal["issues"])
            cautions.extend(prefix + ": " + x for x in audit["warnings"] + personal["warnings"])
            peer_turns += audit.get("metrics", {}).get("peer_or_prior_replies", 0)
            row_count += len(msgs)
            issue_counts[scene_id] = len(audit["issues"]) + len(personal["issues"])
            links = scene.get("continuity_refs", [])
            if not isinstance(links, list):
                problems.append(prefix + ": continuity_refs must be an array")
                links = []
            for link in links:
                if not isinstance(link, dict) or not isinstance(link.get("scene_id"), str):
                    problems.append(prefix + ": invalid continuity reference")
                    continue
                reference = link["scene_id"]
                if reference in scene_book and link.get("scope") == "sandbox_rehearsal":
                    old_callbacks += 1
                elif reference in approved_book and link.get("scope") == "approved_history":
                    old_callbacks += 1
                else:
                    problems.append(prefix + ": reference is not an earlier rehearsal scene or approved history")
            scene_book[scene_id] = {"date": iso, "node": node_id, "sandbox_only": True}
    if len(dates) == 3:
        if len(set(dates)) != 3 or not (dates[0] < dates[1] < dates[2]):
            problems.append("days must be strictly increasing and distinct")
        elif any((dates[i] - dates[i-1]).days != 1 for i in (1, 2)):
            problems.append("days must be consecutive")
    for phrase, places in repeated_phrases.items():
        if len({day for day, _ in places}) > 1:
            cautions.append("identical member phrase repeated across rehearsal days: " + phrase[:35])
    if old_callbacks == 0:
        cautions.append("no supported callbacks in this run; do not invent a past disagreement to fill the gap")
    if source_report["status"] == "NOT_RECEIVED":
        cautions.append("no incoming source data supplied: news fact checking cannot be performed")
    return {
        "status": "STRUCTURAL_BLOCKED" if problems else "NEEDS_HUMAN_EDITION",
        "issues": problems, "warnings": cautions,
        "day_count": len(dates), "scene_count": len(scene_book),
        "metrics": {"member_turns": row_count, "assistant_scenes": assistant_slots,
                    "professor_scenes": professor_slots, "peer_reply_turns": peer_turns,
                    "supported_continuity_references": old_callbacks},
        "source_review": source_report,
        "all_intra_package_history_is_sandbox_only": True,
        "approved_memory_mutated": False,
        "market_facts_verified": False,
        "character_naturalness_verified": False,
        "human_editor_required": True,
        "publication_allowed": False,
    }


def main(argv=None):
    """Offline quality check; does not import memory or send any messages."""
    import argparse
    import json
    from pathlib import Path
    from chennan_writing import load_profiles

    p = argparse.ArgumentParser(description="Three-day fictional educational rehearsal audit")
    p.add_argument("--input", required=True, help="JSON three-day rehearsal input")
    p.add_argument("--out", help="Write a review report JSON; nothing is published")
    args = p.parse_args(argv)
    package = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = inspect_three_day_rehearsal(package, load_profiles())
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 2 if report["status"] == "STRUCTURAL_BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
