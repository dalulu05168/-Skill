"""Only synthetic feed tests; no fake market observation can be published."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import rss_intake as rss

XML = """<rss version="2.0"><channel><item><guid>fake-1</guid>
<title>Test suspendare</title>
<link>https://www.bvb.ro/notice/test-only</link>
<description>synthetic text</description>
<pubDate>Fri, 09 Oct 2026 12:00:00 +0300</pubDate>
</item></channel></rss>"""


class RSSIntakeTests(unittest.TestCase):
    def test_non_live_evidence_and_timezone(self):
        rows = rss.parse_feed(XML.encode(), "BVB_NEWS_RSS")
        self.assertEqual(rows[0]["evidence_status"], "unverified_requires_original_article_review")
        self.assertEqual(rows[0]["urgency_hint"], "priority_review_candidate")
        self.assertEqual(rows[0]["published_at"], "2026-10-09T09:00:00+00:00")

    def test_new_repeat_and_material_revision(self):
        rows = rss.parse_feed(XML.encode(), "BVB_NEWS_RSS")
        saved, a = rss.triage(rows)
        self.assertEqual(a[0]["change_state"], "new")
        saved, b = rss.triage(rows, saved)
        self.assertEqual(b[0]["change_state"], "unchanged")
        self.assertFalse(b[0]["review_required"])
        _, c = rss.triage(rss.parse_feed(XML.replace("synthetic text", "corrected notice").encode(),
                                        "BVB_NEWS_RSS"), saved)
        self.assertEqual(c[0]["change_state"], "revised")

    def test_duplicate_entry_suppressed(self):
        two = XML.replace("</channel>", XML[XML.index("<item>"):XML.index("</channel>")] + "</channel>")
        self.assertEqual(len(rss.triage(rss.parse_feed(two.encode(), "BVB_NEWS_RSS"))[1]), 1)

    def test_untrusted_and_missing_feed_rejected(self):
        with self.assertRaises(ValueError):
            rss.parse_feed(XML.replace("www.bvb.ro", "evil.example").encode(), "BVB_NEWS_RSS")
        with self.assertRaises(ValueError):
            rss.parse_feed(XML.encode(), "UNREGISTERED")
        with self.assertRaises(ValueError):
            rss.parse_feed(b"<rss><channel /></rss>", "BVB_NEWS_RSS")

    def test_local_cli_keeps_publication_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "sample.xml").write_text(XML, encoding="utf-8")
            args = ["--source-id", "BVB_NEWS_RSS", "--input", str(root / "sample.xml"),
                    "--state", str(root / "seen.json"), "--out", str(root / "queue.json")]
            self.assertEqual(rss.main(args), 0)
            first = json.loads((root / "queue.json").read_text(encoding="utf-8"))
            self.assertEqual(first["publish_status"], "blocked_pending_manual_evidence_review")
            self.assertEqual(first["items"][0]["change_state"], "new")
            self.assertEqual(rss.main(args), 0)
            second = json.loads((root / "queue.json").read_text(encoding="utf-8"))
            self.assertEqual(second["items"][0]["change_state"], "unchanged")


if __name__ == "__main__":
    unittest.main()
