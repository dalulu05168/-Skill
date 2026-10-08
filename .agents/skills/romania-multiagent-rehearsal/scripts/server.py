"""Minimal read-only Render health endpoint for Romanian rehearsal setup.

Does not handle WhatsApp traffic, accept API keys, generate conversations or
publish content. Runtime dependencies are Python standard library only.
"""
from __future__ import annotations
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from engine import preflight, registry


def status():
    info = preflight()
    try:
        count = len(registry())
        profiles_ok = count == 65
    except (ValueError, OSError, json.JSONDecodeError):
        count, profiles_ok = 0, False
    return {
        "service": "romania-multiagent-rehearsal",
        "mode": "setup_only",
        "simulated_persona_count": count,
        "persona_registry_ok": profiles_ok,
        "model_runtime_ready": bool(info["real_llm_test_possible"]),
        "whatsapp_delivery_enabled": False,
        "public_simulation_api_enabled": False
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/healthz", "/readyz"):
            self.send_error(404)
            return
        state = status()
        ok = state["persona_registry_ok"] and (
            self.path == "/healthz" or state["model_runtime_ready"]
        )
        data = json.dumps(state, ensure_ascii=False).encode("utf-8")
        self.send_response(200 if ok else 503)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        return


def serve():
    port = int(os.environ.get("PORT","10000"))
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be valid")
    ThreadingHTTPServer(("0.0.0.0",port),Handler).serve_forever()


if __name__ == "__main__":
    serve()
