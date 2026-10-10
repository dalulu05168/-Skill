"""Export the P004 65-persona finance hub without mixing other projects.

Produces two self-contained GitHub-source archives:
- STANDALONE: all tracked files except isolated legacy/ migration sources
- FULL-REPO-SNAPSHOT: every tracked file, with legacy/ kept in its own directory

Never exports untracked runtime files, secrets, local memories or cloud data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = "P004-65-Persona-Finance-Workspace"
PROFILE_DIR = "skills/romania-market-director/characters/profiles/"
CANONICAL_INDEX = "skills/romania-market-director/characters/index.json"

START_HERE = """# P004 · 65人物四合一财经工作台

此压缩包来自 dalulu05168/-Skill，**不是** Brantone CRM，也不是另外的客户端／后台子账户／总账户交易平台。

## 四个功能入口
1. `/` 新闻推送、BVB 资讯候审与人工审核。
2. `/trading` 65人完整虚构档案 + 教育用模拟开户、股票计划、买卖持仓。
3. `/skill` 财经 Skill、助理／教授／65名人物群聊编剧、审核及正式采用的本机记忆。
4. `/trade-platform` **图片编辑器外链**，保留旧URL兼容；并非实盘交易平台。

## 目录
- `tools/`：Python API、页面、65人模拟账本、新闻/对话审核、自动化测试、导出脚本。
- `skills/`：导演和增强 Skill、65份正式人物档案、人物索引、表情素材及规则。
- `.agents/`：罗马尼亚财经情报 Skill 与测试。
- `third_party/`：许可证明确的第三方参考资料。
- `docs/`：运行/功能/差距/架构说明与本次完整审核报告。
- `.github/`：质量门禁和项目打包工作流。
- `START-FINANCE-SKILL.cmd`：Windows 本地一键启动。
- `README.md` 与 `bundle-manifest.json`：系统入口与 65 人物规范。

本 ZIP 只含仓库受版本控制的内容。用户电脑上未提交的正式会话、交易模拟状态、账号、密钥、云盘内未同步的媒体原件以及其他仓库代码均**不在包内**。如果需要保留这些真实本地历史，须另行在原设备上备份。

Windows 需 Python 3.11+，解压后双击 START-FINANCE-SKILL.cmd；跨平台可运行 `python tools/finance_skill_api.py`，再访问 http://127.0.0.1:8765/ 。勿将此本地版本未经安全验收直接放到公网。

详情请看 `docs/P004-MODULE-AUDIT-2026-10-11.md`；校验请看 `EXPORT-MANIFEST.json`。
"""

def tracked_paths(root: Path) -> list[str]:
    raw = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z", "--cached"])
    paths = sorted(p.decode("utf-8") for p in raw.split(b"\0") if p)
    for relative in paths:
        path = root / relative
        if path.is_symlink():
            raise ValueError(f"Refusing symlink in source bundle: {relative}")
        if not path.is_file() or path.resolve().is_relative_to(root.resolve()) is False:
            raise ValueError(f"Missing or unsafe tracked file: {relative}")
    return paths

def selection(paths: list[str], *, standalone: bool) -> list[str]:
    if standalone:
        # Old 005/70/72-person source is preserved ONLY in full history archive.
        return [p for p in paths if not p.startswith("legacy/")]
    return list(paths)

def export(root: Path, output_dir: Path) -> dict[str, dict]:
    paths = tracked_paths(root)
    profiles = [p for p in paths if p.startswith(PROFILE_DIR) and p.endswith("_AI_Profile.json")]
    if len(profiles) != 65 or CANONICAL_INDEX not in paths:
        raise ValueError(f"Canonical persona roster incomplete: {len(profiles)} profiles")
    report_path = "docs/P004-MODULE-AUDIT-2026-10-11.md"
    if report_path not in paths:
        raise ValueError("Project audit report is missing from tracked source")
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for scope, standalone in (("STANDALONE", True), ("FULL-REPO-SNAPSHOT", False)):
        selected = selection(paths, standalone=standalone)
        file_manifest = []
        archive_path = output_dir / f"P004-65personas-{scope}.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as zf:
            for relative in selected:
                source = root / relative
                data = source.read_bytes()
                zf.writestr(f"{PROJECT_DIR}/{relative}", data)
                file_manifest.append({
                    "path": relative, "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                })
            manifest = {
                "project": "P004", "name": "罗马尼亚财经四合一 · 65正式人物",
                "repo": "dalulu05168/-Skill",
                "scope": scope,
                "canonical_profile_count": 65,
                "tracked_file_count": len(file_manifest),
                "total_source_bytes": sum(f["bytes"] for f in file_manifest),
                "excluded_paths": ["legacy/"] if standalone else [],
                "includes_runtime_user_state": False,
                "files": file_manifest,
            }
            zf.writestr(f"{PROJECT_DIR}/README-START-HERE.md", START_HERE)
            zf.writestr(
                f"{PROJECT_DIR}/EXPORT-MANIFEST.json",
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            )
        # Validate archive contents and manifest at creation, without extracting.
        with zipfile.ZipFile(archive_path) as archive:
            broken = archive.testzip()
            if broken:
                raise ValueError(f"Corrupt ZIP entry: {broken}")
            for profile in profiles:
                if f"{PROJECT_DIR}/{profile}" not in archive.namelist():
                    raise ValueError(f"Profile missing from ZIP: {profile}")
        result[scope] = {
            "archive": str(archive_path),
            "tracked_file_count": len(file_manifest),
            "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
            "size_bytes": archive_path.stat().st_size,
        }
    (output_dir / "EXPORT-SUMMARY.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build" / "project-export")
    args = parser.parse_args()
    print(json.dumps(export(ROOT, args.output_dir), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
