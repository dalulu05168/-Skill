"""External Render smoke probe executed from GitHub Actions, not from local CI.

Checks HTTP status and safety invariants. No API keys, no model calls, no
WhatsApp traffic, no user content. Free instance warmup is tolerated.
"""
from __future__ import annotations
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def fetch(url: str, timeout: int = 20):
    try:
        with urlopen(url, timeout=timeout) as response:
            return response.status, response.read(32768)
    except HTTPError as error:
        return error.code, error.read(32768)


def probe(base: str, attempts: int = 14, pause: int = 10) -> dict:
    base = base.rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("Smoke target must be HTTPS")
    last = None
    for attempt in range(attempts):
        try:
            status, raw = fetch(base + "/healthz")
            if status == 200:
                health = json.loads(raw.decode("utf-8"))
                if (health.get("simulated_persona_count") != 65
                        or not health.get("persona_registry_ok")
                        or health.get("whatsapp_delivery_enabled") is not False
                        or health.get("public_simulation_api_enabled") is not False):
                    raise AssertionError("Unsafe or incomplete deployed persona registry")
                ready_status, ready_raw = fetch(base + "/readyz")
                if ready_status not in (200, 503):
                    raise AssertionError(f"Unexpected readiness HTTP status {ready_status}")
                if ready_raw:
                    ready = json.loads(ready_raw.decode("utf-8"))
                    if ready.get("whatsapp_delivery_enabled") is not False:
                        raise AssertionError("WhatsApp delivery unexpectedly enabled")
                missing_status, _ = fetch(base + "/this-route-must-not-exist")
                if missing_status != 404:
                    raise AssertionError(f"Unexpected public endpoint: {missing_status}")
                return {
                    "health_http_status":status, "ready_http_status":ready_status,
                    "nonexistent_route_http_status":missing_status,
                    "simulated_personas":65,
                    "backend_status":"PASS",
                    "real_model_tested":False
                }
            last = f"healthz status {status}"
        except (URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as exc:
            last = type(exc).__name__
        if attempt != attempts - 1:
            time.sleep(pause)
    raise RuntimeError(f"Remote health probe failed after {attempts} tries ({last})")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv)>1 else "https://romania-finance-director.onrender.com"
    result = probe(target)
    print(json.dumps(result,indent=2,ensure_ascii=False))
