"""Structural editorial triage only; submitted evidence still needs human review."""

def audit_editorial(packet, messages):
    if packet is None:
        return {"status": "not_run", "issues": [], "human_review_required": True}
    issues = []
    if not isinstance(packet, dict):
        return {"status": "fail", "issues": ["editorial_packet must be an object"],
                "human_review_required": True}

    def require(obj, fields, label):
        if not isinstance(obj, dict):
            issues.append(label + ": object required")
            return
        for field in fields:
            if not isinstance(obj.get(field), str) or not obj[field].strip():
                issues.append(label + ": missing " + field)

    require(packet, ("date", "node_id", "theme", "learning_goal", "handoff"), "execution")
    require(packet.get("owners"), ("evidence", "editor", "assistant", "homework_reviewer"), "owners")
    require(packet.get("course_chain"),
            ("previous_record_or_unknown", "problem", "prerequisites", "example",
             "homework", "rubric", "next_lesson"), "course_chain")
    require(packet.get("reply_plan"), ("assistant_scope", "professor_pending", "follow_up_node"), "reply_plan")
    for field, required in (
        ("hotspots", ("source_url", "event_at", "published_at", "observed_at",
                      "timezone", "units_and_baseline", "delay", "conflicts",
                      "impact", "counter_factors", "reviewer")),
        ("credentials", ("claim", "source_url", "checked_at", "authorization", "scope")),
        ("real_experiences", ("source", "authorization", "verification", "anonymization")),
    ):
        rows = packet.get(field)
        if not isinstance(rows, list):
            issues.append(field + ": array required (empty means no claims)")
            continue
        for row in rows:
            require(row, required, field)

    seen = set()
    last_praise = False
    for i, msg in enumerate(messages, 1):
        if not isinstance(msg, dict):
            continue  # identity validator reports malformed messages
        mid = msg.get("message_id")
        if not isinstance(mid, str) or not mid.strip() or mid in seen:
            issues.append(f"message {i}: unique message_id required")
        member = msg.get("character_id") is not None
        if member and (msg.get("simulation_only") is not True or
                       "虚构教学模拟" not in msg.get("text", "")):
            issues.append(f"message {i}: standalone simulation label required")
        if member and msg.get("experience_kind") not in ("none", "hypothetical"):
            issues.append(f"message {i}: fictional member cannot claim real experience")
        if msg.get("experience_kind") == "hypothetical" and "假设" not in msg.get("text", ""):
            issues.append(f"message {i}: hypothetical example label required")
        if msg.get("intent") in ("question", "answer") and msg.get("reply_to") not in seen:
            issues.append(f"message {i}: reply_to must reference an earlier message")
        praise = member and msg.get("intent") == "praise"
        if praise and last_praise:
            issues.append(f"message {i}: praise chorus requires editing")
        last_praise = praise
        if msg.get("single_focus") is not True:
            issues.append(f"message {i}: single_focus editorial attestation required")
        if isinstance(mid, str):
            seen.add(mid)
    return {"status": "fail" if issues else "needs_human_review", "issues": issues,
            "human_review_required": True, "facts_verified": False,
            "scope": "structure_and_editor_attestations_only"}
