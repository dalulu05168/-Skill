"""Only explicitly approved and attributable 65-person fictional history may be staged."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from approved_scene_memory import stage_approved_scene, apply_staged_scene
from chennan_writing import load_profiles


class MemoryImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load_profiles()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = self.root / "skills/romania-market-director/library/approved"
        self.base.mkdir(parents=True)
        self.path = self.base / "approved_scene.json"
        self.person = self.profiles["01"]
        self.doc = {
            "approved_by_user": True, "simulation_only": True,
            "scene_id": "2026-10-12-RO-10-v1", "date": "2026-10-12",
            "node": "RO-10", "messages": [{
                "character_id": "01",
                "name": self.person["identity_extension"]["姓名"],
                "gender": self.person["source_profile"]["性别"],
                "role": self.person["source_profile"]["学员资历"],
                "message_id": "m1", "simulation_only": True,
                "text": "【虚构教学模拟】我觉得这个成交量还得看看。",
            }]
        }
        self.state = {"schema_version": "1.0", "scope": "fictional_simulation_only",
                      "adopted_scenes": [], "characters": {},
                      "unresolved_questions": [], "pending_conflicts": []}

    def save(self):
        self.path.write_text(json.dumps(self.doc, ensure_ascii=False), encoding="utf-8")
        return self.path.relative_to(self.root).as_posix()

    def test_requires_explicit_approved_user_source(self):
        path = self.save()
        self.doc["approved_by_user"] = False
        self.save()
        with self.assertRaises(ValueError):
            stage_approved_scene(self.root, path, self.state, self.profiles)

    def test_staging_does_not_mutate_memory_then_requires_confirmation(self):
        path = self.save()
        before = copy.deepcopy(self.state)
        stage = stage_approved_scene(self.root, path, self.state, self.profiles)
        self.assertEqual(self.state, before)
        with self.assertRaises(ValueError):
            apply_staged_scene(self.state, stage)
        after = apply_staged_scene(self.state, stage, operator_confirmed=True)
        self.assertEqual(len(after["adopted_scenes"]), 1)
        self.assertEqual(after["characters"]["01"]["speech_events"][0]["message_ref"], "m1")
        with self.assertRaises(ValueError):
            apply_staged_scene(after, stage, operator_confirmed=True)

    def test_identity_and_fictional_disclosure_must_match(self):
        path = self.save()
        self.doc["messages"][0]["name"] = "Wrong person"
        self.save()
        with self.assertRaises(ValueError):
            stage_approved_scene(self.root, path, self.state, self.profiles)
        self.doc["messages"][0]["name"] = self.person["identity_extension"]["姓名"]
        self.doc["messages"][0]["text"] = "Unlabeled imitation"
        self.save()
        with self.assertRaises(ValueError):
            stage_approved_scene(self.root, path, self.state, self.profiles)

    def test_draft_directory_never_importable(self):
        self.save()
        self.assertRaises(ValueError, stage_approved_scene,
                          self.root, "skills/romania-market-director/library/drafts/draft.json",
                          self.state, self.profiles)


if __name__ == "__main__":
    unittest.main()
