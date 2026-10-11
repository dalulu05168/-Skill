#!/usr/bin/env python3
"""Real user-like web checks via Playwright; defaults to BLOCKED, never assumes success."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys

BROWSER_GATES = ('functional', 'ui', 'auth', 'data', 'regression')

def status(ok, details, evidence=None):
    return {'status': 'PASS' if ok else 'FAIL', 'reason': '; '.join(details)[:1800], 'evidence': evidence or []}

def json_path(value, path):
    for token in path.split('.'):
        if isinstance(value, list):
            value = value[int(token)]
        else:
            value = value[token]
    return value

def validate_policy(policy):
    # A placeholder policy can NEVER be accepted as tested evidence.
    if 'REPLACE_WITH' in json.dumps(policy):
        raise ValueError('Unconfigured REPLACE_WITH template placeholder')
    pages = policy.get('pages', [])
    screens = policy.get('screens', [])
    scenarios = policy.get('scenarios', [])
    auth = policy.get('auth', [])
    data_checks = policy.get('data_checks', [])
    assert pages and all(p.get('path') and (p.get('selectors') or p.get('expect_text')) for p in pages), 'pages require real expectations'
    assert len(screens) >= 2, 'desktop AND mobile viewports required'
    assert any(int(s.get('width', 0)) >= 1000 and abs(int(s.get('width', 0))/max(1,int(s.get('height', 0))) - 16/9) < 0.04 for s in screens), 'desktop 16:9 missing'
    assert any(int(s.get('width', 0)) < 600 and int(s.get('height', 0)) >= 600 for s in screens), 'mobile viewport missing'
    assert scenarios, 'scenarios missing'
    for k in ('regression', 'functional'):
        eligible = [s for s in scenarios if s.get('kind') == k]
        assert eligible, k + ' scenario missing'
        assert all(s.get('name') and s.get('path') and any(x in s for x in ('expect_text','expect_selector','expect_url_pattern')) for s in eligible), k + ' assertion missing'
    assert auth, 'auth missing'
    auth_keys = ('name', 'login_path', 'protected_path', 'protected_selector', 'user_selector', 'pass_selector', 'submit_selector', 'success_selector', 'logout_selector', 'username_env', 'password_env')
    assert all(all(a.get(k) for k in auth_keys) for a in auth), 'auth requires login, rejection, protection and logout selectors'
    assert data_checks and all(all(d.get(k) for k in ('name','page_path','selector','api_path','json_path')) for d in data_checks), 'data_checks need UI and independent API assertion'

def evaluate(policy, base_url, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    checks = {k: {'status': 'BLOCKED', 'reason': 'Not executed', 'evidence': []} for k in BROWSER_GATES}
    try:
        validate_policy(policy)
    except Exception as exc:
        return {k: {'status': 'BLOCKED', 'reason': 'Incomplete test configuration: ' + str(exc), 'evidence': []} for k in BROWSER_GATES}
    from playwright.sync_api import sync_playwright
    base = base_url.rstrip('/')
    details = {k: [] for k in BROWSER_GATES}
    evid = {k: [] for k in BROWSER_GATES}
    ok = {k: True for k in BROWSER_GATES}
    browser_errors = []
    with sync_playwright() as pw:
        executable = os.getenv('QA_BROWSER_EXECUTABLE')
        if not executable:
            executable = shutil.which('chromium') or shutil.which('chromium-browser')
        browser = pw.chromium.launch(headless=True, executable_path=executable) if executable else pw.chromium.launch(headless=True)
        try:
            for screen in policy['screens']:
                name = screen['name']
                context = browser.new_context(viewport={'width': int(screen['width']), 'height': int(screen['height'])})
                page = context.new_page()
                page.on('pageerror', lambda err: browser_errors.append('JS exception: '+ str(err)))
                for route in policy['pages']:
                    try:
                        page.goto(base + route['path'], wait_until='domcontentloaded', timeout=30000)
                        page.wait_for_timeout(int(policy.get('render_settle_ms', 500)))
                        path = outdir / f'page-{re.sub("[^a-zA-Z0-9_-]", "_", name)}-{re.sub("[^a-zA-Z0-9_-]", "_", route["path"])}.png'
                        page.screenshot(path=str(path), full_page=True)
                        evid['ui'].append(str(path))
                        for text in route.get('expect_text', []):
                            if page.get_by_text(text, exact=False).count() == 0:
                                raise AssertionError(f'page {route["path"]} missing text: {text}')
                        for css in route.get('selectors', []):
                            if not page.locator(css).first.is_visible():
                                raise AssertionError(f'page {route["path"]} hidden/missing selector: {css}')
                        # 16:9 desktop overflow may be forbidden; mobile can use different policy.
                        if screen.get('no_vertical_scroll', False):
                            scroll = page.evaluate('Math.max(document.documentElement.scrollHeight,document.body.scrollHeight) > window.innerHeight + 3')
                            if scroll:
                                raise AssertionError(f'{name} {route["path"]} vertical overflow')
                        # Detect visibly clipped content; excludes deliberate overflow containers.
                        clipped = page.evaluate('''() => Array.from(document.querySelectorAll('[data-qa-no-clip]'))
                          .filter(e=>e.scrollWidth > e.clientWidth + 2 || e.scrollHeight > e.clientHeight + 2)
                          .slice(0,15).map(e=>e.getAttribute('data-testid')||e.tagName)''')
                        if clipped:
                            raise AssertionError(f'{name} clipped text/layout: {clipped}')
                    except Exception as exc:
                        ok['ui'] = False
                        details['ui'].append(f'{name} {route.get("path")}: {exc}')
                context.close()
            if browser_errors:
                ok['functional'] = False
                details['functional'].extend(browser_errors[:10])
            for scenario in policy['scenarios']:
                kind = scenario['kind']
                if kind not in ('functional', 'regression'):
                    continue
                context = browser.new_context()
                page = context.new_page()
                try:
                    page.goto(base + scenario['path'], wait_until='domcontentloaded')
                    for item in scenario.get('fill', []):
                        page.locator(item['selector']).fill(str(item['value']))
                    if 'click' in scenario:
                        page.locator(scenario['click']).click()
                    if 'expect_text' in scenario:
                        if not page.get_by_text(scenario['expect_text'], exact=False).first.is_visible(timeout=5000):
                            raise AssertionError('Expected visible text not found')
                    if 'expect_selector' in scenario:
                        page.locator(scenario['expect_selector']).wait_for(state='visible', timeout=5000)
                    if 'expect_url_pattern' in scenario:
                        page.wait_for_url(re.compile(scenario['expect_url_pattern']), timeout=5000)
                    if not any(k in scenario for k in ('expect_text', 'expect_selector', 'expect_url_pattern')):
                        raise AssertionError('Scenario lacks any verifiable assertion')
                    screenshot = outdir / ('scenario-' + re.sub('[^a-zA-Z0-9_-]', '_', scenario['name']) + '.png')
                    page.screenshot(path=str(screenshot))
                    evid[kind].append(str(screenshot))
                except Exception as exc:
                    ok[kind] = False
                    details[kind].append(f'{scenario["name"]}: {exc}')
                finally:
                    context.close()
            for cfg in policy['auth']:
                name = cfg['name']
                username = os.getenv(cfg['username_env'])
                password = os.getenv(cfg['password_env'])
                if not username or not password:
                    ok['auth'] = False
                    details['auth'].append(name + ': missing secrets')
                    continue
                context = browser.new_context()
                page = context.new_page()
                try:
                    # Check an unauthenticated user cannot view protected content.
                    page.goto(base + cfg['protected_path'], wait_until='domcontentloaded')
                    if page.locator(cfg['protected_selector']).count() and page.locator(cfg['protected_selector']).first.is_visible():
                        raise AssertionError('Protected information visible without login')
                    # Invalid password must not succeed.
                    page.goto(base + cfg['login_path'], wait_until='domcontentloaded')
                    page.locator(cfg['user_selector']).fill(username)
                    page.locator(cfg['pass_selector']).fill('QA_INVALID_PASSWORD_SHOULD_FAIL_987654')
                    page.locator(cfg['submit_selector']).click()
                    page.wait_for_timeout(500)
                    if page.locator(cfg['success_selector']).count() and page.locator(cfg['success_selector']).first.is_visible():
                        raise AssertionError('Invalid credential logged in')
                    # Correct role must log in and see own information.
                    page.goto(base + cfg['login_path'], wait_until='domcontentloaded')
                    page.locator(cfg['user_selector']).fill(username)
                    page.locator(cfg['pass_selector']).fill(password)
                    page.locator(cfg['submit_selector']).click()
                    page.locator(cfg['success_selector']).wait_for(state='visible', timeout=15000)
                    if cfg.get('logout_selector'):
                        page.locator(cfg['logout_selector']).click()
                        page.goto(base + cfg['protected_path'])
                        if page.locator(cfg['protected_selector']).count() and page.locator(cfg['protected_selector']).first.is_visible():
                            raise AssertionError('Protected data still visible after logout')
                    evid['auth'].append('browser role check: ' + name)
                except Exception as exc:
                    ok['auth'] = False
                    details['auth'].append(name + ': ' + str(exc))
                finally:
                    context.close()
            for cfg in policy['data_checks']:
                context = browser.new_context()
                page = context.new_page()
                try:
                    # Data checks must compare UI against a real independently queried endpoint.
                    page.goto(base + cfg['page_path'], wait_until='domcontentloaded')
                    visible = page.locator(cfg['selector']).first.inner_text().strip()
                    response = context.request.get(base + cfg['api_path'], timeout=15000)
                    if not response.ok:
                        raise AssertionError('API returned ' + str(response.status))
                    expected = str(json_path(response.json(), cfg['json_path'])).strip()
                    if visible != expected:
                        raise AssertionError(f'UI={visible!r} != API={expected!r}')
                    evid['data'].append('UI matched API: ' + cfg['name'])
                except Exception as exc:
                    ok['data'] = False
                    details['data'].append(cfg['name'] + ': ' + str(exc))
                finally:
                    context.close()
        finally:
            browser.close()
    return {k: status(ok[k], details[k] or ['Verified by current browser run'], evid[k]) for k in BROWSER_GATES}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--policy', required=True)
    p.add_argument('--base-url', required=True)
    p.add_argument('--outdir', required=True)
    a = p.parse_args()
    dest = Path(a.outdir).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    checks = {}
    try:
        policy = json.loads(Path(a.policy).read_text(encoding='utf-8'))
        checks = evaluate(policy, a.base_url, dest)
    except Exception as exc:
        checks = {k: {'status': 'BLOCKED', 'reason': type(exc).__name__ + ': ' + str(exc), 'evidence': []} for k in BROWSER_GATES}
    (dest / 'browser-evidence.json').write_text(json.dumps({'checks': checks}, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if all(item['status'] == 'PASS' for item in checks.values()) else 1

if __name__ == '__main__':
    sys.exit(main())
