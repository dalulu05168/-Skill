#!/usr/bin/env python3
"""Fail-closed independent acceptance gate. Stdlib; browser checks require Playwright."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

MANDATORY = ('build', 'unit', 'security', 'functional', 'ui', 'auth', 'data', 'regression')
STATUS = ('PASS', 'FAIL', 'BLOCKED')


def load_policy(path):
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(obj, dict) or not obj.get('project'):
        raise ValueError('Policy must name a project')
    cmds = obj.get('commands', {})
    for key in ('build', 'unit', 'security'):
        if not isinstance(cmds.get(key), list) or not cmds[key] or not all(isinstance(x, str) for x in cmds[key]):
            raise ValueError(f'commands.{key} must be a nonempty argv list')
    required = obj.get('required_gates')
    if required is not None and set(required) != set(MANDATORY):
        raise ValueError(f'required_gates must include exactly all baseline gates: {MANDATORY}')
    return obj


def run_command(argv, cwd, timeout, log_file):
    try:
        result = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                                timeout=timeout, check=False, env=os.environ.copy())
        out = (result.stdout or '') + '\n--- STDERR ---\n' + (result.stderr or '')
        log_file.write_text(out[-100000:], encoding='utf-8', errors='replace')
        return ('PASS' if result.returncode == 0 else 'FAIL', f'exit={result.returncode}', str(log_file))
    except (OSError, subprocess.TimeoutExpired) as exc:
        log_file.write_text(str(exc), encoding='utf-8')
        return ('FAIL', type(exc).__name__ + ': ' + str(exc), str(log_file))


def render_report(project, result, outdir):
    statuses = result['checks']
    lines = [f'# {project} — 独立验收报告', '',
             f"- 时间 (UTC): {result['timestamp_utc']}",
             f"- 总体：**{result['overall']}**", '- 通过规则：八项必需门禁全部有本次执行证据且 PASS', '',
             '| 项目 | 结论 | 证据 |', '|---|---|---|']
    for name in MANDATORY:
        item = statuses.get(name, {})
        evidence = ', '.join(item.get('evidence', [])) or '无'
        lines.append(f"| {name} | {item.get('status', 'BLOCKED')} | {evidence} |")
        if item.get('reason'):
            lines.append(f"\n**{name}：** {item['reason']}")
    lines.extend(['', '## 审核声明', '',
                  '没有真实执行、缺少凭据、测试失败、页面信息缺失或无法核验真实数据时，不得标为通过。',
                  '即使此报告为 PASS，也只是技术验收；独立复核、PR 审核、主分支保护和正式上线授权需另外配置。',
                  '开发者本人填写 PASS 或伪造日志不构成独立证据。'])
    (outdir / 'acceptance-report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def run(policy_path, project_root, outdir, base_url, command_timeout=300):
    project_root = Path(project_root).resolve()
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    result = {'project': '', 'timestamp_utc': now, 'checks': {}, 'overall': 'REJECTED',
              'tool': 'nuvexa-independent-qa', 'version': '0.1.0'}
    try:
        policy = load_policy(policy_path)
        result['project'] = policy['project']
        if not project_root.is_dir():
            raise ValueError('Project root does not exist')
        for key in ('build', 'unit', 'security'):
            log = outdir / f'{key}.log'
            state, why, ev = run_command(policy['commands'][key], project_root, command_timeout, log)
            result['checks'][key] = {'status': state, 'reason': why, 'evidence': [ev]}
        # Browser checks execute in a new browser context; never accept developer-supplied PASS JSON.
        browser_result = outdir / 'browser-evidence.json'
        browser_result.unlink(missing_ok=True)  # Never reuse prior run's browser PASS.
        runner = Path(__file__).with_name('browser_checks.py')
        if not base_url:
            for key in ('functional', 'ui', 'auth', 'data', 'regression'):
                result['checks'][key] = {'status': 'BLOCKED', 'reason': 'Missing --base-url', 'evidence': []}
        else:
            cmd = [sys.executable, str(runner), '--policy', str(Path(policy_path).resolve()),
                   '--base-url', base_url, '--outdir', str(outdir)]
            state, why, ev = run_command(cmd, project_root, int(policy.get('browser_timeout_s', 240)), outdir / 'browser.log')
            if browser_result.exists():
                try:
                    browser = json.loads(browser_result.read_text(encoding='utf-8'))
                    for key in ('functional', 'ui', 'auth', 'data', 'regression'):
                        item = browser.get('checks', {}).get(key, {})
                        if item.get('status') not in STATUS:
                            item = {'status': 'FAIL', 'reason': 'Invalid/missing browser status', 'evidence': []}
                        # The child browser checker MUST exit cleanly. Do not trust a
                        # forged or partial PASS JSON when its process failed.
                        if state != 'PASS' and item.get('status') == 'PASS':
                            item = {'status': 'FAIL', 'reason': 'Browser checker exited unsuccessfully: ' + why, 'evidence': []}
                        item.setdefault('evidence', [])
                        item['evidence'].extend([ev, str(browser_result)])
                        result['checks'][key] = item
                except (ValueError, OSError) as exc:
                    why += '; invalid browser evidence: ' + str(exc)
            for key in ('functional', 'ui', 'auth', 'data', 'regression'):
                result['checks'].setdefault(key, {'status': 'BLOCKED', 'reason': why, 'evidence': [ev]})
            if state != 'PASS':
                # Do not claim the browser execution passed even if its report is tampered with.
                for key in ('functional', 'ui', 'auth', 'data', 'regression'):
                    if result['checks'][key].get('status') == 'PASS':
                        result['checks'][key] = {'status': 'FAIL', 'reason': 'Browser process did not exit successfully', 'evidence': [ev]}
        result['overall'] = 'PASS' if all(result['checks'].get(k, {}).get('status') == 'PASS' for k in MANDATORY) else 'REJECTED'
    except Exception as exc:
        result['fatal_error'] = str(exc)
        result['traceback'] = traceback.format_exc()[-3000:]
        result['overall'] = 'REJECTED'
    (outdir / 'acceptance.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    render_report(result['project'] or 'UNKNOWN', result, outdir)
    return result


def main():
    p = argparse.ArgumentParser(description='Independent, fail-closed acceptance gate')
    p.add_argument('--policy', required=True)
    p.add_argument('--project-root', default='.')
    p.add_argument('--outdir', default='qa-evidence')
    p.add_argument('--base-url', default=os.getenv('QA_BASE_URL'))
    p.add_argument('--command-timeout', type=int, default=300)
    a = p.parse_args()
    r = run(a.policy, a.project_root, a.outdir, a.base_url, a.command_timeout)
    for k in MANDATORY:
        c = r['checks'].get(k, {'status': 'BLOCKED'})
        print(f'{k:12s} {c["status"]}')
    print('OVERALL:', r['overall'], '\nREPORT:', Path(a.outdir).resolve() / 'acceptance-report.md')
    return 0 if r['overall'] == 'PASS' else 1

if __name__ == '__main__':
    sys.exit(main())
