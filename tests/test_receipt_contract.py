"""Dependency-free contract tests for the Frontier Console response envelope.

These run without network, GPU, secrets, or a FastAPI installation. Importing
the real app.py with a deliberately narrow fake framework exercises the actual
response assembly, receipt hashing, and /api/health semantics.
"""
import hashlib
import importlib.util
import json
import re
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class FakeFastAPI:
    def __init__(self, *args, **kwargs):
        self.paths = []

    def get(self, path, *args, **kwargs):
        self.paths.append(path)
        return lambda handler: handler


class FakeResponse:
    def __init__(self, content=b"", media_type=None, **kwargs):
        self.body = content
        self.headers = {}


def load_app():
    fake_fastapi = types.ModuleType("fastapi")
    fake_fastapi.FastAPI = FakeFastAPI
    fake_responses = types.ModuleType("fastapi.responses")
    fake_responses.Response = FakeResponse
    fake_responses.FileResponse = FakeResponse
    with patch.dict(sys.modules, {
        "fastapi": fake_fastapi, "fastapi.responses": fake_responses
    }):
        spec = importlib.util.spec_from_file_location("szl_frontier_contract", ROOT / "app.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class FrontierConsoleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_app()

    def test_health_is_receipted_and_current(self):
        response = self.module.health()
        payload = json.loads(response.body)
        self.assertEqual(payload["status"], "OK")
        self.assertEqual(payload["data"]["version"], self.module.APP_VERSION)
        self.assertEqual(response.headers["X-SZL-App"], "frontier-console/" + self.module.APP_VERSION)
        self.assertEqual(
            response.headers["X-SZL-Receipt"],
            "sha256:" + hashlib.sha256(response.body).hexdigest(),
        )

    def test_self_hash_matches_source(self):
        self.assertEqual(
            self.module.SELF_SHA256, hashlib.sha256((ROOT / "app.py").read_bytes()).hexdigest()
        )

    def test_failure_envelope_never_becomes_ok(self):
        response = self.module.receipted({"reason": "unavailable"}, status="UNAVAILABLE")
        self.assertEqual(json.loads(response.body)["status"], "UNAVAILABLE")
        self.assertEqual(
            response.headers["X-SZL-Receipt"],
            "sha256:" + hashlib.sha256(response.body).hexdigest(),
        )

    def test_api_routes_are_registered(self):
        for route in ("/api/health", "/api/estate", "/api/hf", "/api/fleet", "/api/mesh", "/api/governance"):
            self.assertIn(route, self.module.app.paths)

    def test_release_version_is_explicit(self):
        self.assertRegex(self.module.APP_VERSION, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
