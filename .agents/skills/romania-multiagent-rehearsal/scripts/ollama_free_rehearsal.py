"""Free local-model Romanian persona rehearsal (Ollama, no API credentials).

Runs on isolated ephemeral GitHub Actions CPU runner. This is an INTERNAL
FICTIONAL SIMULATION ONLY, not a source for authentic financial testimonials
or WhatsApp publication. Does not contact hosted LLM APIs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from engine import panel, registry

SAFE_MODELS = {"qwen2.5:1.5b", "qwen2.5:0.5b"}
DEFAULT_HOST = "http://127.0.0.1:11434"


def query_model(*, prompt: str, model: str, host: str = DEFAULT_HOST, timeout: int = 150) -> str:
    if model not in SAFE_MODELS:
        raise ValueError("Model not in reviewed open-model allowlist")
    if host != DEFAULT_HOST:
        raise ValueError("Only isolated loopback Ollama is permitted")
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.72, "num_predict": 90,
                                  "num_ctx": 2048, "num_thread": 2}}).encode("utf-8")
    request = Request(host + "/api/generate", data=body,
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read(2_000_000).decode("utf-8"))
    if "error" in result:
        raise RuntimeError("Local Ollama model returned an error")
    text = str(result.get("response", "")).strip()
    if not text:
        raise RuntimeError("Empty model response")
    return text


def compose_prompt(person: dict, topic: str, recent: list[str]) -> str:
    occupation = str(person.get("occupation") or "persoană")
    tags = ", ".join(str(x) for x in person.get("personality", [])[:5])
    language_dna = json.dumps(person.get("language_dna", {}), ensure_ascii=False)[:450]
    recent_text = "\n".join(recent[-2:])
    return f"""EXPERIMENT INTERN, PARTICIPANŢI FICTIVI. Do not pretend to be real investors.
You are a fictional Romanian adult in an internal test of FINANCIAL EDUCATION conversation.
Full name: {person["name"]}; age {person.get("age")}; occupation: {occupation}.
Temperament: {tags or "natural, distinctive"}; style reference: {language_dna}.
Write ONE natural Romanian WhatsApp-like reply, roughly 4-28 Romanian words.
A greeting is optional. Use at most ONE emoji; short everyday language.
Don't write your character's name or label; no other characters' lines.
Use a distinctive voice grounded in the identity. Some uncertainty, question
or skepticism is welcome. No purchase or sale instructions. No imagined
returns, account balances, market prices, recommendations, testimonials,
professional credentials, or promises.
Topic: {topic}
Assistant's educational opener: "Discutăm despre diversificare şi
incertitudine; riscul nu dispare doar pentru că avem mai multe poziţii."
Previous fictional test replies:
{recent_text or "(none)"}
One short Romanian reply:"""


def safety_flags(text: str) -> list[str]:
    if not isinstance(text, str):
        return ["invalid_type"]
    patterns = {
        "financial_guarantee": r"(?i)\b(garantat|garantez|garantăm|garantie\s+profit|profit\s+sigur|câştig\s+sigur)\b",
        "directional_trade_instruction": r"(?i)\b(cumpără\s+acum|vinde\s+acum|buy\s+now|sell\s+now)\b",
        "suspicious_link": r"(?i)https?://|www\.",
        "looks_like_phone": r"(?<!\d)(?:\+40|0040)\s?\d{9}(?!\d)",
        "potential_fake_return": r"(?i)\b(?:profit|randament|câştig)\b.{0,20}\b\d+(?:[.,]\d+)?\s?%",
    }
    return [name for name,regex in patterns.items() if re.search(regex,text)]


def run(topic: str, model: str, output: Path, *, dry_run: bool = False,
        llm=query_model, root: Path | None = None) -> dict:
    if model not in SAFE_MODELS:
        raise ValueError("Unreviewed model")
    root = root or Path(__file__).resolve().parents[4]
    people = registry(root)
    all_rounds = []
    total_calls = 0
    for r in range(3):
        plan = panel(topic=topic, session=r, size=5, root=root)
        recent = []
        turns = []
        for person in plan["participants"]:
            prompt = compose_prompt(person, topic, recent)
            if dry_run:
                spoken = None
                result = "DRY_RUN_NO_AI_CALL"
                flags = []
            else:
                try:
                    spoken = llm(prompt=prompt, model=model)
                    flags = safety_flags(spoken)
                    result = "REJECTED_SAFETY_CHECK" if flags else "SIMULATION_ONLY_HUMAN_REVIEW_REQUIRED"
                    if not flags:
                        recent.append(spoken)
                    total_calls += 1
                except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError, OSError) as exc:
                    spoken = None
                    flags = ["model_request_failed"]
                    result = "MODEL_CALL_FAILED"
                    # No exception details exposed; provider errors can include private data.
            turns.append({
                "simulated_persona_id": person["id"],
                "fictitious_character_name": person["name"],
                "text": spoken,
                "quality_status": result, "flags": flags,
                "publication_allowed": False
            })
        all_rounds.append({"round":r + 1, "kind":"INTERNAL_FICTIONAL_REHEARSAL",
                           "participants":turns, "publication_allowed":False})
    results={
        "kind":"INTERNAL_FICTIONAL_REHEARSAL",
        "created_at_utc":datetime.now(timezone.utc).isoformat(),
        "model":model, "model_calls_attempted":total_calls,
        "real_model_used": not dry_run,
        "financial_market_values_verified":False,
        "publication_allowed":False,
        "whatsapp_messages_sent":0,
        "role_count":65 + 2,
        "review_status":"HOLD_FOR_HUMAN_REVIEW",
        "topic":topic, "rounds":all_rounds,
        "caveats":["The characters are fictional, never authentic investor testimony.",
                   "Small open models may make grammatical, cultural or factual errors.",
                   "Do not distribute this as real WhatsApp group conversation."]
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as f:
        os.chmod(output, 0o600)
        json.dump(results,f,ensure_ascii=False,indent=2)
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--topic",default="Educaţie financiară: diversificarea şi riscul")
    p.add_argument("--model",default="qwen2.5:1.5b",choices=sorted(SAFE_MODELS))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--dry-run",action="store_true")
    x=p.parse_args()
    result=run(x.topic,x.model,x.output,dry_run=x.dry_run)
    all_turns=[t for r in result["rounds"] for t in r["participants"]]
    good=sum(t["quality_status"]=="SIMULATION_ONLY_HUMAN_REVIEW_REQUIRED" for t in all_turns)
    failed=sum(t["quality_status"]=="MODEL_CALL_FAILED" for t in all_turns)
    print(json.dumps({"mode":"dry_run" if x.dry_run else "actual_local_open_model",
                       "model_calls_attempted":result["model_calls_attempted"],
                       "turns_generated":good,"call_failures":failed,
                       "turns_review_needed":good,
                       "publication_allowed":False,
                       "output":str(x.output)},indent=2))
    if not x.dry_run and (failed or good < 15):
        raise SystemExit("Not all 15 simulated responses were successfully generated; see artifact")


if __name__=="__main__":
    main()
