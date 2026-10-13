"""Regression tests for safe stock-plan edits and stock-level aggregates."""
import unittest
from trading_65 import apply, fresh_state, summary, today

P = {f"{i:02d}": {"character_id": f"{i:02d}",
     "identity_extension": {"姓名": f"角色{i}", "居住城市": "布加勒斯特"},
     "source_profile": {"性别": "男", "年龄": 45, "学员资历": "新男", "工作_职业": "测试"}}
     for i in range(1, 66)}

class PlanEditRegression(unittest.TestCase):
    def setUp(self):
        self.s = fresh_state()
        self.plan = apply(self.s, P, "create_offer", {
            "symbol": "TLV", "name": "测试", "market": "BVB", "currency": "RON",
            "unit_price": 10, "min_shares": 2, "hold_days": 0,
            "participant_count": 3, "discount_pct": 0})

    def test_edit_uncommitted_plan_and_metrics(self):
        edited = apply(self.s, P, "edit_offer", {"offer_id": self.plan["id"],
            "symbol": "SNP", "unit_price": 11.5, "participant_count": 2})
        self.assertEqual(edited["symbol"], "SNP")
        self.assertEqual(edited["unit_price"], 11.5)
        self.assertEqual(summary(self.s, P)["stock_stats"][0],
            {"offer_id": self.plan["id"], "symbol": "SNP",
             "holding_members": 0, "holding_count": 0, "sold_count": 0})

    def test_recommendation_freezes_plan_and_revision(self):
        apply(self.s, P, "recommend", {"offer_id": self.plan["id"], "date": today()})
        rev = self.s["revision"]
        with self.assertRaisesRegex(ValueError, "不可修改"):
            apply(self.s, P, "edit_offer", {"offer_id": self.plan["id"], "unit_price": 100})
        self.assertEqual(self.plan["unit_price"], 10)
        self.assertEqual(self.s["revision"], rev)

    def test_invalid_edit_does_not_partially_change(self):
        before = dict(self.plan)
        with self.assertRaisesRegex(ValueError, "范围"):
            apply(self.s, P, "edit_offer", {"offer_id": self.plan["id"],
                "symbol": "SNP", "min_shares": 0})
        self.assertEqual(self.plan, before)

if __name__ == "__main__":
    unittest.main()
