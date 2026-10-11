"""Contract gate and bounded editor loop for P004 fictional sandbox drafts.

No calls to models, network, persistence or publication occur here.
A real LLM callback is an explicit host-integration, not included by default.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from director_storyflow import STORY, STATUS, prepare, writer_prompt

OK = "STRUCTURE_PASS_EDITORIAL_REVIEW_REQUIRED"
PAST_WORDS = re.compile(r"\b(?:ieri|alaltăieri|data trecută|săptămâna trecută|yesterday)\b|昨天|上次", re.I)
ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
UNVERIFIED_TRADE = re.compile(r"\b(?:am cumpărat|am vândut|am făcut profit|am câștigat sigur|profit garantat)\b", re.I)
UNVERIFIED_TICKER_FIGURE = re.compile(r"(?:\b(?:BET|BVB|TLV|SNP|BRD)\b.{0,70}\d+(?:[.,]\d+)?\s*%|\d+(?:[.,]\d+)?\s*%.{0,70}\b(?:BET|BVB|TLV|SNP|BRD)\b)", re.I)


def review(draft, plan):
    """Deterministic checks only; language quality remains an editorial issue."""
    bad, notes=[],[]
    if not isinstance(draft,dict):
        return {"status":"REJECTED","errors":["JSON object required"],"warnings":[],
                "publishable":False,"memory_written":False}
    expected={"story_id":STORY,"status":STATUS,"source_status":"HYPOTHETICAL",
              "simulation_only":True,"scene_id":plan["scene_id"],
              "story_date":plan["story_date"],"daypart":plan["daypart"]}
    for k,v in expected.items():
        if draft.get(k)!=v:bad.append(k+" does not match director plan")
    msgs=draft.get("messages")
    if not isinstance(msgs,list) or not 1<=len(msgs)<=100:
        bad.append("messages must contain 1-100 lines")
        msgs=[]
    cast={c["id"]:c for c in plan["cast"]}
    allowed=set(cast)|{"assistant"}
    if plan["professor_allowed"]:allowed.add("professor")
    previous={(p["scene_id"],p["message_id"],p["speaker_id"])
              for p in plan["history"]}
    used=set();exact=set();members=set();replies=0
    for i,m in enumerate(msgs,1):
        if not isinstance(m,dict):
            bad.append(f"message {i} not an object")
            continue
        mid, speaker, text=m.get("message_id"),m.get("speaker_id"),m.get("text")
        if not isinstance(mid,str) or not ID.fullmatch(mid) or mid in used:
            bad.append(f"message {i} duplicate/invalid message_id")
        if speaker not in allowed:
            bad.append(f"message {i} speaker not selected or forbidden at this time")
        if not isinstance(text,str) or not text.strip():
            bad.append(f"message {i} empty text")
        else:
            limit=2200 if speaker=="professor" else 1200 if speaker=="assistant" else 750
            if len(text)>limit:bad.append(f"message {i} length exceeds role limit")
            normalized=" ".join(text.strip().casefold().split())
            if normalized in exact:bad.append(f"message {i} repeats dialogue verbatim")
            exact.add(normalized)
            if UNVERIFIED_TRADE.search(text):
                bad.append(f"message {i} unsupported past trade or promised result")
            if UNVERIFIED_TICKER_FIGURE.search(text):
                bad.append(f"message {i} unverified ticker performance figure")
            if PAST_WORDS.search(text) and not m.get("continuity_ref"):
                bad.append(f"message {i} requires a sourced continuity_ref")
        if not isinstance(m.get("director_note"),str) or not m["director_note"].strip():
            bad.append(f"message {i} missing causal director_note")
        reply=m.get("reply_to")
        if reply is not None:
            if not isinstance(reply,str) or reply not in used:
                bad.append(f"message {i} reply_to not an earlier message")
            else:replies+=1
        ref=m.get("continuity_ref")
        if ref is not None:
            if not isinstance(ref,dict) or (
                ref.get("scene_id"),ref.get("message_id"),ref.get("speaker_id")) not in previous:
                bad.append(f"message {i} unsourced continuity_ref")
        if speaker in cast:
            members.add(speaker)
            exemplar=cast[speaker]["voice"].get("romanian_audition_line")
            if isinstance(text,str) and exemplar and text.strip()==exemplar.strip():
                notes.append(f"member {speaker} repeated an audition example; rewrite naturally")
        if isinstance(mid,str):used.add(mid)
    if len(members)>=3 and replies==0:
        notes.append("Several members spoke without replying; review queue-like dialogue")
    notes.append("Fictional screenplay only; Romanian fluency, cultural texture, "
                 "investment factual validity and narrative quality still need editorial review")
    return {"status":"REJECTED" if bad else OK,"errors":bad,"warnings":notes,
            "messages":len(msgs),"members":len(members),
            "publishable":False,"memory_written":False}


def execute(roster, request, *, model_fn=None, history=None, attempts=3):
    """Return prompt if no author; otherwise retry rejected drafts with issues."""
    plan=prepare(roster,request,history=history)
    if model_fn is None:
        return {"state":"AWAITING_AUTHOR","plan":plan,"prompt":writer_prompt(plan),
                "publishable":False,"memory_written":False}
    if not callable(model_fn):raise ValueError("model_fn must be callable")
    if type(attempts) is not int or not 1<=attempts<=3:
        raise ValueError("attempts must be 1-3")
    issues=[];reviews=[]
    for attempt in range(1,attempts+1):
        produced=model_fn(writer_prompt(plan,issues))
        if isinstance(produced,str):
            try:produced=json.loads(produced)
            except json.JSONDecodeError:produced=None
        report=review(produced,plan)
        reviews.append({"attempt":attempt,"result":report["status"],
                        "errors":report["errors"]})
        if report["status"]==OK:
            return {"state":"EDITORIAL_REVIEW_REQUIRED","plan":plan,
                    "draft":produced,"qa":report,"attempts":reviews,
                    "publishable":False,"memory_written":False}
        issues=report["errors"]
    return {"state":"REJECTED_MAX_RETRIES","plan":plan,"attempts":reviews,
            "last_errors":issues,"publishable":False,"memory_written":False}


if __name__=="__main__":
    import argparse
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser()
    parser.add_argument("--roster",type=Path,default=root/"characters"/"drafts"/"roster-v2.json")
    parser.add_argument("--request",type=Path,required=True)
    parser.add_argument("--draft",type=Path,required=True)
    args=parser.parse_args()
    roster=json.loads(args.roster.read_text(encoding="utf-8"))
    request=json.loads(args.request.read_text(encoding="utf-8"))
    draft=json.loads(args.draft.read_text(encoding="utf-8"))
    print(json.dumps(review(draft,prepare(roster,request)),indent=2,ensure_ascii=False))
