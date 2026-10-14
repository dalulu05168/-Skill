"""Tests for the Windows desktop entry point and its reduced module set."""
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import desktop_app
from finance_skill_api import make_handler


class DesktopAppTests(unittest.TestCase):
    def test_uses_per_user_local_app_data_directory_when_available(self):
        value = os.path.join("C:\\Users", "sample", "AppData", "Local")
        with patch.dict(os.environ, {"LOCALAPPDATA": value}):
            result = desktop_app.app_data_dir()
        self.assertTrue(str(result).endswith(os.path.join("NUVEXA", "RomaniaFinanceSkillHub")))

    def test_has_source_bundle_root_and_lazy_webview_import(self):
        self.assertTrue(desktop_app.BUNDLE_ROOT.exists())
        self.assertTrue(callable(desktop_app.main))
        # Importing the backend remains possible on Linux and does not launch a GUI.

    def test_desktop_edition_hides_and_blocks_finance_skill_only(self):
        with tempfile.TemporaryDirectory() as folder:
            server = ThreadingHTTPServer(
                ("127.0.0.1", 0), make_handler(Path(folder), desktop_mode=True))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                for route in ("/", "/trading", "/image-editor"):
                    with urlopen(base + route) as response:
                        page = response.read().decode("utf-8")
                    self.assertNotRegex(page, r'<a class="ws-rail-link[^\"]*" href="/skill"')
                    self.assertIn('.ws-frame > .app > .top + nav,.ws-frame > .app > .top + .nav{display:none!important}', page)
                    self.assertIn('href="/trading"', page)
                    self.assertIn('href="/image-editor"', page)
                    if route == "/trading":
                        self.assertNotIn('<a href="/skill">财经 Skill</a>', page)
                        self.assertNotIn('前往财经 Skill', page)
                for route in ("/skill", "/writing", "/api/trading/state", "/api/writing/state"):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(base + route)
                    self.assertEqual(error.exception.code, 404)
                with urlopen(base + "/api/trading/people") as response:
                    self.assertEqual(response.status, 200)
                request = Request(base + "/api/writing/docs", data=b"{}",
                                  headers={"Content-Type": "application/json"}, method="POST")
                with self.assertRaises(HTTPError) as error:
                    urlopen(request)
                self.assertEqual(error.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
