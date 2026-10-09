"""Offline tests for REAL-call adapter boundaries. No external model is contacted."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import finance_skill_generate as gen

FRIDAY = datetime(2026, 10, 9, 11, 15, tzinfo=timezone.utc)
SATURDAY = datetime(2026, 10, 10, 11, 15, tzinfo=timezone.utc)


def stub_model(path, *, payload):
    if path != "/api/generate" or payload.get("stream") is not False:
        raise AssertionError("Wrong local model call")
    assert payload["model"] in gen.ALLOWED_MODELS
    return {"response": "首先讨论风险控制，然后根据证据判断情景是否发生。"}


class LocalModelGenerationTests(unittest.TestCase):
    def test_real_model_adapter_is_injectable_but_always_internal(self):
        result = gen.generate_draft(topic="如何理解成交量和交易风险？",
                                    node="RO-08", role="assistant",
                                    clock=FRIDAY, query=stub_model)
        self.assertEqual(result["status"], "HOLD_FOR_HUMAN_REVIEW")
        self.assertTrue(result["model_request_completed"])
        self.assertFalse(result["publication_allowed"])
        self.assertFalse(result["news_and_market_facts_verified"])
        self.assertEqual(result["messages_sent"], 0)
        self.assertIsNone(result["persona"])

    def test_member_v41_identity_loaded_and_checked(self):
        result = gen.generate_draft(topic="如何更谨慎地理解风险？",
                                    role="member", person_id="07", node="RO-08",
                                    clock=FRIDAY, query=stub_model)
        self.assertEqual(result["persona_id"], "07")
        self.assertEqual(result["persona"]["gender"], "女")
        self.assertEqual(result["status"], "HOLD_FOR_HUMAN_REVIEW")
        with self.assertRaises(ValueError):
            gen.generate_draft(topic="如何更谨慎地理解风险？",
                               role="member", person_id="70", node="RO-08",
                               clock=FRIDAY, query=stub_model)

    def test_professor_enforces_present_schedule_and_weekday(self):
        result = gen.generate_draft(topic="怎样建立纪律与复盘机制？",
                                    role="professor", node="RO-10",
                                    clock=FRIDAY, query=stub_model)
        self.assertEqual(result["slot_id"], "RO-10")
        with self.assertRaises(ValueError):
            gen.generate_draft(topic="怎样建立纪律与复盘机制？",
                               role="professor", node="RO-08",
                               clock=FRIDAY, query=stub_model)
        with self.assertRaises(ValueError):
            gen.generate_draft(topic="怎样建立纪律与复盘机制？",
                               role="professor", node="RO-10",
                               clock=SATURDAY, query=stub_model)

    def test_model_hallucinated_numbers_or_guarantees_are_rejected(self):
        responses = ["BET今天涨了100点", "这是稳赚机会", "Buy now!",
                     "https://example.com is my evidence"]
        for text in responses:
            with self.subTest(text=text):
                response = gen.generate_draft(
                    topic="如何辨认不确定性与交易风险？",
                    clock=FRIDAY, node="RO-08",
                    query=lambda path, *, payload: {"response": text})
                self.assertEqual(response["status"], "REJECTED_MODEL_OUTPUT")
                self.assertIsNone(response["text"])
                self.assertTrue(response["flags"])
                self.assertFalse(response["publication_allowed"])

    def test_no_unsupported_provider_host_models_or_unsafe_topic(self):
        with self.assertRaises(ValueError):
            gen.generate_draft(topic="关于投资纪律的课堂讨论",
                               model="arbitrary_remote_model", clock=FRIDAY)
        with self.assertRaises(ValueError):
            gen.generate_draft(topic="a", clock=FRIDAY)
        with self.assertRaises(ValueError):
            gen.generate_draft(topic="关于投资纪律的课堂讨论", role="real_investor", clock=FRIDAY)
        with self.assertRaises(ValueError):
            gen.generate_draft(topic="关于投资纪律的课堂讨论",
                               role="assistant", person_id="01", clock=FRIDAY)
        with self.assertRaises(ValueError):
            gen._model_response("/some/external/path")

    def test_actual_readiness_checks_no_false_success(self):
        with patch.object(gen, "_model_response",
                          return_value={"models": [{"name": "qwen2.5:1.5b"}]}):
            status = gen.model_status()
        self.assertTrue(status["connected"])
        self.assertTrue(status["can_generate"])
        with patch.object(gen, "_model_response", side_effect=RuntimeError("offline")):
            offline = gen.model_status()
        self.assertFalse(offline["can_generate"])
        self.assertFalse(offline["connected"])


if __name__ == "__main__":
    unittest.main()
