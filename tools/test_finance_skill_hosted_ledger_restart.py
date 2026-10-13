"""Hosted 65-person ledger persistence, authorization and restart regression."""
import base64
import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import finance_skill_api as api


def credentials():
    token = base64.b64encode(b"admin:test-only-password-not-a-real-secret").decode()
    return {"Authorization": "Basic " + token}


class HostedLedgerRestartTests(unittest.TestCase):
    def test_authenticated_ledger_survives_restart_without_fake_executions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def start():
                srv = ThreadingHTTPServer(("127.0.0.1", 0),
                    api.make_handler(root, public_mode=True, auth_username="admin",
                                     auth_password="test-only-password-not-a-real-secret"))
                thread = threading.Thread(target=srv.serve_forever, daemon=True)
                thread.start()
                return srv, thread, f"http://127.0.0.1:{srv.server_port}"
            def stop(srv, thread):
                srv.shutdown()
                thread.join(timeout=5)
                srv.server_close()
            server, thread, base = start()
            try:
                with self.assertRaises(HTTPError) as denied:
                    urlopen(base + "/api/trading/sim/state")
                self.assertEqual(denied.exception.code, 401)
                with urlopen(Request(base + "/api/trading/sim/state", headers=credentials())) as resp:
                    first = json.load(resp)
                self.assertEqual(first["metrics"]["people"], 65)
                self.assertEqual(first["transactions"], [])
                self.assertFalse((root / "trading-65.json").exists())
                body = json.dumps({"action":"eligibility","person_id":"01","opened":True,
                                   "currency":"RON","funds":250,"frequency":"HIGH",
                                   "required_today":False}).encode()
                with self.assertRaises(HTTPError) as denied:
                    urlopen(Request(base + "/api/trading/sim/action", data=body,
                        headers={"Content-Type":"application/json"},method="POST"))
                self.assertEqual(denied.exception.code, 401)
                headers = {**credentials(), "Content-Type":"application/json",
                           "Origin":"https://127.0.0.1:"+str(server.server_port)}
                with urlopen(Request(base + "/api/trading/sim/action", data=body,
                                    headers=headers,method="POST")) as resp:
                    updated = json.load(resp)
                self.assertEqual(updated["revision"],1)
                self.assertTrue((root / "trading-65.json").is_file())
            finally:
                stop(server, thread)
            server, thread, base = start()
            try:
                with urlopen(Request(base + "/api/trading/sim/state",
                                     headers=credentials())) as resp:
                    state=json.load(resp)
                person = next(p for p in state["people"] if p["id"] == "01")
                self.assertTrue(person["opened"])
                self.assertEqual(person["funds"]["RON"],250)
                self.assertEqual(state["revision"],1)
                self.assertEqual(state["transactions"],[])
            finally:
                stop(server,thread)

if __name__=="__main__":
    unittest.main()
