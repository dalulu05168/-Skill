"""Offline contract checks for optional BVB v3.3 cloud news collector."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
import bvb_v33_api_cloud as api

RSS='''<?xml version="1.0"?><rss><channel><item><title>BVB announcement</title><link>https://www.bvb.ro/Stocks/News</link><description>Public data</description><guid>release-one</guid><pubDate>Sat, 10 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'''

class CloudCollectorContract(unittest.TestCase):
    def test_parses_real_xml_without_fabricating_success(self):
        with patch.object(api,"get_url",return_value=RSS):
            news,state=api.fetch_feed(api.FEEDS[0])
        self.assertEqual(len(news),1)
        self.assertEqual(state["state"],"ok")
        self.assertEqual(news[0]["title"],"BVB announcement")
        self.assertEqual(news[0]["sourceId"],"bvb-market")
        with patch.object(api,"get_url",side_effect=TimeoutError("upstream failed")):
            news,state=api.fetch_feed(api.FEEDS[0])
        self.assertEqual(news,[])
        self.assertEqual(state["state"],"failed")
        self.assertIn("upstream failed",state["message"])

    def test_quote_unavailable_and_article_url_restricted(self):
        with patch.object(api,"get_url",side_effect=TimeoutError("HTTP 500")):
            quote=api.quote_bet()
        self.assertEqual(quote["state"],"unavailable")
        self.assertIsNone(quote["value"])
        self.assertIn("HTTP 500",quote["note"])
        for url in ("http://127.0.0.1:8000/internal","https://example.com/",
                    "https://evil.example/bvb.ro","file:///etc/passwd"):
            with self.assertRaises(ValueError):
                api.fetch_article(url)

    def test_cloud_schema_is_compatible_with_restored_browser(self):
        self.assertEqual(len(api.FEEDS),5)
        self.assertEqual(set(x["id"] for x in api.FEEDS),
                         {"bvb-market","bvb-issuer","bvb-operation","ecb","bursa"})
        self.assertIn("https://invest.sasakic.cc",api.ALLOWED_ORIGINS)

if __name__=="__main__":
    unittest.main()
