"""Safe, cross-project development handoff. This does not call external plugins."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from delivery_gate.validator import evaluate

PROFILES = ("web", "service", "content")
STAGES = (
    ("scope", "GitHub", "确认现有代码、范围和测试"),
    ("research", "Context7", "核实依赖/API的官方文档"),
    ("implementation", "GitHub + Replit/Floot（按访问权限选择）", "真实代码变更及分支提交"),
    ("developer_tests", "Superpowers + 项目测试", "真实构建/测试/调试日志"),
    ("independent_acceptance", "独立验收 Skill + delivery_gate", "来源可追溯的验收证据"),
    ("merge_review", "GitHub + 用户", "独立批准后才合并主分支"),
    ("release_review", "Render + 用户", "独立批准后才正式部署或改DNS"),
)
RELEASE_POLICY = {
    "requires_explicit_merge_approval": True,
    "requires_explicit_production_approval": True,
    "requires_explicit_dns_approval": True,
    "requires_explicit_cost_approval": True,
    "auto_deploy": False,
}

def validate_task(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["任务文件应是JSON对象"]
    problems = []
    if data.get("schema_version") != 1:
        problems.append("无效schema_version")
    repo = data.get("repository")
    if not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        problems.append("repository应为owner/repo")
    if not isinstance(data.get("task"), str) or not data["task"].strip():
        problems.append("缺失任务说明")
    if data.get("profile") not in PROFILES:
        problems.append("验收类型无效")
    for field in ("base_branch", "work_branch"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            problems.append(f"{field}无效")
    if data.get("base_branch") == data.get("work_branch"):
        problems.append("工作分支不可等于主分支")
    if data.get("release_policy") != RELEASE_POLICY:
        problems.append("任务不得关闭人工审批策略")
    phases = data.get("phases")
    if not isinstance(phases, list) or [p.get("id") if isinstance(p, dict) else None for p in phases] != [p[0] for p in STAGES]:
        problems.append("阶段缺失/顺序异常")
    else:
        for item in phases:
            if item.get("state") not in ("pending", "in_progress", "blocked", "ready_for_review"):
                problems.append(f"{item['id']}: 不可在任务文件标注已通过验收")
            if item.get("state") == "ready_for_review" and not item.get("evidence"):
                problems.append(f"{item['id']}: 缺失交接证据")
    return problems

def new_task(repository: str, task: str, branch: str, profile: str, base: str = "main") -> dict:
    data = {
        "schema_version": 1, "repository": repository, "task": task,
        "profile": profile, "base_branch": base, "work_branch": branch,
        "release_policy": dict(RELEASE_POLICY),
        "phases": [{"id": name, "owner": owner, "deliverable": expected,
                    "state": "pending", "evidence": None}
                   for name, owner, expected in STAGES],
    }
    problems = validate_task(data)
    if problems:
        raise ValueError("; ".join(problems))
    return data

def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_task(data)
    if errors:
        raise ValueError("; ".join(errors))
    return data

def acceptance(task: dict, report: Path, root: Path, sha: str) -> dict:
    """Only hash/structure check; trusted CI + independent reviewers establish provenance."""
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return {"decision": "BLOCK", "issues": ["无效的提交SHA"]}
    try:
        payload = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {"decision": "BLOCK", "issues": ["无法读取验收证据"]}
    if not isinstance(payload, dict) or payload.get("project_id") != task["repository"]:
        return {"decision": "BLOCK", "issues": ["验收项目与任务仓库不一致"]}
    result = evaluate(payload, root, sha, task["profile"])
    result["warning"] = "证据哈希校验不证明独立执行；仍需受保护CI和人工授权"
    return result

def main() -> int:
    ap = argparse.ArgumentParser(description="Nuvexa开发交接框架（无自动部署）")
    subs = ap.add_subparsers(dest="action", required=True)
    init = subs.add_parser("init")
    for flag in ("repo", "task", "branch"):
        init.add_argument("--" + flag, required=True)
    init.add_argument("--base", default="main")
    init.add_argument("--profile", choices=PROFILES, required=True)
    init.add_argument("--out", type=Path, required=True)
    for action in ("show", "check", "gate"):
        sub = subs.add_parser(action)
        sub.add_argument("--file", type=Path, required=True)
        if action == "gate":
            sub.add_argument("--report", type=Path, required=True)
            sub.add_argument("--root", type=Path, required=True)
            sub.add_argument("--sha", required=True)
            sub.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.action == "init":
            task = new_task(args.repo, args.task, args.branch, args.profile, args.base)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8") as fh:
                json.dump(task, fh, ensure_ascii=False, indent=2)
            print(f"已建立待执行任务 {args.out}；没有执行开发、测试或部署")
            return 0
        task = load(args.file)
        if args.action == "show":
            print(f"项目 {task['repository']}，隔离分支 {task['work_branch']}")
            for p in task["phases"]:
                print(f"{p['state']:<16} {p['id']:<24} {p['owner']}")
            print("插件不是自动联动；合并、正式发布、DNS及收费需单独授权")
        elif args.action == "check":
            print("任务结构合规（NOT ACCEPTED：尚未验证业务功能）")
        else:
            decision = acceptance(task, args.report, args.root, args.sha)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(decision, ensure_ascii=False))
            return 0 if decision["decision"] == "PASS" else 1
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"BLOCK: {type(exc).__name__}: {exc}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
