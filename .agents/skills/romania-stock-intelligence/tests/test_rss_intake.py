"""Synthetic RSS regression tests; never treated as real market observations."""
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
        saved, first = rss.triage(rows)
        self.assertEqual(first[0]["change_state"], "new")
        saved, second = rss.triage(rows, saved)
        # Unchanged on the feed never means approved/reviewed.
        self.assertEqual(len(second), 1)
        self.assertEqual(second[0]["change_state"], "new")
        self.assertTrue(second[0]["review_required"])
        saved, removed = rss.triage(rows, saved, [
            {"item_id": first[0]["item_id"], "digest": first[0]["digest"]}])
        self.assertEqual(removed, [])
        _, revised = rss.triage(
            rss.parse_feed(XML.replace("synthetic text", "corrected notice").encode(),
                           "BVB_NEWS_RSS"), saved)
        self.assertEqual(len(revised), 1)
        self.assertEqual(revised[0]["change_state"], "revised")

    def test_url_revision_and_fragment_are_handled(self):
        rows = rss.parse_feed(XML.encode(), "BVB_NEWS_RSS")
        _, initial = rss.triage(rows)
        changed_url = XML.replace("/notice/test-only", "/notice/corrected")
        _, revised = rss.triage(rss.parse_feed(changed_url.encode(), "BVB_NEWS_RSS"),
                                {"version": 2, "entries": {rows[0]["item_id"]: rows[0]["digest"]}})
        self.assertEqual(revised[0]["change_state"], "revised")
        fragment = XML.replace("/notice/test-only", "/notice/test-only#section")
        self.assertEqual(rss.parse_feed(fragment.encode(), "BVB_NEWS_RSS")[0]["digest"],
                         rows[0]["digest"])

    def test_pending_versions_not_dropped_when_feed_revises(self):
        first_items = rss.parse_feed(XML.encode(), "BVB_NEWS_RSS")
        state, first = rss.triage(first_items)
        corrected = rss.parse_feed(XML.replace("synthetic text", "revision 2").encode(),
                                   "BVB_NEWS_RSS")
        state, queued = rss.triage(corrected, state)
        self.assertEqual([item["change_state"] for item in queued], ["new", "revised"])
        state, again = rss.triage(corrected, state)
        self.assertEqual(len(again), 2)
        state, still_pending = rss.triage(corrected, state, [
            {"item_id": first[0]["item_id"], "digest": first[0]["digest"]}])
        self.assertEqual(len(still_pending), 1)
        self.assertEqual(still_pending[0]["digest"], corrected[0]["digest"])

    def test_pending_from_older_feed_remains_in_queue(self):
        old = rss.parse_feed(XML.encode(), "BVB_NEWS_RSS")
        state, _ = rss.triage(old)
        fresh = rss.parse_feed(XML.replace("fake-1", "fake-2").encode(), "BVB_NEWS_RSS")
        _, queued = rss.triage(fresh, state)
        self.assertEqual({x["guid"] for x in queued}, {"fake-1", "fake-2"})

    def test_version_1_seen_state_requeues_for_human_review(self):
        rows = rss.parse_feed(XML.encode(), "BVB_NEWS_RSS")
        v1 = {"version": 1, "entries": {rows[0]["item_id"]: rows[0]["digest"]}}
        upgraded, queued = rss.triage(rows, v1)
        self.assertEqual(upgraded["version"], 2)
        self.assertEqual(queued[0]["change_state"], "legacy_unreviewed")
        _, again = rss.triage(rows, upgraded)
        self.assertEqual(len(again), 1)

    def test_bad_ack_is_rejected(self):
        rows = rss.parse_feed(XML.encode(), "BVB_NEWS_RSS")
        state, _ = rss.triage(rows)
        with self.assertRaises(ValueError):
            rss.triage(rows, state, [{"item_id": rows[0]["item_id"], "digest": "wrong"}])

    def test_duplicate_entry_suppressed(self):
        two = XML.replace("</channel>", XML[XML.index("<item>"):XML.index("</channel>")] + "</channel>")
        self.assertEqual(len(rss.triage(rss.parse_feed(two.encode(), "BVB_NEWS_RSS"))[1]), 1)

    def test_untrusted_and_missing_feed_rejected(self):
        with self.assertRaises(ValueError):
            rss.parse_feed(XML.replace("www.bvb.ro", "evil.example").encode(), "BVB_NEWS_RSS")
        with self.assertRaises(ValueError):
            rss.parse_feed(XML.replace("www.bvb.ro", "www.bvb.ro:5555").encode(), "BVB_NEWS_RSS")
        with self.assertRaises(ValueError):
            rss.parse_feed(XML.encode(), "UNREGISTERED")
        with self.assertRaises(ValueError):
            rss.parse_feed(b"<rss><channel /></rss>", "BVB_NEWS_RSS")

    def test_local_cli_preserves_unreviewed_queue_and_manual_ack(self):
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
            self.assertEqual(len(second["items"]), 1)
            self.assertTrue(second["items"][0]["review_required"])
            row = first["items"][0]
            (root / "ack.json").write_text(json.dumps({"acknowledged": [
                {"item_id": row["item_id"], "digest": row["digest"]}]}), encoding="utf-8")
            self.assertEqual(rss.main(args + ["--ack-file", str(root / "ack.json")]), 0)
            acknowledged = json.loads((root / "queue.json").read_text(encoding="utf-8"))
            self.assertEqual(acknowledged["items"], [])
            self.assertEqual(rss.main(args), 0)
            self.assertEqual(json.loads((root / "queue.json").read_text(encoding="utf-8"))["items"], [])
            saved = json.loads((root / "seen.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["version"], 2)


if __name__ == "__main__":
    unittest.main()
