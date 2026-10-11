"""Real local HTTP acceptance checks for P004 studio.
No fake site buttons: exercise requests, persistence, review, model adapter,
CSRF, unapproved roster gate, and explicit model absence.
"""
import json
import os
import pathlib
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import director_studio as studio


class DirectorStudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = studio.create_server(0, pathlib.Path(self.temp.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:" + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=3)
        self.server.server_close()
        self.temp.cleanup()

    def req(self, endpoint, payload=None, *, token=True, origin=True):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Director-Token"] = self.server.csrf_token
        if origin:
            headers["Origin"] = self.base
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(self.base + endpoint, data=body,
                      headers=headers, method="POST" if body else "GET")
        try:
            with urlopen(req, timeout=4) as r:
                content = r.read().decode("utf-8")
                return r.status, json.loads(content) if endpoint != "/" else content
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def prepared(self, *, scene="scene-test-1", daypart="afternoon", story_date="2026-10-14"):
        return self.req("/api/prepare", {
            "scene_id": scene, "story_date": story_date,
            "daypart": daypart, "topic": "能源,交通",
            "max_members": 8, "director_note": "两种不同观点"
        })

    def valid_draft(self, prepared):
        task = prepared["task"]
        return {"story_id": task["story_id"], "scene_id": task["scene_id"],
                "story_date": task["story_date"], "daypart": task["daypart"],
                "lesson_type": task["lesson_type"], "simulation_only": True,
                "fictional_case_only": True, "status": "DRAFT_NOT_ADOPTED",
                "approved_by_user": False, "publishable": False,
                "messages": [
                    {"message_id": "m01", "speaker_id": "assistant",
                     "text": "Să discutăm un exemplu imaginar despre costuri."},
                    {"message_id": "m02", "speaker_id": task["cast"][0]["speaker_id"],
                     "reply_to": "m01", "text": "Dar cum știm dacă este relevant?"},
                    {"message_id": "m03", "speaker_id": task["cast"][-1]["speaker_id"],
                     "reply_to": "m02", "text": "Eu aș vedea și riscurile."}
                ]}

    def test_real_status_and_ui(self):
        status, result = self.req("/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(result["candidate_personas"], 65)
        self.assertEqual(result["approved_personas"], 0)
        self.assertFalse(result["ready_for_final_adoption"])
        with urlopen(self.base + "/", timeout=4) as r:
            page = r.read().decode("utf-8")
            self.assertIn("真实选角", page)
            self.assertIn("调用本地 AI 编剧", page)
            self.assertIn(self.server.csrf_token, page)
            self.assertIn("viewport", page)
            self.assertNotIn("__STUDIO_CSRF__", page)

    def test_local_csrf_origin_and_oversize_blocks(self):
        status, result = self.req("/api/prepare", {}, token=False)
        self.assertEqual(status, 403)
        self.assertIn("令牌", result["error"])
        req = Request(self.base + "/api/prepare", data=b"{}",
            headers={"X-Director-Token": self.server.csrf_token,
                     "Origin": "http://evil.example",
                     "Content-Type": "application/json"}, method="POST")
        with self.assertRaises(HTTPError) as error:
            urlopen(req, timeout=4)
        self.assertEqual(error.exception.code, 403)

    def test_prepare_recover_review_and_cannot_adopt_without_approved_roster(self):
        status, out = self.prepared()
        self.assertEqual(status, 200)
        token = out["token"]
        self.assertEqual(out["prepared"]["stage"], "AWAITING_SCREENWRITER_JSON")
        self.assertTrue(out["prepared"]["cast_count"])
        self.assertFalse(out["prepared"]["model_invoked"])
        self.assertEqual(self.req("/api/load", {"token": token})[0], 200)
        draft = self.valid_draft(out["prepared"])
        code, answer = self.req("/api/review", {"token": token, "manuscript": draft})
        self.assertEqual(code, 200)
        self.assertEqual(answer["qa"]["status"], "EDITORIAL_REVIEW_REQUIRED")
        code, blocked = self.req("/api/adopt", {"token": token,
            "editorial_confirmed": True, "operator_confirmed": True})
        self.assertEqual(code, 400)
        self.assertIn("正式65人", blocked["error"])
        self.assertFalse(self.server.history_db.exists())
        self.assertEqual(self.req("/api/load", {"token": token})[1]["draft"], draft)

    def test_unknown_speaker_never_passes_review_or_memory(self):
        _, out = self.prepared(scene="scene-review-negative")
        draft = self.valid_draft(out["prepared"])
        draft["messages"][1]["speaker_id"] = "99"
        code, ans = self.req("/api/review", {
            "token": out["token"], "manuscript": draft})
        self.assertEqual(code, 200)
        self.assertEqual(ans["qa"]["status"], "BLOCKED_REWRITE_REQUIRED")
        self.assertIsNone(self.req("/api/load", {"token": out["token"]})[1]["draft"])
        code, _ = self.req("/api/adopt", {
            "token": out["token"],
            "editorial_confirmed": True, "operator_confirmed": True})
        self.assertEqual(code, 400)

    def test_ai_without_model_clearly_fails_no_fake_success(self):
        _, out = self.prepared(scene="scene-no-model")
        with patch.dict(os.environ, {"P004_OLLAMA_MODEL": ""}):
            code, result = self.req("/api/generate", {"token": out["token"]})
        self.assertEqual(code, 503)
        self.assertIn("Ollama", result["error"])
        self.assertIsNone(self.req("/api/load", {"token": out["token"]})[1]["draft"])

    def test_real_model_call_path_with_explicit_test_double(self):
        _, out = self.prepared(scene="scene-model-contract")
        manuscript = self.valid_draft(out["prepared"])
        calls = []

        def fake_model(prompt):
            calls.append(prompt)
            return json.dumps(manuscript, ensure_ascii=False)

        with patch.dict(os.environ, {"P004_OLLAMA_MODEL": "local-test-model"}), \
             patch.object(studio, "_ollama_generate", side_effect=fake_model):
            code, result = self.req("/api/generate", {"token": out["token"]})
        self.assertEqual(code, 200)
        self.assertEqual(result["status"], "EDITORIAL_REVIEW_REQUIRED")
        self.assertTrue(result["ai_generation_performed"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["manuscript"], manuscript)
        self.assertFalse(self.server.history_db.exists())

    def test_explicit_approval_writes_actual_sqlite_and_refuses_duplicate(self):
        # Synthetic approved roster exists ONLY inside this isolated test temp dir.
        # It does not approve the real 65 candidates or change the repository file.
        draft_roster = studio._read_json(studio.DRAFT_ROSTER)
        official = pathlib.Path(self.temp.name) / "synthetic-approved.json"
        official.write_text(json.dumps({
            "story_id": "p004-fiction-director-independent",
            "characters": [
                {"id": person["id"], "approved_by_user": True}
                for person in draft_roster["people"]
            ]}, ensure_ascii=False), encoding="utf-8")
        with patch.object(studio, "APPROVED_ROSTER", official):
            _, out = self.prepared(scene="scene-adopt-positive")
            manuscript = self.valid_draft(out["prepared"])
            _, reviewed = self.req("/api/review", {
                "token": out["token"], "manuscript": manuscript})
            self.assertEqual(reviewed["qa"]["status"], "EDITORIAL_REVIEW_REQUIRED")
            code, refused = self.req("/api/adopt", {
                "token": out["token"],
                "operator_confirmed": True, "editorial_confirmed": False})
            self.assertEqual(code, 400)
            self.assertIn("分别", refused["error"])
            self.assertFalse(self.server.history_db.exists())
            code, success = self.req("/api/adopt", {
                "token": out["token"],
                "operator_confirmed": True, "editorial_confirmed": True})
            self.assertEqual(code, 200)
            self.assertTrue(success["result"]["official_story_memory_written"])
            self.assertFalse(success["result"]["published_to_whatsapp"])
            self.assertTrue(self.server.history_db.exists())
            from scene_memory import person_history
            rows = person_history(self.server.history_db, official, "assistant")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["scene_id"], "scene-adopt-positive")
            code, refused = self.req("/api/adopt", {
                "token": out["token"],
                "operator_confirmed": True, "editorial_confirmed": True})
            self.assertEqual(code, 400)
            self.assertIn("已采用", refused["error"])

    def test_persisted_scene_survives_server_restart(self):
        _, out = self.prepared(scene="scene-restored")
        token = out["token"]
        path = pathlib.Path(self.temp.name) / "drafts" / (token + ".json")
        self.assertTrue(path.is_file())
        # Reopen the persisted state without relying on process RAM.
        new = studio.create_server(0, pathlib.Path(self.temp.name))
        try:
            state = new.load(token)
            self.assertEqual(state["prepared"]["task"]["scene_id"], "scene-restored")
            self.assertIsNone(state["draft"])
        finally:
            new.server_close()


if __name__ == "__main__":
    unittest.main()
