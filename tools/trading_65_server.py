"""A strictly isolated public entrypoint for the 65-person simulation.
No newsroom, model generation, skill-memory writes or external-trade controls
are exposed on the free ephemeral instance.
"""
import argparse
import os
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from finance_skill_api import make_handler
from trading_65_storage import check_connection, is_durable

ALLOWED_GET = {
    "/healthz", "/trading", "/api/trading/sim/state",
    "/api/trading/sim/snapshot", "/api/trading/people",
    "/api/trading/profile",
}
ALLOWED_POST = {"/api/trading/sim/action"}


def trading_handler(data_dir, *, username, password):
    base = make_handler(data_dir, public_mode=True, auth_username=username, auth_password=password)

    class TradingOnly(base):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path != "/healthz" and not self._authorized():
                self._challenge()
                return
            if path == "/":
                self.send_response(302)
                self.send_header("Location", "/trading")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if path not in ALLOWED_GET:
                self.respond(404, {"error": "Not available on isolated trading service"})
                return
            return super().do_GET()

        def do_POST(self):
            if not self._authorized():
                self._challenge()
                return
            if urlsplit(self.path).path not in ALLOWED_POST:
                self.respond(404, {"error": "Not available on isolated trading service"})
                return
            return super().do_POST()

    return TradingOnly


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()
    user = os.environ.get("FINANCE_ACCESS_USER", "")
    password = os.environ.get("FINANCE_ACCESS_PASSWORD", "")
    if not user or len(password) < 16:
        parser.error("FINANCE_ACCESS_USER and a 16+ character FINANCE_ACCESS_PASSWORD are mandatory")
    if not is_durable():
        parser.error("P004_TRADE_DATABASE_URL is mandatory; no temporary file fallback")
    try:
        if not check_connection():
            raise RuntimeError("database unavailable")
    except Exception:
        parser.error("Persistent trading database is unavailable; refusing startup")
    os.environ["FINANCE_REQUIRE_DURABLE_STORAGE"] = "1"
    path = Path(os.environ.get("FINANCE_DATA_DIR", "/tmp/p004-trading"))
    path.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port),
                                 trading_handler(path, username=user, password=password))
    print("Isolated authenticated 65-person simulation API listening (external PostgreSQL storage)")
    try:
        server.serve_forever()
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
