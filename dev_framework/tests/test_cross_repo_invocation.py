"""A foreign consumer repository can run the pinned gate without local package installs."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2]
SHA = "a"*40


class CrossRepositoryInvocationTests(unittest.TestCase):
    def test_module_invocation_from_foreign_directory_fails_closed_not_import_error(self):
        with tempfile.TemporaryDirectory() as d:
            foreign = Path(d)
            (foreign / "pr.json").write_text(json.dumps({
                "number": 1, "state": "open", "merged": False, "draft": True,
                "head": {"sha": SHA, "repo": {"full_name": "owner/test"}},
                "base": {"ref": "main"}, "user": {"login": "author", "type": "User"}
            }), encoding="utf-8")
            (foreign / "checks.json").write_text('{"check_runs":[]}', encoding="utf-8")
            (foreign / "reviews.json").write_text('[]', encoding="utf-8")
            (foreign / "branch.json").write_text(
                '{"name":"main","protected":false,"protection":{"enabled":false}}', encoding="utf-8")
            args = [
                sys.executable, "-m", "dev_framework.release_readiness",
                "--repo", "owner/test",
                "--pr", "pr.json", "--checks", "checks.json",
                "--reviews", "reviews.json", "--branch", "branch.json",
                "--require-check", "real-build", "--out", "result.json",
            ]
            env = dict(os.environ)
            env["PYTHONPATH"] = str(SOURCE_ROOT)
            result = subprocess.run(args, cwd=foreign, env=env,
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("ModuleNotFoundError", result.stderr)
            self.assertEqual(json.loads((foreign/"result.json").read_text(encoding="utf-8"))["decision"], "BLOCK")

if __name__ == "__main__":
    unittest.main()
