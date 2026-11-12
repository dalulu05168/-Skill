"""Conservative, read-only assessment of a GitHub PR's technical readiness.

Input must be acquired *fresh* by a trusted, read-only CI job from GitHub API.
This tool never approves a merge, deploys code, or decides user authorization.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from dev_framework.governance_audit import audit_branch

SHA = re.compile(r"^[0-9a-f]{40}$")
CHECK_OK = "success"


def _list_payload(value: object, key: str) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and isinstance(value.get(key), list):
        return value[key]
    return []


def evaluate_pr(repository: str, pr: object, checks: object,
                reviews: object, branch: object, mandatory_checks: list[str]) -> dict:
    issues: list[str] = []
    if not isinstance(repository, str) or "/" not in repository:
        return {"decision": "BLOCK", "issues": ["缺失项目标识"]}
    if not isinstance(pr, dict):
        return {"decision": "BLOCK", "issues": ["缺失PR实时快照"]}
    head = pr.get("head") if isinstance(pr.get("head"), dict) else {}
    base = pr.get("base") if isinstance(pr.get("base"), dict) else {}
    user = pr.get("user") if isinstance(pr.get("user"), dict) else {}
    sha = head.get("sha")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        issues.append("PR缺失可核实的40位头提交")
    if pr.get("state") != "open" or pr.get("merged", False):
        issues.append("PR不是待审合并状态")
    if pr.get("draft") is not False:
        issues.append("草稿PR不可作为正式交付候选")
    if base.get("ref") != "main":
        issues.append("目标分支不是main")
    if not isinstance(pr.get("number"), int) or pr["number"] <= 0:
        issues.append("缺少有效PR编号")
    if not isinstance(head.get("repo"), dict) or head["repo"].get("full_name") != repository:
        issues.append("PR头代码不属于预期仓库")
    who = user.get("login")
    if not isinstance(who, str) or not who:
        issues.append("PR作者未知，无法验证独立审查")

    gov = audit_branch(branch, repository, "main")
    if gov["decision"] != "PASS_BRANCH_CHECKS_ONLY":
        issues.extend("分支保护：" + x for x in gov["issues"])
    enforced = set(gov.get("required_check_names", []))
    mandated = set(mandatory_checks) if isinstance(mandatory_checks, list) else set()
    if not mandated or any(not isinstance(x, str) or not x.strip() for x in mandated):
        issues.append("没有受信任的必需检查清单")
        mandated = set()
    if not mandated.issubset(enforced):
        issues.append("分支保护未强制所有Nuvexa必需检查")

    all_checks = _list_payload(checks, "check_runs")
    for name in sorted(mandated | enforced):
        found = [c for c in all_checks if isinstance(c, dict) and c.get("name") == name]
        if len(found) != 1:
            issues.append(f"必需检查 {name}：找不到唯一运行结果")
            continue
        check = found[0]
        if check.get("head_sha") != sha or check.get("status") != "completed" or check.get("conclusion") != CHECK_OK:
            issues.append(f"必需检查 {name}：未在当前SHA上成功结束")

    # Require an *independent* current-commit review, never AI self-attestation.
    # Latest review for each user wins; changes requested cannot be hidden behind
    # an earlier approval. Out-of-order/missing timestamps are treated as untrusted.
    entries = _list_payload(reviews, "reviews")
    latest = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        reviewer = entry.get("user") if isinstance(entry.get("user"), dict) else {}
        login = reviewer.get("login")
        submitted = entry.get("submitted_at")
        if not isinstance(login, str) or not login or not isinstance(submitted, str) or not submitted:
            continue
        if login not in latest or submitted > latest[login].get("submitted_at", ""):
            latest[login] = entry
    trusted_approvals = []
    for login, entry in latest.items():
        reviewer = entry.get("user", {})
        if (login != who and not login.endswith("[bot]") and reviewer.get("type") == "User"
            and entry.get("state") == "APPROVED" and entry.get("commit_id") == sha):
            trusted_approvals.append(login)
    if not trusted_approvals:
        issues.append("没有来自其他真实用户且对应当前提交的有效PR审核")

    return {
        "decision": "BLOCK" if issues else "READY_FOR_HUMAN_AUTHORIZATION",
        "repository": repository, "head_sha": sha, "reviewers": sorted(trusted_approvals),
        "mandatory_checks": sorted(mandated), "issues": issues,
        "limitations": "即便技术审核满足，也不能自动合并或部署；仍须用户独立批准、可信CI来源、生产环境保护和真实业务端到端证据。"
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="只读检查候选PR，不执行合并或发布")
    for name in ("pr", "checks", "reviews", "branch"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--require-check", action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        snapshots = [json.loads(getattr(args, key).read_text(encoding="utf-8"))
                     for key in ("pr", "checks", "reviews", "branch")]
        result = evaluate_pr(args.repo, *snapshots, args.require_check)
    except (OSError, ValueError, TypeError) as exc:
        result = {"decision": "BLOCK", "issues": ["GitHub快照读取失败：" + type(exc).__name__]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["decision"] != "BLOCK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
