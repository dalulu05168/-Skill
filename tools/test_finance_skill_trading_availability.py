"""API/preview separation and actionable failure feedback regression gates."""
import unittest

from trading_65_ui import SECTION, SCRIPT
from trading_center_ui import PAGE
import build_finance_ui_preview as preview

class TradingUiAvailabilityContract(unittest.TestCase):
    def test_hosted_page_reports_backend_failure_not_false_success(self):
        self.assertIn('role="status"', SECTION)
        self.assertIn('aria-live="polite"', SECTION)
        self.assertIn('function failedLoad(error)', SCRIPT)
        self.assertIn("failedLoad(e)", SCRIPT)
        self.assertIn('load().catch(failedLoad)', SCRIPT)
        self.assertIn("next.people.length!==65", SCRIPT)
        self.assertIn('交易数据正在从受保护服务读取', SECTION)

    def test_static_preview_disables_submissions_but_has_65_summaries(self):
        people=[{"character_id":f"{i:02d}","name":f"Person{i}",
                 "occupation":"Test","city":"Bucharest","role":"Student"}
                for i in range(1,66)]
        trading=preview._compose_trading_preview(PAGE,people)
        self.assertIn('Person65', trading)
        self.assertIn('交易账本、资金、持仓与保存 API 均未连接', trading)
        self.assertNotIn('交易数据尚未载入。', trading)
        self.assertNotIn('正在载入成员…', trading)
        self.assertIn('id="sim-people-table"', trading)

if __name__=='__main__':
    unittest.main()
