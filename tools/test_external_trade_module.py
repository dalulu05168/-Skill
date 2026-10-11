"""Module four must be a real local image editor, never a trading redirect."""
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import finance_skill_api as api
from image_editor_ui import PAGE

class ImageEditorModuleTests(unittest.TestCase):
    def test_editor_has_real_canvas_controls_and_no_external_destination(self):
        for expected in ('<canvas id="stage"', 'id="photo"', 'id="caption"',
                         'id="brightness"', 'id="color"', 'id="font"',
                         'id="fit"', 'id="export"', 'id="reset"',
                         'out.width=3840', 'out.height=2160', 'toBlob',
                         'addEventListener', 'href="/"'):
            self.assertIn(expected, PAGE)
        for forbidden in ("brantone-veyor-trading.onrender.com",
                          "trade.sasakic.cc", "https://", "<iframe",
                          "localStorage", "XMLHttpRequest"):
            self.assertNotIn(forbidden, PAGE)

    def test_four_modules_route_and_api_remain_isolated(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            with ThreadingHTTPServer(("127.0.0.1", 0), api.make_handler(data)) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    for route in ("/", "/news", "/trading", "/skill", "/image-editor"):
                        with self.subTest(route=route), urlopen(base+route) as response:
                            self.assertEqual(response.status, 200)
                            html = response.read().decode("utf-8")
                            self.assertIn("text/html", response.headers.get("Content-Type"))
                            self.assertNotIn("brantone-veyor-trading.onrender.com", html)
                            if route == "/":
                                self.assertIn('href="/image-editor"', html)
                            elif route == "/image-editor":
                                self.assertIn("图片编辑工作台", html)
                                self.assertIn("导出 4K PNG", html)
                    with urlopen(base+"/image-editor") as response:
                        policy=response.headers.get("Content-Security-Policy", "")
                        self.assertIn("frame-src 'none'", policy)
                        self.assertIn("script-src 'unsafe-inline'", policy)
                    with urlopen(base+"/trade-platform") as response:
                        self.assertIn("图片编辑工作台", response.read().decode("utf-8"))
                    with urlopen(base+"/api/trading/people") as response:
                        self.assertEqual(json.load(response)["count"], 65)
                    self.assertEqual(list(data.iterdir()), [])
                finally:
                    server.shutdown()
                    thread.join(timeout=5)

if __name__ == "__main__":
    unittest.main()
