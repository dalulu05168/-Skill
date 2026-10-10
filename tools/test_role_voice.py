"""P004 voice-level regression tests: ordinary 65 members vs expert hosts.

No model call and no claims about real investor conversations or market prices.
"""
import unittest

from role_voice import (audit_member_register, member_voice_briefs,
                        role_voice_contract)
from chennan_writing import empty_state, load_profiles, make_prompt, validate_messages


def member(cid, text):
    return {"character_id": cid, "text": "【虚构教学模拟】" + text}


class RoleVoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load_profiles()

    def test_three_distinct_host_and_member_registers(self):
        contract = role_voice_contract()
        self.assertEqual(set(contract), {"member", "assistant", "professor"})
        self.assertEqual(contract["member"]["register"], "everyday_conversational")
        self.assertEqual(contract["assistant"]["register"], "professional_accessible")
        self.assertEqual(contract["professor"]["register"], "expert_academic")
        self.assertIn("19:30", contract["professor"]["schedule"])

    def test_all_65_briefs_are_grounded_in_unique_profiles(self):
        ids = sorted(self.profiles)
        self.assertEqual(len(ids), 65)
        briefs = member_voice_briefs(self.profiles, ids)
        self.assertEqual([a["character_id"] for a in briefs], ids)
        self.assertEqual(len({a["name"] for a in briefs}), 65)
        self.assertEqual(briefs[0]["name"], "Andrei Popescu")
        self.assertEqual(briefs[1]["name"], "Elena Ionescu")
        self.assertNotEqual(briefs[0]["occupation"], briefs[1]["occupation"])
        self.assertTrue(all(b["native_language"] for b in briefs))
        self.assertTrue(all(b["register"].startswith("自然") for b in briefs))
        with self.assertRaises(ValueError):
            member_voice_briefs(self.profiles, ["70"])

    def test_ordinary_member_question_is_not_banned_for_finance_words(self):
        r = audit_member_register([
            member("01", "成交量我大概懂了，不过银行利率到底会影响哪一块？"),
            member("02", "我更关心成本，先看看有没有原文。")
        ], self.profiles)
        self.assertEqual(r["issues"], [])
        self.assertEqual(r["warnings"], [])

    def test_member_research_note_gets_warning_not_fake_verified(self):
        r = audit_member_register([
            member("02", "综上所述，我们应该基于上述分析全面审视该行业结构性机会。")
        ], self.profiles)
        self.assertEqual(r["issues"], [])
        self.assertTrue(any("professional market report" in w for w in r["warnings"]))
        self.assertFalse(r["member_voice_verified"])
        self.assertFalse(r["semantic_register_verified"])

    def test_unsupported_adviser_claim_gets_blocked(self):
        r = audit_member_register([
            member("01", "我们建议投资者买入这一股票。"),
            member("02", "大家必须跟上我说的。")
        ], self.profiles)
        self.assertTrue(any("professional investment adviser" in x for x in r["issues"]))
        self.assertTrue(any("pressures others" in x for x in r["issues"]))

    def test_claiming_professional_finance_credential_requires_review(self):
        r = audit_member_register([
            member("03", "我作为一名持牌投资顾问可以确认这个结论。")
        ], self.profiles)
        self.assertTrue(any("claims financial credentials" in w for w in r["warnings"]))

    def test_identical_long_words_across_distinct_members_warning(self):
        shared = "我现在真的没想明白银行贷款利率到底是什么意思。"
        a = audit_member_register([member("01", shared), member("02", shared)], self.profiles)
        self.assertTrue(any("copy-like wording" in x for x in a["warnings"]))
        b = audit_member_register([member("01", shared), member("01", shared)], self.profiles)
        self.assertFalse(any("copy-like wording" in x for x in b["warnings"]))

    def test_professor_and_assistant_are_not_forced_to_use_member_register(self):
        r = audit_member_register([
            {"speaker": "助理", "text": "从宏观层面来看，我们需要先对照央行原文。"},
            {"speaker": "教授", "text": "我们首先定义净息差，再分析传导路径和条件。"}
        ], self.profiles)
        self.assertEqual(r["issues"], [])
        self.assertEqual(r["warnings"], [])

    def test_workflow_prompt_and_adoption_gate_are_wired(self):
        request = {"date": "2026-10-10", "node": "RO-08",
                   "source_kind": "assistant", "source_text": "先讨论已知的银行融资条件。",
                   "selected_ids": ["01", "02"], "topic": "银行融资成本"}
        prompt, state = make_prompt(request, self.profiles, empty_state())
        self.assertEqual(len(prompt["selected_personal_voice_briefs"]), 2)
        self.assertEqual(prompt["role_voice_contract"]["professor"]["register"], "expert_academic")
        self.assertTrue(any("普通成员" in x for x in prompt["instructions"]))
        draft = state["drafts"][prompt["draft_id"]]
        profile = self.profiles["01"]
        identity = {"character_id": "01",
                    "name": profile["identity_extension"]["姓名"],
                    "gender": profile["source_profile"]["性别"],
                    "role": profile["source_profile"]["学员资历"]}
        bad = validate_messages({"messages": [{**identity,
                           "text": "我们建议投资者买入该股票。"}]}, draft, self.profiles, [])
        self.assertFalse(bad["valid"])
        self.assertTrue(bad["role_voice_quality"]["issues"])
        good = validate_messages({"messages": [{**identity,
                           "text": "我想先弄清楚银行的成本会不会变。"}]}, draft, self.profiles, [])
        self.assertTrue(good["valid"], good["errors"])
        self.assertEqual(good["role_voice_quality"]["issues"], [])


if __name__ == "__main__":
    unittest.main()
