"""Hosted 16:9 login must authenticate on server, not in localStorage."""
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import (Request, build_opener, HTTPRedirectHandler)

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import finance_skill_api as api

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class HostedLoginTests(unittest.TestCase):
    def test_login_gate_cookie_and_logout_are_server_backed(self):
        with tempfile.TemporaryDirectory() as folder:
            with ThreadingHTTPServer(("127.0.0.1",0),
                     api.make_handler(Path(folder),public_mode=True,
                                      auth_username="test-editor",
                                      auth_password="long-test-pass-2026")) as server:
                thread=threading.Thread(target=server.serve_forever,daemon=True)
                thread.start()
                root=f"http://127.0.0.1:{server.server_port}"
                opener=build_opener(NoRedirect())
                try:
                    with self.assertRaises(HTTPError) as missing:
                        opener.open(root+"/")
                    self.assertEqual(missing.exception.code,303)
                    self.assertEqual(missing.exception.headers["Location"],"/login")
                    with opener.open(root+"/login") as page:
                        html=page.read().decode("utf-8")
                        self.assertIn('action="/login"',html)
                        self.assertIn('name="password"',html)
                        self.assertIn("aspect-ratio:16/9",html)
                    incorrect=Request(root+"/login",data=urlencode({
                        "username":"test-editor","password":"wrong"}).encode(),
                        headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
                    with self.assertRaises(HTTPError) as bad:
                        opener.open(incorrect)
                    self.assertEqual(bad.exception.code,401)
                    valid=Request(root+"/login",data=urlencode({
                        "username":"test-editor","password":"long-test-pass-2026"}).encode(),
                        headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
                    with self.assertRaises(HTTPError) as accepted:
                        opener.open(valid)
                    self.assertEqual(accepted.exception.code,303)
                    cookie=accepted.exception.headers["Set-Cookie"]
                    self.assertIn("HttpOnly",cookie)
                    self.assertIn("Secure",cookie)
                    self.assertIn("SameSite=Lax",cookie)
                    credential=cookie.split(";",1)[0]
                    with opener.open(Request(root+"/",headers={"Cookie":credential})) as page:
                        self.assertIn("四合一管理工作台",page.read().decode("utf-8"))
                    with opener.open(Request(root+"/image-editor",headers={"Cookie":credential})) as page:
                        self.assertIn("图片编辑工作台",page.read().decode("utf-8"))
                    logout=Request(root+"/logout",data=b"",method="POST",headers={"Cookie":credential})
                    with self.assertRaises(HTTPError) as removed:
                        opener.open(logout)
                    self.assertEqual(removed.exception.code,303)
                    with self.assertRaises(HTTPError) as expired:
                        opener.open(Request(root+"/",headers={"Cookie":credential}))
                    self.assertEqual(expired.exception.code,303)
                finally:
                    server.shutdown()
                    thread.join(timeout=5)
if __name__=="__main__":
    unittest.main()
