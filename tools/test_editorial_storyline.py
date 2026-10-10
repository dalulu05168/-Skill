"""Simulation-only director scene and upstream news prioritization tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from editorial_storyline import plan_disclosed_scene, rank_news_for_review
import chennan_writing as writing


def item(item_id, impact, relevance, novelty, talkability, *, risk=False):
    return {"item_id": item_id, "headline": "Synthetic testing headline " + item_id,
            "original_url": "https://example.org/testing/" + item_id,
            "published_at": "2026-10-10T09:15:00+03:00",
            "market_materiality": impact, "romania_relevance": relevance,
            "new_evidence": novelty, "discussion_potential": talkability,
            "material_downside_risk": risk, "verified": True}


class DirectorStorylineTests(unittest.TestCase):
    def test_economic_relevance_outweighs_shallow_chatbait(self):
        res = rank_news_for_review([
            item("attention", 0, 0, 1, 4),
            item("significant-risk", 4, 4, 2, 0, risk=True),
            item("neutral-policy", 3, 3, 4, 1),
        ], max_candidates=2)
        self.assertEqual(res["shortlist_for_fact_check"][0]["item_id"], "significant-risk")
        self.assertTrue(res["do_not_hide_material_negative_news"])
        self.assertEqual(len(res["excluded_as_not_current_shortlist"]), 1)
        self.assertFalse(res["source_facts_verified"])

    def test_supplied_verified_flag_does_not_grant_release(self):
        x = rank_news_for_review([item("unreviewed", 3, 3, 3, 3)])
        self.assertEqual(x["review_queue"][0]["fact_status"], "UNVERIFIED")
        self.assertFalse(x["review_queue"][0]["publication_approved"])
        self.assertTrue(x["not_a_publish_queue"])

    def test_invalid_headline_score_and_source_fail(self):
        row = item("test", 3, 2, 2, 2)
        row["original_url"] = "file:///etc/passwd"
        with self.assertRaises(ValueError):
            rank_news_for_review([row])
        row["original_url"] = "https://example.org/original"
        row["market_materiality"] = 5
        with self.assertRaises(ValueError):
            rank_news_for_review([row])

    def test_no_fake_yesterday_argument_from_unadopted_draft(self):
        draft = {"id": "draft-1", "topic": "Old topic", "status": "draft",
                 "messages": [{"character_id": "01", "text": "fictional draft"}]}
        plan = plan_disclosed_scene("RO-08", "New market story", ["01"], [draft],
                                    unresolved_threads=[{"scene_id": "draft-1", "status": "open",
                                                         "question": "Old topic?"}])
        self.assertEqual(plan["continuity_candidates"], [])
        self.assertEqual(plan["previous_unresolved_threads"], [])
        self.assertEqual(plan["previous_disagreement_claim"], "none_on_record")
        self.assertTrue(plan["requires_disclosure"])

    def test_adopted_old_disagreement_can_run_parallel_to_new_news(self):
        approved = {"id": "adopted-1", "topic": "Morning question",
                    "date": "2026-10-09", "status": "adopted",
                    "messages": [{"character_id": "01", "text": "【虚构教学模拟】I disagree."},
                                 {"character_id": "02", "text": "【虚构教学模拟】Why?"}]}
        plan = plan_disclosed_scene("RO-08", "Latest afternoon news", ["01", "02"],
                                    [approved], unresolved_threads=[
                                       {"scene_id": "adopted-1", "status": "open",
                                        "question": "Do we have original volume data?"}])
        self.assertEqual(len(plan["continuity_candidates"]), 1)
        self.assertEqual(len(plan["previous_unresolved_threads"]), 1)
        self.assertFalse(plan["auto_publish"])
        self.assertIn("no_fixed", plan["attendance"])
        self.assertIn("previous", plan["optional_beats"][1]["id"].replace("overlap", "previous"))

    def test_new_writing_prompt_includes_adopted_only_parallel_plot(self):
        profiles = writing.load_profiles()
        approved = {
            "id": "old-approved", "draft_id": "draft-old", "date": "2026-10-09",
            "source_kind": "assistant", "source_text": "【虚构教学模拟】旧场次",
            "topic": "旧问题", "node": "RO-08", "status": "adopted",
            "messages": [{"character_id": "01", "text": "【虚构教学模拟】我没明白。"}],
        }
        state = writing.empty_state()
        state["sessions"].append(approved)
        state["unresolved_threads"] = [{"scene_id": "old-approved", "status": "open",
                                        "question": "旧公告时间需要核对"}]
        payload = {"date": "2026-10-10", "node": "RO-08",
                   "source_kind": "assistant", "source_text": "今天新消息需要原文核对。",
                   "selected_ids": ["01"], "topic": "市场事实争论"}
        prompt, _ = writing.make_prompt(payload, profiles, state)
        self.assertEqual(prompt["storyline_plan"]["previous_unresolved_threads"][0]["scene_id"], "old-approved")
        self.assertTrue(any("双线叙事" in rule for rule in prompt["instructions"]))
        self.assertEqual(prompt["mode"], "explicitly_disclosed_fictional_educational_simulation")


if __name__ == "__main__":
    unittest.main()
