"""Self-test against a synthetic local fixture, NOT a user's live application."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import gate

HOME = '''<!DOCTYPE html><html><head><meta charset="utf-8"><title>QA fixture</title></head>
<body style="margin:0"><main><h1>QA Sandbox</h1><span data-testid="real-account-count">3</span>
<button data-testid="open-dashboard" onclick="document.getElementById('dashboard').style.display='block'">Open dashboard</button>
<div data-testid="dashboard" style="display:none">Dashboard rendered</div>
<button data-testid="original-bug-action" onclick="document.getElementById('fixed').style.display='block'">Trigger fix</button>
<div id="fixed" style="display:none">Regression fixed</div></main></body></html>'''
LOGIN = '''<!DOCTYPE html><html><body><main><form onsubmit="event.preventDefault();if(this.email.value==='fixture-user'&&this.password.value==='fixture-secret'){document.cookie='auth=1;path=/';location.href='/dashboard'}else{document.getElementById('err').textContent='Denied'}">
<input name="email"><input name="password" type="password"><button type="submit">Login</button><p id="err"></p></form></main></body></html>'''
DASH = '''<!DOCTYPE html><html><body><main><section data-testid="private-dashboard">Protected fixture</section><button data-testid="logout" onclick="document.cookie='auth=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';location.href='/login'">Logout</button></main></body></html>'''

class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = self.path.split('?')[0]
        if route == '/api/public/account-count':
            content = json.dumps({'count': 3}).encode()
            mime = 'application/json'
        elif route == '/login':
            content, mime = LOGIN.encode(), 'text/html'
        elif route == '/dashboard':
            if 'auth=1' not in self.headers.get('Cookie', ''):
                content, mime = LOGIN.encode(), 'text/html'
            else:
                content, mime = DASH.encode(), 'text/html'
        else:
            content, mime = HOME.encode(), 'text/html'
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)
    def log_message(self, *args):
        pass

def browser_can_open_urls():
    import shutil
    policy_dir = Path('/etc/chromium/policies/managed')
    if policy_dir.exists():
        for item in policy_dir.glob('*.json'):
            try:
                obj = json.loads(item.read_text())
                if '*' in obj.get('URLBlocklist', []):
                    return False
            except Exception:
                continue
    return bool(shutil.which('chromium') or shutil.which('chromium-browser') or (Path.home()/'.cache/ms-playwright').exists())

@unittest.skipUnless(browser_can_open_urls(), 'Browser self-test blocked: Chromium policy denies all URLs or browser unavailable')
class BrowserIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        p = {
          'project':'synthetic-test-fixture',
          'commands':{k:[sys.executable,'-c','print("fixture OK")'] for k in ('build','unit','security')},
          'screens':[{'name':'desktop_16_9','width':1440,'height':810,'no_vertical_scroll':True},
                     {'name':'mobile','width':390,'height':844,'no_vertical_scroll':False}],
          'pages':[{'path':'/','expect_text':['QA Sandbox'],'selectors':['main']}],
          'scenarios':[
            {'name':'show-dashboard','kind':'functional','path':'/','click':'[data-testid="open-dashboard"]','expect_selector':'[data-testid="dashboard"]'},
            {'name':'fix-regression','kind':'regression','path':'/','click':'[data-testid="original-bug-action"]','expect_text':'Regression fixed'}],
          'auth':[{'name':'fixture-role','login_path':'/login','protected_path':'/dashboard',
            'protected_selector':'[data-testid="private-dashboard"]','user_selector':'input[name="email"]',
            'pass_selector':'input[name="password"]','submit_selector':'button[type="submit"]',
            'success_selector':'[data-testid="private-dashboard"]','logout_selector':'[data-testid="logout"]',
            'username_env':'QA_USER','password_env':'QA_PASSWORD'}],
          'data_checks':[{'name':'fixture-count','page_path':'/','selector':'[data-testid="real-account-count"]',
                          'api_path':'/api/public/account-count','json_path':'count'}]
        }
        self.policy = self.root / 'policy.json'
        self.policy.write_text(json.dumps(p))
        os.environ['QA_USER']='fixture-user'
        os.environ['QA_PASSWORD']='fixture-secret'
        os.environ['QA_BROWSER_EXECUTABLE']='/usr/bin/chromium'

    def tearDown(self):
        self.tmp.cleanup()
        for k in ('QA_USER','QA_PASSWORD','QA_BROWSER_EXECUTABLE'):
            os.environ.pop(k, None)

    def test_full_browser_acceptance_on_synthetic_fixture(self):
        address = 'http://127.0.0.1:'+str(self.server.server_port)
        output = self.root / 'fresh-report'
        report = gate.run(self.policy, self.root, output, address)
        self.assertEqual('PASS', report['overall'], json.dumps(report['checks'], ensure_ascii=False)[:3600])
        self.assertTrue(list(output.glob('page-*.png')))
        self.assertTrue(list(output.glob('scenario-*.png')))

    def test_missing_actual_ui_text_is_rejected(self):
        p=json.loads(self.policy.read_text())
        p['pages'][0]['expect_text']=['THIS_TEXT_DOES_NOT_EXIST']
        self.policy.write_text(json.dumps(p))
        output=self.root/'failed-report'
        report = gate.run(self.policy, self.root, output, 'http://127.0.0.1:'+str(self.server.server_port))
        self.assertEqual('REJECTED', report['overall'])
        self.assertEqual('FAIL', report['checks']['ui']['status'])

if __name__ == '__main__':
    unittest.main()
