"""Contract checks for the complete/isolated P004 65-persona source archive."""
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from export_p004_project import CANONICAL_INDEX, PROFILE_DIR, PROJECT_DIR, export, tracked_paths


class P004ExportTests(unittest.TestCase):
    def test_complete_source_export_separates_legacy_and_preserves_65(self):
        tracked = tracked_paths(ROOT)
        self.assertIn(CANONICAL_INDEX, tracked)
        self.assertEqual(65, len([p for p in tracked if p.startswith(PROFILE_DIR) and p.endswith("_AI_Profile.json")]))
        with tempfile.TemporaryDirectory() as tmp:
            result = export(ROOT, Path(tmp))
            self.assertEqual({"STANDALONE", "FULL-REPO-SNAPSHOT"}, set(result))
            for scope in result:
                with self.subTest(scope=scope):
                    archive_path = Path(result[scope]["archive"])
                    self.assertTrue(archive_path.is_file())
                    self.assertEqual(
                        result[scope]["archive_sha256"],
                        hashlib.sha256(archive_path.read_bytes()).hexdigest(),
                    )
                    with zipfile.ZipFile(archive_path) as bundle:
                        self.assertIsNone(bundle.testzip())
                        prefix = f"{PROJECT_DIR}/"
                        manifest = json.loads(bundle.read(prefix + "EXPORT-MANIFEST.json"))
                        self.assertEqual(65, manifest["canonical_profile_count"])
                        self.assertEqual(result[scope]["tracked_file_count"], manifest["tracked_file_count"])
                        self.assertIn(prefix + "README-START-HERE.md", bundle.namelist())
                        self.assertIn(prefix + CANONICAL_INDEX, bundle.namelist())
                        self.assertIn(prefix + "docs/P004-MODULE-AUDIT-2026-10-11.md", bundle.namelist())
                        self.assertEqual(65, len([m for m in bundle.namelist() if m.startswith(prefix + PROFILE_DIR) and m.endswith("_AI_Profile.json")]))
                        self.assertTrue(any(m.endswith(".gif") for m in bundle.namelist()), "Source media must be present")
                        for record in manifest["files"]:
                            self.assertEqual(hashlib.sha256(bundle.read(prefix + record["path"])).hexdigest(), record["sha256"])
                        legacy = [m for m in bundle.namelist() if m.startswith(prefix + "legacy/")]
                        if scope == "STANDALONE":
                            self.assertFalse(legacy, "Other project's historical code must stay outside standalone package")
                            self.assertEqual(len(tracked) - len([p for p in tracked if p.startswith("legacy/")]), manifest["tracked_file_count"])
                        else:
                            self.assertTrue(legacy, "Full snapshot should retain isolated historical sources")
                            self.assertEqual(len(tracked), manifest["tracked_file_count"])


if __name__ == "__main__":
    unittest.main()
