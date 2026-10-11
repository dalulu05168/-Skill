"""Security contract for trusted browser smoke runner (static guard, not E2E proof)."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "browser_check.mjs").read_text(encoding="utf-8")

class BrowserPolicyTests(unittest.TestCase):
    def test_credentials_only_sent_to_tls_origin(self):
        self.assertIn("approvedUrl.protocol !== 'https:'", SOURCE)

    def test_login_form_cannot_post_to_foreign_origin(self):
        self.assertIn("form.action", SOURCE)
        self.assertIn("form action targets another origin", SOURCE)

if __name__ == "__main__":
    unittest.main()
