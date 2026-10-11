"""Customer-path contract for the four-module landing page and retained routes."""
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import finance_skill_api as api
from four_module_gateway import MODULES,render_gateway
from external_trade_ui import EXTERNAL_TRADE_URL

class UnifiedGatewayTests(unittest.TestCase):
    def test_four_module_gateway_is_an_actual_navigation_page(self):
        self.assertEqual(len(MODULES),4)
        self.assertEqual([x[0] for x in MODULES],["01","02","03","04"])
        self.assertEqual([x[3] for x in MODULES],
            ["/news","/trading","/skill","/trade-platform"])
        html=render_gateway()
        self.assertIn('lang="zh-CN"',html)
        self.assertIn("四合一管理工作台",html)
        self.assertIn('class="gate-grid"',html)
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))',html)
        self.assertIn('max-width:650px',html)
        self.assertIn("prefers-reduced-motion",html)
        for code,name,_,href,_ in MODULES:
            self.assertIn('href="'+href+'"',html)
            self.assertIn('进入模块'+code+' '+name,html)
        self.assertNotIn("trade.sasakic.cc",html)
        self.assertNotIn("<iframe",html)
        self.assertNotIn("fake price",html.lower())

    def test_all_routes_load_and_fourth_does_not_link_to_repurposed_gateway_domain(self):
        with tempfile.TemporaryDirectory() as folder:
            with ThreadingHTTPServer(("127.0.0.1",0),
                      api.make_handler(Path(folder))) as server:
                thread=threading.Thread(target=server.serve_forever,daemon=True)
                thread.start()
                root=f"http://127.0.0.1:{server.server_port}"
                try:
                    for route in ["/","/news","/trading","/skill","/trade-platform"]:
                        with self.subTest(route=route),urlopen(root+route) as res:
                            self.assertEqual(res.status,200)
                            html=res.read().decode("utf-8")
                            self.assertIn("<!doctype html>",html.lower())
                            if route=="/":
                                self.assertIn("四合一管理工作台",html)
                                self.assertNotIn("id=\"ws-members-body\"",html)
                            else:
                                self.assertIn('class="ws-frame"',html)
                                self.assertIn('href="/"',html)
                    with urlopen(root+"/news") as res:
                        html=res.read().decode("utf-8")
                        self.assertIn("BVB",html)
                        self.assertIn("fetchApi",html)
                    with urlopen(root+"/trade-platform") as res:
                        html=res.read().decode("utf-8")
                        self.assertEqual(EXTERNAL_TRADE_URL, "")
                        self.assertIn("外部域名链接已取消",html)
                        self.assertNotIn("trade.sasakic.cc",html)
                        self.assertNotIn("brantone-veyor-trading.onrender.com",html)
                        self.assertNotIn("打开交易平台 ↗",html)
                        self.assertNotIn('target="_blank"',html)
                        self.assertIn("script-src 'none'",res.headers["Content-Security-Policy"])
                    self.assertEqual(list(Path(folder).iterdir()),[])
                finally:
                    server.shutdown();thread.join(timeout=5)

if __name__=="__main__":unittest.main()
