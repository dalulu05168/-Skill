"""Browser form authentication for the isolated trading service only."""
import hashlib
import hmac
import os
import secrets
import time
from http.cookies import SimpleCookie, CookieError
from threading import Lock
from urllib.parse import parse_qs, urlsplit

COOKIE = '__Host-trading_session'
TTL = 8 * 60 * 60

PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nuvexa | Sign in</title><style>
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:#101724;color:#ecf0f7;font:16px system-ui;padding:24px}
main{width:100%;max-width:400px;background:#1b2638;padding:32px;border-radius:16px}
h1{font-size:26px}label{display:block;margin-top:20px}input,button{width:100%;padding:13px;border-radius:8px;font:inherit;margin-top:8px;border:1px solid #657189}button{background:#90c8ff;color:#102033;font-weight:700;margin-top:24px;cursor:pointer}p{color:#b9c7d9;line-height:1.5}.error{color:#ffb5b5}</style>
<main><h1>Nuvexa Trading</h1><p>Private workspace · 65-person simulation</p>ERROR
<form method="post" action="/login"><label for="username">Username</label>
<input id="username" name="username" autocomplete="username" required>
<label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" required>
<button type="submit">Sign in</button></form></main></html>'''


def browser_login(base, username, password):
    secret = secrets.token_bytes(32)
    failures = {}
    lock = Lock()

    class BrowserLogin(base):
        def _authorized(self):
            if super()._authorized():
                return True
            try:
                cookies = SimpleCookie(self.headers.get('Cookie', ''))
                token = cookies[COOKIE].value
                expiry, nonce, signature = token.split('.')
                payload = expiry + '.' + nonce
                expected = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
                remaining = int(expiry) - time.time()
                return 0 < remaining <= TTL and hmac.compare_digest(signature, expected)
            except (KeyError, ValueError, CookieError):
                return False

        def _redirect(self, location, cookie=None):
            self.send_response(303)
            self.send_header('Location', location)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'same-origin')
            if cookie:
                self.send_header('Set-Cookie', cookie)
            self.send_header('Content-Length', '0')
            self.end_headers()

        def _challenge(self):
            if self.command == 'GET' and not urlsplit(self.path).path.startswith('/api/'):
                self._redirect('/login')
            else:
                self.respond(401, {'error': 'Sign in required', 'login': '/login'})

        def _login_page(self, error='', status=200):
            body = PAGE.replace('ERROR', '<p class="error">' + error + '</p>' if error else '').encode()
            self.send_response(status)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'same-origin')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if urlsplit(self.path).path == '/login':
                return self._login_page()
            return super().do_GET()

        def do_POST(self):
            if urlsplit(self.path).path != '/login':
                # Cookie-authenticated mutations must originate from this site.
                if self.headers.get('Cookie') and not self._same_origin():
                    return self.respond(403, {'error': 'Cross-site request rejected'})
                return super().do_POST()
            if not self._same_origin():
                return self.respond(403, {'error': 'Cross-site request rejected'})
            now = time.time()
            # A single shared private account: use a global limit rather than
            # trusting client-provided forwarding headers for client identity.
            with lock:
                recent = [t for t in failures.get('account', []) if now - t < 300]
                if len(recent) >= 5:
                    return self._login_page('Too many attempts. Try again in 5 minutes.', 429)
                recent.append(now)
                failures['account'] = recent
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 4096:
                    raise ValueError()
                if self.headers.get_content_type() != 'application/x-www-form-urlencoded':
                    raise ValueError()
                form = parse_qs(self.rfile.read(length).decode('utf-8'), max_num_fields=4)
                user = form.get('username', [''])[0]
                supplied = form.get('password', [''])[0]
            except (ValueError, UnicodeDecodeError):
                return self._login_page('Invalid sign-in request.', 400)
            if not (hmac.compare_digest(user.encode(), username.encode()) and
                    hmac.compare_digest(supplied.encode(), password.encode())):
                return self._login_page('Incorrect username or password.', 401)
            with lock:
                failures.clear()
            payload = str(int(time.time()) + TTL) + '.' + secrets.token_hex(16)
            signature = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
            cookie = f'{COOKIE}={payload}.{signature}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age={TTL}'
            return self._redirect('/trading', cookie)

        def _same_origin(self):
            origin = self.headers.get('Origin')
            if not origin:
                return self.headers.get('Sec-Fetch-Site') != 'cross-site'
            parsed = urlsplit(origin)
            # Render terminates TLS at its reverse proxy; the upstream Host
            # can differ from the browser's public origin. Trust only the
            # platform-provided external URL, never X-Forwarded-Host.
            external = os.environ.get('RENDER_EXTERNAL_URL', '').rstrip('/')
            if external and origin == external:
                return True
            allowed = parsed.scheme in ('http', 'https') and parsed.netloc == self.headers.get('Host')
            if not allowed:
                self.log_message('Login origin rejected: origin=%r host=%r', origin, self.headers.get('Host'))
            return allowed

    return BrowserLogin
