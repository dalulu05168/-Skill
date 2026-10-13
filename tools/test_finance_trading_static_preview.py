"""Static trading preview must clearly identify its offline API while rendering real roster summaries."""
import unittest
import build_finance_ui_preview as p

class TradingPreviewTests(unittest.TestCase):
    def test_renders_all_65_without_fabricated_trades(self):
        from trading_center_ui import PAGE
        people=[{"character_id":f"{i:02d}","name":f"Person{i}","occupation":"Sample","city":"Bucharest","role":"Student"} for i in range(1,66)]
        out=p._compose_trading_preview(PAGE,people)
        self.assertIn("正式人物档案摘要",out)
        self.assertIn("静态只读预览",out)
        self.assertIn("Person65",out)
        self.assertNotIn("交易数据尚未载入。",out)
        self.assertNotIn("正在载入成员…",out)
        self.assertNotIn("加载中…",out)

    def test_missing_member_blocks_preview(self):
        from trading_center_ui import PAGE
        with self.assertRaisesRegex(RuntimeError,"65"):
            p._compose_trading_preview(PAGE,[])

if __name__=="__main__":
    unittest.main()
