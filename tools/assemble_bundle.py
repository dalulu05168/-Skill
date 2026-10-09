#!/usr/bin/env python3
"""Rebuild the two source bundles from current files without mutating old dist ZIPs."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__", ".pytest_cache", ".DS_Store"}


def collect(inputs):
    result = {}
    for path in inputs:
        base = ROOT / path
        if not base.exists():
            raise FileNotFoundError(base)
        for item in ([base] if base.is_file() else base.rglob("*")):
            if item.is_file() and not SKIP.intersection(item.relative_to(ROOT).parts):
                result[item.relative_to(ROOT).as_posix()] = item
    return result


def create(destination, files):
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as output:
        for name, path in sorted(files.items()):
            info = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            output.writestr(info, path.read_bytes())
    with ZipFile(destination) as result:
        names = set(result.namelist())
        assert result.testzip() is None, "ZIP corruption"
        assert "skills/romania-market-director/SKILL.md" in names
        assert "bundle-manifest.json" in names
        manifest = json.loads(result.read("bundle-manifest.json"))
        assert manifest["bundle_version"] == "2.3.0"
        assert len([n for n in names if n.startswith(
            "skills/romania-market-director/characters/profiles/"
        ) and n.endswith("_AI_Profile.json")]) == manifest["modules"]["personas"]["count"] == 65
        return len(names)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", required=True)
    args = p.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    shared = ["AGENTS.md", "README.md", "bundle-manifest.json",
              "skills/romania-market-director"]
    small = out / "romania-market-director-skill.zip"
    large = out / "romania-finance-bundle.zip"
    small_count = create(small, collect(shared))
    large_count = create(large, collect(shared + [
        ".agents/skills/romania-stock-intelligence",
        "skills/accuracy-enhancement",
        "skills/bvb-fact-check",
        "skills/news-priority",
        "skills/character-consistency",
        "skills/script-qa",
        "third_party/orchestra-research",
        "tools/test_accuracy_pack.py",
        "tools/finance_skill_hub.py",
        "tools/finance_skill_editorial.py",
        "tools/finance_skill_api.py",
        "tools/finance_skill_generate.py",
        "docs/UNIFIED-FINANCE-SKILL-HUB.md",
        "docs/CHATGPT-FIRST-WORKFLOW.md",
    ]))
    with ZipFile(large) as z:
        assert ".agents/skills/romania-stock-intelligence/scripts/rss_intake.py" in z.namelist()
        assert "skills/bvb-fact-check/SKILL.md" in z.namelist()
        assert "skills/script-qa/SKILL.md" in z.namelist()
        assert "third_party/orchestra-research/AI-Research-SKILLs/LICENSE" in z.namelist()
    print("SUCCESS: verified director", small_count, "and full", large_count, "files.")


if __name__ == "__main__":
    main()
