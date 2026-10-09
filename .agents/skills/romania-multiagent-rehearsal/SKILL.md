---
name: romania-multiagent-rehearsal
description: Prepare source-preserving 65-person Romanian financial education conversation rehearsals with optional TinyTroupe, Mem0 and CrewAI adapters; never publish synthetic investor dialogue as real customer messages.
---

# Romania Multi-Agent Rehearsal v1.3

An **additive optional Skill**, not a replacement for `skills/romania-market-director/SKILL.md` or `.agents/skills/romania-stock-intelligence/SKILL.md`.

## Authority
- Preserve the existing 65-character v4.1 JSON files and professor/assistant editorial roles (67 total slots).
- Existing main director 2.0 owns daytime 50/45 independent-message output quotas and content quality; this Skill **does not alter them**. Do not pad or split messages to meet quotas.
- Current user instruction owns evening professor scheduling: Mon/Wed/Fri technical, Tue/Thu investment philosophy; formal lessons only **20:20–20:50 Europe/Bucharest** and real Q&A **20:50–21:10**. No morning professor or daytime formal professor classes.
- Market intelligence uses `07:00/12:00/17:00 Europe/Bucharest`, with full source URL, time-of-observation, baseline and actual preceding briefing ID.
- Simulated persona messages are **internal fiction only**. The real WhatsApp group can receive only accurately sourced educational copy published by an authorized human after review, without deceptive social proof or fabricated investments. No WhatsApp sending capability is included.

## Operating commands (from repository root)
```bash
python .agents/skills/romania-multiagent-rehearsal/scripts/engine.py preflight
python .agents/skills/romania-multiagent-rehearsal/scripts/engine.py course --date 2026-10-12
python .agents/skills/romania-multiagent-rehearsal/scripts/engine.py three-rounds --topic "gestionarea riscului" --output local-three-rounds.json
python -m unittest discover -s .agents/skills/romania-multiagent-rehearsal/tests -v
```
The three-rounds command tests deterministic selection **without making model calls**; a real three-generation test requires API keys, dependencies and separately executing `live-rehearsal` three times with `--ack-internal`.

## Optional runtime (local, no secrets committed)
Use Python 3.10–3.12 for easier dependency compatibility. Install with a virtual environment; follow the current official versions and avoid blindly mixing libraries in an existing working environment:
```bash
pip install 'git+https://github.com/microsoft/TinyTroupe.git@main'
pip install mem0ai crewai
```
For TinyTroupe, configure `OPENAI_API_KEY` or the provider-specific Azure credentials **locally**, never in GitHub files. `mem0` v3 uses `search(query, filters={"user_id": "simulation_ro_persona_01"})`; users 01–65 remain fully isolated. CrewAI produces only a `HOLD_FOR_HUMAN_REVIEW` editorial draft.

## Use sequence
1. Read current main director SKILL and its v4.1 source persona rules.
2. Run preflight and verify 65 source files are present; schedule by local `Europe/Bucharest` date.
3. Run three-round *offline* blueprints, inspect 5 simulated personalities per round.
4. Optionally perform model-backed internal simulations and check language length, expressiveness, contradiction, repetition, false facts, source quality and cost.
5. Author any real educator-facing draft *separately* under professor or assistant's authorized identity, validate finance claims, require human review.

For detailed installation and 3-step acceptance refer to `README_中文.md`. This package makes **no changes to production schedules, external services or WhatsApp accounts**.
