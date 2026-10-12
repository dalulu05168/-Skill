import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode

from trading_65_server import trading_handler


class LoginTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), trading_handler(
            Path(self.tmp.name), username='tester', password='test-password-123456'))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def request(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        c.request(method, path, body, headers or {})
        r = c.getresponse()
        result = r.status, dict(r.getheaders()), r.read()
        c.close()
        return result

    def test_browser_login_and_api_protection(self):
        status, headers, _ = self.request('GET', '/trading')
        self.assertEqual(status, 303)
        self.assertEqual(headers['Location'], '/login')
        self.assertNotIn('WWW-Authenticate', headers)
        status, _, body = self.request('GET', '/login')
        self.assertEqual(status, 200)
        self.assertIn(b'autocomplete="current-password"', body)
        self.assertEqual(self.request('GET', '/api/trading/sim/state')[0], 401)
        form = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.assertEqual(self.request('POST', '/login', urlencode(
            {'username': 'tester', 'password': 'wrong'}), form)[0], 401)
        status, headers, _ = self.request('POST', '/login', urlencode(
            {'username': 'tester', 'password': 'test-password-123456'}), form)
        self.assertEqual(status, 303)
        cookie = headers['Set-Cookie']
        for flag in ['Secure', 'HttpOnly', 'SameSite=Strict']:
            self.assertIn(flag, cookie)
        auth = {'Cookie': cookie.split(';')[0]}
        self.assertEqual(self.request('GET', '/trading', headers=auth)[0], 200)
        self.assertEqual(self.request('GET', '/api/news', headers=auth)[0], 404)
        self.assertEqual(self.request('GET', '/trading', headers={
            'Cookie': auth['Cookie'] + 'tampered'})[0], 303)

    def test_cross_site_login_rejected(self):
        status, _, _ = self.request('POST', '/login', urlencode(
            {'username': 'tester', 'password': 'test-password-123456'}), {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://evil.example', 'Sec-Fetch-Site': 'cross-site'})
        self.assertEqual(status, 403)

    def test_login_rate_limit(self):
        for _ in range(5):
            self.assertEqual(self.request('POST', '/login', 'username=x&password=y',
                {'Content-Type': 'application/x-www-form-urlencoded'})[0], 401)
        self.assertEqual(self.request('POST', '/login', 'username=x&password=y',
            {'Content-Type': 'application/x-www-form-urlencoded'})[0], 429)


if __name__ == '__main__':
    unittest.main()
