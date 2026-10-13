"""Small platform-neutral contract tests for the Windows desktop entry point."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import desktop_app


class DesktopAppTests(unittest.TestCase):
    def test_uses_per_user_local_app_data_directory_when_available(self):
        with patch.dict(os.environ, {"LOCALAPPDATA": os.path.join("C:\\Users", "sample", "AppData", "Local")}):
            result = desktop_app.app_data_dir()
        self.assertTrue(str(result).endswith(os.path.join("NUVEXA", "RomaniaFinanceSkillHub")))

    def test_has_source_bundle_root_and_lazy_webview_import(self):
        self.assertTrue(desktop_app.BUNDLE_ROOT.exists())
        self.assertTrue(callable(desktop_app.main))
        # Importing the backend remains possible on Linux and does not launch a GUI.


if __name__ == "__main__":
    unittest.main()
