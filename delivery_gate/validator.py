"""Fail-closed acceptance evidence validator. Verified evidence format is not proof of independent execution without trusted CI."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

PROFILES = {
    'web': ('build', 'unit', 'integration', 'login', 'navigation', 'ui_desktop',
            'ui_mobile', 'data', 'security', 'regression', 'independent_review'),
    'service': ('build', 'unit', 'integration', 'api', 'data', 'security',
                'regression', 'independent_review'),
    'content': ('sources', 'consistency', 'compliance', 'independent_review'),
}

def evaluate(report: dict, root: Path, expected_sha: str, profile: str = 'web') -> dict:
    issues = []
    if profile not in PROFILES:
        return {'decision': 'BLOCK', 'issues': ['Unknown acceptance profile']}
    if not isinstance(report, dict) or report.get('schema_version') != 1:
        return {'decision': 'BLOCK', 'issues': ['Missing or invalid schema_version']}
    if not isinstance(report.get('project_id'), str) or not report['project_id'].strip():
        issues.append('Missing project_id')
    if not re.fullmatch(r'[0-9a-f]{40}', str(expected_sha)):
        issues.append('Invalid expected commit SHA')
    if report.get('target_sha') != expected_sha:
        issues.append('Evidence does not match the reviewed commit')
    checks = report.get('checks')
    if not isinstance(checks, dict):
        checks = {}
        issues.append('No check records')
    anchor = root.resolve()
    for item in PROFILES[profile]:
        check = checks.get(item)
        if not isinstance(check, dict):
            issues.append(f'{item}: missing')
            continue
        if check.get('status') != 'pass':
            issues.append(f'{item}: not passed ({check.get("status", "missing")})')
            continue
        for field in ('artifact', 'sha256', 'executor', 'command'):
            if not isinstance(check.get(field), str) or not check[field].strip():
                issues.append(f'{item}: missing {field}')
        path_str = check.get('artifact')
        if not isinstance(path_str, str) or not path_str:
            continue
        p = Path(path_str)
        if p.is_absolute() or '..' in p.parts:
            issues.append(f'{item}: unsafe artifact path')
            continue
        artifact = (anchor / p).resolve()
        if not artifact.is_relative_to(anchor) or not artifact.is_file():
            issues.append(f'{item}: artifact absent or outside evidence root')
            continue
        raw = artifact.read_bytes()
        if not raw.strip():
            issues.append(f'{item}: empty evidence')
        if hashlib.sha256(raw).hexdigest() != check.get('sha256'):
            issues.append(f'{item}: artifact digest mismatch')
    return {'decision': 'PASS' if not issues else 'BLOCK', 'issues': issues,
            'project_id': report.get('project_id'), 'target_sha': expected_sha, 'profile': profile}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', required=True)
    ap.add_argument('--root', required=True)
    ap.add_argument('--expected-sha', required=True)
    ap.add_argument('--profile', choices=tuple(PROFILES), default='web')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    try:
        decision = evaluate(json.loads(Path(a.report).read_text(encoding='utf-8')),
                            Path(a.root), a.expected_sha, a.profile)
    except (OSError, ValueError, TypeError) as exc:
        decision = {'decision': 'BLOCK', 'issues': [f'Report unavailable or invalid: {type(exc).__name__}']}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(decision, ensure_ascii=False))
    return 0 if decision['decision'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
