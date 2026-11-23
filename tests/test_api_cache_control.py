"""Offline contract: live console telemetry must not be stored by HTTP caches.

This is an HTTP response policy test, not a claim of signed receipts,
source/runtime parity, fleet freshness, or release readiness.
"""
import hashlib
import unittest

from test_receipt_contract import load_app


class CacheControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_app()

    def test_health_does_not_store_live_telemetry(self):
        response = self.module.health()
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")

    def test_unavailable_envelope_is_not_stored(self):
        response = self.module.receipted({"reason": "unavailable"}, status="UNAVAILABLE")
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")

    def test_receipt_remains_raw_body_checksum(self):
        response = self.module.receipted({"source": "synthetic-no-network"})
        self.assertEqual(
            response.headers["X-SZL-Receipt"],
            "sha256:" + hashlib.sha256(response.body).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
