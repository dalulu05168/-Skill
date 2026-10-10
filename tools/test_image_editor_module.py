"""Tests for the in-workspace image editor link and iframe permission boundary.

No requests are sent to the hosted image editor during unit tests.
"""
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from finance_skill_api import make_handler
from image_editor_ui import PAGE, IMAGE_EDITOR_URL


class ImageEditorModuleTests(unittest.TestCase):
    def test_reuses_original_existing_editor_without_proxying(self):
        self.assertEqual(IMAGE_EDITOR_URL,"https://trade.sasakic.cc/")
        self.assertIn('iframe src="https://trade.sasakic.cc/"',PAGE)
        self.assertIn('target="_blank"',PAGE)
        self.assertIn('allow-downloads',PAGE)
        self.assertIn('referrerpolicy="no-referrer"',PAGE)
        self.assertNotIn("TemplateImageEditor",PAGE)
        self.assertNotIn("fetch(",PAGE)

    def test_internal_route_and_current_functions_are_still_available(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            with ThreadingHTTPServer(("127.0.0.1",0),make_handler(folder)) as server:
                th=threading.Thread(target=server.serve_forever,daemon=True)
                th.start()
                base=f"http://127.0.0.1:{server.server_port}"
                try:
                    for route in ("/","/trading","/skill","/image-editor"):
                        with self.subTest(route=route),urlopen(base+route) as resp:
                            self.assertEqual(resp.status,200)
                            page=resp.read().decode("utf-8")
                            self.assertIn('href="/image-editor"',page)
                            self.assertIn("图片",page)
                    with urlopen(base+"/image-editor") as resp:
                        csp=resp.headers.get("Content-Security-Policy","")
                        self.assertIn("frame-src https://trade.sasakic.cc",csp)
                        self.assertIn("script-src 'none'",csp)
                        self.assertEqual(resp.headers.get("Referrer-Policy"),"no-referrer")
                        self.assertEqual(resp.headers.get("Cache-Control"),"no-store")
                    with urlopen(base+"/trade-platform") as resp:
                        self.assertEqual(resp.status,200)
                        self.assertEqual(resp.url,base+"/image-editor")
                        self.assertIn("frame-src https://trade.sasakic.cc",resp.headers.get("Content-Security-Policy",""))
                    with urlopen(base+"/api/trading/people") as resp:
                        self.assertEqual(json.load(resp)["count"],65)
                    self.assertEqual(list(folder.iterdir()),[])
                finally:
                    server.shutdown()
                    th.join(timeout=5)


if __name__=="__main__":
    unittest.main()
