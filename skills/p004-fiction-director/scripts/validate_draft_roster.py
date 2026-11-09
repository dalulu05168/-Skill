"""Structural validator for new P004 fictional 65-character draft rosters.

Python stdlib only; never reads legacy personas, trading ledgers or external data.
Pass means only structural consistency, never naturalness or editorial approval.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

STORY_ID = "p004-fiction-director-independent"
TYPE_COUNTS = {
    "追随者": 11, "观望者": 12, "反驳者": 9, "提问者": 12,
    "独立研究者": 7, "情绪型": 6, "幽默生活型": 5, "少言型": 3,
}
BASE_FIELDS = frozenset({
    "id", "name", "gender", "age", "region", "occupation", "family_motivation",
    "main_behavior", "secondary_behavior", "voice", "interest_triggers",
    "silence_cues", "availability_note", "first_scene_example_zh",
    "first_scene_example_is_history", "initial_relationships",
    "initial_history", "fictional_only", "approved_by_user",
})
V2_FIELDS = BASE_FIELDS | {"turn_taking", "memory_policy"}
BASE_VOICE_FIELDS = frozenset({
    "sentence_length", "register", "catchphrases", "emoji_style", "coarse_language_style",
})
V2_VOICE_FIELDS = BASE_VOICE_FIELDS | {"romanian_audition_line", "romanian_audition_is_history"}


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip().casefold()


def validate_draft(data: dict) -> dict:
    """Raise ValueError for incorrect identifiers, approval, or history."""
    if not isinstance(data, dict) or data.get("story_id") != STORY_ID:
        raise ValueError("not the independent P004 fictional story")
    if data.get("status") != "DRAFT_NOT_APPROVED" or data.get("fictional_educational_story") is not True:
        raise ValueError("draft-only and fictional labels are mandatory")
    version = data.get("version")
    if version not in {"draft-v1", "draft-v2"}:
        raise ValueError("unsupported draft version")
    v2 = version == "draft-v2"
    people = data.get("people")
    if not isinstance(people, list) or len(people) != 65:
        raise ValueError("roster must contain exactly 65 draft people")
    if data.get("type_counts") != TYPE_COUNTS:
        raise ValueError("the explicit proposed group count is inconsistent")

    names, phrases, samples, vocal, ro_samples, warnings = [], [], [], [], [], []
    groups = Counter()
    for n, p in enumerate(people, 1):
        cid = f"{n:02d}"
        if not isinstance(p, dict) or set(p) != (V2_FIELDS if v2 else BASE_FIELDS):
            raise ValueError(f"person {cid} has missing or unexpected fields")
        if p["id"] != cid:
            raise ValueError(f"person {cid} has nonsequential/invalid ID")
        for key in ("name", "region", "occupation", "family_motivation",
                    "availability_note", "first_scene_example_zh"):
            if not isinstance(p[key], str) or not p[key].strip():
                raise ValueError(f"person {cid} missing {key}")
        if p["gender"] not in ("女", "男") or type(p["age"]) is not int or not 40 <= p["age"] <= 68:
            raise ValueError(f"person {cid} invalid age/gender (provisional design)")
        if p["main_behavior"] not in TYPE_COUNTS or p["secondary_behavior"] not in TYPE_COUNTS:
            raise ValueError(f"person {cid} invalid behavior")
        if p["main_behavior"] == p["secondary_behavior"]:
            raise ValueError(f"person {cid} must have two distinct tendencies")
        groups[p["main_behavior"]] += 1
        voice = p["voice"]
        if not isinstance(voice, dict) or set(voice) != (V2_VOICE_FIELDS if v2 else BASE_VOICE_FIELDS):
            raise ValueError(f"person {cid} invalid voice DNA")
        for key in ("register", "sentence_length", "emoji_style", "coarse_language_style"):
            if not isinstance(voice[key], str) or not voice[key].strip():
                raise ValueError(f"person {cid} missing voice {key}")
        if not isinstance(voice["catchphrases"], list) or not voice["catchphrases"] or not all(
            isinstance(x, str) and x.strip() for x in voice["catchphrases"]
        ):
            raise ValueError(f"person {cid} missing verbal tic")
        for key in ("interest_triggers", "silence_cues"):
            if not isinstance(p[key], list) or not p[key] or not all(
                isinstance(x, str) and x.strip() for x in p[key]
            ):
                raise ValueError(f"person {cid} missing {key}")
        if v2 and "退休" in p["occupation"] and re.search(r"忙于退休.+?职责", " ".join(p["silence_cues"])):
            raise ValueError(f"person {cid} erroneously assigned a retired person's old work duties")
        if p["approved_by_user"] is not False or p["fictional_only"] is not True:
            raise ValueError(f"person {cid} is marked approved or real")
        if p["first_scene_example_is_history"] is not False:
            raise ValueError(f"person {cid} claims example is real history")
        if p["initial_history"] != [] or p["initial_relationships"] != []:
            raise ValueError(f"person {cid} has fabricated pre-story history")
        if any(k in p for k in ("real_profit", "confirmed_returns", "executed_trades", "transactions")):
            raise ValueError(f"person {cid} has invented trade data")
        if v2:
            for key in ("starts_when", "pacing", "confronted"):
                if not isinstance(p["turn_taking"], dict) or not isinstance(p["turn_taking"].get(key), str) or not p["turn_taking"][key].strip():
                    raise ValueError(f"person {cid} missing turn_taking.{key}")
            if p["turn_taking"].get("may_decline_to_speak") is not True:
                raise ValueError(f"person {cid} forced to speak")
            if not isinstance(p["memory_policy"], str) or not p["memory_policy"].strip():
                raise ValueError(f"person {cid} missing memory_policy")
            line = voice["romanian_audition_line"]
            if not isinstance(line, str) or not line.strip() or voice["romanian_audition_is_history"] is not False:
                raise ValueError(f"person {cid} invalid Romanian audition")
            ro_samples.append(_norm(line))
        names.append(_norm(p["name"]))
        phrases.append(_norm(voice["catchphrases"][0]))
        samples.append(_norm(p["first_scene_example_zh"]))
        vocal.append(_norm(voice["register"]))
    if groups != Counter(TYPE_COUNTS):
        raise ValueError(f"behavior distribution changed: {dict(groups)}")
    for title, values in (("names", names), ("catchphrases", phrases),
                          ("sample lines", samples), ("voice registers", vocal),
                          ("Romanian auditions", ro_samples)):
        if len(set(values)) != len(values):
            raise ValueError(f"duplicate {title}")
    if v2:
        # High lexical similarity is merely a review hint, not proof of same voice.
        for a in range(len(ro_samples)):
            for b in range(a + 1, len(ro_samples)):
                if difflib.SequenceMatcher(None, ro_samples[a], ro_samples[b]).ratio() > 0.84:
                    warnings.append(f"possibly similar Romanian auditions: {a+1:02d}/{b+1:02d}")
    return {
        "status": "STRUCTURE_VALID_DRAFT_ONLY",
        "version":version, "people":65, "group_counts":dict(groups),
        "genders":dict(Counter(p["gender"] for p in people)),
        "distinct_regions":len({p["region"] for p in people}),
        "distinct_occupations":len({p["occupation"] for p in people}),
        "distinct_voice_signatures":len(set(vocal)),
        "distinct_romanian_auditions":len(set(ro_samples)),
        "review_warnings":warnings,
        "approved_people":0,"prior_story_events":0,
        "human_language_and_literary_review_required":True
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate isolated 65-person fictional roster draft")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    report = validate_draft(json.loads(args.file.read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2, ensure_ascii=False))
