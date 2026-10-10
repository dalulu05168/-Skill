"""Storycraft pressure tests for P004. No live markets, invented credentials or posting."""
import unittest

from storycraft_contract import DISCLOSURE, audit_storycraft
from chennan_writing import load_profiles, validate_messages


def say(mid, body, **metadata):
    return {"character_id": "01", "message_id": mid,
            "text": DISCLOSURE + body, "simulation_only": True, **metadata}


def approved_session(*, status="adopted", day="2026-10-09", cid="01"):
    return {"id": "scene-1", "date": day, "status": status,
            "messages": [{"message_id": "m-old", "character_id": cid,
                          "text": DISCLOSURE + "先核对公告原文再讨论银行融资成本。"}]}


DRAFT = {"id": "draft-1", "date": "2026-10-10",
         "topic": "银行融资成本", "selected_ids": ["01"]}


class StorycraftAuditTests(unittest.TestCase):
    def test_generic_question_has_no_unsupported_history(self):
        result = audit_storycraft([say("a", "银行融资成本怎么计算？")],
                                  draft=DRAFT, sessions=[])
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertFalse(result["facts_verified"])
        self.assertFalse(result["naturalness_verified"])
        self.assertFalse(result["publication_allowed"])

    def test_history_with_precise_approved_citation(self):
        ref = {"session_id": "scene-1", "message_id": "m-old"}
        result = audit_storycraft([say("a", "你上次说过要核对公告，这次银行融资成本的新证据我想先问清楚。",
                                         historical_claim=True, continuity_ref=ref)],
                                  draft=DRAFT, sessions=[approved_session()])
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["metrics"]["history_citations_verified"], 1)
        self.assertEqual(result["warnings"], [])

    def test_missing_or_unapproved_memory_blocks_explicit_history(self):
        with self.subTest("missing"):
            r = audit_storycraft([say("a", "你上次说过银行融资成本有变化。",
                                      historical_claim=True)], draft=DRAFT)
            self.assertTrue(r["issues"])
        ref = {"session_id": "scene-1", "message_id": "m-old"}
        for scene in [approved_session(status="draft"),
                      approved_session(day="2026-10-11"),
                      approved_session(cid="02")]:
            with self.subTest(scene=scene):
                r = audit_storycraft([say("a", "银行融资成本的上次说法，今天可以再核对。",
                                          historical_claim=True, continuity_ref=ref)],
                                     draft=DRAFT, sessions=[scene])
                self.assertEqual(r["status"], "BLOCKED")
        for ref in [{"session_id": "scene-1", "message_id": "wrong"},
                    {"session_id": "", "message_id": "m-old"}, "scene-1"]:
            with self.subTest(ref=ref):
                self.assertEqual(audit_storycraft(
                    [say("a", "这个问题继续讨论。", continuity_ref=ref)],
                    draft=DRAFT, sessions=[approved_session()])["status"], "BLOCKED")

    def test_history_sounding_sentence_without_citation_is_warning(self):
        r = audit_storycraft([say("a", "你昨天说过银行融资成本会下降，是有什么新数据吗？")],
                             draft=DRAFT, sessions=[])
        self.assertEqual(r["issues"], [])
        self.assertGreater(r["metrics"]["history_claims_without_citations"], 0)
        self.assertTrue(any("previous-dialogue" in w for w in r["warnings"]))

    def test_meta_role_language_warns_without_inventing_authority(self):
        r = audit_storycraft([say("a", "我是一名虚拟投资者，按照剧本安排开始提问。")],
                             draft=DRAFT)
        self.assertTrue(any("production notes" in w for w in r["warnings"]))

    def test_empathy_pressure_and_attack_are_different_severities(self):
        warm = audit_storycraft([say("a", "你担心银行融资成本影响预算吧？我们先查数据。")],
                                draft=DRAFT)
        self.assertEqual(warm["issues"], [])
        dismissive = audit_storycraft([say("a", "你想太多了，银行融资成本没什么要考虑。")],
                                     draft=DRAFT)
        self.assertEqual(dismissive["issues"], [])
        self.assertTrue(any("dismissive" in x for x in dismissive["warnings"]))
        for body in ("不买就后悔，必须今天买入。", "你这种蠢货就不配发言。"):
            with self.subTest(body=body):
                r = audit_storycraft([say("a", body)], draft=DRAFT)
                self.assertEqual(r["status"], "BLOCKED")

    def test_possible_off_topic_and_repeated_opening_are_advisory_only(self):
        rows = [say("a", "周末我准备去书店挑几本小说，顺便看看新的电影排期表。"),
                say("b", "周末我准备去公园散散步，顺便看看那里的摄影展览。"),
                say("c", "周末我准备去山里爬爬山，顺便看看那里的湖泊。")]
        r = audit_storycraft(rows, draft=DRAFT)
        self.assertEqual(r["issues"], [])
        self.assertTrue(any("topic drift" in x for x in r["warnings"]))
        self.assertTrue(any("same opening" in x for x in r["warnings"]))

    def test_writer_flow_integration_rejects_fabricated_citation(self):
        profiles = load_profiles()
        p = profiles["01"]
        base = {"character_id": "01",
                "name": p["identity_extension"]["姓名"],
                "gender": p["source_profile"]["性别"],
                "role": p["source_profile"]["学员资历"],
                "text": "我还想确认一下银行融资成本。",
                "historical_claim": True,
                "continuity_ref": {"session_id": "scene-missing", "message_id": "m1"}}
        bad = validate_messages({"messages": [base]}, DRAFT, profiles, [])
        self.assertFalse(bad["valid"])
        self.assertIn("storycraft_quality", bad)
        base["text"] = "银行融资成本的例子我想再确认一下。"
        base["historical_claim"] = False
        base["continuity_ref"] = None
        good = validate_messages({"messages": [base]}, DRAFT, profiles, [])
        self.assertTrue(good["valid"], good["errors"])


if __name__ == "__main__":
    unittest.main()
