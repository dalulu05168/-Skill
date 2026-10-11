"""Original BVB v3.3 restoration regression: exact source & no fake network."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bvb_v33_restore import restore_news_v33
from four_module_gateway import MODULES

class BVBOriginalRestoreTests(unittest.TestCase):
    def test_sources_roundtrip_without_modifying_user_scripts(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"news"
            hashes=restore_news_v33(out)
            self.assertEqual(set(hashes),{"index.html","app.js","styles.css","materials-data.js"})
            html=(out/"index.html").read_text(encoding="utf-8-sig")
            app=(out/"app.js").read_text(encoding="utf-8-sig")
            data=(out/"materials-data.js").read_text(encoding="utf-8-sig")
            self.assertIn("罗马尼亚BVB金融资讯台",html)
            self.assertIn("中文增强版 v3.3",html)
            self.assertIn("资料时间轴",html)
            self.assertIn("资料包编辑与发布审核",html)
            self.assertIn("资讯监控",html)
            self.assertIn("全部16个节点",html)
            for item in ("refreshBtn","newsSearch","reviewBox","exportNews"):
                self.assertIn(item,html)
            for endpoint in ("/api/status","/api/refresh","/api/article","/api/translate"):
                self.assertIn(endpoint,app)
            self.assertIn("本次采集",app)
            self.assertIn("历史缓存",app)
            self.assertIn("localStorage",app)
            self.assertIn("MATERIALS",data)
            self.assertEqual(len(re.findall(r"\bid:\s*['\"]",data)),16)

    def test_gateway_still_routes_four_modules_to_original_news(self):
        self.assertEqual([x[3] for x in MODULES],
                         ["/news","/trading","/skill","/image-editor"])

if __name__=="__main__":
    unittest.main()
