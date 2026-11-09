"""Offline end-to-end handoff test: director -> JSON task -> gate -> corrections.

All actors fictional, output is NOT AI-generated. No external API or trading.
"""
import copy
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import director_workflow as wf
import scene_memory as mem

ROSTER = json.loads((ROOT/"characters"/"drafts"/"roster-v2.json").read_text(encoding="utf-8"))


def request(**updates):
    obj = {"simulation_only": True, "source_status": "HYPOTHETICAL",
           "scene_id": "sample-monday", "story_date": "2026-10-12",
           "daypart": "morning", "topic_keywords": ["能源", "交通"],
           "max_members": 8}
    obj.update(updates)
    return obj


def output(prepared, *, evening=False):
    t = prepared["task"]
    chosen = t["cast"]
    assert chosen
    msgs = [
        {"message_id": "m01", "speaker_id": "assistant",
         "text": "Bună dimineața! Discutăm un exemplu imaginar, nu știrile de azi."},
        {"message_id": "m02", "speaker_id": chosen[0]["speaker_id"],
         "reply_to": "m01", "text": "Și ce costuri trebuie să verificăm?"},
        {"message_id": "m03", "speaker_id": chosen[-1]["speaker_id"],
         "reply_to": "m02", "text": "Nu cred că e atât de simplu."},
    ]
    if evening:
        msgs.append({"message_id": "m04", "speaker_id": "professor",
                     "reply_to": "m02", "text": "Să privim întâi costurile și riscul. Exersați mâine, pentru decizii mai clare în familie. Noapte bună!"})
    return {"story_id": wf.STORY, "scene_id": t["scene_id"],
            "story_date": t["story_date"], "daypart": t["daypart"],
            "lesson_type": t["lesson_type"],
            "simulation_only": True, "fictional_case_only": True,
            "status": "DRAFT_NOT_ADOPTED", "approved_by_user": False,
            "publishable": False, "messages": msgs}


