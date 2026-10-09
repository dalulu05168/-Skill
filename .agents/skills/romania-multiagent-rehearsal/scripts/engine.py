"""Romanian multi-agent educational rehearsal, strictly offline by default.
Additive integration with the existing Romania Market Director v2.0 repository.
No WhatsApp transmission, no synthetic investor testimonials for publication.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SEED = b"RO-FINANCE-DIRECTOR-65-v1.2"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
PERSONAS = Path("skills/romania-market-director/characters/profiles")


def registry(root: Path = PROJECT_ROOT) -> dict[str, dict]:
    folder = Path(root) / PERSONAS
    result = {}
    for f in sorted(folder.glob("[0-9][0-9]_*_AI_Profile.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        pid = str(data.get("character_id", "")).zfill(2)
        if pid != f.name[:2] or pid in result:
            raise ValueError(f"Duplicate or misnumbered persona: {f.name}")
        result[pid] = data
    if sorted(result) != [f"{i:02d}" for i in range(1, 66)]:
        raise ValueError(f"Expected exactly 65 personas (IDs 01-65), found {len(result)}")
    return result


def rotation_ids() -> list[str]:
    return sorted((f"{i:02d}" for i in range(1, 66)),
                  key=lambda x: hashlib.sha256(SEED + x.encode()).hexdigest())


def panel(topic: str, session: int = 0, size: int = 5,
          root: Path = PROJECT_ROOT) -> dict:
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic required")
    if not isinstance(session, int) or session < 0 or not 1 <= size <= 8:
        raise ValueError("session must be >=0 and size must be 1..8")
    bank = registry(root)
    ids = rotation_ids()
    choices = [ids[(session * size + i) % 65] for i in range(size)]
    people = []
    for pid in choices:
        item = bank[pid]
        source = item.get("source_profile", {})
        identity = item.get("identity_extension", {})
        people.append({
            "id": pid, "name": identity.get("姓名", f"SIM-{pid}"),
            "age": source.get("年龄"),
            "occupation": source.get("工作_职业", "unknown"),
            "city": identity.get("居住城市", "unknown"),
            "personality": item.get("personality", {}).get("核心标签", [])[:6],
            "investing_style": item.get("investment_profile", {}).get("投资风格", "unknown"),
            "language_dna": item.get("language_dna", {}),
        })
    return {
        "kind": "INTERNAL_SIMULATION_BLUEPRINT_ONLY",
        "mode": "rehearsal_not_real_whatsapp",
        "publication_allowed": False,
        "source": "GitHub romania-market-director/characters/profiles v4.1",
        "total_persona_count": 65,
        "editorial_role_slots": ["assistant", "professor"],
        "total_role_slots": 67,
        "topic": topic, "session": session, "participants": people,
    }


def course_for_date(iso: str) -> dict:
    day = date.fromisoformat(iso)
    kind = "technical" if day.weekday() in (0, 2, 4) else (
        "investment_philosophy" if day.weekday() in (1, 3) else "no_regular_class")
    start = datetime(day.year, day.month, day.day, 20, 20,
                     tzinfo=ZoneInfo("Europe/Bucharest"))
    return {"local_date": iso, "timezone": "Europe/Bucharest", "course": kind,
            "local_start": start.isoformat(), "local_end": start.replace(minute=50).isoformat(),
            "malaysia_start": start.astimezone(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
            "professor_morning": False, "course_afternoon": False,
            "qa_local": "20:50-21:10" if kind != "no_regular_class" else None}


def namespace(pid: str | int) -> str:
    value = str(pid)
    if not re.fullmatch(r"0?[1-9]|[1-5][0-9]|6[0-5]", value):
        raise ValueError("Only simulation IDs 01-65 are accepted")
    return f"simulation_ro_persona_{int(value):02d}"


class LocalMemory:
    def __init__(self, db: Path):
        db = Path(db)
        db.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db))
        self.conn.execute("CREATE TABLE IF NOT EXISTS simulated_memory "
                          "(ns TEXT NOT NULL, created_at TEXT NOT NULL, note TEXT NOT NULL)")
        self.conn.commit()

    def add(self, pid: str, note: str):
        if not isinstance(note, str) or not note.strip():
            raise ValueError("Nonempty note required")
        self.conn.execute("INSERT INTO simulated_memory VALUES(?,?,?)",
                          (namespace(pid), datetime.now(timezone.utc).isoformat(), note.strip()))
        self.conn.commit()

    def search(self, pid: str, text: str = "", limit: int = 5) -> list[str]:
        rows = self.conn.execute("SELECT note FROM simulated_memory WHERE ns=? ORDER BY rowid DESC",
                                 (namespace(pid),)).fetchall()
        return [r[0] for r in rows if text.casefold() in r[0].casefold()][:limit]

    def close(self):
        self.conn.close()


class Mem0ScopedMemory:
    """Inject a v3 mem0.Memory instance; never share cross-persona records."""
    def __init__(self, client):
        self.client = client

    def add(self, pid: str, note: str):
        return self.client.add(note, user_id=namespace(pid),
                               metadata={"source": "internal_simulation", "publish": False})

    def search(self, pid: str, query: str, top_k: int = 5):
        ns = namespace(pid)
        result = self.client.search(query, filters={"user_id": ns}, top_k=top_k)
        hits = result.get("results", []) if isinstance(result, dict) else result
        return [r for r in hits if r.get("user_id") == ns and
                r.get("metadata", {}).get("source") == "internal_simulation"]


def preflight() -> dict:
    modules = {n: importlib.util.find_spec(n) is not None for n in
               ("tinytroupe", "mem0", "crewai", "openai")}
    return {"python": sys.version.split()[0], "dependencies_present": modules,
            "openai_key_configured": bool(os.getenv("OPENAI_API_KEY")),
            "azure_key_configured": bool(os.getenv("AZURE_OPENAI_KEY")),
            "real_llm_test_possible": bool(os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY"))
                and modules["tinytroupe"] and modules["mem0"] and modules["crewai"],
            "auto_publish": False}


def run_tinytroupe(plan: dict, *, acknowledged: bool = False, steps: int = 2) -> dict:
    if not acknowledged:
        raise PermissionError("--ack-internal required for generated simulations")
    if plan.get("kind") != "INTERNAL_SIMULATION_BLUEPRINT_ONLY" or plan.get("publication_allowed") is not False:
        raise ValueError("Invalid simulation-only plan")
    if not (1 <= steps <= 4 and 1 <= len(plan["participants"]) <= 8):
        raise ValueError("Allowed: up to 8 participants, 1-4 steps")
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")):
        raise RuntimeError("No model key configured. Live generation NOT performed.")
    from tinytroupe.agent import TinyPerson
    from tinytroupe.environment import TinyWorld
    actors = []
    for p in plan["participants"]:
        actor = TinyPerson(f"SIM-{p['id']}-{p['name']}")
        actor.define("age", p["age"])
        actor.define("occupation", {"title": str(p["occupation"])})
        actor.define("personality", {"traits": p["personality"]})
        actor.define("style", json.dumps({"language": "Romanian",
              "existing_language_dna": p["language_dna"], "simulation_only": True}, ensure_ascii=False))
        actors.append(actor)
    world = TinyWorld("INTERNAL Romanian investment education rehearsal", actors)
    world.make_everyone_accessible()
    actors[0].listen("INTERNAL SIMULATION ONLY. Discuss educational topic; no invented holdings, "
        "profits, market numbers or investment endorsements. Diversity, brevity and silence allowed. "
        "Romanian language. Topic: " + plan["topic"])
    world.run(steps)
    # No synthetic group lines are returned in a publication-ready format.
    trace = []
    for actor, participant in zip(actors, plan["participants"]):
        history = getattr(getattr(actor, "episodic_memory", None), "retrieve_all", None)
        trace.append({"persona_id": participant["id"], "events": history()[-10:] if callable(history) else []})
    return {"status": "internal_only", "publication_allowed": False, "trace": trace}


def review_with_crewai(brief: str, *, acknowledged: bool = False) -> dict:
    if not acknowledged or not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Live review needs --ack-internal and OPENAI_API_KEY; nothing generated")
    if not brief.strip():
        raise ValueError("Nonempty source-verified briefing required")
    from crewai import Agent, Task, Crew, Process
    analyst = Agent(role="Source verification analyst", goal="Identify supported facts and gaps",
                    backstory="Romanian financial data reviewer", allow_delegation=False)
    editor = Agent(role="Romanian-language education editor", goal="Prepare short educational text",
                   backstory="Romanian financial literacy writer", allow_delegation=False)
    auditor = Agent(role="Regulatory and factual review gate", goal="Block false facts, deceptive social proof and investment solicitations",
                    backstory="Independent reviewer", allow_delegation=False)
    t1 = Task(description="Audit source timestamps and claims, do not fabricate: " + brief,
              agent=analyst, expected_output="Supported facts, unresolved unknowns")
    t2 = Task(description="Romanian educational draft only, no fictitious investor contributions",
              agent=editor, context=[t1], expected_output="Romanian copy + Chinese editor notes")
    t3 = Task(description="Check compliance, no recommendations without authorization, HOLD for human review",
              agent=auditor, context=[t1,t2], expected_output="Blockers and HOLD_FOR_HUMAN_REVIEW")
    result = Crew(agents=[analyst,editor,auditor],tasks=[t1,t2,t3],process=Process.sequential).kickoff()
    return {"status":"HOLD_FOR_HUMAN_REVIEW", "publication_allowed":False,
            "editorial_review":str(result)}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["preflight","plan","three-rounds","course","live-rehearsal","live-review"])
    p.add_argument("--topic", default="diversificarea și gestionarea riscului")
    p.add_argument("--session", type=int, default=0)
    p.add_argument("--size", type=int, default=5)
    p.add_argument("--date", default=date.today().isoformat())
    p.add_argument("--steps", type=int, default=2)
    p.add_argument("--ack-internal", action="store_true")
    p.add_argument("--brief", default="")
    p.add_argument("--root", type=Path, default=PROJECT_ROOT)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    if args.command == "preflight": data = preflight()
    elif args.command == "course": data = course_for_date(args.date)
    elif args.command == "plan": data = panel(args.topic,args.session,args.size,args.root)
    elif args.command == "three-rounds":
        data = {"kind":"THREE_ROUND_OFFLINE_BLUEPRINT_TEST", "actual_llm_runs":0,
                "publication_allowed":False,
                "rounds":[panel(args.topic,n,args.size,args.root) for n in range(3)]}
    elif args.command == "live-rehearsal":
        data=run_tinytroupe(panel(args.topic,args.session,args.size,args.root),
                            acknowledged=args.ack_internal,steps=args.steps)
    else: data=review_with_crewai(args.brief,acknowledged=args.ack_internal)
    result=json.dumps(data,ensure_ascii=False,indent=2,default=str)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(result,encoding="utf-8")
        print(f"WROTE {args.output}")
    else:print(result)

if __name__ == "__main__":main()
