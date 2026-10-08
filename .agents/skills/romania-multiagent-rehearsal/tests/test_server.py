"""Validate safe, read-only endpoints without network or external dependencies."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("ro_safe_server", SCRIPTS / "server.py")
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)


class HealthTests(unittest.TestCase):
    def test_65_personas_and_no_delivery(self):
        state = srv.status()
        self.assertTrue(state["persona_registry_ok"])
        self.assertEqual(state["simulated_persona_count"], 65)
        self.assertFalse(state["whatsapp_delivery_enabled"])
        self.assertFalse(state["public_simulation_api_enabled"])

    def test_no_llm_without_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            state=srv.status()
            self.assertFalse(state["model_runtime_ready"])

    def test_routes_whitelisted(self):
        # No endpoints for creating simulated group messages or publishing to customers.
        self.assertTrue(hasattr(srv.Handler,"do_GET"))
        self.assertFalse(hasattr(srv.Handler,"do_POST"))

if __name__ == "__main__":
    unittest.main()
