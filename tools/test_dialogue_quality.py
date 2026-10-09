"""Regression tests: independent conversations, realistic short words, red lines.

All messages are synthetic and explicitly fictional; no market data, account or API.
"""
import unittest
from dialogue_quality import DISCLOSURE, audit_dialogue


def m(mid, text, reply=None, **kw):
    return {"message_id": mid, "character_id": "01", "simulation_only": True,
            "text": DISCLOSURE + text, "reply_to": reply, **kw}


class DialogueQualityTests(unittest.TestCase):
    def test_short_independent_questions_and_member_to_member_replies_pass(self):
        rows = [
            m("m1", "这个量放大了，怎么价格还没动？"),
            m("m2", "我也想问这个。先看看是不是一两只权重股在撑？", "m1"),
            m("m3", "另外，明天有重要公告吗？"),
            m("m4", "我先核一下公司公告，别急着下结论。", "m3"),
        ]
        report = audit_dialogue(rows)
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["metrics"]["independent_turns"], 2)
        self.assertEqual(report["metrics"]["peer_or_prior_replies"], 2)

    def test_late_reply_can_reference_earlier_member_without_immediate_responding(self):
        rows = [
            m("m1", "昨天那篇公告的数字是什么口径？"),
            m("m2", "今天先看看成交情况。"),
            m("m3", "我还没看到原文。"),
            m("m4", "你问的数字我找到了，口径是半年报。", "m1"),
        ]
        self.assertFalse(audit_dialogue(rows)["issues"])

    def test_future_and_bad_reply_references_fail(self):
        self.assertTrue(audit_dialogue([m("m1", "这个数据要核对。", "m2"), m("m2", "好。")])["issues"])
        self.assertTrue(audit_dialogue([m("m1", "先确认。", {"x": 1})])["issues"])
        self.assertTrue(audit_dialogue([m("m1", "先确认。", "m1")])["issues"])

    def test_personal_trading_needs_explicit_hypothetical_label(self):
        self.assertTrue(audit_dialogue([m("m1", "我今天买入了这只股票。")])["issues"])
        self.assertFalse(audit_dialogue([m("m1", "【假设】我今天买入了，这种情况怎么设置止损？")])["issues"])

    def test_guaranteed_returns_blocked_but_warning_about_guarantees_allowed(self):
        self.assertTrue(audit_dialogue([m("m1", "保证收益，稳赚不赔。")])["issues"])
        self.assertFalse(audit_dialogue([m("m1", "别信稳赚不赔的说法，先看风险。")])["issues"])

    def test_disguising_personas_as_real_blocks(self):
        self.assertTrue(audit_dialogue([m("m1", "只是教学演练", simulation_only=False)])["issues"])
        self.assertTrue(audit_dialogue([m("m1", "这是我的经历", experience_kind="real")])["issues"])

    def test_praise_chorus_blocks_but_single_specific_agreement_is_not_banned(self):
        chorus = [m("m1", "教授太厉害了"), m("m2", "老师真厉害")]
        self.assertTrue(any("praise" in x for x in audit_dialogue(chorus)["issues"]))
        self.assertFalse(audit_dialogue([
            m("m1", "教授这个成交量例子挺清楚。"),
            m("m2", "但我还是不知道成交量为什么突然放大。"),
        ])["issues"])

    def test_repetitive_low_value_and_formalism_warnings_not_fake_certainty(self):
        rows = [m("m1", "同意"), m("m2", "同意"), m("m3", "学到了"),
                m("m4", "说得对"), m("m5", "综上所述，我们应该继续深入思考。")]
        report = audit_dialogue(rows)
        self.assertTrue(report["warnings"])
        self.assertTrue(report["human_review_required"])
        self.assertFalse(report["naturalness_verified"])
        self.assertFalse(report["facts_verified"])

    def test_no_fixed_member_or_reply_quota(self):
        self.assertEqual(audit_dialogue([])["issues"], [])
        self.assertEqual(audit_dialogue([m("m1", "先看公告原文。")])["issues"], [])


if __name__ == "__main__":
    unittest.main()
