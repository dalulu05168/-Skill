"""Fail-closed audit of GitHub branch controls from a *current* GitHub API snapshot.

Never treats AI-authored assertions as the proof of CI/branch protection.
This is only one check; reviewer independence and deployment isolation must
be verified separately.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

def audit_branch(snapshot: object, repository: str, branch: str = "main") -> dict:
    issues = []
    if not isinstance(snapshot, dict):
        return {"decision": "BLOCK", "issues": ["分支API响应不是对象"]}
    if snapshot.get("name") != branch:
        issues.append("分支名或快照不匹配")
    if snapshot.get("protected") is not True:
        issues.append("主分支没有启用保护")
    rule = snapshot.get("protection") if isinstance(snapshot.get("protection"), dict) else {}
    if rule.get("enabled") is not True:
        issues.append("分支保护规则未启用")
    statuses = rule.get("required_status_checks") if isinstance(rule.get("required_status_checks"), dict) else {}
    names = [entry.get("context") for entry in statuses.get("checks", [])
             if isinstance(entry, dict) and isinstance(entry.get("context"), str) and entry["context"].strip()]
    names += [entry for entry in statuses.get("contexts", []) if isinstance(entry, str) and entry.strip()]
    names = sorted(set(names))
    if statuses.get("enforcement_level") != "everyone" or not names:
        issues.append("未验证对所有人强制的必需CI状态检查")
    return {
        "repository": repository, "branch": branch, "decision": "BLOCK" if issues else "PASS_BRANCH_CHECKS_ONLY",
        "required_check_names": names, "issues": issues,
        "limitations": "输入须来自当前有权限的GitHub API；即便分支状态合格，也不能代替PR独立审核、规则集旁路检查、环境保护及部署密钥隔离",
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="审计GitHub分支保护快照，不更改仓库")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", default="main")
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        obj = json.loads(args.input.read_text(encoding="utf-8"))
        result = audit_branch(obj, args.repo, args.branch)
    except (OSError, ValueError, TypeError):
        result = {"decision": "BLOCK", "issues": ["无法读取可信的分支控制数据"]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["decision"] != "BLOCK" else 1

if __name__ == "__main__":
    raise SystemExit(main())
