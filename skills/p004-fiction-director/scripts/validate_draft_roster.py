"""Deterministic structural QA for a NEW fictional 65-person DRAFT roster.

No imports from legacy persona datasets, trading histories or external services.
Does not claim to validate human-like dialogue or Romanian cultural authenticity.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

STORY_ID = "p004-fiction-director-independent"
TYPE_COUNTS = {
    "追随者": 11, "观望者": 12, "反驳者": 9, "提问者": 12,
    "独立研究者": 7, "情绪型": 6, "幽默生活型": 5, "少言型": 3,
}
FIELDS = frozenset({
    "id", "name", "gender", "age", "region", "occupation", "family_motivation",
    "main_behavior", "secondary_behavior", "voice", "interest_triggers",
    "silence_cues", "availability_note", "first_scene_example_zh",
    "first_scene_example_is_history", "initial_relationships",
    "initial_history", "fictional_only", "approved_by_user",
})
VOICE_FIELDS = frozenset({
    "sentence_length", "register", "catchphrases", "emoji_style", "coarse_language_style",
})


def validate_draft(data: dict) -> dict:
    """Raises ValueError on structural problems and unauthorized approval."""
    if not isinstance(data, dict) or data.get("story_id") != STORY_ID:
        raise ValueError("not the independent P004 fictional story")
    if data.get("status") != "DRAFT_NOT_APPROVED" or data.get("fictional_educational_story") is not True:
        raise ValueError("draft-only and fictional labels are mandatory")
    people = data.get("people")
    if not isinstance(people, list) or len(people) != 65:
        raise ValueError("roster must contain exactly 65 draft people")
    if data.get("type_counts") != TYPE_COUNTS:
        raise ValueError("the explicit proposed group count is inconsistent")
    ids, names, phrases, samples, vocal = [], [], [], [], []
    groups = Counter()
    for n, p in enumerate(people, 1):
        if not isinstance(p, dict) or set(p) != FIELDS:
            raise ValueError(f"person {n} has missing or unexpected fields")
        cid = f"{n:02d}"
        if p["id"] != cid:
            raise ValueError(f"person {n} has nonsequential/invalid ID")
        ids.append(cid)
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
        if not isinstance(voice, dict) or set(voice) != VOICE_FIELDS:
            raise ValueError(f"person {cid} invalid voice DNA")
        for key in ("register", "sentence_length", "emoji_style", "coarse_language_style"):
            if not isinstance(voice[key], str) or not voice[key]:
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
        if p["approved_by_user"] is not False or p["fictional_only"] is not True:
            raise ValueError(f"person {cid} is marked approved or real")
        if p["first_scene_example_is_history"] is not False:
            raise ValueError(f"person {cid} claims example is real history")
        if p["initial_history"] != [] or p["initial_relationships"] != []:
            raise ValueError(f"person {cid} has fabricated pre-story history")
        names.append(p["name"].strip().casefold())
        phrases.append(voice["catchphrases"][0].strip().casefold())
        samples.append(p["first_scene_example_zh"].strip())
        vocal.append(voice["register"])
    if groups != Counter(TYPE_COUNTS):
        raise ValueError(f"behavior distribution changed: {dict(groups)}")
    for title, values in (("names", names), ("catchphrases", phrases),
                          ("sample lines", samples), ("voice registers", vocal)):
        if len(set(values)) != 65:
            raise ValueError(f"duplicate {title}")
    return {"status": "STRUCTURE_VALID_DRAFT_ONLY", "people": 65,
            "group_counts": dict(groups),
            "genders": dict(Counter(p["gender"] for p in people)),
            "distinct_regions": len({p["region"] for p in people}),
            "distinct_occupations": len({p["occupation"] for p in people}),
            "distinct_voice_signatures": len(set(vocal)),
            "approved_people": 0, "prior_story_events": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate new 65-person draft roster")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    report = validate_draft(json.loads(args.file.read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2, ensure_ascii=False))