class DirectorWorkflowTests(unittest.TestCase):
    def test_full_handoff_and_manual_editorial_boundary(self):
        p = wf.prepare(ROSTER, request())
        self.assertEqual("AWAITING_SCREENWRITER_JSON", p["stage"])
        self.assertEqual(False, p["model_invoked"])
        self.assertEqual(False, p["can_publish"])
        self.assertIn("approved_history", p["llm_prompt"])
        self.assertEqual([], p["task"]["approved_history"])
        self.assertEqual([], p["task"]["known_trade_events"])
        r = wf.review(p, output(p))
        self.assertEqual("EDITORIAL_REVIEW_REQUIRED", r["status"])
        self.assertFalse(r["approved_for_publication"])
        self.assertFalse(r["memory_written"])
        self.assertFalse(r["fact_check_completed"])

    def test_wrong_person_blocks_and_returns_specific_rewrite(self):
        p = wf.prepare(ROSTER, request())
        m = output(p)
        m["messages"][1]["speaker_id"] = "65" if "65" not in [x["speaker_id"] for x in p["task"]["cast"]] else "99"
        result = wf.review(p, m)
        self.assertEqual("BLOCKED_REWRITE_REQUIRED", result["status"])
        self.assertIn("unauthorized speaker", result["rewrite_instruction"])

    def test_wrong_weekly_professor_and_daytime_gate(self):
        p = wf.prepare(ROSTER, request())
        m = output(p)
        m["messages"].append({"message_id": "m04", "speaker_id": "professor", "text": "Așadar..."})
        self.assertEqual("BLOCKED_REWRITE_REQUIRED", wf.review(p, m)["status"])
        p2 = wf.prepare(ROSTER, request(scene_id="monday-evening", daypart="evening"))
        self.assertEqual("technical", p2["task"]["lesson_type"])
        self.assertEqual("EDITORIAL_REVIEW_REQUIRED", wf.review(p2, output(p2,evening=True))["status"])
        m2 = output(p2, evening=True)
        m2["lesson_type"] = "philosophy"
        self.assertEqual("BLOCKED_REWRITE_REQUIRED", wf.review(p2,m2)["status"])

    def test_causal_reference_and_unknown_backstory_rejected(self):
        p=wf.prepare(ROSTER, request())
        m=output(p)
        m["messages"][1]["reply_to"]="m999"
        self.assertIn("reply_to", wf.review(p,m)["rewrite_instruction"])
        m=output(p)
        m["messages"][2]["history_reference"]={"scene_id":"yesterday","message_id":"aa","speaker_id":"01"}
        self.assertIn("history_reference", wf.review(p,m)["rewrite_instruction"])

    def test_fake_trade_and_guarantee_blocked(self):
        p=wf.prepare(ROSTER, request())
        m=output(p)
        m["messages"][1]["trade_reference"]={"transaction_id":"fake"}
        m["messages"][1]["text"]="Câștig garantat, azi cu siguranță!"
        result=wf.review(p,m)
        self.assertEqual("BLOCKED_REWRITE_REQUIRED",result["status"])
        self.assertTrue(any("trade reference" in x for x in result["blocking_issues"]))
        self.assertTrue(any("guaranteed-return" in x for x in result["blocking_issues"]))

    def test_unverified_news_or_real_trading_cannot_enter_pipeline(self):
        with self.assertRaisesRegex(ValueError,"hypothetical"):
            wf.prepare(ROSTER,request(source_status="UNVERIFIED"))
        with self.assertRaisesRegex(ValueError,"publishing and trading"):
            wf.prepare(ROSTER,request(real_trading=True))
        with self.assertRaisesRegex(ValueError,"publishing and trading"):
            wf.prepare(ROSTER,request(automatic_publish=True))

    def test_director_instruction_limited_but_preserved(self):
        p=wf.prepare(ROSTER,request(director_override="临时插播：能源与家庭账单；未交付内容先调整顺序"))
        self.assertIn("临时插播",p["llm_prompt"])
        self.assertIn("临时插播",p["task"]["director_override"])
        with self.assertRaisesRegex(ValueError,"director_override"):
            wf.prepare(ROSTER,request(director_override="a"*1001))

    def test_cannot_adopt_from_unapproved_personas(self):
        p=wf.prepare(ROSTER,request())
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            official=root/"roster.json"
            official.write_text(json.dumps({"story_id":wf.STORY,"characters":[]}),encoding="utf-8")
            mem.initialize(root/"history.sqlite3")
            self.assertEqual([],mem.person_history(root/"history.sqlite3",official,"assistant"))
            self.assertFalse(wf.review(p,output(p))["memory_written"])
            self.assertEqual([],mem.person_history(root/"history.sqlite3",official,"assistant"))

    def test_65_persona_stress_all_profiles_have_selectable_themes(self):
        # Select across all 65 unique interest themes, not falsely claim 65
        # actors actually talked in one scene or that a model was invoked.
        included=set()
        roster_ids={x["id"] for x in ROSTER["people"]}
        for index,c in enumerate(ROSTER["people"]):
            p=wf.prepare(ROSTER,request(scene_id=f"stress{index:02d}",
                 topic_keywords=[c["interest_triggers"][0]],max_members=15))
            included.update(x["speaker_id"] for x in p["task"]["cast"])
            self.assertTrue(p["task"]["cast"])
            self.assertFalse(p["can_adopt_memory"])
        self.assertEqual(roster_ids,included)

    def test_draft_cannot_claim_approval_or_other_story(self):
        p=wf.prepare(ROSTER,request())
        m=output(p)
        m["approved_by_user"]=True
        self.assertEqual("BLOCKED_REWRITE_REQUIRED", wf.review(p,m)["status"])
        m=output(p)
        m["story_id"]="old-story"
        self.assertEqual("BLOCKED_REWRITE_REQUIRED", wf.review(p,m)["status"])


if __name__ == "__main__":
    unittest.main()
