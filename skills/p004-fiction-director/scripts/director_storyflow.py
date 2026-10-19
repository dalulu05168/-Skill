"""Isolated P004 fictional director pipeline. Standard library, no model or network.
A host may provide an AI author callback; model access and cost are never automatic.
All outputs remain unapproved rehearsal fiction, not real investor discussion.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from director_cast import plan as cast_plan

STORY = "p004-fiction-director-independent"
STATUS = "FICTION_DRAFT_NOT_APPROVED"
GOOD = "STRUCTURE_PASS_EDITORIAL_REVIEW_REQUIRED"
ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def prepare(roster, request, history=None):
    """Bind an eligible cast to a hypothetical scene and explicit provenance."""
    if not isinstance(request, dict):
        raise ValueError("request object required")
    scene = request.get("scene_id")
    if not isinstance(scene, str) or not ID.fullmatch(scene):
        raise ValueError("scene_id must be a safe identifier")
    topic = request.get("topic")
    if not isinstance(topic, str) or not 3 <= len(topic.strip()) <= 300:
        raise ValueError("topic must be 3-300 characters")
    cast = cast_plan(roster, request)
    history = history or []
    if not isinstance(history, list) or len(history)>50:
        raise ValueError("history is a bounded list")
    prior = []
    for row in history:
        if not isinstance(row,dict) or row.get("provenance") not in ("ADOPTED_SQLITE", "SAME_RUN_SANDBOX"):
            raise ValueError("historical source provenance required")
        if row.get("scene_id") == scene:
            raise ValueError("cannot import same scene as prior history")
        if not all(isinstance(row.get(k),str) and row[k].strip() for k in ("scene_id","message_id","speaker_id","text")):
            raise ValueError("history reference incomplete")
        prior.append({k:row[k] for k in ("scene_id","message_id","speaker_id","text","provenance")})
    persons={p["id"]:p for p in roster["people"]}
    cards=[]
    for c in cast["cast"]:
        p=persons[c["speaker_id"]]
        cards.append({"id":p["id"],"name":p["name"],"role":p["main_behavior"],
                      "secondary":p["secondary_behavior"],"job":p["occupation"],
                      "interest":p["interest_triggers"],"voice":p["voice"],
                      "interaction":p["turn_taking"],"may_remain_silent":True})
    return {"story_id":STORY,"scene_id":scene,"story_date":request["story_date"],
            "daypart":request["daypart"],"topic":topic,"source_status":"HYPOTHETICAL",
            "simulation_only":True,"professor_allowed":cast["professor_allowed"],
            "cast":cards,"history":prior,"approved":False,"publishable":False}


def writer_prompt(plan, issues=None):
    """Prompt for the configured ChatGPT/model writer; itself makes no model call."""
    if plan.get("story_id") != STORY or plan.get("approved") is not False:
        raise ValueError("isolated unapproved plan required")
    sample={"story_id":STORY,"status":STATUS,"simulation_only":True,
            "source_status":"HYPOTHETICAL","scene_id":plan["scene_id"],
            "story_date":plan["story_date"],"daypart":plan["daypart"],
            "messages":[{"message_id":"m01","speaker_id":"assistant",
                         "text":"Exemplu ipotetic, nu știre de azi.",
                         "director_note":"educational opening"}]}
    return "\n".join([
        "Compose a fictional Romanian-language educational dialogue for a story.",
        "Return one JSON object only, no markdown. All characters are fictional.",
        "Write short, individual voices. Characters can disagree, joke, stay silent.",
        "Use ONLY the selected cast, assistant, and professor if allowed at night.",
        "Never invent real stock quotes, executed trades, public testimonials or past events.",
        "When mentioning a prior event supply continuity_ref {scene_id,message_id,speaker_id}.",
        "Only use prior events from the verified context; reply_to references earlier lines of this scene.",
        "Each message requires message_id, speaker_id, text and director_note.",
        "Keep the source status hypothetical and require human editorial review.",
        "Expected JSON skeleton: "+json.dumps(sample,ensure_ascii=False),
        "Director context: "+json.dumps(plan,ensure_ascii=False),
        "Corrections requested: "+json.dumps(issues or [],ensure_ascii=False)
    ])


def roster_coverage(roster):
    """Check all 65 personas can be suggested by personal interests, not drafted."""
    missed=[];seen=0
    for person in roster["people"]:
        selected=False
        for part in ("morning","afternoon","evening"):
            request={"simulation_only":True,"source_status":"HYPOTHETICAL",
                     "scene_id":"coverage-"+person["id"],"story_date":"2026-10-14",
                     "daypart":part,"topic":"individual topic casting",
                     "topic_keywords":[person["interest_triggers"][0]],"max_members":15}
            out=prepare(roster,request)
            if any(c["id"]==person["id"] for c in out["cast"]):
                selected=True
                break
        if selected:seen+=1
        else:missed.append(person["id"])
    return {"status":"CASTING_COVERAGE_ONLY","selected":seen,"out_of":65,
            "missing":missed,"ai_dialogue_tested":False,
            "memory_written":False,"approved":False}


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("operation",choices=("plan","coverage"))
    parser.add_argument("--roster",type=Path,default=Path(__file__).resolve().parents[1]/"characters"/"drafts"/"roster-v2.json")
    parser.add_argument("--request",type=Path)
    args=parser.parse_args()
    people=json.loads(args.roster.read_text(encoding="utf-8"))
    if args.operation=="coverage":result=roster_coverage(people)
    else:
        if not args.request:parser.error("--request required for plan")
        result=prepare(people,json.loads(args.request.read_text(encoding="utf-8")))
        result={"plan":result,"prompt":writer_prompt(result)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
