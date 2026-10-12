"""Test free hosting's fail-closed behavior and SQL compare-and-swap without network."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from threading import Thread
import base64

import trading_65_storage as store
from trading_65 import fresh_state, apply
from trading_65_server import trading_handler

P = {f"{i:02d}": {"character_id": f"{i:02d}",
     "identity_extension": {"姓名": f"模拟{i}"},
     "source_profile": {"年龄": 45, "性别": "男", "学员资历": "新男", "工作_职业": "测试"}}
     for i in range(1, 66)}


class Cursor:
    def __init__(self, row=None, count=0):
        self.row, self.rowcount = row, count

    def fetchone(self):
        return self.row


class FakePostgres:
    def __init__(self, storage):
        self.storage = storage

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, args=()):
        if sql.startswith("CREATE TABLE"):
            return Cursor()
        if sql.startswith("SELECT payload::text"):
            row = self.storage.get("row")
            return Cursor((row["payload"],) if row else None)
        if sql.startswith("SELECT 1"):
            return Cursor((1,))
        if sql.startswith("UPDATE"):
            payload, rev, key, previous = args
            row = self.storage.get("row")
            if row and row["revision"] == previous:
                self.storage["row"] = {"payload": payload, "revision": rev}
                return Cursor(count=1)
            return Cursor(count=0)
        if sql.startswith("INSERT"):
            key, payload, rev = args
            if "row" not in self.storage:
                self.storage["row"] = {"payload": payload, "revision": rev}
                return Cursor(count=1)
            return Cursor(count=0)
        raise AssertionError("Unexpected SQL")


class DurableStorageTests(unittest.TestCase):
    def test_no_database_uses_local_persistence(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"P004_TRADE_DATABASE_URL": ""}):
            path = Path(folder) / "trading-65.json"
            state = fresh_state()
            apply(state, P, "eligibility", {"person_id": "01", "opened": True, "currency": "RON", "funds": 123})
            store.write_trade_state(path, state)
            self.assertTrue(path.exists())
            self.assertEqual(store.read_trade_state(path)["revision"], 1)

    def test_postgres_write_read_restart_and_revision_conflict(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"P004_TRADE_DATABASE_URL": "postgresql://test-only"}):
            path = Path(folder) / "never-write-local.json"
            record = {}
            with patch.object(store, "_connect", side_effect=lambda: FakePostgres(record)):
                self.assertEqual(store.read_trade_state(path)["revision"], 0)
                state = fresh_state()
                apply(state, P, "eligibility", {"person_id": "01", "opened": True, "currency": "RON", "funds": 250})
                store.write_trade_state(path, state)
                self.assertFalse(path.exists(), "Hosted service must not write ephemeral ledger")
                self.assertEqual(store.read_trade_state(path)["eligibility"]["01"]["funds"]["RON"], 250)
                with self.assertRaisesRegex(ValueError, "版本已变化"):
                    store.write_trade_state(path, state)
                apply(state, P, "create_offer", {"symbol": "TLV", "name": "演练", "unit_price": 10,
                    "min_shares": 1, "hold_days": 1, "participant_count": 2})
                store.write_trade_state(path, state)
                self.assertEqual(store.read_trade_state(path)["revision"], 2)

    def test_database_failure_never_falls_back_to_json(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"P004_TRADE_DATABASE_URL": "postgresql://test-only"}):
            path = Path(folder) / "trading-65.json"
            with patch.object(store, "_connect", side_effect=OSError("db offline")):
                with self.assertRaises(OSError):
                    store.read_trade_state(path)
                with self.assertRaises(OSError):
                    store.write_trade_state(path, fresh_state())
            self.assertFalse(path.exists())

    def test_free_host_isolates_unrelated_write_endpoints(self):
        token = base64.b64encode(b"admin:a-very-long-test-only-password").decode()
        headers = {"Authorization": "Basic " + token}
        with tempfile.TemporaryDirectory() as folder:
            with ThreadingHTTPServer(("127.0.0.1", 0), trading_handler(
                    Path(folder), username="admin", password="a-very-long-test-only-password")) as server:
                thread = Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    with urlopen(base + "/healthz") as resp:
                        self.assertEqual(json.load(resp)["status"], "ok")
                    with self.assertRaises(HTTPError) as e:
                        urlopen(base + "/api/trading/sim/state")
                    self.assertEqual(e.exception.code, 401)
                    with urlopen(Request(base + "/api/trading/sim/state", headers=headers)) as resp:
                        self.assertEqual(json.load(resp)["metrics"]["people"], 65)
                    for uri in ("/api/dashboard/summary", "/skill", "/api/trading/state"):
                        with self.assertRaises(HTTPError) as forbidden:
                            urlopen(Request(base + uri, headers=headers))
                        self.assertEqual(forbidden.exception.code, 404)
                    post = Request(base + "/api/prepare", data=b"{}", method="POST",
                        headers={**headers, "Content-Type": "application/json"})
                    with self.assertRaises(HTTPError) as e:
                        urlopen(post)
                    self.assertEqual(e.exception.code, 404)
                finally:
                    server.shutdown()
                    thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
