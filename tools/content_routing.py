"""Read-only content routing metadata for the existing BVB Finance skill hub.

The authoritative 16-node schedule is NEVER modified here.  The local service
exposes classification metadata that a separate BVB dashboard can adopt without
replacing its UI, data or scheduler.  Numeric targets are editorial guidance,
never automated publication quotas.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEL_CONFIG = ROOT / ".agents" / "skills" / "romania-stock-intelligence" / "config"


def routing_snapshot():
    config = json.loads((INTEL_CONFIG / "content-classification.json").read_text(encoding="utf-8"))
    schedule = json.loads((INTEL_CONFIG / "schedule.json").read_text(encoding="utf-8"))
    runs = schedule["runs"]
    nodes = config["nodes"]
    expected = [row["id"] for row in runs]
    if len(expected) != 16 or len(set(expected)) != 16:
        raise ValueError("The authoritative 16-node schedule changed; stop classification")
    if [row["id"] for row in nodes] != expected:
        raise ValueError("Category map does not exactly match canonical 16-node schedule/order")
    if schedule.get("timezone") != config.get("timezone") or schedule.get("timezone") != "Europe/Bucharest":
        raise ValueError("Timezones differ; stop classification")
    category_ids = [row["id"] for row in config["categories"]]
    if len(category_ids) != 4 or set(category_ids) != {"news", "market", "course", "interaction"}:
        raise ValueError("Four content categories must remain unique")
    all_counted = set()
    for period, quota in config["daily_targets"].items():
        target = quota["target"]
        low, high = quota["guidance_range"]
        if not (low <= target <= high and target-low <= 3 and high-target <= 3):
            raise ValueError("Daypart target must allow no more than +/-3")
        for node in quota["counted_nodes"]:
            if node in all_counted or node not in expected:
                raise ValueError("Overlapping or unknown weekday counting node")
            all_counted.add(node)
    if all_counted != {r["id"] for r in runs if r["days"] == "工作日"} - {"RO-01"}:
        raise ValueError("Weekday counting nodes do not cover every external node exactly once")
    enriched = []
    for node, run in zip(nodes, runs):
        if node["category"] not in category_ids or any(t not in category_ids for t in node["secondary"]):
            raise ValueError("Unknown category")
        enriched.append({**node,
                         "days": run["days"],
                         "publication": run["publication"],
                         "preparation": run["preparation"],
                         "topic": run["topic"]})
    return {
        "schema_version": config["schema_version"],
        "timezone": config["timezone"],
        "categories": config["categories"],
        "daily_targets": config["daily_targets"],
        "counting_rules": config["counting_rules"],
        "review_gates": config["review_gates"],
        "publication_boundary": config["publication_boundary"],
        "nodes": enriched,
        "source_schedule_status": schedule["status"],
        "read_only": True,
    }


def period_guidance(period, actual_count):
    """Describe progress, without making a factual claim of publication or approval."""
    data = routing_snapshot()
    if period not in data["daily_targets"]:
        raise ValueError("Unknown weekday period")
    if type(actual_count) is not int or actual_count < 0:
        raise ValueError("Count must be a nonnegative integer")
    q = data["daily_targets"][period]
    low, high = q["guidance_range"]
    return {
        "period": period, "target": q["target"],
        "guidance_range": [low, high], "supplied_count": actual_count,
        "within_guidance": low <= actual_count <= high,
        "advisory_only": True,
        "no_automatic_send_or_fill": True,
        "quality_over_count": True,
    }
